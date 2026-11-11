"""Work out what kind of release the changes since the last one require.

The versioning rules are in ``.github/CONTRIBUTING.md``. In short:

* **major** -- something users rely on changed: the model's ID or file
  location, or **any growth call** in ``data/known_growth_phenotypes.tsv``
  flipped between the previous release and now;
* **minor** -- the model file changed, but no growth call flipped;
* **patch** -- the model file is unchanged.

The growth-call rule is the reason this module exists: it makes the bump a
measurement instead of a judgement. Both models are scored against the
*current* phenotype table with the shared scorer in :mod:`tools.phenotypes`,
so a row added to the table since the last release is compared like any other
and a change to the data alone never counts as a change to the model.

Every row counts, including those with an ``exclude_reason``: excluding a row
from the accuracy numbers does not stop someone relying on its prediction.
A change between a call and no call (an invalid solve) also counts as a flip.

What cannot be measured is left to the person releasing: renaming reactions or
metabolites someone else uses is breaking, but a rename looks exactly like a
removal plus an addition. The report lists removed and added IDs so that call
can be made with the evidence in front of you.

Typical use, from the repo root::

    PYTHONPATH=code python -m tools.release check
    PYTHONPATH=code python -m tools.release check --bump minor   # exit 1 if too small
    PYTHONPATH=code python -m tools.release next-version --bump minor
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass, field

import pandas as pd
from tools.paths import (
    CHANGELOG_PATH,
    MODEL_PATH,
    MODEL_RELPATH,
    MODEL_RELPATH_HISTORY,
    REPO_ROOT,
    VERSION_PATH,
)

#: Release kinds, smallest first. The order is what "at least" means below.
BUMPS = ("patch", "minor", "major")

_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


# --------------------------------------------------------------------------
# Version numbers
# --------------------------------------------------------------------------


def parse_version(version: str) -> tuple[int, int, int]:
    """Split ``"4.1.0"`` into ``(4, 1, 0)``.

    A leading ``v`` is accepted, because the releases before the standard-GEM
    rename were tagged that way (``v3.1.0``).

    Raises:
        ValueError: If ``version`` is not ``MAJOR.MINOR.PATCH``.
    """
    match = _VERSION_RE.match(version.strip().removeprefix("v"))
    if not match:
        raise ValueError(f"not a MAJOR.MINOR.PATCH version: {version!r}")
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


def bump_version(version: str, bump: str) -> str:
    """Return the version that follows ``version`` for a ``bump`` release.

    >>> bump_version("3.1.0", "major")
    '4.0.0'
    >>> bump_version("4.0.0", "patch")
    '4.0.1'
    """
    if bump not in BUMPS:
        raise ValueError(f"bump must be one of {BUMPS}, not {bump!r}")
    major, minor, patch = parse_version(version)
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def read_version(path: str | os.PathLike = VERSION_PATH) -> str:
    """The version of the latest release, from ``version.txt``."""
    with open(path, encoding="utf-8") as handle:
        version = handle.read().strip()
    parse_version(version)  # fail here, not later, if the file is malformed
    return version


def is_at_least(bump: str, required: str) -> bool:
    """True if a ``bump`` release is big enough for changes needing ``required``."""
    return BUMPS.index(bump) >= BUMPS.index(required)


# --------------------------------------------------------------------------
# Reading the previous release from git
# --------------------------------------------------------------------------


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )


def release_tag(version: str) -> str:
    """The git tag of the release ``version``.

    Tries ``4.0.0`` first (the standard-GEM format) and then ``v4.0.0`` (how
    releases up to 3.1.0 were tagged).

    Raises:
        LookupError: If neither tag exists locally. In CI, check out with
            ``fetch-depth: 0`` so that tags are present.
    """
    plain = version.removeprefix("v")
    for tag in (plain, f"v{plain}"):
        if _git("rev-parse", "--verify", "--quiet", f"refs/tags/{tag}").returncode == 0:
            return tag
    raise LookupError(
        f"no tag {plain!r} or 'v{plain}' in this clone. Fetch tags "
        "(`git fetch --tags`) or pass --against with a ref that exists."
    )


def latest_release_tag() -> tuple[str, str]:
    """The most recent release, as ``(tag, version)``.

    "Most recent" means the highest version number among tags that look like
    ``X.Y.Z`` or ``vX.Y.Z``, not the newest tag by date.

    Raises:
        LookupError: If there are no release tags in this clone.
    """
    best = None
    for tag in _git("tag", "--list").stdout.split():
        try:
            number = parse_version(tag)
        except ValueError:
            continue
        if best is None or number > best[0]:
            best = (number, tag)
    if best is None:
        raise LookupError(
            "no release tags in this clone; fetch them with `git fetch --tags`"
        )
    number, tag = best
    return tag, ".".join(str(part) for part in number)


def model_file_at(ref: str) -> tuple[str, bytes]:
    """The SBML model as committed at ``ref``, and the path it was at.

    Every path in :data:`tools.paths.MODEL_RELPATH_HISTORY` is tried, newest
    first, because older releases have the model at ``model.xml``.

    Raises:
        LookupError: If ``ref`` has the model at none of those paths.
    """
    for relpath in MODEL_RELPATH_HISTORY:
        result = subprocess.run(
            ["git", "show", f"{ref}:{relpath}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            return relpath, result.stdout
    raise LookupError(f"{ref} has no model at any of {MODEL_RELPATH_HISTORY}")


def _read_model(sbml: bytes):
    """Load SBML bytes into a COBRApy model (cobra needs a file)."""
    import cobra

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as handle:
        handle.write(sbml)
        tmp = handle.name
    try:
        return cobra.io.read_sbml_model(tmp)
    finally:
        os.remove(tmp)


# --------------------------------------------------------------------------
# Comparing two models
# --------------------------------------------------------------------------


def diff_growth_calls(previous: pd.DataFrame, current: pd.DataFrame) -> pd.DataFrame:
    """Conditions whose predicted growth call differs between two evaluations.

    Both arguments are outputs of :func:`tools.phenotypes.evaluate_phenotypes`
    run on the same phenotype table.

    Returns:
        One row per flipped condition, with columns ``condition``,
        ``previous`` and ``current`` (``"Yes"``, ``"No"`` or ``None`` for an
        invalid solve), ``experimental`` (the observed ``growth`` value),
        ``agrees_now`` (whether the current call matches the experiment) and
        ``excluded`` (whether the row has an ``exclude_reason``).
    """
    before = previous.set_index("condition")["predicted"]
    after = current.set_index("condition")
    rows = []
    for condition, now in after["predicted"].items():
        then = before.get(condition)
        if pd.isna(then):
            then = None
        if pd.isna(now):
            now = None
        if then == now:
            continue
        experimental = after.at[condition, "growth"]
        rows.append(
            {
                "condition": condition,
                "previous": then,
                "current": now,
                "experimental": experimental,
                "agrees_now": now is not None and now == experimental,
                "excluded": bool(after.at[condition, "exclude_reason"]),
            }
        )
    columns = [
        "condition",
        "previous",
        "current",
        "experimental",
        "agrees_now",
        "excluded",
    ]
    return pd.DataFrame(rows, columns=columns)


@dataclass
class ReleaseCheck:
    """Everything that decides the bump, and the bump it decides."""

    against: str
    previous_path: str
    model_changed: bool
    previous_id: str
    current_id: str
    flips: pd.DataFrame
    removed_reactions: list[str] = field(default_factory=list)
    added_reactions: list[str] = field(default_factory=list)
    removed_metabolites: list[str] = field(default_factory=list)
    added_metabolites: list[str] = field(default_factory=list)

    @property
    def major_reasons(self) -> list[str]:
        """Why this has to be a major release, if it does."""
        reasons = []
        if self.previous_path != MODEL_RELPATH:
            reasons.append(f"model file moved: {self.previous_path} -> {MODEL_RELPATH}")
        if self.previous_id != self.current_id:
            reasons.append(f"model ID changed: {self.previous_id} -> {self.current_id}")
        if len(self.flips):
            reasons.append(f"{len(self.flips)} growth call(s) flipped")
        return reasons

    @property
    def required(self) -> str:
        """The smallest bump these changes allow."""
        if self.major_reasons:
            return "major"
        if self.model_changed:
            return "minor"
        return "patch"


def check_release(
    against: str | None = None, phenotypes: pd.DataFrame | None = None
) -> ReleaseCheck:
    """Compare the working-tree model with the one released at ``against``.

    Args:
        against: A git ref for the previous release. Defaults to the tag of
            the version in ``version.txt``.
        phenotypes: Phenotype table to score both models on; defaults to the
            current ``data/known_growth_phenotypes.tsv``.
    """
    import cobra
    from tools.phenotypes import evaluate_phenotypes, load_phenotypes

    if against is None:
        against = release_tag(read_version())
    if phenotypes is None:
        phenotypes = load_phenotypes()

    previous_path, previous_sbml = model_file_at(against)
    with open(MODEL_PATH, "rb") as handle:
        current_sbml = handle.read()

    previous = _read_model(previous_sbml)
    current = cobra.io.read_sbml_model(str(MODEL_PATH))

    flips = diff_growth_calls(
        evaluate_phenotypes(previous, phenotypes),
        evaluate_phenotypes(current, phenotypes),
    )

    prev_rxns = {r.id for r in previous.reactions}
    curr_rxns = {r.id for r in current.reactions}
    prev_mets = {m.id for m in previous.metabolites}
    curr_mets = {m.id for m in current.metabolites}
    return ReleaseCheck(
        against=against,
        previous_path=previous_path,
        model_changed=previous_sbml != current_sbml,
        previous_id=previous.id,
        current_id=current.id,
        flips=flips,
        removed_reactions=sorted(prev_rxns - curr_rxns),
        added_reactions=sorted(curr_rxns - prev_rxns),
        removed_metabolites=sorted(prev_mets - curr_mets),
        added_metabolites=sorted(curr_mets - prev_mets),
    )


def _cell(text: str) -> str:
    """Escape a value for a Markdown table cell (condition keys contain ``|``)."""
    return str(text).replace("|", "\\|")


def flips_table(flips: pd.DataFrame) -> list[str]:
    """The flipped growth calls as Markdown table lines."""
    lines = [
        "| Condition | Previous | Now | Experiment | Agrees now | Excluded |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in flips.itertuples():
        lines.append(
            f"| {_cell(row.condition)} | {row.previous or 'invalid'} | "
            f"{row.current or 'invalid'} | {row.experimental} | "
            f"{'yes' if row.agrees_now else 'no'} | "
            f"{'yes' if row.excluded else ''} |"
        )
    return lines


def format_report(result: ReleaseCheck) -> str:
    """A Markdown report, readable in a terminal and as a PR comment."""
    lines = [f"## Release check against `{result.against}`", ""]
    lines.append(f"**Required bump: {result.required}**")
    lines.append("")
    if result.major_reasons:
        lines += [f"- {reason}" for reason in result.major_reasons]
    elif result.model_changed:
        lines.append("- model file changed; no growth call flipped")
    else:
        lines.append("- model file unchanged")
    lines.append("")

    if len(result.flips):
        lines += ["### Flipped growth calls", "", *flips_table(result.flips), ""]

    lines += [
        "### Identifier changes",
        "",
        (
            "A rename looks like a removal plus an addition. If anything removed "
            "here was renamed rather than dropped, this should be a major release."
        ),
        "",
    ]
    for label, ids in (
        ("Reactions removed", result.removed_reactions),
        ("Reactions added", result.added_reactions),
        ("Metabolites removed", result.removed_metabolites),
        ("Metabolites added", result.added_metabolites),
    ):
        shown = ", ".join(f"`{i}`" for i in ids[:20])
        more = f" and {len(ids) - 20} more" if len(ids) > 20 else ""
        lines.append(
            f"- {label} ({len(ids)}): {shown}{more}" if ids else f"- {label}: none"
        )
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Changelog
# --------------------------------------------------------------------------

#: The top of ``CHANGELOG.md``; entries are inserted below it, newest first.
CHANGELOG_HEADER = (
    "# Changelog\n\n"
    "All notable changes to MIT1002-GEM, newest first. The versioning rules are in\n"
    "[`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md). Each entry is generated\n"
    "by `python -m tools.release prepare` when the release is prepared.\n"
)

_PR_MERGE_RE = re.compile(r"^Merge pull request #(\d+) from [^/\s]+/(\S+)")
_CONVENTIONAL_RE = re.compile(
    r"^(?P<kind>[A-Za-z]+)(\([^)]*\))?(?P<bang>!)?: ?(?P<text>.+)"
)

#: Change kinds left out of the changelog when they are direct commits rather
#: than pull requests: CI bookkeeping ("chore: add Test-and-Report results") and
#: the version bump itself ("release: 4.0.0").
SKIPPED_DIRECT_KINDS = ("chore", "release")


@dataclass
class Change:
    """One line of the changelog: a merged pull request or a direct commit."""

    kind: str
    title: str
    pr: int | None
    touches_model: bool
    breaking: bool = False

    def markdown(self) -> str:
        ref = f" (#{self.pr})" if self.pr else ""
        flag = " **(breaking)**" if self.breaking else ""
        return f"- **{self.kind}**: {self.title}{ref}{flag}"


def parse_conventional(subject: str) -> tuple[str, str, bool]:
    """Split ``"fix!: drop rxn00001"`` into ``("fix", "drop rxn00001", True)``.

    Subjects that are not conventional commits come back with kind ``"other"``.
    """
    match = _CONVENTIONAL_RE.match(subject.strip())
    if not match:
        return "other", subject.strip(), False
    return match["kind"].lower(), match["text"].strip(), bool(match["bang"])


def parse_pr_title(body: str, branch: str) -> tuple[str, str, bool]:
    """Kind, title and breaking flag of a merged PR, from its merge commit.

    GitHub puts the PR title in the first line of the merge commit's body. A
    title GitHub made up from the branch name ("Feat/gapfill pep") is not a
    conventional commit, so the kind is taken from the branch prefix instead.
    """
    title = next((line.strip() for line in body.splitlines() if line.strip()), branch)
    kind, text, breaking = parse_conventional(title)
    if kind == "other" and "/" in branch:
        kind = branch.split("/", 1)[0].lower()
        text = re.sub(r"^[A-Za-z]+/", "", title).strip()
    return kind, text, breaking


def _touches_model(parent: str, commit: str) -> bool:
    changed = _git("diff", "--name-only", parent, commit, "--", *MODEL_RELPATH_HISTORY)
    return bool(changed.stdout.strip())


def changes_since(ref: str, until: str = "HEAD") -> list[Change]:
    """What was merged into the current branch since ``ref``.

    Walks the first-parent history, so each merged pull request is one entry
    (titled with the PR title, which GitHub puts in the merge commit's body)
    rather than one per commit inside it. Commits pushed directly to the
    branch are listed on their own, except bookkeeping kinds in
    :data:`SKIPPED_DIRECT_KINDS`. ``Merge branch ...`` commits are skipped.
    """
    log = _git(
        "log", "--first-parent", "--format=%H%x1f%P%x1f%s%x1f%b%x1e", f"{ref}..{until}"
    )
    changes = []
    for record in filter(None, (r.strip("\n") for r in log.stdout.split("\x1e"))):
        sha, parents, subject, body = record.split("\x1f")
        parents = parents.split()
        merge = _PR_MERGE_RE.match(subject)
        if merge:
            pr, branch = int(merge[1]), merge[2]
            kind, text, breaking = parse_pr_title(body, branch)
            changes.append(
                Change(kind, text, pr, _touches_model(parents[0], sha), breaking)
            )
        elif len(parents) > 1 or subject.startswith("Merge "):
            continue
        else:
            kind, text, breaking = parse_conventional(subject)
            if kind in SKIPPED_DIRECT_KINDS:
                continue
            parent = parents[0] if parents else ref
            changes.append(
                Change(kind, text, None, _touches_model(parent, sha), breaking)
            )
    return changes


def changelog_entry(
    version: str, date: str, changes: Sequence[Change], check: ReleaseCheck
) -> str:
    """The ``CHANGELOG.md`` section for one release."""
    previous = check.against.removeprefix("v")
    lines = [f"## {version} - {date}", ""]
    lines.append(f"Compared with {previous}: **{check.required}** release.")
    lines.append("")
    if check.major_reasons:
        lines += [f"- {reason}" for reason in check.major_reasons]
        lines.append("")

    model = [c for c in changes if c.touches_model]
    other = [c for c in changes if not c.touches_model]
    if model:
        lines += ["### Changes to the model", "", *(c.markdown() for c in model), ""]
    if other:
        lines += ["### Other changes", "", *(c.markdown() for c in other), ""]
    if len(check.flips):
        lines += [
            f"### Growth calls changed since {previous}",
            "",
            *flips_table(check.flips),
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def changelog_section(version: str, path: str | os.PathLike = CHANGELOG_PATH) -> str:
    """The body of the ``CHANGELOG.md`` entry for ``version``, for release notes.

    Raises:
        LookupError: If the changelog has no entry for ``version``.
    """
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    match = re.search(
        rf"^## {re.escape(version)}(?: [^\n]*)?\n(.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not match:
        raise LookupError(f"CHANGELOG.md has no entry for {version}")
    return match.group(1).strip() + "\n"


def prepend_changelog(entry: str, path: str | os.PathLike = CHANGELOG_PATH) -> None:
    """Insert ``entry`` at the top of the changelog, creating it if needed."""
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except FileNotFoundError:
        text = CHANGELOG_HEADER
    first = text.find("\n## ")
    if first == -1:
        text = text.rstrip() + "\n\n" + entry
    else:
        text = text[: first + 1] + entry + "\n" + text[first + 1 :]
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


@dataclass
class PreparedRelease:
    """What :func:`prepare_release` decided and wrote."""

    version: str
    check: ReleaseCheck
    entry: str

    @property
    def pr_body(self) -> str:
        """Release PR description: the changelog entry, then the full check."""
        return (
            f"Release {self.version}. Merging this into `main` publishes it.\n\n"
            f"{self.entry}\n---\n\n{format_report(self.check)}"
        )


class BumpTooSmall(Exception):
    """The requested bump is smaller than the changes require."""


def prepare_release(
    bump: str,
    against: str | None = None,
    date: str | None = None,
    write: bool = True,
) -> PreparedRelease:
    """Check the changes, then bump ``version.txt`` and add the changelog entry.

    Args:
        bump: ``"major"``, ``"minor"`` or ``"patch"``, chosen by the person
            releasing. It must be at least what :func:`check_release` requires.
        against: Ref of the previous release; defaults to its tag.
        date: Release date for the changelog, ``YYYY-MM-DD``; defaults to today.
        write: False to compute everything but change no files.

    Raises:
        BumpTooSmall: If ``bump`` is smaller than the changes require.
        ValueError: If the new version is already tagged.
    """
    import datetime as dt

    current = read_version()
    if against is None:
        against = release_tag(current)
    check = check_release(against)
    if not is_at_least(bump, check.required):
        raise BumpTooSmall(
            f"a {bump} release is too small: the changes since {against} need at "
            f"least {check.required} ({'; '.join(check.major_reasons) or 'model changed'})"
        )

    version = bump_version(current, bump)
    try:
        existing = release_tag(version)
    except LookupError:
        existing = None
    if existing:
        raise ValueError(f"{version} is already released (tag {existing})")

    date = date or dt.datetime.now(dt.timezone.utc).date().isoformat()
    entry = changelog_entry(version, date, changes_since(against), check)
    if write:
        with open(VERSION_PATH, "w", encoding="utf-8") as handle:
            handle.write(version + "\n")
        prepend_changelog(entry)
    return PreparedRelease(version, check, entry)


def bump_between(previous: str, new: str) -> str | None:
    """Which bump turns ``previous`` into ``new``, or None if none does exactly."""
    for bump in BUMPS:
        if bump_version(previous, bump) == new:
            return bump
    return None


@dataclass
class Verification:
    """The result of :func:`verify_release`: what was checked, and what failed."""

    previous_tag: str
    version: str
    bump: str | None
    check: ReleaseCheck | None
    problems: list[str]

    def report(self) -> str:
        if self.problems:
            head = ["## Release checks failed", ""]
            head += [f"- {problem}" for problem in self.problems]
        else:
            head = [f"## Release {self.version} is ready ({self.bump})", ""]
        body = format_report(self.check) if self.check else ""
        return "\n".join(head) + "\n\n" + body


def verify_release(changelog: str | os.PathLike = CHANGELOG_PATH) -> Verification:
    """Check a prepared release before it is merged into ``main``.

    Fails when ``version.txt`` is not exactly one bump past the latest release,
    that version is already tagged, ``CHANGELOG.md`` has no entry for it, or the
    bump is smaller than the changes since the latest release require.
    """
    problems = []
    previous_tag, previous = latest_release_tag()
    version = read_version()

    bump = bump_between(previous, version)
    if bump is None:
        problems.append(
            f"version.txt says {version}, which is not one major, minor or patch "
            f"step after the latest release {previous}. Run the Release: Prepare workflow."
        )
    try:
        problems.append(f"{version} is already released (tag {release_tag(version)}).")
    except LookupError:
        pass

    try:
        with open(changelog, encoding="utf-8") as handle:
            entries = handle.read()
    except FileNotFoundError:
        entries = ""
    if not re.search(rf"^## {re.escape(version)}( |$)", entries, flags=re.MULTILINE):
        problems.append(f"CHANGELOG.md has no entry for {version}.")

    check = check_release(previous_tag)
    if bump and not is_at_least(bump, check.required):
        problems.append(
            f"a {bump} release is too small: the changes since {previous} need at "
            f"least {check.required}."
        )
    return Verification(previous_tag, version, bump, check, problems)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="PYTHONPATH=code python -m tools.release",
        description="Check what kind of release the changes since the last one need.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="compare the model with the last release")
    check.add_argument(
        "--against",
        help="git ref of the previous release (default: the tag for version.txt)",
    )
    check.add_argument(
        "--bump",
        choices=BUMPS,
        help="the bump you intend; exit 1 if the changes need a bigger one",
    )
    check.add_argument("--report", help="also write the Markdown report to this file")

    nxt = sub.add_parser("next-version", help="print the version after version.txt")
    nxt.add_argument("--bump", choices=BUMPS, required=True)

    notes = sub.add_parser(
        "notes", help="print the CHANGELOG.md entry for a version (release notes)"
    )
    notes.add_argument("--version", help="default: the version in version.txt")

    ver = sub.add_parser(
        "verify", help="check a prepared release (run on the release PR)"
    )
    ver.add_argument("--report", help="also write the Markdown report to this file")

    prep = sub.add_parser(
        "prepare",
        help="check, then bump version.txt and add the CHANGELOG.md entry",
    )
    prep.add_argument("--bump", choices=BUMPS, required=True)
    prep.add_argument("--against", help="git ref of the previous release")
    prep.add_argument("--date", help="release date, YYYY-MM-DD (default: today)")
    prep.add_argument("--pr-body", help="write the release PR description here")
    prep.add_argument(
        "--dry-run", action="store_true", help="print the entry and change no files"
    )

    args = parser.parse_args(argv)

    if args.command == "next-version":
        print(bump_version(read_version(), args.bump))
        return 0

    if args.command == "notes":
        try:
            print(changelog_section(args.version or read_version()), end="")
        except LookupError as error:
            print(error, file=sys.stderr)
            return 1
        return 0

    if args.command == "verify":
        verification = verify_release()
        report = verification.report()
        print(report)
        if args.report:
            with open(args.report, "w", encoding="utf-8") as handle:
                handle.write(report)
        return 1 if verification.problems else 0

    if args.command == "prepare":
        try:
            prepared = prepare_release(
                args.bump, args.against, args.date, write=not args.dry_run
            )
        except (BumpTooSmall, ValueError) as error:
            print(f"Not preparing a release: {error}", file=sys.stderr)
            return 1
        print(prepared.entry)
        if args.pr_body:
            with open(args.pr_body, "w", encoding="utf-8") as handle:
                handle.write(prepared.pr_body)
        if not args.dry_run:
            print(f"Wrote version.txt ({prepared.version}) and CHANGELOG.md.")
        return 0

    result = check_release(args.against)
    report = format_report(result)
    print(report)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as handle:
            handle.write(report)
    if args.bump and not is_at_least(args.bump, result.required):
        print(
            f"A {args.bump} release is too small: these changes need at least "
            f"{result.required}.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
