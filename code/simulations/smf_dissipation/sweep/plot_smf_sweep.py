"""
Fig. S5: growth rate falls as the sodium motive force is dissipated.

Reads results/smf_sweep_results.csv (written by run_smf_sweep.py) and draws
one line per substrate: predicted growth rate against the forced Na+ import
that stands in for a Na+-powered flagellum.

Outputs
-------
figures/growth_vs_smf_dissipation.{png,svg}
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

FILE_PATH = Path(__file__).resolve().parent
IN_PATH = FILE_PATH / "results"
OUT_PATH = FILE_PATH / "figures"
OUT_PATH.mkdir(exist_ok=True)

sys.path.insert(0, str(FILE_PATH.parents[2]))  # make `tools` importable
from tools.plot_styles import set_manuscript_style, set_plot_style, summer_colors  # noqa: E402

# Global figure style (font, sizes, vector text) -- must run before any figure
# or axes is created, see set_manuscript_style's docstring.
set_manuscript_style()

# Legend order and colours. Substrates in the CSV but not listed here are an
# error, so a new substrate in run_smf_sweep.py can't silently go uncoloured.
SUBSTRATE_COLORS = {
    "glucose": summer_colors["teal"],
    "glutamate": summer_colors["pink"],
    "aspartate": summer_colors["yellow"],
}


def main():
    df = pd.read_csv(IN_PATH / "smf_sweep_results.csv")

    unknown = set(df["substrate"]) - set(SUBSTRATE_COLORS)
    if unknown:
        raise ValueError(f"No colour set for substrate(s): {sorted(unknown)}")
    infeasible = df[~df["feasible"]]
    if not infeasible.empty:
        print(f"  WARN  {len(infeasible)} infeasible points not plotted")

    fig, ax = plt.subplots(figsize=(5.5, 4))

    for sub, color in SUBSTRATE_COLORS.items():
        sub_df = df[(df["substrate"] == sub) & df["feasible"]]
        sub_df = sub_df.sort_values("dissipation")
        ax.plot(
            sub_df["dissipation"],
            sub_df["growth_rate"],
            color=color,
            lw=2,
            label=sub.capitalize(),
        )

    ax.set_xlim(0, df["dissipation"].max())
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Forced Na⁺ import (mmol Na⁺ gDW⁻¹ h⁻¹)")
    ax.set_ylabel("Growth rate (h⁻¹)")
    ax.set_title("Growth rate vs. SMF dissipation", fontsize=12, pad=8)
    ax.legend(frameon=False, loc="lower left")

    fig.tight_layout()
    # Set the plot style (gray axes, ticks, labels, title and legend)
    set_plot_style(ax)

    for ext in ("png", "svg"):
        fig.savefig(
            OUT_PATH / f"growth_vs_smf_dissipation.{ext}", dpi=300, bbox_inches="tight"
        )
    plt.close(fig)
    print("Saved: figures/growth_vs_smf_dissipation.png/svg")


if __name__ == "__main__":
    main()
