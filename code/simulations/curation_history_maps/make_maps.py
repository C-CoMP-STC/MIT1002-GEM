"""Draw the Escher maps comparing model versions from the pFBA fluxes.

Reads ``versions.tsv`` and the flux files written by
``run_pfba_at_versions.py``, and writes one PNG map per row to
``figures/<change>_<label>.png``. Each map is built as a standalone Escher
HTML page and rendered in headless Chromium (needs ``playwright``; see
README). The HTML is a temporary intermediate; pass ``--keep-html`` to also
save it next to the PNG for interactive inspection.

The before and after maps of one change share a colour scale (see
``reaction_scale``): pink is the largest absolute flux drawn on either map, so
the two panels can be compared directly. Width carries the same information as
colour, so the maps still read without colour vision.

    python code/simulations/curation_history_maps/make_maps.py [--keep-html]
"""

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

import escher
import pandas as pd
from escher import Builder

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))  # make `tools` importable
from tools.paths import CODE_DIR  # noqa: E402
from tools.plot_styles import summer_colors  # noqa: E402

VERSIONS_PATH = HERE / "versions.tsv"
RESULTS_DIR = HERE / "results"
FIGURES_DIR = HERE / "figures"
MAP_DIR = CODE_DIR / "escher"

#: Absolute flux (mmol/gDW/h) drawn in teal; typical central-carbon flux at a
#: 10 mmol/gDW/h glucose uptake. Pink is set per change by reaction_scale().
TEAL_FLUX = 10

#: Metabolite circles: tan from the summer palette, with a darker tan outline
#: (Escher's default is orange).
METABOLITE_FILL = summer_colors["dark_tan"]
METABOLITE_STROKE = "#8C7F5E"

BUILDER_OPTIONS = {
    # "abs": colour/size by |flux|, so a +-1000 loop shows as large either way
    "reaction_styles": ["color", "size", "text", "abs"],
    "reaction_no_data_color": "#EEEEEE",
    "reaction_no_data_size": 6,
    "never_ask_before_quit": True,
    "menu": "zoom",
    "enable_editing": False,
    # Label every node by its "name". relabel_map() sets each reaction's name
    # to its ModelSEED ID; metabolites keep the names stored in the map.
    "identifiers_on_map": "name",
}

# Escher's own colour legend, menus and buttons are HTML laid over the map;
# hide everything except the map SVG before screenshotting. Draw the legend in
# the figure layout instead (Escher's crams the 0 and 10 stops together).
HIDE_OVERLAYS_CSS = """
body * { visibility: hidden !important; }
svg:has(g.reaction), svg:has(g.reaction) * { visibility: visible !important; }
"""


def relabel_map(escher_map: list) -> list:
    """Label reactions by ModelSEED ID; metabolites keep their stored names.

    Escher labels both reactions and metabolites from the same field
    (``identifiers_on_map``), so to mix the two, each reaction's ``name`` is
    overwritten with its ID. Metabolite names are the ones saved in the map.
    """
    _, body = escher_map
    for reaction in body["reactions"].values():
        reaction["name"] = reaction["bigg_id"]
    return escher_map


def escher_css() -> str:
    """Escher's default map stylesheet with the metabolite circles recoloured.

    Escher has no option for the colour of metabolite circles when there is no
    metabolite data; it comes from the map's stylesheet. The ``embedded_css``
    option replaces that whole stylesheet, so this starts from the default one
    built into the installed escher.min.js and changes only the
    metabolite-circle rule. It raises rather than silently drawing orange
    circles if a different Escher version lays the stylesheet out differently.
    """
    js = (Path(escher.__file__).parent / "static" / "escher.min.js").read_text()
    match = re.search(r'"(svg\.escher-svg #mouse-node \{.*?)",this\.map_data', js, re.S)
    if match is None:
        raise RuntimeError("default stylesheet not found in escher.min.js")
    css = json.loads(f'"{match.group(1)}"')  # undo the JS string escaping
    default = (".metabolite-circle {\n  stroke: rgb(162, 69, 16);\n"
               "  fill: rgb(224, 134, 91);\n}")
    if css.count(default) != 1:
        raise RuntimeError("metabolite-circle rule not found in Escher's stylesheet")
    return css.replace(default, (f".metabolite-circle {{\n  stroke: {METABOLITE_STROKE};\n"
                                 f"  fill: {METABOLITE_FILL};\n}}"))


