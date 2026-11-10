from pathlib import Path
from typing import Optional

import cobra
import pandas as pd

FILE_PATH = Path(__file__).resolve().parent

import sys

sys.path.insert(0, str(FILE_PATH.parents[1]))  # make `tools` importable
from tools.paths import DATA_DIR, MODEL_PATH  # noqa: E402

OUT_PATH = FILE_PATH / "results"
OUT_PATH.mkdir(exist_ok=True)

# Entry point into central metabolism = the first central-metabolism
# intermediate the substrate's catabolism produces.
ENTRY_POINT = {
    "cpd00027": "Glycolysis",  # Glucose      → G6P
    "cpd00108": "Glycolysis",  # Galactose    → G1P → G6P
    "cpd00080": "Glycolysis",  # Glycerol-3-P → DHAP
    "cpd00035": "Pyruvate",  # Alanine      → Pyr
    "cpd00033": "Pyruvate",  # Glycine      → Ser → Pyr
    "cpd23538": "Pyruvate",  # DHPS         → Pyr + sulfite
    "cpd00029": "Acetyl-CoA",  # Acetate      → AcCoA
    "cpd00797": "Acetyl-CoA",  # 3-HB         → 2× AcCoA
    "cpd00107": "Acetyl-CoA",  # Leucine      → AcCoA
    "cpd00039": "Acetyl-CoA",  # Lysine       → AcCoA
    "cpd00023": "TCA — α-KG",  # Glutamate    → α-KG
    "cpd00129": "TCA — α-KG",  # Proline      → Glu → α-KG
    "cpd00051": "TCA — α-KG",  # Arginine     → Glu → α-KG
    "cpd00041": "TCA — OAA",  # Aspartate    → OAA
    "cpd00156": "TCA — Succinyl-CoA",  # Valine       → succinyl-CoA
    "cpd00322": "TCA — Succinyl-CoA",  # Isoleucine   → succinyl-CoA
    "cpd00123": "TCA — Succinyl-CoA",  # KIC          → succinyl-CoA
    "cpd00069": "Aromatic catabolism",  # Tyrosine     → fumarate + AcAcCoA
    "cpd00127": "Aromatic catabolism",  # Phenol       → succinyl-CoA + AcCoA
    "cpd01384": "ED - KDPG",  # D-Mannuronate → KDPG
    "cpd00280": "ED - KDPG",  # D-Galacturonate → KDPG
}

def main():
    # Load the model
    model = cobra.io.read_sbml_model(MODEL_PATH)

    # Load the known growth phenotypes table with predicted results
    df = pd.read_csv(DATA_DIR / "known_growth_phenotypes.tsv", sep="\t")

    # Filter the growth phenotypes to keep:
    # substrates where growth is observed
    df = df[df["growth"] == "Yes"]
    # substrates that don't have a comma in the met_id (those are cases where multiple substrates were added together)
    df = df[~df["met_id"].astype(str).str.contains(",", na=True)].copy()

    # Drop rows with duplicate met_id values
    df = df.drop_duplicates(subset=["met_id"], keep="first")

    # Drop the unnecessary columns
    # Keep only "c_source" and "met_id"
    df = df.drop(df.columns.difference(["c_source", "met_id"]), axis=1)

    # Add pyruvate to the substrate panel
    # Franzi tested it in conjunction with other substrates, but not alone
    # Add aspartate and glycine to the substrate panel
    # They were measured in the Prochlorococcus exometabolome, but not tested for Amac growth
    # Only add if they aren't already there
    for name, met_id in [
        ("Pyruvate", "cpd00020"),
        ("Aspartate", "cpd00041"),
        ("Glycine", "cpd00033"),
    ]:
        if met_id not in df["met_id"].values:
            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        [
                            {
                                "minimal_media": "l1",
                                "c_source": name,
                                "met_id": met_id,
                                "growth": "Yes",
                                "pro_exomet": "Yes",
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            )

    # Get a list of reaction IDs in the model for later use
    rxn_ids = {r.id for r in model.reactions}

    # Loop through the substrates (rows) and build a record for each one with the information we want to keep
    records = []
    for _, row in df.iterrows():
        # Extract information from the row, stripping whitespace and converting to strings
        met_id = str(row["met_id"]).strip()
        c_source = str(row["c_source"]).strip()
        media_key = str(row["minimal_media"]).strip()

        # Check that the exchange reaction for this substrate exists in the model
        ex_id = f"EX_{met_id}_e0"
        if ex_id not in rxn_ids:
            print(f"  SKIP (no exchange rxn)  : {c_source} ({met_id})")
            continue

        # Get the metabolite
        met = model.metabolites.get_by_id(f"{met_id}_e0")

        # Get basic information about the metabolite
        n_c = met.elements.get("C", 0)
        model_name = met.name[:-5]  # drop " [e0]" suffix

        # Calculate the NOSC
        nosc = calculate_nosc(met.elements, met.charge)

        # Add the record for this substrate to the list of records
        records.append(
            {
                "name": c_source,
                "name_in_model": model_name,
                "met_id": met_id,
                "exchange_id": ex_id,
                "n_c": n_c,
                "entry_point": ENTRY_POINT.get(met_id, "Other"),
                "nosc": nosc,
            }
        )

    # Convert the list of records to a DataFrame
    substrate_df = pd.DataFrame(records)

    # Save the substrate df
    substrate_df.to_csv(OUT_PATH / "substrate_panel.csv", index=False)


def calculate_nosc(elements: dict, charge: float) -> Optional[float]:
    # Extract the number of atoms of each element, defaulting to 0 if not present
    C = elements.get("C", 0)
    H = elements.get("H", 0)
    N = elements.get("N", 0)
    O = elements.get("O", 0)
    P = elements.get("P", 0)
    S = elements.get("S", 0)

    # Calulate NOSC
    nosc = 4 - ((4 * C) + H - (3 * N) - (2 * O) + (5 * P) - (2 * S) - charge) / C
    return nosc


if __name__ == "__main__":
    main()
