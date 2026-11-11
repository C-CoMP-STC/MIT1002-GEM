"""Plot every growth curve: one panel per substrate, one line per replicate well.

Lines are coloured by carbon concentration. Dashed grey lines mark the
thresholds used for the provisional growth calls in
``summarise_growth_curves.py``, and each panel title carries that call.

Writes ``results/growth_curves.pdf`` and ``results/growth_curves.png``.

    python data/growth_curves/plot_growth_curves.py
"""

import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarise_growth_curves import (  # noqa: E402
    NO_THRESHOLD,
    RESULTS_DIR,
    YES_THRESHOLD,
    load_curves,
    summarise,
)
from tools.plot_styles import set_manuscript_style, set_plot_style  # noqa: E402

N_COLS = 6

#: Colour per concentration (mM C); None is the unknown "?C" amount.
CONC_COLORS = {12: "#1b6ca8", 8: "#e08214", 6: "#4dac26", None: "#9e3d8f"}


def as_conc(value):
    """carbon_mM_C as an int, or None for the unknown ("?C") amount."""
    return None if pd.isna(value) else int(value)


def conc_label(conc) -> str:
    return "Unknown" if conc is None else f"{conc} mM C"


def main() -> None:
    set_manuscript_style(font_size=8)
    curves = load_curves()
    calls = summarise(curves)

    substrates = sorted(curves["substrate"].unique(), key=str.lower)
    n_rows = math.ceil(len(substrates) / N_COLS)
    fig, axes = plt.subplots(n_rows, N_COLS, figsize=(N_COLS * 1.9, n_rows * 1.6),
                             sharex=True, sharey=True)
    axes = axes.ravel()
    ymax = curves["OD600"].max() * 1.05

    for ax, substrate in zip(axes, substrates):
        sub = curves[curves["substrate"] == substrate]
        for (conc, _rep), well in sub.groupby(["carbon_mM_C", "replicate"], dropna=False):
            ax.plot(well["time_h"], well["OD600"], color=CONC_COLORS[as_conc(conc)], lw=0.8, alpha=0.85)
        for y in (NO_THRESHOLD, YES_THRESHOLD):
            ax.axhline(y, color="0.6", lw=0.5, ls="--", zorder=0)

        sub_calls = calls[calls["substrate"] == substrate]
        call_text = ", ".join(
            f"{'?' if as_conc(c) is None else as_conc(c)}: {v}"
            for c, v in zip(sub_calls["carbon_mM_C"], sub_calls["provisional_call"])
        )
        ax.set_title(f"{substrate}\n({call_text})", fontsize=7)
        ax.set_ylim(-0.01, ymax)
        set_plot_style(ax)

    for ax in axes[len(substrates):]:
        ax.set_visible(False)

    fig.supxlabel("Time (h)")
    fig.supylabel("OD600 (blank-subtracted)")
    present = {as_conc(c) for c in curves["carbon_mM_C"].unique()}
    handles = [Line2D([], [], color=CONC_COLORS[c], label=conc_label(c))
               for c in [12, 8, 6, None] if c in present]
    handles.append(Line2D([], [], color="0.6", ls="--", lw=0.5,
                          label=f"Thresholds ({NO_THRESHOLD}, {YES_THRESHOLD})"))
    fig.legend(handles=handles, loc="upper center", ncol=len(handles), frameon=False,
               bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.98))

    RESULTS_DIR.mkdir(exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(RESULTS_DIR / f"growth_curves.{ext}", dpi=200)
    print(f"Wrote {len(substrates)} panels to {RESULTS_DIR}/growth_curves.{{pdf,png}}")


if __name__ == "__main__":
    main()
