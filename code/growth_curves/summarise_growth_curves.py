"""Summarise each growth curve as an OD600 increase and a provisional growth call.

Reads ``data/growth_curves/MIT1002_growth_curves.csv`` and writes
``results/growth_curve_summary.csv``, one row per substrate x concentration.

The call is **provisional**: it is the rule below applied mechanically, for the
curator to check against the plots before anything is copied into
``data/known_growth_phenotypes.tsv``. This script deliberately does not edit
that file, because changing a growth call changes what the model is tested
against.

Rule (see README.md for the reasoning):

* Each well's increase = peak OD600 (3-point rolling median, to ignore single
  noisy reads) minus its mean OD600 over the first three readings.
* ``Yes`` if every replicate's increase is >= ``YES_THRESHOLD``.
* ``No`` if every replicate's increase is < ``NO_THRESHOLD``.
* ``Unsure`` otherwise (in between, or replicates disagree).

    python code/growth_curves/summarise_growth_curves.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.paths import DATA_DIR  # noqa: E402

TIDY_CSV = DATA_DIR / "growth_curves" / "MIT1002_growth_curves.csv"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
SUMMARY_CSV = RESULTS_DIR / "growth_curve_summary.csv"

#: Clear non-growers (alginate, allantoin, formate, glycolate, xylose, ...) all
#: rise by <= ~0.015, so this sits just above that noise floor.
NO_THRESHOLD = 0.02
#: Comfortably above the noise floor; roughly a quarter of the glucose increase.
YES_THRESHOLD = 0.05

BASELINE_POINTS = 3
SMOOTHING_WINDOW = 3


def load_curves(path: Path = TIDY_CSV) -> pd.DataFrame:
    """Read the tidy CSV, keeping carbon_mM_C as a nullable integer."""
    return pd.read_csv(path, comment="#", dtype={"carbon_mM_C": "Int64"})


def well_increase(well: pd.DataFrame) -> float:
    """Peak (smoothed) OD600 minus the starting OD600 for one well."""
    od = well.sort_values("time_h")["OD600"].reset_index(drop=True)
    baseline = od.iloc[:BASELINE_POINTS].mean()
    peak = od.rolling(SMOOTHING_WINDOW, center=True, min_periods=1).median().max()
    return peak - baseline


def call(increases: pd.Series) -> str:
    if (increases >= YES_THRESHOLD).all():
        return "Yes"
    if (increases < NO_THRESHOLD).all():
        return "No"
    return "Unsure"


def summarise(curves: pd.DataFrame) -> pd.DataFrame:
    keys = ["substrate", "carbon_mM_C"]
    wells = (curves.groupby(keys + ["replicate"], dropna=False)
             .apply(lambda w: pd.Series({"increase": well_increase(w),
                                         "last_time_h": w["time_h"].max()}),
                    include_groups=False)
             .reset_index())
    summary = (wells.groupby(keys, dropna=False)
               .agg(n_replicates=("replicate", "count"),
                    last_time_h=("last_time_h", "max"),
                    increase_mean=("increase", "mean"),
                    increase_min=("increase", "min"),
                    increase_max=("increase", "max"),
                    provisional_call=("increase", call))
               .reset_index())
    for col in ["increase_mean", "increase_min", "increase_max"]:
        summary[col] = summary[col].round(3)
    return summary


def main() -> None:
    summary = summarise(load_curves())
    RESULTS_DIR.mkdir(exist_ok=True)
    summary.to_csv(SUMMARY_CSV, index=False, lineterminator="\n")
    counts = summary["provisional_call"].value_counts().to_dict()
    print(f"Wrote {len(summary)} conditions to {SUMMARY_CSV}: {counts}")


if __name__ == "__main__":
    main()
