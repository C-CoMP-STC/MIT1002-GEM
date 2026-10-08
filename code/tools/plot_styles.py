from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager

# Directory holding the vendored Source Sans 3 faces (SIL Open Font License,
# see code/tools/fonts/LICENSE.md). Shipping the font files in the repo means a
# fresh clone renders figures identically instead of silently falling back to
# matplotlib's default DejaVu Sans.
FONT_DIR = Path(__file__).resolve().parent / "fonts"

_FONTS_REGISTERED = False


def _register_fonts():
    """Add the vendored font files to matplotlib's font manager (idempotent)."""
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    for ttf in sorted(FONT_DIR.glob("*.ttf")):
        font_manager.fontManager.addfont(str(ttf))
    _FONTS_REGISTERED = True


def set_manuscript_style(font_size=12):
    """Set the global rcParams shared by every manuscript figure.

    Call this once at the top of a plotting script, BEFORE creating any
    figures or axes. It cannot live inside `set_plot_style` because that
    function takes an Axes that already exists: matplotlib reads rcParams
    when an artist is created, so changing "font.size" afterwards would
    leave the tick labels at whatever size was in effect when the axes were
    drawn. The two functions are deliberately different scopes -- this one
    is global and runs first, `set_plot_style` is per-axes and runs last.

    Sets three things that used to be copy-pasted (inconsistently) across
    the plotting scripts:

    1. Font family. Source Sans 3, vendored under code/tools/fonts/. It is the
       open-licensed sibling of Myriad Pro (same designer, same humanist
       skeleton), which is what ASM journals use for body text and figure
       captions. Myriad Pro itself is kept as the second choice for anyone
       who has it installed, with DejaVu Sans as the last resort.
    2. Font size. Default 9 pt. Aim for 7-8 pt on the printed page after
       the figure is scaled to column width, so in-figure text sits close
       to the ~7.5 pt of the journal's typeset caption. Pass `font_size` to
       override for a figure that is scaled unusually.
    3. Vector text output. `pdf.fonttype`/`ps.fonttype` 42 embeds TrueType
       rather than converting text to Type 3 subsets, which keeps the text
       selectable and editable in Illustrator and avoids the Type 3
       rejections some journals issue at submission.
    """
    _register_fonts()
    matplotlib.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Source Sans 3", "Myriad Pro", "DejaVu Sans"],
            "font.size": font_size,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,  # editable text in Illustrator
            "ps.fonttype": 42,
        }
    )


# Define the colors from the C-CoMP pallette
ccomp_colors = {
    "light_blue": "#3CB3C0",
    "dark_blue": "#024064",
    "orange": "#FF6C2C",
    "light_orange": "#FFBB62",  # Not technically a C-CoMP color, but I used it on my ISME poster
}

# Define the colors for the "Summer I Turned Pretty" palette
summer_colors = {
    "teal": "#5B8C8F",
    "light_blue": "#BBD5E9",
    "green": "#7E9B6B",
    "pink": "#E57E66",
    "dark_pink": "#893625",
    "yellow": "#EBB309",
    "dark_tan": "#C9BC9B",
    "light_tan": "#FBF9EA",
}


# "CO2" with a real subscript 2. Uses the Unicode subscript character (U+2082)
# rather than mathtext ("CO$_2$"): Source Sans 3 and Myriad Pro both draw
# that glyph, so it matches the surrounding text, whereas mathtext would
# typeset it in a different font unless mathtext.fontset is overridden.
CO2_LABEL = "CO\u2082"


# Define the style for the plots (gray axes, no top or right axis lines)
def set_plot_style(g, color="gray"):
    # Make the axis lines the defined color
    g.spines["bottom"].set_color(color)
    g.spines["left"].set_color(color)
    # Make the tick marks the defined color
    g.tick_params(axis="x", colors=color)
    g.tick_params(axis="y", colors=color)
    # Remove the top and right axis lines
    g.spines["top"].set_visible(False)
    g.spines["right"].set_visible(False)
    # Make all text (axis labels, tick labels, title, and legend) the defined color
    g.xaxis.label.set_color(color)
    g.yaxis.label.set_color(color)
    g.title.set_color(color)
    if g.get_legend() is not None:
        g.get_legend().get_title().set_color(color)
        for text in g.get_legend().get_texts():
            text.set_color(color)


