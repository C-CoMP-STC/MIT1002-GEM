"""CUE vs substrate degree of reduction at saturating O2 (Fig. 6B).

FBA's CUE ranking at saturating O2 is the stoichiometric expectation for
MIT1002: what mass, electron and energy balance alone predict. Plotting it
against the substrate's degree of reduction (gamma = 4 - NOSC, electrons per
carbon) shows how much of that ranking substrate chemistry explains and which
substrates deviate because of pathway-specific costs (aromatic ring cleavage
by oxygenases).

Uses the O2 bound shared with the carbon fates bars (SUBSTRATE_ORDER_O2_BOUND
= 50), where no substrate is O2-limited and carbon goes only to biomass or CO2.
Do not pool across O2 levels: under O2 limitation CUE = 1 - CO2/uptake counts
secreted acetate as efficiently used carbon, which swamps the pattern
(calculate_regressions.py pools all levels and gets R^2 = 0.07).
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FILE_PATH = Path(__file__).resolve().parent
sys.path.insert(0, str(FILE_PATH.parents[1]))  # make `tools` importable
from tools.plot_styles import (  # noqa: E402
    set_manuscript_style,
    set_plot_style,
    summer_colors,
)

# Must run before any figure or axes is created (see its docstring).
set_manuscript_style()

IN_PATH = FILE_PATH / "results"
OUT_PATH = FILE_PATH / "figures"
OUT_PATH.mkdir(exist_ok=True)

# Same O2 bound as panel A (carbon_fates_across_substrates_o2_50).
O2_BOUND = 50

# NOSC correction for sulfonates. define_substrate_panel.calculate_nosc uses
# the LaRowe & Van Cappellen (2011) formula, which counts S at -2 (right for
# thiols such as cysteine/methionine). In DHPS the S is a sulfonate (~+4) and
# leaves catabolism as sulfite, so its carbon is far less oxidized than the
# formula says: +1.33 by the formula vs -0.67 from the actual oxidation states
# (C3H7O5S-: 7 H(+1) + 5 O(-2) + S(+4) + charge -1 -> sum over C = -2, /3 C).
NOSC_OVERRIDE = {"cpd23538": -2 / 3}  # DHPS

AROMATIC = "Aromatic catabolism"
POINT_COLOR = summer_colors["teal"]
AROMATIC_COLOR = summer_colors["pink"]
# Different marker so the aromatics still stand out in grayscale, where pink
# and teal are close in lightness.
POINT_MARKER = "o"
AROMATIC_MARKER = "D"

# Shorter display names, and identical points merged into one label.
DISPLAY_NAME = {
    "DHPS (dihydroxypropanesulfonate)": "DHPS",
    "Glycerol-3-phosphate": "Glycerol-3-P",
    "3-methyl-2-oxobutanoic acid": "3-Methyl-2-oxobutanoate",
    "3-hydroxybutyrate": "3-Hydroxybutyrate",
    "Mannuronic Acid": "Mannuronate\nGalacturonate",
    "Galacturonic Acid": None,  # same point as mannuronate, labelled there
}

# Label offsets in points (dx, dy, horizontal alignment), placed by hand.
LABEL_OFFSET = {
    "Glycine": (5, -3, "left"),
    "Aspartate": (5, 2, "left"),
    "Pyruvate": (5, -6, "left"),
    "Mannuronate\nGalacturonate": (-5, 6, "right"),
    "Glutamate": (-5, 2, "right"),
    "Arginine": (5, -3, "left"),
    "Acetate": (-5, 0, "right"),
    "Alanine": (-6, 0, "right"),
    "Galactose": (-5, -4, "right"),
    "Glucose": (-5, 3, "right"),
    "Tyrosine": (5, 0, "left"),
    "Proline": (-5, 4, "right"),
    "3-Methyl-2-oxobutanoate": (5, -5, "left"),
    "3-Hydroxybutyrate": (5, 2, "left"),
    "Lysine": (5, -3, "left"),
    "Phenol": (5, 0, "left"),
    "Glycerol-3-P": (-5, 0, "right"),
    "DHPS": (-5, 2, "right"),
    "Valine": (5, -4, "left"),
    "Leucine": (5, -2, "left"),
    "Isoleucine": (5, 0, "left"),
}


def load_data() -> pd.DataFrame:
    results = pd.read_csv(IN_PATH / "growth_and_cue.csv")
    panel = pd.read_csv(IN_PATH / "substrate_panel.csv")
    df = results[np.isclose(results["o2_bound"], O2_BOUND)].merge(
        panel[["met_id", "nosc", "entry_point"]], on="met_id"
    )
    df["nosc"] = df["met_id"].map(NOSC_OVERRIDE).fillna(df["nosc"])
    df["gamma"] = 4 - df["nosc"]
    df["aromatic"] = df["entry_point"] == AROMATIC
    df["label"] = df["substrate"].map(lambda s: DISPLAY_NAME.get(s, s))
    return df


def spearman(x, y) -> float:
    return pd.Series(x).rank().corr(pd.Series(y).rank())


def draw_scatter(ax, df):
    """Draw the CUE vs degree-of-reduction scatter into `ax`.

    Shared with plot_fig6.py, which puts this next to the carbon fates bars.
    Returns (rho_all, rho_excluding_aromatics)."""
    rest = df[~df["aromatic"]]
    rho_all = spearman(df["gamma"], df["cue"])
    rho_rest = spearman(rest["gamma"], rest["cue"])

    # Least-squares line through the non-aromatic substrates only.
    slope, intercept = np.polyfit(rest["gamma"], rest["cue"], 1)
    xs = np.array([df["gamma"].min() - 0.1, df["gamma"].max() + 0.1])
    ax.plot(xs, slope * xs + intercept, ls="--", lw=0.8, color="gray", zorder=1)

    for aromatic, color, marker, size, name in [
        (False, POINT_COLOR, POINT_MARKER, 28, "Other substrates"),
        (True, AROMATIC_COLOR, AROMATIC_MARKER, 24, "Aromatic (oxygenase-dependent)"),
    ]:
        sub = df[df["aromatic"] == aromatic]
        ax.scatter(sub["gamma"], sub["cue"], s=size, color=color, marker=marker,
                   edgecolor="white", linewidth=0.5, zorder=3, label=name)

    for _, row in df.iterrows():
        if row["label"] is None:
            continue
        dx, dy, ha = LABEL_OFFSET.get(row["label"], (5, 0, "left"))
        ax.annotate(row["label"], (row["gamma"], row["cue"]),
                    xytext=(dx, dy), textcoords="offset points",
                    ha=ha, va="center", fontsize=7)

    ax.set_xlabel("Substrate degree of reduction, γ (e⁻ per C)")
    ax.set_ylabel("CUE")
    ax.set_xlim(2.75, 5.45)

    ax.text(0.02, 0.98,
            f"Spearman ρ = {rho_all:.2f} (all {len(df)})\n"
            f"ρ = {rho_rest:.2f} excluding aromatics",
            transform=ax.transAxes, ha="left", va="top", fontsize=7.5)
    ax.legend(loc="upper left", bbox_to_anchor=(0, 0.89), frameon=False,
              fontsize=7.5, handletextpad=0.3, borderaxespad=0.3)
    set_plot_style(ax)
    return rho_all, rho_rest


def main():
    df = load_data()
    fig, ax = plt.subplots(figsize=(5.5, 4.2))
    rho_all, rho_rest = draw_scatter(ax, df)

    for ext in ("png", "svg"):
        fig.savefig(OUT_PATH / f"cue_vs_degree_of_reduction.{ext}",
                    dpi=300, bbox_inches="tight")
    print(f"rho all = {rho_all:.3f}, rho excluding aromatics = {rho_rest:.3f}, n = {len(df)}")


if __name__ == "__main__":
    main()