def load_inputs(row: pd.Series) -> tuple[dict, list]:
    """The fluxes and the (relabelled) Escher map for one row of versions.tsv."""
    with open(RESULTS_DIR / f"{row['change']}_{row['label']}_fluxes.json") as f:
        fluxes = json.load(f)
    with open(MAP_DIR / row["escher_map"]) as f:
        escher_map = relabel_map(json.load(f))
    return fluxes, escher_map


def max_drawn_flux(fluxes: dict, escher_map: list) -> float:
    """Largest absolute flux among the reactions drawn on the map."""
    drawn = {r["bigg_id"] for r in escher_map[1]["reactions"].values()}
    return max(abs(v) for k, v in fluxes.items() if k in drawn)


def reaction_scale(max_flux: float) -> list[dict]:
    """Grey at 0, teal at TEAL_FLUX, pink at ``max_flux`` (all absolute)."""
    # If nothing on the maps exceeds TEAL_FLUX, put teal halfway so the
    # stops stay in increasing order.
    teal = min(TEAL_FLUX, max_flux / 2)
    return [
        {"type": "value", "value": 0, "color": "#BBBBBB", "size": 8},
        {"type": "value", "value": teal, "color": summer_colors["teal"], "size": 16},
        {"type": "value", "value": max_flux, "color": summer_colors["pink"], "size": 30},
    ]


def build_map(row: pd.Series, scale: list[dict], out_dir: Path) -> Path:
    """Write the Escher map for one row of versions.tsv as standalone HTML."""
    stem = f"{row['change']}_{row['label']}"
    fluxes, escher_map = load_inputs(row)
    builder = Builder(
        map_json=json.dumps(escher_map),
        reaction_data=fluxes,
        reaction_scale=scale,
        embedded_css=escher_css(),
        **BUILDER_OPTIONS,
    )
    out = out_dir / f"{stem}.html"
    builder.save_html(str(out))
    return out


def html_to_png(html: Path, out: Path, scale: int = 3) -> Path:
    """Render a saved map to PNG with headless Chromium.

    The saved HTML loads Escher's JavaScript from unpkg. That request is
    answered from the copy shipped inside the installed escher package, so
    rendering works offline and always uses the same Escher version as the
    Python package that wrote the HTML.
    """
    import escher
    from playwright.sync_api import sync_playwright

    escher_js = Path(escher.__file__).parent / "static" / "escher.min.js"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=scale,
                                viewport={"width": 1600, "height": 1200})
        page.route("**/escher.min.js", lambda route: route.fulfill(
            path=str(escher_js), content_type="application/javascript"))
        page.goto(html.resolve().as_uri())
        page.wait_for_selector("svg g.reaction", state="attached", timeout=30_000)
        page.add_style_tag(content=HIDE_OVERLAYS_CSS)
        page.wait_for_timeout(500)  # let the zoom-to-fit transition finish
        page.locator("svg:has(g.reaction)").first.screenshot(path=str(out))
        browser.close()
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--keep-html", action="store_true",
                        help="also save the interactive HTML map in figures/")
    args = parser.parse_args()

    FIGURES_DIR.mkdir(exist_ok=True)
    versions = pd.read_csv(VERSIONS_PATH, sep="\t", dtype=str)
    # One scale per change, so its before and after maps are comparable
    max_flux = {
        change: max(max_drawn_flux(*load_inputs(row)) for _, row in group.iterrows())
        for change, group in versions.groupby("change", sort=False)
    }
    with tempfile.TemporaryDirectory() as tmp:
        html_dir = FIGURES_DIR if args.keep_html else Path(tmp)
        for _, row in versions.iterrows():
            scale = reaction_scale(max_flux[row["change"]])
            print(f"{row['change']}: pink = |flux| {max_flux[row['change']]:.3g}")
            html = build_map(row, scale, html_dir)
            png = html_to_png(html, FIGURES_DIR / f"{html.stem}.png")
            print(f"wrote {png.relative_to(HERE)}")
            if args.keep_html:
                print(f"wrote {html.relative_to(HERE)}")


if __name__ == "__main__":
    main()