def carbon_fates_bar(data, byproduct_colors=None, ax=None, legend_min_fraction=0.0):
    """Stacked bar plot of the fate of carbon: biomass, organic byproducts, CO2.

    By default `data` must have exactly the columns "biomass", "organic_c",
    and "co2", and the organic byproducts are shown as a single lumped bar.

    Pass `byproduct_colors` (an ordered {column_name: color} dict, e.g. from
    `build_byproduct_palette`) to instead split that bar into one segment per
    organic byproduct. `data` must then have a "biomass" and "co2" column
    plus one column per byproduct named in `byproduct_colors` (any columns
    named in `byproduct_colors` but absent from `data` are simply skipped, so
    the same palette can be reused across substrates that release different
    byproducts). Passing the same `byproduct_colors` dict across multiple
    calls keeps a given byproduct's color consistent across figures.

    Pass `ax` to draw into an existing Axes (e.g. one from a figure with a
    custom size); by default pandas makes a new figure.

    Pass `legend_min_fraction` to leave out of the legend any segment that is
    too thin to see: a column is only listed if its largest value is at least
    this fraction of the tallest bar. The segment is still drawn, so the bars
    keep their true heights. Because the cutoff is relative to the tallest
    bar, it works the same for raw and normalized fluxes.
    """
    if byproduct_colors is not None:
        # Check that the required columns are present
        assert "biomass" in data.columns and "co2" in data.columns
        byproduct_cols = [c for c in byproduct_colors if c in data.columns]
        # Check that there aren't any unexpected byproduct columns
        extra_cols = set(data.columns) - set(byproduct_cols) - {"biomass", "co2"}
        assert (
            not extra_cols
        ), f"Columns not found in byproduct_colors palette: {extra_cols}"
        # Set the column order
        data = data[["biomass"] + byproduct_cols + ["co2"]]
        colors = (
            [summer_colors["teal"]]
            + [byproduct_colors[c] for c in byproduct_cols]
            + [summer_colors["yellow"]]
        )
        custom_labels = ["Biomass"] + byproduct_cols + [CO2_LABEL]
    else:
        # Check that the column names are correct
        assert set(data.columns) == set(["co2", "organic_c", "biomass"])
        # Set the column order
        data = data[["biomass", "organic_c", "co2"]]
        colors = [
            summer_colors["teal"],
            summer_colors["light_blue"],
            summer_colors["yellow"],
        ]
        custom_labels = ["Biomass", "Organic C", CO2_LABEL]
    # Plot the stacked bar plot
    g = data.plot(
        kind="bar",
        stacked=True,
        color=colors,
        ax=ax,
    )
    # Only list the segments that are big enough to see somewhere in the plot
    cutoff = legend_min_fraction * data.sum(axis=1).max()
    handles = g.get_legend_handles_labels()[0]
    visible = [
        (handle, label)
        for handle, label, col in zip(handles, custom_labels, data.columns)
        if data[col].abs().max() >= cutoff
    ]
    # Move the legend outside of the plot
    lgd = g.legend(
        [handle for handle, _ in visible],
        [label for _, label in visible],
        bbox_to_anchor=(1.25, 0.5),
        loc="center right",
        borderaxespad=0.0,
        ncol=1,
    )
    # Make the legend text gray too
    for text in lgd.get_texts():
        text.set_color("gray")
    # Adjust the bottom margin
    plt.subplots_adjust(bottom=0.2)
    # Style
    set_plot_style(g)
    # Title the plot and make it gray
    g.set_title("Fate of Carbon", color="gray")

    # Return the plot
    return g
