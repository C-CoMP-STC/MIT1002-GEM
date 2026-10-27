"""Manuscript Fig. 6: carbon fates and CUE across substrates at saturating O2.

A) Fraction of each substrate's carbon uptake going to biomass vs CO2, bars
   ordered by CUE from lowest to highest, so they rise left to right like B.
B) CUE vs substrate degree of reduction (from plot_cue_vs_reduction.py).

Both panels use the O2 bound of plot_cue_vs_reduction.O2_BOUND (50), where no
substrate is O2-limited. Drawn as one figure so the panels share a size,
font scale and substrate names. At 11 in wide with set_manuscript_style()'s
12 pt default, scaling to the ~7 in ASM page width gives ~7.5 pt text.

The standalone panels made by plot_cue_vs_growth.py
(carbon_fates_across_substrates_o2_50_normalized) and plot_cue_vs_reduction.py
are kept for exploration; this is the version for the paper.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from plot_cue_vs_reduction import (
    DISPLAY_NAME,
    IN_PATH,
    O2_BOUND,
    OUT_PATH,
    draw_scatter,
    load_data,
)
from tools.plot_styles import CO2_LABEL, set_plot_style, summer_colors

# Bars need their own name for each substrate (the scatter merges the two
# sugar acids into one label because they sit on the same point).
BAR_NAME = {
    **{k: v for k, v in DISPLAY_NAME.items() if v is not None},
    "Mannuronic Acid": "Mannuronate",
    "Galacturonic Acid": "Galacturonate",
}

# Same colours as carbon_fates_bar, so this matches every other fates plot.
FATE_COLORS = {
    "Biomass": summer_colors["teal"],
    "Organic C": summer_colors["light_blue"],
    CO2_LABEL: summer_colors["yellow"],
}
# Fates thinner than this everywhere are drawn but left out of the legend
# (same rule as plot_cue_vs_growth.LEGEND_MIN_FRACTION). At O2 = 50 this
# hides organic C, whose largest share is ~0.1% of uptake.
LEGEND_MIN_FRACTION = 0.005


def load_fates() -> pd.DataFrame:
    df = pd.read_csv(IN_PATH / "growth_and_cue.csv")
    df = df[np.isclose(df["o2_bound"], O2_BOUND)].copy()
    uptake = df["biomass_c"] + df["organic_c_flux"] + df["co2_flux"]
    fates = pd.DataFrame(
        {
            "Biomass": df["biomass_c"] / uptake,
            "Organic C": df["organic_c_flux"] / uptake,
            CO2_LABEL: df["co2_flux"] / uptake,
        }
    )
    fates.index = df["substrate"].map(lambda s: BAR_NAME.get(s, s))
    # Lowest CUE on the left, so the bars rise left to right like panel B
    order = (1 - fates[CO2_LABEL]).sort_values(kind="stable").index
    return fates.loc[order]


def draw_fates(ax, fates):
    x = np.arange(len(fates))
    bottom = np.zeros(len(fates))
    handles = []
    for fate, color in FATE_COLORS.items():
        bars = ax.bar(x, fates[fate], bottom=bottom, color=color, width=0.8,
                      label=fate)
        bottom += fates[fate].to_numpy()
        if fates[fate].max() >= LEGEND_MIN_FRACTION:
            handles.append(bars)
    ax.set_xticks(x)
    ax.set_xticklabels(fates.index, rotation=60, ha="right",
                       rotation_mode="anchor", fontsize=8)
    ax.set_xlim(-0.6, len(fates) - 0.4)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Fraction of carbon uptake")
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.0),
              ncol=len(handles), frameon=False, fontsize=8,
              handlelength=1, borderaxespad=0.2, columnspacing=1)
    set_plot_style(ax)


def main():
    fig, (ax_a, ax_b) = plt.subplots(
        1, 2, figsize=(11, 4.4), gridspec_kw={"wspace": 0.25}
    )
    draw_fates(ax_a, load_fates())
    rho_all, rho_rest = draw_scatter(ax_b, load_data())

    for ax, letter in [(ax_a, "A"), (ax_b, "B")]:
        ax.text(-0.13, 1.08, letter, transform=ax.transAxes, fontsize=14,
                fontweight="bold", va="bottom", ha="left")

    for ext in ("png", "svg", "pdf"):
        fig.savefig(OUT_PATH / f"fig6.{ext}", dpi=300, bbox_inches="tight")
    print(f"Saved fig6 (rho all = {rho_all:.2f}, excluding aromatics = {rho_rest:.2f})")


if __name__ == "__main__":
    main()
