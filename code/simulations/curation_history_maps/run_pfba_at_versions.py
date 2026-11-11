"""Run pFBA on past versions of the model, for before/after Escher maps.

Each row of ``versions.tsv`` names a git ref and a growth condition. For each
row this script reads the SBML model as it was committed at that ref (no
checkout needed), applies the condition using the *current* media
definitions, runs pFBA, and writes:

* ``results/<change>_<label>_fluxes.json`` -- reaction ID -> flux, the format
  Escher takes as reaction data (Python package or website upload).
* ``results/<change>_<label>_meta.json`` -- full commit SHA, the path the model
  was at, cobra version, growth rate and key exchanges.
* ``results/summary.tsv`` -- the metadata for every row in one table.

Only the model changes between rows; media and pFBA settings come from the
current code, so before/after differences come from the curation change alone.

Run from anywhere::

    python code/simulations/curation_history_maps/run_pfba_at_versions.py
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import cobra
import cobra.flux_analysis
import pandas as pd
from gem_utilities import media as media_utils

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))  # make `tools` importable
from tools.media import MEDIA  # noqa: E402
from tools.paths import REPO_ROOT  # noqa: E402
from tools.release import model_file_at  # noqa: E402

VERSIONS_PATH = HERE / "versions.tsv"
RESULTS_DIR = HERE / "results"

#: Exchanges reported alongside the growth rate.
REPORTED_EXCHANGES = {"EX_o2": "EX_cpd00007_e0", "EX_co2": "EX_cpd00011_e0"}


def full_sha(ref: str) -> str:
    """Resolve a ref (tag, branch, ``abc123^1``) to its full commit SHA."""
    return subprocess.run(
        ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.strip()


def load_model_at(ref: str) -> tuple[cobra.Model, str]:
    """The model committed at ``ref``, and the repo path it was read from."""
    relpath, sbml = model_file_at(ref)
    # cobra needs a file on disk
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as handle:
        handle.write(sbml)
        tmp = handle.name
    try:
        return cobra.io.read_sbml_model(tmp), relpath
    finally:
        os.remove(tmp)


def set_condition(model: cobra.Model, row: pd.Series) -> None:
    """Apply the medium plus the carbon source at a fixed carbon uptake.

    Same convention as ``simulations/pFBA``: uptake bound = total C uptake /
    number of C atoms in the substrate (60 mmol C = 10 mmol glucose).
    """
    medium = MEDIA[row["medium"]].copy()
    met = model.metabolites.get_by_id(f"{row['carbon_met']}_c0")
    n_carbon = met.elements.get("C")
    if not n_carbon:
        raise ValueError(f"{met.id} has no carbon in its formula")
    medium[f"EX_{row['carbon_met']}_e0"] = float(row["c_uptake_mmolC"]) / n_carbon
    model.medium = media_utils.clean_media(model, medium)


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    versions = pd.read_csv(VERSIONS_PATH, sep="\t", dtype=str)
    summary = []
    for _, row in versions.iterrows():
        stem = f"{row['change']}_{row['label']}"
        sha = full_sha(row["git_ref"])
        print(f"{stem}: {row['git_ref']} -> {sha[:10]}")

        model, relpath = load_model_at(sha)
        objective = [r.id for r in model.reactions if r.objective_coefficient]
        set_condition(model, row)
        fluxes = cobra.flux_analysis.pfba(model).fluxes

        with open(RESULTS_DIR / f"{stem}_fluxes.json", "w") as f:
            json.dump(fluxes.round(6).to_dict(), f, indent=1)

        meta = {
            "change": row["change"],
            "label": row["label"],
            "git_ref": row["git_ref"],
            "commit_sha": sha,
            "model_path_at_commit": relpath,
            "cobra_version": cobra.__version__,
            "medium": row["medium"],
            "carbon_met": row["carbon_met"],
            "c_uptake_mmolC": float(row["c_uptake_mmolC"]),
            "objective": ",".join(objective),
            "growth_rate": round(float(sum(fluxes[r] for r in objective)), 4),
        }
        for name, rxn in REPORTED_EXCHANGES.items():
            meta[name] = round(float(fluxes[rxn]), 4) if rxn in fluxes else None
        with open(RESULTS_DIR / f"{stem}_meta.json", "w") as f:
            json.dump(meta, f, indent=2)
        summary.append(meta)

    pd.DataFrame(summary).to_csv(RESULTS_DIR / "summary.tsv", sep="\t", index=False)
    print(f"Wrote {len(summary)} flux sets to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
