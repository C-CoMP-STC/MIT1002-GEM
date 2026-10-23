"""Model size and growth-phenotype agreement for every tagged release.

This replaces the two confusion matrices that used to sit in figure 2A. The
numbers are measured from the model as committed at each release tag, scored
with the shared scorer in :mod:`tools.phenotypes` against the *current*
phenotype table, so every release is judged on the same 52 conditions.

Why score the tags rather than read ``code/curation_process/
phenotype_confusion_over_time.csv``: that file is keyed by PR, not release,
and only covers PRs whose model it has replayed. A release can include model
changes that file has not caught up with (4.0.0 included #453, which it did
not), and figure 2A had already drifted from the release it was labelled with
as a result. Reading the model at the tag removes the mapping step entirely.

Two outputs, from one table of measurements:

* :func:`gather_release_stats` -- one row per release with everything the
  scorer reports. Kept in full because it is cheap and it is the record.
* :func:`paper_table` -- the manuscript view: first release (the draft) and
  latest release side by side, statistics as rows.
"""

from __future__ import annotations

import pandas as pd
from tools.phenotypes import evaluate_phenotypes, summarise
from tools.release import _git, _read_model, model_file_at, parse_version

#: Columns of the full per-release table, in order. Everything after
#: ``genes`` comes straight from :func:`tools.phenotypes.summarise`.
FULL_COLUMNS = [
    "version",
    "tag",
    "date",
    "commit",
    "model_id",
    "reactions",
    "metabolites",
    "genes",
    "n_conditions",
    "n_scored",
    "n_unsure",
    "n_excluded",
    "n_invalid_solve",
    "n_no_uptake_route",
    "true_positive",
    "false_negative",
    "false_positive",
    "true_negative",
    "matches",
    "sensitivity",
    "specificity",
]

#: Rows of the manuscript table: (label, column in the full table). A ``None``
#: column marks a section heading. The four outcome rows are spelled out rather
#: than called TP/FN/FP/TN so the table reads without a legend, and in the
#: same order as the 2x2 grids they replace (growth observed first).
PAPER_ROWS = [
    ("Model size", None),
    ("Reactions", "reactions"),
    ("Metabolites", "metabolites"),
    ("Genes", "genes"),
    ("Growth phenotypes (n = {n})", None),
    ("Matches", "matches"),
    ("Growth observed, growth predicted", "true_positive"),
    ("Growth observed, no growth predicted", "false_negative"),
    ("No growth observed, growth predicted", "false_positive"),
    ("No growth observed, no growth predicted", "true_negative"),
]

STATISTIC_COLUMN = "Statistic"


def release_tags() -> list[tuple[str, str]]:
    """Every release tag as ``(tag, version)``, oldest version first.

    Same rule as :func:`tools.release.latest_release_tag`: anything that parses
    as ``X.Y.Z`` or ``vX.Y.Z`` is a release, ordered by version number.
    """
    found = []
    for tag in _git("tag", "--list").stdout.split():
        try:
            number = parse_version(tag)
        except ValueError:
            continue
        found.append((number, tag))
    if not found:
        raise LookupError(
            "no release tags in this clone; fetch them with `git fetch --tags`"
        )
    return [(tag, ".".join(map(str, number))) for number, tag in sorted(found)]


def measure_release(tag: str, version: str) -> dict:
    """Size and phenotype scores of the model as committed at ``tag``."""
    _, sbml = model_file_at(tag)
    model = _read_model(sbml)
    summary = summarise(evaluate_phenotypes(model))
    date, commit = (
        _git("log", "-1", "--format=%ad %h", "--date=short", tag).stdout.split()
    )
    return {
        "version": version,
        "tag": tag,
        "date": date,
        "commit": commit,
        "model_id": model.id,
        "reactions": len(model.reactions),
        "metabolites": len(model.metabolites),
        "genes": len(model.genes),
        **summary,
    }


def gather_release_stats(tags: list[tuple[str, str]] | None = None) -> pd.DataFrame:
    """Measure every release (or just ``tags``), oldest first."""
    if tags is None:
        tags = release_tags()
    rows = [measure_release(tag, version) for tag, version in tags]
    # Same precision as phenotype_confusion_over_time.csv
    return pd.DataFrame(rows)[FULL_COLUMNS].round(
        {"sensitivity": 4, "specificity": 4}
    )


def _scored_denominator(stats: pd.DataFrame) -> int:
    """The number of scored conditions, which must be the same for every row.

    Every release is scored against the same phenotype table, so a difference
    here means a release produced an invalid solve on a condition the others
    could score -- and then "matches" in two columns would be out of different
    totals. Refuse rather than print a table that cannot be compared across.
    """
    totals = stats["n_scored"].unique()
    if len(totals) != 1:
        raise ValueError(
            f"releases were scored out of different totals {sorted(totals)}; "
            "the match counts are not comparable. Check n_invalid_solve."
        )
    return int(totals[0])


def _release_label(role: str, version: str) -> str:
    # Always "v" + number: the tags themselves switched from v3.1.0 to 4.0.0,
    # and a table reading "v1.0.0" next to "4.0.1" looks like a typo.
    return f"{role} (v{version})"


def paper_table(stats: pd.DataFrame) -> pd.DataFrame:
    """The manuscript table: first release vs latest release.

    ``stats`` is the output of :func:`gather_release_stats`. The first release
    is the oldest row and the current one the newest (``stats`` is ordered by
    version). Values are strings, ready to write, so the CSV and
    the Word file are guaranteed to show the same thing.
    """
    stats = stats.reset_index(drop=True)
    first = stats.iloc[0]
    latest = stats.iloc[-1]
    columns = {
        _release_label("Draft", first["version"]): first,
        _release_label("Current", latest["version"]): latest,
    }

    n_scored = _scored_denominator(stats.loc[[first.name, latest.name]])

    records = []
    for label, column in PAPER_ROWS:
        record = {STATISTIC_COLUMN: label.format(n=n_scored)}
        for header, release in columns.items():
            if column is None:
                record[header] = ""
            elif column == "matches":
                share = round(100 * release["matches"] / n_scored)
                record[header] = f"{int(release['matches'])} ({share}%)"
            else:
                record[header] = str(int(release[column]))
        records.append(record)
    return pd.DataFrame(records)


def section_rows(table: pd.DataFrame) -> list[int]:
    """Row positions in ``table`` that are section headings, not statistics.

    A heading is the only kind of row with no value in any release column.
    """
    values = table.drop(columns=STATISTIC_COLUMN)
    return [i for i, row in enumerate(values.itertuples(index=False)) if not any(row)]
