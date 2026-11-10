# Growth curves

Cleaning, summarising and plotting the Moran lab growth curves in
`data/growth_curves/` (see the README there for the experiment and the data).

Run from the repo root, in this order:

| Script | Reads | Writes |
| --- | --- | --- |
| `clean_growth_curves.py` | `data/growth_curves/raw/MIT1002_growth_tests_ALL_raw.csv` (or, with `--from-xlsx PATH`, a new workbook first) | `data/growth_curves/MIT1002_growth_curves.csv` |
| `summarise_growth_curves.py` | the tidy CSV | `results/growth_curve_summary.csv` |
| `plot_growth_curves.py` | the tidy CSV | `results/growth_curves.{pdf,png}` |

When a new workbook arrives, run `clean_growth_curves.py --from-xlsx PATH`, then
update the checksum table in `data/growth_curves/README.md`.

## Growth calls

`summarise_growth_curves.py` reduces each well to one number, its **increase**:
the peak OD600 (3-point rolling median, so a single noisy read cannot set the
peak) minus the mean of its first three readings. A substrate x concentration
is then called:

| Call | Rule |
| --- | --- |
| `Yes` | every replicate increased by ≥ 0.05 |
| `No` | every replicate increased by < 0.02 |
| `Unsure` | anything else: in between, or replicates disagree |

Why these numbers: the substrates that clearly did not grow (alginate,
allantoin, formate, glycolate, glyoxylate, xylose, …) all rise by ≤ 0.015, so
0.02 sits just above that noise floor. 0.05 is well clear of it, about a quarter
of the glucose increase. There is no natural gap between the two, so a handful
of substrates (DHPS, glycine, tyrosine, 12 mM C 6-phosphogluconate and PEP, 8 mM
C glycerol) land in `Unsure`. The thresholds are constants at the top of the
script; change them there, not by hand in the output.

The call only uses magnitude, not shape or timing, and short runs can
under-call a substrate still rising at the end. The calls are **provisional**:
check them against `results/growth_curves.pdf` before copying anything into
`data/known_growth_phenotypes.tsv`. The scripts never edit that file.
