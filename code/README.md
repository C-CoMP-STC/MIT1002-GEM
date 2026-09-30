# Code

All code used to build, curate, test and analyse MIT1002-GEM. This folder is
required by [standard-GEM](https://github.com/MetabolicAtlas/standard-GEM),
which asks that it carry a README describing how it is organised.

## Shared code

| Folder | Contains | How it runs |
| --- | --- | --- |
| `test/` | Checks that assert something about the model and pass or fail | `pytest` from the repo root, and in CI. A failure blocks the PR |
| `scripts/` | Code that generates an artifact for a person to look at: a table, a plot, an exported model file | In CI, writing to `scripts/results/`; `python code/scripts/<name>.py` by hand |
| `tools/` | Importable functions and definitions, and command-line utilities a curator runs deliberately | Imported by the above; `PYTHONPATH=code python -m tools.<name>` |

### Tests
#### Examples of Tests on the Model
* `test_biomass.py`
    * `TestBiomass`
        * `test_biomass_weight`:
            * Tests that the biomass reactions component metabolites add up to 1 g
            * this ensures that one mole of the biomass pseudometabolite is equal to 1 g of dry weight
            * this is important to ensure that the flux through the biomass reaction is indeed equivalent to growth rate
            * this test uses `gem_utils.biomass.calculate_biomass_weight()`
* `test_cycles.py`:
    * `TestCycles`
        * `test_atp_generating_cycles`
            * Tests that there are no erroneous energy generating cycles capable of regenerating ATP without an input carbon source, using the MEMOTE function `memote.support.consistency.detect_energy_generating_cycles()` [@lieven2020memote]
* `test_exchanges.py`:
    * `TestExchanges`
        * `test_dead_end_extrac_mets`
            * Tests that there are no dead-end transporters (i.e., external metabolites without an exchange reaction).
* `test_growth.py`:
    * `TestGrowthWithoutCarbon`
        * `test_no_growth_without_carbon`
            * Tests that the model is not capable of growth without a carbon source in the medium.
    * `TestExpectedGrowthPhenotypes`
        * `test_no_new_mismatches`
            * Tests that the model never gets worse (i.e., that there is never a new mismatch)
            * Compares against a committed baseline of accepted mismatches
            * This keeps you from having a test you will fail for the majority of time of curation
            * It's a ratchet, once the model is better (i.e., you've gap-filled for a new reaction), the baseline is updated, so that you now compare against it
        * `test_no_stale_baseline_entries`
            * Tests that baseline mismatches that now match are removed from the baseline mismatch file
        * `test_mismatch_categories_are_unchanged`
            * Tests that the category of mismatch (i.e., false positive or false negative) is correct and current- these can become wrong if the file is edited by hand
        * `test_excluded_rows_are_not_scored`
            * Tests that growth phenotypes that are marked to be excluded (e.g., because we were unsure about the data, or a control was missing) were not included in the matching score
        * `test_every_phenotype_was_evaluated`
            * Tests that all growth phenotypes were evaluated- none were silently dropped
* `test_sbml.py`:
    * `TestValidSBML`
        * `test_valid_sbml`
            * Tests that the SBML file is valid
                * Important as COBRApy may fail to load a model with a malformed file
                * KBase created such files- they had "null" in `fbc:chemicalFormula`
        * `test_isolated_genes_and_mets`
            * Tests for genes and metabolites in the model not associated with any reaction
            * Taken from the Human-GEM repo
        * `test_mass_balance`
            * Tests that all reactions were mass and charge balanced
            * Using the built-in COBRApy function, `cobra.manipulation.check_mass_balance()`

