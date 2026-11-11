# Changelog

All notable changes to MIT1002-GEM, newest first. The versioning rules are in
[`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md). Each entry is generated
by `python -m tools.release prepare` when the release is prepared.

## 4.0.2 - 2026-11-11

Compared with 4.0.1: **patch** release.

### Other changes

- **feat**: Moran lab growth curves and updated growth phenotypes (#480)
- **fix**: Label every medium and use colour-blind-safe colours in the biomass producibility heatmap (#475)
- **feat**: Publication figures and pre-submission clean-up (#474)
- **chore**: move continuous curation manuscript to segrelab/continuous-cur… (#473)
- **refactor**: remove glycerol-3-phosphate from ed vs emp sim (#467)
- **feat**: growth cue carbon fates (#466)
- **refactor**: simplify SMF dissipation sweep to growth vs. dissipation (#465)
- **fix**: change name of Franzi's medium from "Marine Broth" (#464)
- **chore**: name the workflows after the curation steps (#463)
- **fix**: show the release tag exactly, without a v, in the version badge (#462)
- **feat**: add doi badge (#461)
- **feat**: add issue template (#457)

## 4.0.1 - 2026-09-25

Compared with 4.0.0: **patch** release.

### Other changes

- **fix**: stop Publish from triggering itself on its own export commit (#455)

## 4.0.0 - 2026-09-24

Compared with 3.1.0: **major** release.

- model file moved: model.xml -> model/MIT1002-GEM.xml
- model ID changed: iHS4156 -> MIT1002_GEM
- 8 growth call(s) flipped

### Changes to the model

- **refactor**: standard gem compliance (#453)
- **feat**: Franzi data mismatches (#449)
- **feat**: track removed rxns (#447)
- **fix**: Ignore pseudoreactions flagged by mass imbalance test (#445)
- **feat**: Gapfill for growth on 6-phosphogluconate (#442)
- **feat**: gapfill pep (#441)
- **feat**: gapfill glutamine (#438)
- **fix**: change the ID to "GEM_MIT1002" (#437)
- **feat**: Publication Simulations and Figures (#431)
- **feat**: gapfill sugar acids (#430)
- **feat**: gapfill lysine (#425)
- **feat**: Add Aspartate Transport and Exchange (#414)

### Other changes

- **feat**: track and test known errored models (#452)
- **feat**: clean pub figs (#451)
- **refactor**: move data files (#448)
- **feat**: remove star for PR 274
- **chore**: Untrack __pycache__ files and broaden .gitignore (#446)
- **feat**: model performace fig style (#443)
- **fix**: update the file path used on the automatic PR comment
- **feat**: add growth phenotypes from Mary Ann to tsv (#435)
- **feat**: bge figs (#434)
- **feat**: Explore SMF Generation/Dissipation and Force Increased Dissipation (#426)
- **fix**: avoid -0.0
- **feat**: control the ammount of carbon and round growth rates
- **feat**: format table (#422)
- **feat**: pro top10 (#421)
- **feat**: BLAST ecoli phe transporters against Michelle's genome (#416)
- **feat**: prodiel data as rates (#411)
- **fix**: export model path (#408)
- **refactor**: cue script (#407)
- **feat**: plot unbounded fluxes over time (#406)
- **feat**: use prodiel data (#405)
- **feat**: add emp vs ed sims (#404)

### Growth calls changed since 3.1.0

| Condition | Previous | Now | Experiment | Agrees now | Excluded |
| --- | --- | --- | --- | --- | --- |
| marine_broth_wo_yeast_and_peptone \| Glutamine | No | Yes | Yes | yes |  |
| marine_broth_wo_yeast_and_peptone \| Lysine | No | Yes | Yes | yes |  |
| marine_broth_wo_yeast_and_peptone_no_n \| Ammonium, Succinate | Yes | No | No | yes |  |
| marine_broth_wo_yeast_and_peptone_no_n \| Nitrate, Succinate | Yes | No | No | yes |  |
| mbm \| Mannuronic Acid | No | Yes | Yes | yes |  |
| mbm \| Galacturonic Acid | No | Yes | Yes | yes |  |
| mbm \| Phosphoenolpyruvate | No | Yes | Yes | yes |  |
| mbm \| 6-Phosphogluconate | No | Yes | Yes | yes |  |
