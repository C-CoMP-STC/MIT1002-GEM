"""Draw the Escher maps comparing model versions from the pFBA fluxes.

Reads ``versions.tsv`` and the flux files written by
``run_pfba_at_versions.py``, and writes one PNG map per row to
``figures/<change>_<label>.png``. Each map is built as a standalone Escher
HTML page and rendered in headless Chromium (needs ``playwright``; see
README). The HTML is a temporary intermediate; pass ``--keep-html`` to also
save it next to the PNG for interactive inspection.

The colour scale is fixed (``REACTION_SCALE`` below) rather than min/max, so
the same flux gets the same colour and width in every panel. Width carries the
same information as colour, so the maps still read without colour vision.

    python code/simulations/curation_history_maps/make_maps.py [--keep-html]
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd
from escher import Builder

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))  # make `tools` importable
from tools.paths import CODE_DIR  # noqa: E402

VERSIONS_PATH = HERE / "versions.tsv"
RESULTS_DIR = HERE / "results"
FIGURES_DIR = HERE / "figures"
MAP_DIR = CODE_DIR / "escher"

# Okabe-Ito colours (colour-blind safe). Stops are absolute flux values
# (mmol/gDW/h) because of "abs" below; tune these to the figures.
REACTION_SCALE = [
    {"type": "value", "value": 0, "color": "#BBBBBB", "size": 8},
    {"type": "value", "value": 10, "color": "#0072B2", "size": 16},
    {"type": "value", "value": 1000, "color": "#D55E00", "size": 30},
]

BUILDER_OPTIONS = {
    # "abs": colour/size by |flux|, so a +-1000 loop shows as large either way
    "reaction_styles": ["color", "size", "text", "abs"],
    "reaction_scale": REACTION_SCALE,
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


def build_map(row: pd.Series, out_dir: Path) -> Path:
    """Write the Escher map for one row of versions.tsv as standalone HTML."""
    stem = f"{row['change']}_{row['label']}"
    with open(RESULTS_DIR / f"{stem}_fluxes.json") as f:
        fluxes = json.load(f)
    with open(MAP_DIR / row["escher_map"]) as f:
        escher_map = relabel_map(json.load(f))
    builder = Builder(
        map_json=json.dumps(escher_map),
        reaction_data=fluxes,
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
    with tempfile.TemporaryDirectory() as tmp:
        html_dir = FIGURES_DIR if args.keep_html else Path(tmp)
        for _, row in versions.iterrows():
            html = build_map(row, html_dir)
            png = html_to_png(html, FIGURES_DIR / f"{html.stem}.png")
            print(f"wrote {png.relative_to(HERE)}")
            if args.keep_html:
                print(f"wrote {html.relative_to(HERE)}")


if __name__ == "__main__":
    main()
