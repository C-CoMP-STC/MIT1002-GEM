# Code

All code used to build, curate, test and analyse MIT1002-GEM. This folder is
required by [standard-GEM](https://github.com/MetabolicAtlas/standard-GEM),
which asks that it carry a README describing how it is organised.

## Shared code

| Folder | Contains | How it runs |
| --- | --- | --- |
| `test/` | Checks that assert something about the model and pass or fail | `pytest` from the repo root, and in CI. A failure blocks the PR |
| `scripts/` | Code that generates an artifact for a person to look at: a table, a plot, an exported model file | In CI, writing to `scripts/results/`; `python code/scripts/<name>.py` by hand |
| `tools/` | Importable functions and definitions, and command-line utilities a curator runs deliberately | Imported by the above; `PYTHONPATH=code python -m tools.<name>` |

## Curation and analysis work

One folder per piece of work, kept together with its inputs and results.

| Folder | What it is |
| --- | --- |
| `curation_process/` | The model's agreement with growth phenotypes replayed across every merged PR (figure 2). See the README there |
| `simulations/` | Simulations and figures for the manuscript |
| `biomass/` | Building and checking the biomass composition |
| `blast/` | BLAST searches used as gene evidence for curation decisions |
| `gene_essentiality/` | Single-gene knockouts compared against the mutant library in `data/mutant_library/` |
| `escher/` | Hand-built Escher maps of MIT1002 pathways |
| `kegg_maps/` | KEGG pathway maps coloured by model coverage |
| `pangenome/` | Adding reactions from the *Alteromonas* pangenome. A record of how it was done; not runnable as-is (see the commit that moved it) |
