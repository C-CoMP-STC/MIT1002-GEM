[![Version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2FC-CoMP-STC%2FMIT1002-GEM%2Freleases%2Flatest&query=%24.tag_name&label=version&color=blue)](https://github.com/C-CoMP-STC/MIT1002-GEM/releases/latest)
[![DOI](https://zenodo.org/badge/514348089.svg)](https://doi.org/10.5281/zenodo.20559168)
[![memote tested](https://img.shields.io/badge/memote-tested-blue.svg?style=plastic)](https://c-comp-stc.github.io/MIT1002-GEM/)

# MIT1002-GEM: A manually curated metabolic model for *Alteromonas macleodii* MIT1002

This repo contains the *Alteromonas macleodii* MIT1002 model, and code associated with its creation, curation, and testing.

The model was generated using GenBank genome for MIT1002 (Accession Number: NZ_JXRW01000001), accessible via KBase.
The narrative for generating the draft model, is available here: https://narrative.kbase.us/narrative/208605

This repo uses GitHub Actions to test and release the model:

1. **Every pull request** (Test-and-Report) runs the tests in `code/test/` -- SBML
   validity, no growth without carbon, the known growth phenotypes, ATP-generating
   cycles, and that no deprecated identifier is back in the model -- and
   regenerates the reports in `code/scripts/results/`.
2. **Release PRs into `main`** (Release: Check) also check the version bump and
   changelog, build the full MEMOTE report, and run the full MACAW suite.
3. **Merging a release into `main`** (Release: Publish) exports the model to every
   format, tags and creates the GitHub release, and publishes the MEMOTE report
   to GitHub Pages.

See "Versioning and releases" in [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md).
To run MACAW locally:
```
python code/scripts/run_macaw.py
```
Its results are written to `code/scripts/results/` with the other generated reports.

## Repository layout

Three directories hold code, and the distinction between them is about *what the
code does*, not what it is about. Please put new code in the matching one.

| Directory | Contains | How it runs |
| --- | --- | --- |
| `code/test/` | Checks that assert something about the model and pass or fail | Automatically, via `pytest` in CI. A failure blocks the PR |
| `code/scripts/` | Code that generates an artifact for a person to look at — a table, a plot, an exported file. No pass/fail | Automatically in CI, writing to `code/scripts/results/` |
| `code/tools/` | Importable functions and definitions, and command-line utilities a curator runs deliberately | By hand, or imported by the above |
| `data/` | Experimental observations, media provenance, and derived tables. See [`data/README.md`](data/README.md) | Read by the above |

Examples of the third kind:

* `code/tools/deprecate.py` — you invoke it yourself when removing a reaction, and
  `code/scripts/export_model.py` and `code/test/test_deprecated.py` both import from it
* `code/tools/media.py` — defines the growth media as importable dictionaries, so
  anything needing a medium does `from tools.media import MEDIA`
* `code/tools/plot_styles.py` — shared colour palettes and figure styling, imported by
  every plotting script so figures stay consistent

The rest of `code/` is curation and analysis work, one folder per piece of work,
each kept together with its own inputs and results:
`code/curation_process/` (the curation history across past PRs),
`code/simulations/`, `code/biomass/`, `code/blast/`, `code/escher/`,
`code/gene_essentiality/`, `code/kegg_maps/` and `code/pangenome/`.
`data/` holds only external inputs -- things received or downloaded, sometimes
with the small script that fetched or cleaned them.

The layout follows [standard-GEM](https://github.com/MetabolicAtlas/standard-GEM).
`code/` is a plain folder, not a Python package, because a package named `code`
would shadow a standard-library module. `pytest.ini` puts `code/` on the path for
the tests and each script adds it itself, so imports stay `from tools.paths
import MODEL_PATH`. Repo locations are defined once, in `code/tools/paths.py`.
The deprecate CLI is run as `PYTHONPATH=code python -m tools.deprecate`.

## Setting Up the Environment
To ensure a smooth setup and avoid system conflicts, follow these steps to create and activate a Python virtual environment before installing dependencies.

1. Check Your Python Version
First, make sure you have Python 3.11 or 3.10 installed.
Run the following command to check your version:
```
python3 --version
```
If it shows Python 3.13, we strongly recommend using Python 3.11 or 3.10, as some dependencies may not yet support Python 3.13.

To install Python 3.11 via Homebrew (if needed), run:
```
brew install python@3.11
```
2. Create a Virtual Environment

Once you have the correct Python version, create a virtual environment:
```
python3.11 -m venv .venv  # Use python3.10 if needed
```
This creates a .venv folder in your project directory, isolating dependencies from the system Python.

3. Activate the Virtual Environment

Before installing packages, activate the virtual environment:

Mac/Linux:
```
source .venv/bin/activate
```
Windows (Command Prompt):
```
.venv\Scripts\activate
```
Windows (PowerShell):
```
.\.venv\Scripts\Activate
```
Your terminal should now show (.venv) at the beginning of the prompt, indicating the environment is active.

4. Upgrade Pip

Inside the virtual environment, upgrade pip to avoid compatibility issues:
```
pip install --upgrade pip setuptools
```
5. Install Dependencies

Now, install all required dependencies:
```
pip install -r requirements.txt
```
If you encounter an error about "externally managed environment", add the following flag:
```
pip install -r requirements.txt --break-system-packages
```
6. Verify Installation

To ensure everything is working correctly, run:
```
python --version  # Should be 3.11 or 3.10
pip list  # Should show installed dependencies
```
If everything looks good, you're ready to start using the project! 🎉

## License

- **Model and data** (`model/`, `data/` and everything else not listed below):
  [CC BY 4.0](LICENSE.md).
- **Code** (`code/`): [MIT](code/LICENSE).

Files obtained from other sources keep their original terms, including:

- the Source Sans 3 fonts in `code/tools/fonts/` (SIL Open Font License; see
  [`code/tools/fonts/LICENSE.md`](code/tools/fonts/LICENSE.md))
- the published media recipes and protocols in `data/media_sources/`
- the supplementary data of Xavier et al. (2017) in `code/biomass/`
- MetaNetX cross-references in the model annotations (CC BY 4.0,
  [MetaNetX](https://www.metanetx.org))
