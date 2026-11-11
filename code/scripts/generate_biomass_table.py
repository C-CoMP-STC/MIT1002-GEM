"""Write the biomass composition table.

Outputs, both in ``code/scripts/results/``:

``<model.id>_biomass_composition_work_table.csv``
    Written by ``gem_utilities.biomass.save_biomass_composition_work_table``:
    one row per (un-lumped) biomass component, plus a Total row. Full
    precision; the record.
``<model.id>_biomass_composition_work_table.docx``
    The same table as Word, for the manuscript (ASM wants main-text tables as
    Word files). Read back from the CSV, so the two cannot disagree; only the
    display changes (rounding, subscripts, header labels).
"""

import os
import re
import sys

import cobra
import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from gem_utilities.biomass import save_biomass_composition_work_table

# Make `tools` importable; everything else comes from tools.paths.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.paths import MODEL_PATH  # noqa: E402

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")

# Same size as the other manuscript tables, so they look alike in the
# submission. Production restyles main-text tables anyway.
DOCX_FONT_SIZE = Pt(9)

# Significant figures for the numeric columns. The CSV keeps full precision.
SIG_FIGS = 4

# Header labels for the Word table. Units are copied from the CSV headers
# unchanged, so the Word table claims nothing the work table does not.
HEADER_LABELS = {
    "metabolite": "Metabolite ID",
    "name": "Name",
    "coefficient": "Coefficient",
    "formula": "Formula",
    "formula_weight (g/mol)": "Formula weight (g/mol)",
    "weight_contribution (g)": "Weight contribution (g)",
    "carbon_content (mol C/mol biomass)": "Carbon content (mol C/mol biomass)",
}

# Portrait US Letter with 1" margins leaves 6.5". The last two columns need
# room for values like "8.598 × 10⁻⁵" on one line; the long lipid names wrap
# instead, which is fine.
COLUMN_WIDTHS = {
    "metabolite": Inches(0.95),
    "name": Inches(1.4),
    "coefficient": Inches(0.8),
    "formula": Inches(1.1),
    "formula_weight (g/mol)": Inches(0.65),
    "weight_contribution (g)": Inches(0.8),
    "carbon_content (mol C/mol biomass)": Inches(0.8),
}

# Left/right cell padding, in twentieths of a point. Word's default is 108
# (0.075"); halving it is what lets seven columns fit in portrait without the
# metabolite IDs breaking.
CELL_SIDE_MARGIN_TWIPS = 50

NUMERIC_COLUMNS = [
    "coefficient",
    "formula_weight (g/mol)",
    "weight_contribution (g)",
    "carbon_content (mol C/mol biomass)",
]


def _repeat_header_row(row):
    """Mark a table row as a header so Word repeats it on every page."""
    tr_pr = row._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    tr_pr.append(header)


def _set_cell_side_margins(table, twips: int):
    """Set the left/right padding of every cell in the table.

    python-docx has no API for this, so ``w:tblCellMar`` goes in by hand.
    """
    margins = OxmlElement("w:tblCellMar")
    for side in ("left", "right"):
        element = OxmlElement(f"w:{side}")
        element.set(qn("w:w"), str(twips))
        element.set(qn("w:type"), "dxa")
        margins.append(element)
    table._tbl.tblPr.append(margins)


def _add_formula(paragraph, formula: str, bold: bool = False):
    """Write a chemical formula with its counts as subscripts (C6H12O6)."""
    for part in re.findall(r"\d+|\D+", formula):
        run = paragraph.add_run(part)
        run.font.size = DOCX_FONT_SIZE
        run.bold = bold
        run.font.subscript = part.isdigit()


def _add_number(paragraph, value: float, bold: bool = False):
    """Write a number to SIG_FIGS significant figures.

    Python's ``g`` format falls back to e-notation for very small or large
    values (e.g. ``8.598e-05``); that is rewritten as ``8.598 × 10⁻⁵`` with a
    real superscript, which is how a journal would set it.
    """
    text = f"{value:.{SIG_FIGS}g}"
    mantissa, _, exponent = text.partition("e")
    # Use a true minus sign, not a hyphen, for negative values.
    mantissa = mantissa.replace("-", "−")
    parts = [(mantissa, False)]
    if exponent:
        parts += [
            (" × 10", False),
            (str(int(exponent)).replace("-", "−"), True),
        ]
    for text_part, superscript in parts:
        run = paragraph.add_run(text_part)
        run.font.size = DOCX_FONT_SIZE
        run.bold = bold
        run.font.superscript = superscript


def save_as_docx(work_table: pd.DataFrame, path: str):
    """Write the biomass work table as Word: portrait, one header row.

    Numbers are rounded to SIG_FIGS and right-aligned; formulas get subscript
    counts; the Total row is bold. Rows stay in the CSV's order.

    No caption is written. The table legend is manuscript text and belongs to
    the author; add it in Word above the table.
    """
    columns = list(work_table.columns)
    missing = set(columns) ^ set(HEADER_LABELS)
    if missing:
        # gem_utilities changed its columns; fail loudly rather than write a
        # table with unlabelled or missing columns.
        raise ValueError(f"Unexpected work table columns: {sorted(missing)}")

    document = Document()
    widths = [COLUMN_WIDTHS[name] for name in columns]

    table = document.add_table(rows=1, cols=len(columns))
    table.style = "Table Grid"
    # Word only honours widths with autofit off and a width on every cell.
    table.autofit = False
    _set_cell_side_margins(table, CELL_SIDE_MARGIN_TWIPS)
    for column, width in zip(table.columns, widths):
        column.width = width

    for cell, name, width in zip(table.rows[0].cells, columns, widths):
        cell.width = width
        run = cell.paragraphs[0].add_run(HEADER_LABELS[name])
        run.bold = True
        run.font.size = DOCX_FONT_SIZE
        if name in NUMERIC_COLUMNS:
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _repeat_header_row(table.rows[0])

    for record in work_table.to_dict("records"):
        is_total = record["metabolite"] == "Total"
        cells = table.add_row().cells
        for cell, name, width in zip(cells, columns, widths):
            cell.width = width
            paragraph = cell.paragraphs[0]
            value = record[name]
            if pd.isna(value) or value == "":
                continue
            if name in NUMERIC_COLUMNS:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                _add_number(paragraph, float(value), bold=is_total)
            elif name == "formula":
                _add_formula(paragraph, str(value), bold=is_total)
            else:
                run = paragraph.add_run(str(value))
                run.font.size = DOCX_FONT_SIZE
                run.bold = is_total

    document.save(path)


if __name__ == "__main__":
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Load the model
    model = cobra.io.read_sbml_model(MODEL_PATH)

    # Save the biomass composition table
    save_biomass_composition_work_table(
        model=model, mets_to_ignore=["cpd11416_c0"], out_dir=RESULTS_DIR
    )

    # And as Word, read back from the CSV that was just written
    csv_path = os.path.join(
        RESULTS_DIR, model.id + "_biomass_composition_work_table.csv"
    )
    work_table = pd.read_csv(csv_path)
    save_as_docx(work_table, os.path.splitext(csv_path)[0] + ".docx")
