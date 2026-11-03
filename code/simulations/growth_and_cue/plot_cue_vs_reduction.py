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

main() also draws the same plot at two O2-limited conditions, for comparison
with the saturating case (see O2_CONDITIONS): a fixed bound of 20 for every
substrate, and 50% of each substrate's own saturating O2 uptake. Under O2
limitation the CUE caveat above applies, so read those as supplementary.
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

# O2 conditions plotted by main(): (results column to match, level, output
# file suffix, title). "o2_bound" is a fixed uptake bound shared by every
# substrate; "o2_percent" is a percentage of each substrate's own saturating
# O2 uptake (run_growth_cue.O2_PERCENTAGE_LEVLS), so the bound differs per
# substrate but the degree of limitation is the same. The O2 = 50 plot keeps
# its original file name.
O2_CONDITIONS = [
    ("o2_bound", O2_BOUND, "", "O$_2$ bound = 50 (saturating)"),
    ("o2_bound", 20, "_o2_20", "O$_2$ bound = 20"),
    ("o2_percent", 50, "_o2_50pct_saturation",
     "O$_2$ = 50% of each substrate's saturating uptake"),
]

# Float tolerance for matching a level against the results file (o2_percent
# is level / saturation * 100, so 50 can land as 49.99999999999999).
LEVEL_TOL = 1e-6

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

# Points move under O2 limitation, so some labels need re-placing. Keyed by
# the O2_CONDITIONS file suffix; entries override LABEL_OFFSET.
LABEL_OFFSET_OVERRIDES = {
    "_o2_20": {
        "Glycerol-3-P": (-5, 3, "right"),
        "DHPS": (5, -2, "left"),
        "3-Hydroxybutyrate": (-5, -5, "right"),
        "Alanine": (-5, 5, "right"),
        "Glucose": (5, 2, "left"),
        "Galactose": (-5, -5, "right"),
        "3-Methyl-2-oxobutanoate": (-5, -4, "right"),
        "Valine": (5, -4, "left"),
    },
    "_o2_50pct_saturation": {
        "Glucose": (-5, 4, "right"),
        "Galactose": (5, 2, "left"),
        "Alanine": (-5, -3, "right"),
        "3-Methyl-2-oxobutanoate": (-5, -4, "right"),
        "Arginine": (-5, -3, "right"),
    },
}


def load_data(column: str = "o2_bound", level: float = O2_BOUND) -> pd.DataFrame:
    """One row per substrate at the given O2 condition (default: bound = 50,
    which is what plot_fig6.py uses)."""
    results = pd.read_csv(IN_PATH / "growth_and_cue.csv")
    panel = pd.read_csv(IN_PATH / "substrate_panel.csv")
    selected = results[np.isclose(results[column], level, rtol=0, atol=LEVEL_TOL)]
    # Each substrate should appear once; a duplicate would mean a fixed bound
    # happened to coincide with a percentage level (or vice versa).
    dupes = selected["met_id"].duplicated(keep=False)
    if dupes.any():
        raise ValueError(f"{column} = {level} matches more than one row for "
                         f"{sorted(selected.loc[dupes, 'substrate'].unique())}")
    df = selected.merge(panel[["met_id", "nosc", "entry_point"]], on="met_id")
    df["nosc"] = df["met_id"].map(NOSC_OVERRIDE).fillna(df["nosc"])
    df["gamma"] = 4 - df["nosc"]
    df["aromatic"] = df["entry_point"] == AROMATIC
    df["label"] = df["substrate"].map(lambda s: DISPLAY_NAME.get(s, s))
    return df


def spearman(x, y) -> float:
    return pd.Series(x).rank().corr(pd.Series(y).rank())


def draw_scatter(ax, df, label_offset=None):
    """Draw the CUE vs degree-of-reduction scatter into `ax`.

    Shared with plot_fig6.py, which puts this next to the carbon fates bars.
    `label_offset` overrides entries of LABEL_OFFSET for this plot.
    Returns (rho_all, rho_excluding_aromatics)."""
    offsets = {**LABEL_OFFSET, **(label_offset or {})}
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
        dx, dy, ha = offsets.get(row["label"], (5, 0, "left"))
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
    for column, level, suffix, title in O2_CONDITIONS:
        df = load_data(column, level)
        fig, ax = plt.subplots(figsize=(5.5, 4.2))
        rho_all, rho_rest = draw_scatter(
            ax, df, LABEL_OFFSET_OVERRIDES.get(suffix))
        ax.set_title(title, fontsize=8)

        for ext in ("png", "svg"):
            fig.savefig(OUT_PATH / f"cue_vs_degree_of_reduction{suffix}.{ext}",
                        dpi=300, bbox_inches="tight")
        plt.close(fig)
        print(f"{column} = {level}: rho all = {rho_all:.3f}, "
              f"rho excluding aromatics = {rho_rest:.3f}, n = {len(df)}")


if __name__ == "__main__":
    main()
