"""
SMF dissipation sweep: how growth rate responds to a forced sodium leak.

Motility in MIT1002 is thought to be driven by a Na+-powered flagellum, which
spends the sodium motive force (SMF) by letting Na+ back into the cell. The
model has no flagellum, so we stand in for it with a single Na+ import reaction
(Na+[e0] -> Na+[c0]) and force a fixed flux through it by raising its lower
bound. Every forced Na+ has to be pumped back out (by Na+-NQR, or by the Na+/H+
antiporter at the expense of the PMF), so the leak is an energy cost, and the
question is simply how much growth it costs.

For each substrate in SUBSTRATES we grow the model on minimal medium with an
equal amount of carbon (TOTAL_UPTAKE / n_c), step the forced Na+ import through
DISSIPATION_LEVELS, and record the predicted growth rate.

Output
------
results/smf_sweep_results.csv
    One row per (substrate, dissipation level): growth rate, plus a
    `feasible` flag that is False if the model could not grow at that level.

Plot it with plot_smf_sweep.py (Fig. S5).
"""

import sys
from pathlib import Path

import cobra
import pandas as pd

FILE_PATH = Path(__file__).resolve().parent

sys.path.insert(0, str(FILE_PATH.parents[2]))  # make `tools` importable
from tools.media import MEDIA  # noqa: E402
from tools.paths import MODEL_PATH  # noqa: E402

OUT_PATH = FILE_PATH / "results"
OUT_PATH.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
TOTAL_UPTAKE = 60  # mmol C gDW-1 h-1, same as the other simulations in the repo
BIOMASS_RXN = "bio1_biomass"
FLAGELLA_RXN = "flagella_Na_import_c0"

# Forced Na+ import (mmol Na+ gDW-1 h-1). For scale, Na+-NQR pumps ~28-39
# mmol Na+ gDW-1 h-1 out of the cell at zero dissipation on these substrates.
DISSIPATION_LEVELS = list(range(0, 151, 5))

# Three contrasting substrates:
#   glucose    taken up without Na+ (control)
#   glutamate  Na+ symporter; loses growth at the same rate as glucose
#   aspartate  Na+ symporter; shallower decline at first, then the same rate
SUBSTRATES = [
    {"name": "glucose", "met_id": "cpd00027", "n_c": 6},
    {"name": "glutamate", "met_id": "cpd00023", "n_c": 5},
    {"name": "aspartate", "met_id": "cpd00041", "n_c": 4},
]


def add_flagella_reaction(model: cobra.Model) -> None:
    """Add the stand-in flagellar Na+ import reaction (in place, bounds 0-1000)."""
    rxn = cobra.Reaction(FLAGELLA_RXN)
    rxn.name = "Flagellar Na+ import (SMF dissipation)"
    rxn.add_metabolites(
        {
            model.metabolites.cpd00971_e0: -1,
            model.metabolites.cpd00971_c0: 1,
        }
    )
    rxn.bounds = (0.0, 1000.0)
    model.add_reactions([rxn])


def growth_at(model: cobra.Model, substrate: dict, dissipation: float) -> float | None:
    """Growth rate on `substrate` with `dissipation` forced Na+ import, or None
    if the model cannot grow."""
    with model:
        media = MEDIA["minimal"].copy()
        media[f"EX_{substrate['met_id']}_e0"] = TOTAL_UPTAKE / substrate["n_c"]
        model.medium = media
        model.reactions.get_by_id(FLAGELLA_RXN).lower_bound = dissipation
        sol = model.optimize()
    if sol.status != "optimal" or sol.objective_value < 1e-9:
        return None
    return sol.objective_value


def main():
    model = cobra.io.read_sbml_model(str(MODEL_PATH))
    model.objective = BIOMASS_RXN
    add_flagella_reaction(model)

    rows = []
    for sub in SUBSTRATES:
        for lb in DISSIPATION_LEVELS:
            mu = growth_at(model, sub, lb)
            rows.append(
                {
                    "substrate": sub["name"],
                    "dissipation": lb,
                    "feasible": mu is not None,
                    "growth_rate": mu,
                }
            )
        grew = [r for r in rows if r["substrate"] == sub["name"] and r["feasible"]]
        if grew:
            print(
                f"  {sub['name']:<10s} growth {grew[0]['growth_rate']:.3f} -> "
                f"{grew[-1]['growth_rate']:.3f} h-1 at {grew[-1]['dissipation']} "
                "mmol Na+ gDW-1 h-1"
            )
        else:
            print(f"  WARN  {sub['name']} cannot grow at any dissipation level")

    df = pd.DataFrame(rows)
    df.to_csv(OUT_PATH / "smf_sweep_results.csv", index=False)
    print(f"Saved: {OUT_PATH / 'smf_sweep_results.csv'}")


if __name__ == "__main__":
    main()