#### Examples of Unit Tests on the Data Files
* `test_deprecated.py`
    * `TestDeprecatedSchema`
        * `test_headers_exact`
            * Tests that the header row are the same column names, in the same order, and with no extra, defined in `COLUMNS` in `tools.deprecate`: "id", "name", "reason", "replaced_by", "pr", "date", "notes"
        * `test_no_duplicate_ids`
            * Tests that there are no duplicate ids in the deprecated tables- i.e. that each ID only has one row
        * `test_reasons_in_vocabulary`
            * Tests that all values in the `reason` column of the deprecated tables are from the list `REASONS` defined in `tools.deprecate`: "duplicate", "id_changed", "no_genomic_evidence", "no_experimental_evidence", "mass_imbalance", "infeasible_cycle", "dead_end", "orphaned", "erroneous_annotation", "out_of_scope", "unknown",
        * `test_ids_have_no_sbml_prefix`
            * Tests that the IDs listed in the deprecated tables do NOT have the SBML prefixes ("R_", "M_", "G_") on them, e.g., a reaction ID should be rxn00196_c0, not R_rxn00196_c0
        * `test_dates_are_iso`
            * Tests that all dates are given in YYYY-MM-DD format
        * `test_pr_format`
            * Tests that all PRs are given as a number sign followed by a number, e.g., #123
        * `test_notes_are_under_200_char`
            * Check that all notes are under 200 characters
            * Notes in the deprecated table should really just be a short summary, you can go into more detail in the PR
    * `TestReplacedBy`
        * `test_separator_is_semicolon`
            * Test that there are no , + [] {} () ' " in the replaced by column
            * If you need a list of ids, they should be separated by semi-colons (;)
        * `test_no_sbml_prefix_on_targets`
            * See `TestDeprecatedSchema` > `test_ids_have_no_sbml_prefix`, now just on the IDs in the `replaced_by` column, instead of the ID column
        * `test_no_duplicate_targets`
            * Tests that for each row in the deprecated tables, the replaced_by column doesn't include any repeats, e.g., your replaced_by column cannot be "cpd9999;cpd9999"
        * `test_required_when_reason_is_relative`
            * Tests that if a row in the deprecated table was removed due to any of the reasons defined in `REASONS_REQUIRING_REPLACEMENT` ("duplicate", "id_changed"), that there is also an entry in that row's replaced_by column
        * `test_not_self_referential`
            * Tests that an ID is not replaced by itself, i.e., that the ID in the ID column and the ID in the replaced_by column are not the same
        * `test_targets_resolve`
            * Tests that all IDs in the replaced_by column are either in the model or are in the deprecated list as well
    * `TestVocabularyDocumented`
        * `test_every_reason_in_readme`
            * Tests that a README file exists at `data/deprecated_identifiers/README.md`
            * Tests that every reason defined in `tools.deprecate.REASONS` ("duplicate", "id_changed", "no_genomic_evidence", "no_experimental_evidence", "mass_imbalance", "infeasible_cycle", "dead_end", "orphaned", "erroneous_annotation", "out_of_scope", "unknown") is defined in a table in the README under the heading "### Controlled vocabulary for `reason`"
* `test_phenotype_data.py`
    * `TestPhenotypeSchema`
        * `test_growth_column_vocabulary`
            * Test that every value in the column `growth` is either "Yes", "No", or "Unsure"
        * `test_exclude_reason_vocabulary`
            * Test that every value used in the "exclude_reason" column, is from the dictionary `EXCLUSION_REASONS` defined in `tools.phenotypes`: "control_failed", "id_uncertain", "conflicting_reports", "not_representable"
        * `test_every_reason_is_documented`
            * Test that every reason for exclusion defined in the EXCLUSION_REASONS dictionary is included in the table in the `### exclude_reason` section of `data/README.md`
        * `test_every_documented_exclusion_reason_has_a_description`
            * Tests that the definition table in the README doesn't include any blank cells
        * `test_condition_keys_are_unique`
            * Test that `minimal_media` + `c_source` identifies a row, there are no duplicates of that value pair
        * `test_met_ids_are_present_and_well_formed`
            * Test that all values in the met_id column are non-empty lists, and each value in the list begins with "cpd"
            * Note, this only works if the model is in the ModelSEED ID namespace, and that all metabolites tested were present in the ModelSEED database (e.g., nothing had to be custom defined)
    * `TestExpectedMisMatches`
        * `test_baseline_has_the_expected_columns`
            * Tests that the baseline mismatch file contains the columns defined in `tools.phenotypes.MISMATCH_COLUMNS`: "minimal_media", "c_source", "category", "notes"
        * `test_baseline_rows_refer_to_real_conditions`
            * Tests that the mismatches listed in the baseline mismatch file exist in the phenotype data file
        * `test_baseline_does_not_list_excluded_conditions`
            * Tests that excluded rows of the phenotype data are not listed in the baseline file
            * Excluded rows are not scored, so they cannot be mismatches, so they should not be in the baseline

