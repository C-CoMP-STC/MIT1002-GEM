The reasoning behind these rules is in docs/continuous-curation.md.

# Contributing Guidelines

## To contribute to the model
1. Make a GitHub account
2. Make a fork/branch of this repo
3. Make your edits to the model on the XML file
4. If you are *removing* a reaction or metabolite, use the deprecation helper rather than deleting it by hand (see below)
5. Open a pull request

## Removing reactions and metabolites

Reactions and metabolites that have been removed from the model are recorded in
[`data/deprecated_identifiers/`](../data/deprecated_identifiers/). Removal is a
curation decision with as much information content as an addition, and recording
it stops the same identifier being re-added or hunted for by someone who found it
in an older figure or script.

Remove things with the helper, which edits the model and updates the list in one
step, and cleans up any metabolite or gene the removal orphaned:

```
PYTHONPATH=code python -m tools.deprecate reaction rxn00196_c0 \
    --reason no_genomic_evidence --dry-run
```

Drop `--dry-run` to actually apply it. `--reason` takes a fixed vocabulary
documented in
[`data/deprecated_identifiers/README.md`](../data/deprecated_identifiers/README.md);
the full reasoning still belongs in the pull request description, which the list
links back to.

You do not need to pass a PR number — you do not have one yet when you are
working on your branch. CI fills it in on every pull request and commits the
result, the same way it stamps the PR number into `code/scripts/results/README.md`.

The identifier lists are also mirrored into the SBML model's `<notes>`, so a
person who downloads only `model/MIT1002-GEM.xml` can still tell that those identifiers were
deliberately removed and where to find the reasons. `code/test/test_deprecated.py`
fails if the model and the lists disagree.

## Versioning and releases

Releases follow [semantic versioning](https://semver.org), `MAJOR.MINOR.PATCH`,
and are tagged without a leading `v` (e.g. `4.0.0`), as standard-GEM requires.
The version of the latest release is in [`version.txt`](../version.txt). Only
the release process changes it; do not edit it in a feature branch.

| Bump | The release... | For example |
| --- | --- | --- |
| **Major** | changes something users of the model rely on: it breaks an identifier or the file layout, **or it flips any growth call** in [`data/known_growth_phenotypes.tsv`](../data/known_growth_phenotypes.tsv) (a condition the previous release predicted growth on now shows no growth, or the reverse) | renaming the model files; a curation that makes the model grow on acetate |
| **Minor** | changes the model without flipping any growth call | fixing GPRs, adding annotations, adding or removing reactions that do not change a call, changing flux values |
| **Patch** | leaves the model file unchanged | code, tests, documentation, CI |

A flipped growth call counts as major because growth predictions are what most
people use a GEM for: a change in one can change someone's downstream result
even when every identifier is the same. It is also checkable, so the bump does
not rest on memory. To see what the changes since the last release require:

```
PYTHONPATH=code python -m tools.release check
```

It compares every condition's predicted growth call with the previous release,
reports the smallest bump allowed, and lists added and removed reaction and
metabolite IDs. A rename looks like a removal plus an addition and cannot be
detected automatically, so check that list: a renamed ID is a major change too.

### Making a release

1. Make sure everything for the release is merged into `develop`.
2. Optionally, preview it locally:
   `PYTHONPATH=code python -m tools.release prepare --bump <kind> --dry-run`.
3. On GitHub, go to **Actions → Release: Prepare → Run workflow**, choose the
   `develop` branch and the kind of release. It refuses a bump smaller than the
   changes need. Otherwise it commits the new `version.txt` and a
   [`CHANGELOG.md`](../CHANGELOG.md) entry to `develop`, and opens a PR from
   `develop` into `main` titled `release: X.Y.Z`.
4. Review the PR: its description lists every merged PR, the growth calls that
   flipped, and the reaction and metabolite IDs added and removed.
5. Wait for Release: Check to pass on the PR. The MACAW job can take hours.
6. Merge it into `main` (with a merge commit, not squash). The Release: Publish workflow then exports
   the model to every format, tags the release `X.Y.Z`, creates the GitHub
   release with the model files attached, and updates the MEMOTE report on
   GitHub Pages.

## standard-GEM

[`.standard-GEM.md`](../.standard-GEM.md) is the
[standard-GEM](https://github.com/MetabolicAtlas/standard-GEM) checklist, and
its first line says which version this repo follows. Edit it only by ticking
or unticking boxes: tick an item once the repo meets it.

When standard-GEM releases a new version, the Standard-GEM-Update workflow
opens an issue (it checks monthly). To update, copy the new upstream file over
ours, use `git diff` to see what changed, re-tick what still holds, work
through the new or reworded items, and commit the checklist last.
