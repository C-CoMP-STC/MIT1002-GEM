"""Turn the Moran lab's plate-reader workbook into the tidy growth-curve CSV.

Two steps, both reproducible:

1. ``--from-xlsx PATH`` (run once, when a new workbook arrives): export the data
   sheet of the workbook *verbatim* to ``data/growth_curves/raw/``. The workbook
   itself is not committed -- a binary cannot be reviewed in a diff -- so its
   SHA-256 is recorded in ``data/growth_curves/README.md`` instead.
2. Always: read that raw CSV and write ``data/growth_curves/MIT1002_growth_curves.csv``,
   one row per well per time point, with a commented metadata header.

Every change made between raw and tidy is listed in ``CLEANING_NOTES`` and is
written into the tidy file's header, so the supplement documents itself.

    python code/growth_curves/clean_growth_curves.py
    python code/growth_curves/clean_growth_curves.py --from-xlsx "MIT1002_growth tests_ALL.xlsx"
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.paths import DATA_DIR  # noqa: E402

GROWTH_DIR = DATA_DIR / "growth_curves"
RAW_CSV = GROWTH_DIR / "raw" / "MIT1002_growth_tests_ALL_raw.csv"
TIDY_CSV = GROWTH_DIR / "MIT1002_growth_curves.csv"

#: Name of the data sheet in the workbook (the other sheet is a free-text readme,
#: transcribed into data/growth_curves/README.md).
DATA_SHEET = "MIT1002_growthtests_all"

#: Raw column labels look like "12C_Acetate" or "?C_Mannuronic acid": the carbon
#: concentration in mM C (or "?" for unknown), then the substrate.
LABEL_PATTERN = re.compile(r"^(?P<carbon>\d+|\?)C_(?P<substrate>.+)$")

#: Spelling fixes applied to substrate names. Anything else is kept as written.
SUBSTRATE_FIXES = {"Glucuronic aid": "Glucuronic acid"}

#: The final row of the sheet has no time value. Readings are hourly and the row
#: before it is 72 h, so it is taken to be 73 h. Only four substrates have a
#: reading in that row (all four have readings at every earlier hour).
MISSING_FINAL_TIME_H = 73.0

#: Raw readings have three decimal places; blank subtraction in the spreadsheet
#: left floating-point residue (e.g. 0.0010000000000000009).
OD_DECIMALS = 3

CLEANING_NOTES = [
    "Reshaped from one column per well to one row per well per time point.",
    "Split each column label (e.g. '12C_Acetate') into carbon_mM_C and substrate;",
    "  '?C_' labels have an empty carbon_mM_C (amount too small to weigh).",
    "Numbered replicate wells 1..n within each substrate and concentration, in sheet order.",
    "Corrected the spelling 'Glucuronic aid' to 'Glucuronic acid'.",
    f"Assigned time_h = {MISSING_FINAL_TIME_H:g} to the final sheet row, which had no time value.",
    "Dropped empty cells (wells not read at that time point, because runs had different lengths).",
    f"Rounded OD600 to {OD_DECIMALS} decimal places, the precision of the instrument output.",
]

HEADER = """\
# Supplementary File SX. Growth curves of Alteromonas macleodii MIT1002 on single carbon sources.
#
# Experiment: Christa B. Smith, Moran lab, Department of Marine Sciences, University of Georgia.
# Medium: Minimal Basal Medium (MBM) with L1 trace element solution, plus one carbon source at
#   6, 8 or 12 mM carbon (carbon_mM_C). An empty carbon_mM_C means a few crystals of dry
#   chemical, too little to weigh, were dissolved in ~1 mL of medium and filter-sterilized.
# Pre-culture: rich medium (1/2 YTSS) for ~4 h to early exponential phase; cells washed three
#   times in, and resuspended in, carbon-free minimal medium.
# Inoculum: 1% of total volume.
# Incubation: 28 C with constant shaking in a BioTek Synergy H1 plate reader, 48- or 96-well
#   plates, OD600 read hourly for up to 72 h.
# Blank: OD600 of uninoculated medium was subtracted from each reading, so values near zero
#   or slightly negative are expected for wells without growth.
#
# Columns:
#   substrate    carbon source added
#   carbon_mM_C  concentration in mM carbon (empty = unknown, see above)
#   replicate    replicate well number within substrate and concentration
#   time_h       hours since inoculation
#   OD600        blank-subtracted optical density at 600 nm
#
# Processing (code/growth_curves/clean_growth_curves.py in the MIT1002-GEM repository):
{notes}
#
"""


def export_raw(xlsx: Path) -> None:
    """Write the workbook's data sheet to RAW_CSV with no changes."""
    sheet = pd.read_excel(xlsx, sheet_name=DATA_SHEET, header=None, dtype=object)
    RAW_CSV.parent.mkdir(parents=True, exist_ok=True)
    sheet.to_csv(RAW_CSV, index=False, header=False, lineterminator="\n")
    print(f"Exported {sheet.shape[0]} rows x {sheet.shape[1]} columns to {RAW_CSV}")


