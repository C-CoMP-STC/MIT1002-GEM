# Curation-history Escher maps

Escher maps comparing pFBA fluxes before and after a curation change:

| `change` | What changed | Before | After |
|---|---|---|---|
| `gapdhn-loop` | GAPDH loop in lower glycolysis fixed (PR #344, `fix/gapd-loop`) | `3e5c456^1` | `3e5c456` |
| `sucd` | Succinate dehydrogenase lumped (PR #392, `fix/lump-SUCD`) | `cf3cfad^1` | `cf3cfad` |

`^1` is the first parent of the merge commit, i.e. `develop` just before the PR
was merged.

## Regenerate

From the repo root:

```bash
python code/simulations/curation_history_maps/run_pfba_at_versions.py
python code/simulations/curation_history_maps/make_maps.py
```

| File | Role |
|---|---|
| `versions.tsv` | One row per map: git ref, growth condition, Escher map. Edit this to add or change panels. |
| `run_pfba_at_versions.py` | Reads the model at each ref from git (no checkout), runs pFBA, writes `results/`. |
| `make_maps.py` | Draws each map with a fixed colour/width scale and renders it to `figures/` as PNG (`--keep-html` also saves the interactive map). |
| `results/<change>_<label>_fluxes.json` | Fluxes in the format Escher takes as reaction data. |
| `results/<change>_<label>_meta.json`, `results/summary.tsv` | Full commit SHA, model path at that commit, cobra version, growth rate, O2/CO2 exchange. |
| `figures/<change>_<label>.png` | Rendered map. |

## How the simulations are set up

- **Only the model varies.** The old model is read from git with
  `tools.release.model_file_at` (which knows the model was at `model.xml`
  before the standard-GEM rename). Media come from the current `tools.media`,
  and the carbon source is added at a fixed carbon uptake (60 mmol C/gDW/h,
  the same convention as `simulations/pFBA`).
- **Labels.** Reactions are labelled with their ModelSEED ID (swapped in
  memory; the map files in `code/escher/` are not changed) and metabolites with
  the descriptive names stored in the map files.
- **Fixed colour scale.** `REACTION_SCALE` in `make_maps.py` uses absolute flux
  values, not min/max, so a flux gets the same colour and width in every panel.
  Colours are from the Okabe-Ito palette. Width carries the same information as
  colour.
- **Offline rendering.** The HTML loads Escher's JavaScript from unpkg. Rendering
  answers that request from the copy inside the installed `escher` package,
  so rendering needs no network and matches the Python package's version.

## Requirements

`cobra`, `gem_utilities`, `escher` (tested with 1.8.1), and
`playwright` plus a browser (`pip install playwright && playwright install chromium`).

## Manual steps

None for the fluxes or maps. Panel layout, the colour legend and labels are
added when the figure is assembled. Escher's built-in legend is hidden in the
PNGs because it crams the low stops together.