#### Examples of Unit Tests on Tools
* `test_growth.py`
    * `TestSummaryArithmetic`
        * `test_every_row_gets_a_known_category`
            * Tests that every row in the expected growth phenotype table gets one of the categories defined in `tools.phenotypes.CATEGORIES`: "true_positive", "true_negative", "false_positive", "false_negative", "unsure", "invalid_solve", "excluded"
        * `test_categories_partition_the_table`
            * Tests that `tools.phenotypes.summarise()` does not count any row twice: the total number of rows in the phenotype table matches the sum of scored rows and unscored rows
        * `test_no_uptake_route_is_a_subset_of_the_negative_predictions`
            * Tests that the number of phenotypes with "no_uptake_route" is less than the total number of phenotypes marked as false negative and tue negative, since a metabolite with no uptake route can never have positive growth
        * `test_a_missing_exchange_does_not_by_itself_decide_the_verdict`
            * Test that no growth phenotypes where the model is missing an exchange, but still grows, is not marked as "no_uptake_route"
        * `test_confusion_matrix_sums_to_the_scored_rows`
        * `test_matches_are_the_concordant_cells`
        * `test_matches_never_exceed_the_interpretable_denominator`
        * `test_excluded_rows_keep_their_underlying_verdict`
* `test_deprecated.py`
    * `TestStampPrNumber`
        * `test_fills_blanks_and_preserves_existing`
        * `test_is_idempotent`
        * `test_rejects_non_numeric`
    * `TestIdentifierListParsing`
        * `test_accepts_common_separators`
        * `test_strips_sbml_prefixes`
        * `test_empty_is_empty`
        * `test_normalizes_to_semicolons`
        * `test_record_normalizes_on_construction`
        * `test_preserves_gene_style_identifiers`
* `test_phenotype_data.py`
    * `TestCountInterpretable`
        * `test_counts_only_definite_unexcluded_rows`
            * Tests that the `tools.phenotypes.count_interpretable()` function works on small 6 row data frame, covering every combination of Yes, No, Unsure and excluded, not
        * `test_one_row_at_a_time`
            * Tests each row in the dummy table one at a time, so that the exact row that caused the failure in the previous is identified
        * `test_empty_table_is_zero`
            * If you give `count_interpretable()` an empty table, it should return 0

#### Examples of Unit Tests on Consistency Between Two Objects
* `test_deprecated.py`
    * `TestDeprecatedNotInModel`
        * `test_deprecated_reactions_absent`
            * Tests that no reactions in the deprecated reactions table are present in the model
            * Could occur if someone adds back a reaction without realizing it was removed before
        * `test_deprecated_metabolites_absent`
            * Tests that no metabolite in the deprecated metabolites table are present in the model
            * Could occur if someone adds back a reaction without realizing it was removed before
    * `TestNotesMirror`
        * `test_mirror_matches_tsv`
        * `test_pointer_present`
        * `test_mirror_survives_cobrapy_round_trip`

## Curation and analysis work

One folder per piece of work, kept together with its inputs and results.

| Folder | What it is |
| --- | --- |
| `curation_process/` | The model's agreement with growth phenotypes replayed across every merged PR (figure 2). See the README there |
| `simulations/` | Simulations and figures for the manuscript |
| `biomass/` | Building and checking the biomass composition |
| `blast/` | BLAST searches used as gene evidence for curation decisions |
| `gene_essentiality/` | Single-gene knockouts compared against the mutant library in `data/mutant_library/` |
| `escher/` | Hand-built Escher maps of MIT1002 pathways |
| `kegg_maps/` | KEGG pathway maps coloured by model coverage |
| `pangenome/` | Adding reactions from the *Alteromonas* pangenome. A record of how it was done; not runnable as-is (see the commit that moved it) |