def tidy(raw: pd.DataFrame) -> pd.DataFrame:
    """Reshape the raw sheet (first row = labels) into one row per reading."""
    labels = raw.iloc[0].tolist()
    if labels[0] != "Time":
        raise ValueError(f"Expected the first column to be 'Time', got {labels[0]!r}")
    body = raw.iloc[1:].reset_index(drop=True)

    time = pd.to_numeric(body.iloc[:, 0])
    missing = time.isna()
    if missing.sum() > 1 or (missing.any() and not missing.iloc[-1]):
        raise ValueError("Only the final row is expected to lack a time value.")
    if missing.any() and time.iloc[-2] != MISSING_FINAL_TIME_H - 1:
        raise ValueError("Final-row time assumption no longer holds; re-check the sheet.")
    time = time.fillna(MISSING_FINAL_TIME_H)

    replicate_counter: dict[tuple, int] = {}
    pieces = []
    for col, label in enumerate(labels[1:], start=1):
        match = LABEL_PATTERN.match(str(label))
        if match is None:
            raise ValueError(f"Column label {label!r} does not match '<n>C_<substrate>'")
        carbon = None if match["carbon"] == "?" else int(match["carbon"])
        substrate = SUBSTRATE_FIXES.get(match["substrate"], match["substrate"]).strip()
        key = (substrate, carbon)
        replicate_counter[key] = replicate_counter.get(key, 0) + 1

        pieces.append(pd.DataFrame({
            "substrate": substrate,
            "carbon_mM_C": carbon,
            "replicate": replicate_counter[key],
            "time_h": time,
            "OD600": pd.to_numeric(body.iloc[:, col]),
        }))

    out = pd.concat(pieces, ignore_index=True).dropna(subset=["OD600"])
    out["OD600"] = out["OD600"].round(OD_DECIMALS)
    out["carbon_mM_C"] = out["carbon_mM_C"].astype("Int64")
    out["time_h"] = out["time_h"].astype(float)
    return out.sort_values(["substrate", "carbon_mM_C", "replicate", "time_h"],
                           na_position="last").reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--from-xlsx", type=Path,
                        help="Re-export the raw CSV from this workbook first.")
    args = parser.parse_args()

    if args.from_xlsx:
        export_raw(args.from_xlsx)

    raw = pd.read_csv(RAW_CSV, header=None, dtype=object)
    data = tidy(raw)

    notes = "\n".join(f"#   {line}" for line in CLEANING_NOTES)
    with TIDY_CSV.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(HEADER.format(notes=notes))
        data.to_csv(handle, index=False, lineterminator="\n")

    n_conditions = data.groupby(["substrate", "carbon_mM_C"], dropna=False).ngroups
    print(f"Wrote {len(data)} readings ({n_conditions} substrate x concentration "
          f"conditions, {data['substrate'].nunique()} substrates) to {TIDY_CSV}")


if __name__ == "__main__":
    main()
