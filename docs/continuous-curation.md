# Continuous Curation: Best Practices for Model Curation Inspired by Software Development

GEMs are, at their heart, a software product, and we took lessons from software development and applied them to the model curation process. We term this constant testing and iterative model improvement strategy “continuous curation”, inspired by continuous integration (CI) for traditional software. This included tracking all changes using version control, having multiple curators collaborate and propose changes by working on branches and opening pull requests, testing the model with defined pass/fail tests, and automatically generating artifacts for curator inspection.

* None of this is really new
    * we borrowed all of this from software engineering
    * other groups do or are developing similar things
        * we took some things directly from human-GEM and standard-GEM
    * the field is crystallizing
    * but the field lacks a single reference point for guidelines

## Motivation
### Why do we need this?
* GEMs are important tools
    * But their quality is often questioned
* Manual curation is hard/messy
    * Manual curation can be an overwhelming task- the typical advice of just go "pathway by pathway" can be paralyzingly large
* Manual curation can last for a long time (including decades, spanning many people and projects)
    * Often one group publishes a model, then another may find it, modify it, and publish a new paper, resulting in branching sets of models


### What have people been doing before this?
#### MEMOTE
* MEMOTE exists [@lieven2020memote]
    * but it's more of a benchmarking tool- a lot of things is just about the file
        * test what the custom tests ever did
* They had a TRAVIS integration where it would run, but MEMOTE can never fail, it always required a human to read, understand, and evaluate the tests

#### standard-GEM
* standard-GEM is a set of requirements for the format of GEMs versioned with git [@anton2023standardgem]
* no tests
    * they show running MACAW in a workflow, and they call it `macawTests.py` but it's not a test, it doesn't assert anything, equivalent to a "script"
    * code/test and MEMOTE are only possibility/capability, not a requirement or even a recommendation
* technically just because it's on git doesn't mean you're regularly pushing- you could upload everything once and meet standard-GEM requirements, even if not in spirit

#### human-GEM and yeast-GEM
* Human-GEM
    * 2023: check-metabolictasks.yml
        * "metabolic tasks" on push and PR
        * using a self-hosted MATLAB runner
    * 2024: Gene essentiality workflow
    * 2026: model-qc.yml
* yeast-GEM
    * 2018: automated benchmarking MEMOTE + Travis CI 
    * 2020: MEMOTE on GitHub actions + YAML-vaildation
    * 2026: model-qc.yml
* A lot of things were not enforced, just reminders and check boxes

### What's new here
* Our specific unit tests- not really clear who go to running it as CI first...
* Biomass component producibility heatmaps
* Improved tracking removed reactions/metabolites

## What's the cost?
* Requires set up and maintenance
* Requires learning more about Git and automation than someone with a biology background may currently have

## Set-Up
### What is GitHub?
Version control is critical for model curation because it tracks the “who”, “what”, and “when” of all changes made to the model. Who edited the model file, when did they make the edits, and what exactly was changed. It also maintains the historical versions of the model file, so at any time you can revert changes and return to an older version of the model.

Version control keeps a historical record of changes made to tracked files in a specialized database called a repository (or “repo”). Git is the software tool that enables version control, and GitHub is one popular cloud-based platform to host Git repositories, that also offers other functionalities such as issue tracking and wiki hosting. While we used GitHub, and will use GitHub-focused terminology (e.g., pull requests, actions) it not the only option for hosting Git repositories, other popular options include GitLab, Bitbucket and Azure DevOps, each of which have analogous tools to those we describe here and could similarly be used for a continuous curation pipeline.

* A Git repository lives in two places...
* Local vs Remote, basic terminology (commit, push, pull, etc.)

![An introduction to basic Git terminology: Local and remote repositories, commit, push, and pull](./figures/png/github-intro.png)

#### Diffs
* How to read a diff

![](./figures/png/diff-sbml.png)

* Not all diffs are equally helpful
    * File types to avoid
        * Microsoft office files: e.g., xlsx

![](./figures/png/diff-excel-vs-csv.png)

For a more in depth coverage, see...

### What's in a Name?: Choosing your Model and Repository Name
* BiGG names models following a pattern, of i{Author's Initials}{Number of genes in the model} [@reed2003ijr904]
    * the i in the name refers to an in silico model (that is, a computer model)
    * e.g., iJR904 is an in silico model (i), built by Jennifer Reed (JR), containing 904 genes (904)
    * The 'i' in the name refers to an in silico model (that is, a computer model). This 'i' is followed by the initials (XX) of the person who developed the model and then the number of genes (xxx) included in the model. [@reed2003ijr904]
    * i.e. the current E. coli model is iML1515
        * M stands from Jonathan Monk, L stands for Colton Lloyd
    * iJO1366 is by Jeffrey Orth
* But this naming is inherently a snapshot, and would have to be continuously updated as the model evolved
    * Every time you add or remove a gene you would need to change the number
    * As new curators contribute to the model or take over, the author list may expand or change, or people may be annoyed to leave an old authors name at the prime spot
* It would be better instead to have a single name that is not dependent on the author or gene list, that is specific to the organism
    * It would be nice to instead have on model with different versions
    * e.g. e.coli model v1, e.coli model v2, to make it clear the lineage of the model
* The recommendation from standard-GEM is to name the repository and model {something}-GEM, a common name, KEGG organism, or taxonomy-derived short name
    * e.g. Human-GEM and yeast-GEM
    * We followed that advice, and named the model MIT1002-GEM

### Branches
Branching is a key feature of Git- it allows developers to isolate their changes so that the main version of the repository is not affected. This allows multiple developers to work simultaneously, and allows developers to test out changes where they will not affect anyone else. We chose to use a branching strategy based on the popular GitFlow strategy. We had two long-lived branches, “main”, the main branch, which had the official releases of the model, and “dev”, the development branch, where all accepted changes to the model were integrate before an official release. All changes made the model were made on feature branches that branched off of and were merged back into the dev branch. This ensured that any new feature development did not disturb the main model. Early on in development, branching is critical to XXX, and later branching became increasingly important to differentiate the version of model from users vs from developers.

![](./figures/png/branches.png)

### Repository Structure
#### Model
##### What file type to use?
* XML
* SBML

#### Data

### GitHub Actions
We used automation through GitHub actions to run tests and scripts upon the opening of a pull request.

#### Defining an Action with a YML file


## The Continuous Curation Loop

![Continuous Curation is an iterative process with the following steps: Curate, Test, Report, Release, Run, and Monitor.
](./figures/png/continuous-curation-loop.png)

The Continuous Curation loop consists of 6 steps:
1. Curate
2. Test
3. Report
4. Release
5. Run
6. Monitor

### Step 1) Curate
*NOTE: We do not discuss here how to make curation decisions, but rather how to implement them*

* How big is one curation task?

#### Removing Reactions/Metabolites
* Palsson said to do it [@thiele2010protocol]
* What we took from human-GEM: the table
* What is new
    * The standard vocabulary of reason
    * The list of removed things in the model file itself
        * And the test to make sure it does not drift
    * The test that no old reactions are still in the model file

#### Commits
* Commit often- don't just wait until the end of all your changes
* Use concise descriptive commit messages
* Use semantic commits
    * <type>[optional scope]: <description>

    * We got this from standard-GEM
    * type
        * chore: updating toolbox, data files, etc.
        * doc: updating documentation or explanatory comments in functions.
        * feat: new feature added, e.g. new reaction / metabolite / function / etc.
        * fix: something that was incorrect in the model and now has been corrected.
        * refactor: see code refactoring.
        * style: minor format changes of model, functions or data (spaces, semi-colons, etc., no code change)
    * scope
        * optional
        * refers to the receiver of the action, i.e. what part of the model/data are you modifying
    * description
        * concise description of what you did
    * some examples (direct copy from yeat-GEM contributing guidelines)
        |commit|commit message|
        |:---:|:---:|
        |Add new rxns|`feat-rxn: methanol pathway`|
        |Remove a metabolite|`fix-met: duplicated citrate`|
        |Add metabolite formula|`feat-met.prop: carbohydrate formulas`|
        |Fix rxn stoichiometry|`fix-rxn.prop: complex V stoich coeffs`|
        |Update gene IDs|`fix-gene.annot: update IDs from SWISSPROT`|
        |Format name of compartment|`style-comp.annot: remove uppercases`|
        |Split a rxn in 2|`refactor-rxn: split isomerase in 2 steps`|
        |Add some data|`feat-data: metabolomics data`|
        |Update documentation of function|`doc: addDBnewRxn.m`|
        |Update toolbox|`chore: update RAVEN version`|

#### Pull Requests
One critical component of the history of changes to the model is the “why”- why was a change to the model made (e.g., was a reaction found to have genomic evidence, was there a mistake in the biochemistry database, etc.). There are text fields in the model file itself where this information can be stored, and there have been cases in the past of defined “codes” used to represent different types of evidence that support each reaction (CITE EXAMPLES) however we have found that these are not well used, lack standardization across the community, and are often not comprehensive enough to fully explain the reasoning behind each change. We instead elected to document these in issues and pull requests on the repository. Issues can be used as a sort of electronic lab notebook. To ensure that all curators (present and future) are reminded to document their reasoning, a pull request template was used.

* Open a pull request, that starts the cycle

### Step 2) Test
* Testing code is important, testing the model is just as important
* Typical software tools can be used, but some concepts need to generalized
* Unit tests are considered critical to the success of any project

#### What is a Unit Test?
* Unit tests are a common software development practice in which the smallest individual parts of the code (called units) are individually tested, to ensure each gives the expected outcome

##### Software example
* Imagine you have a python module called `hello` with a single function, also called `hello`, that says "Hello" to a person, given their name:
```python
def hello(name: str):
    message = 'Hello, ' + name + '!'

    return message
```
* To write the unit test, you would make a new file, by convention in a directory named "test" or "tests", and name the file "test_[module name]", for that individual python module, so in our case "test_hello"
* While there are other testing frameworks, we show the python standard-library testing framework, unittest
* In your test, you first import unittest, and your function that you are testing
```python
import unittest

from hello import hello
```
* All tests are put within a class
```python
class TestHello(unittest.TestCase):
```
* Within that class you can write multiple tests
* For example, first test an expected input, e.g., "Helen"
    * ```python
        def test_helen(self):
            # Define a name
            name = 'Helen'
            # Call the function
            message = hello(name)

            # Assert that the function returns the correct string
            self.assertEqual(message, 'Hello, Helen!')
        ```
    * You define if the output is correct or not with an assert statement
    * There are other options for assert statements that make sense for different kinds of tests
        * Table/list of assert statements
* Then test an edge case, something that could return a bad output if your function is not properly written, e.g. a number
```python
    # Add a test checking that the function fails when an integer is passed
    def test_integer(self):
        # Define a name
        name = 123
        # Call the function
        with self.assertRaises(TypeError):
            message = hello.hello(name)
```
* At the end of the file- set it to run all of the classes
```python
if __name__ == '__main__':
    unittest.main()
```
* Unit tests can be run manually- e.g., a developer runs them on their own computer and verifies that they all pass before pushing code
* Or they can be run automatically (e.g., as part of a GitHub action)
* In MIT1002-GEM we run them all automatically in the CI-workflow, finding and executing tests with `pytest`

#### What makes a Good Unit Test?
* Needs to pass/fail, have an expected outcome, not generate an artifact
    * Boolean result- pass or fail
    * Self-validating — it returns pass or fail, not output a human must inspect
* One reason to fail — a test asserting five things tells you "something broke," not what
* Fast — slow tests don't get run, and a suite people skip provides no safety
* Independent — no test depends on another's state or on run order
* Repeatable — same result on any machine, any time; no network, no clock, no randomness
* Deterministic — the intermittent test is worse than no test, because it trains people to re-run until green
* No logic in the test — conditionals and loops inside a test can themselves be buggy, and then you're debugging your test
* Tests behavior, not implementation — a test that breaks when you refactor without changing behavior is a liability
* A name that says what broke without opening the file

* Table with columns:
    * Example of good unit tests
        * Test that a script generate the correct data and saves a plot with the correct path
    * Example of bad unit tests
        * Generate a figure, that you need to look at
        * A test you know will fail, and you will just ignore it (skip the test or mark it a known failure instead)

* We can differentiate the tests used in MIT1002-GEM by what they tested, the model, the data files, the helper tools, or consistency between two things. A single test file can contain multiple different kinds of tests, so some file names may repeat across the list.

#### Examples of Unit Tests on the Model
* In traditional software engineering, the unit being tested is often a function, however for the case of model curation, we are testing the model as a whole, but can write tests to focus on individual aspects of the model
* The ones we present here are by no means an exhaustive list of everything that could or should be tested.
* Many of these tests use previously published tools (e.g., MEMOTE), but we found that by implementing them with unit tests on a GitHub action it was easier to track model performance over time and recognize errors introduced into the model quickly.
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
Part of the MIT1002-GEM repo is helper functions (i.e. for XXX), these functions, just like any other functions in a python module should be tested.
For example:
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


### Step 3) Report
#### Scripts vs Tests
* Scripts differ from tests because they cannot “pass” or “fail”, and instead generate artifacts (e.g., plots) for a human curator to look at
* If you can state in advance what is right or wrong- make a test
* If you can use the information, but you're not sure what is right- make a scripts
* Tests can block a merge- you need to pass all tests before you can merge a PR
* Scripts don't block anything
* Automated- also ran through GitHub actions
    * Doesn't include any arguments or hand editing
* Should be something you need continually- not just a one off for a specific question
    * If no one is looking at the artifact- you don't need the script
* They might share code with tests
    * E.g. the growth phenotype plot uses the same code as the growth phenotype ratchet test
    * Make sure shared code lives in tools, not recreated in both files
#### Examples of Scripts Used for Model Curation
* Using the same underlying code as the growth test, we generated a plot of which experimentally known growth phenotypes the model matched or not. The heatmap visualization was useful for sharing results.
* While this graph is useful to grasp model performance at a glance, it was not the most instructive when gap-filling the model (just knowing that the model does not grow does not help you find a gap). Instead we checked the model’s ability to produce each individual biomass component (i.e., we added a demand/sink reaction for each biomass component that take the metabolite and removes it from the system (similar to an exchange reaction), and looped through the list of biomass components and set each as the objective, maximizing the flux through that sink reaction. A positive value indicated that the model was capable of producing that biomass component. This helped narrow down searches for gaps (e.g., could say that a subset of amino acids was not producible, therefore there must be a gap in that pathway). When using an objective other than the biomass, we considered if there should be free transport/exchange/sinks for all biomass components simultaneously or if only the one being maximized should have a sink. Theoretically, there could be components whose production is tied and without flux through the biomass reaction, dead ends could appear that block flux.

### Step 4) Release
* What is semantic versioning
    * [Semantic Versioning](https://semver.org) is a way to define your program's version based on the type of changes you've introduced. It's defined as a three-number string (separated with a period) in the format of MAJOR.MINOR.PATCH.
    * MAJOR version when you make incompatible API changes
    * MINOR version when you add functionality in a backward compatible manner
    * PATCH version when you make backward compatible bug fixes
* What counts as a major/minor/patch change for a GEM
    * major: an ID or file layout breaks, or any growth call flips
    * minor: the model file changes without flipping a call
    * patch: the model file is unchanged
* What counts as a new version
    * With continuous curation (as in continuous integration) the `develop` branch is always tested (there shouldn't be anything broken on the `develop` branch), so a release isn't any better quality
    * A release is really just a fixed point that someone can point at and cite
    * Possible triggers of when to make a release
        * When the model leaves the lab
            * i.e., when you publish a paper, give a talk, or send the model to a collaborator for them to use
            * So that no one outside the lab/curators is ever pointing to the `develop` branch
        * When the model needs a major bump
            * Whenever you have a growth call flipped or a broken ID
        * Time-based
            * e.g. every week, or every month
            * Keeps changes from piling up, and from `develop` getting too far ahead of `main`, but some of the changes may be so small (patches), that they are meaningless on their own
        * Every merged model change (continuous delivery)
            * Every change to the model (i.e., every merge to `develop`) gets its own release
            * now every version is a very small change
            * This is continuous delivery in software engineering, and since releases are automated, there is no real cost to doing this, but most of the releases aren't really useful
    * We sit somewhere between a & b, with multiple releases before publication as major changes in the model occurred
        * trigger a (publication) is the hard rule
1. Decide what size bump is required
    * Run locally: `PYTHONPATH=code python -m tools.release check`
2. On GitHub -> Actions -> Prepare-Release -> Run Workflow
    * Branch: develop
    * Kind: whatever size bump you decided on in 1
3. Prepare-Release runs
    * It commits changes to develop with the message `release: {new version number}`
        * Updates version.txt
        * Updates the CHANGELOG.md entry
    * And opens a PR from `develop` into `main` called `release: {new version number}`
4. Upon the release PR being opened, Release-Checks runs
    * MEMOTE report [@lieven2020memote]
    * MACAW [@moyer2025macaw]
5. Wait for Release-Checks to finish
    * Can take ~15 min because of MACAW
6. Then merge the PR into main
7. The merge triggers the Publish workflow to run
    * Exports model to all formats
    * Make a tag for the new release
    * Creates the GuitHub release
        * Zenodo integration makes the DOI
    * Deploys MEMOTE to Pages

### Step 5) Run
* This is the fun part, where you, or others, actually try to use the model
* Who might be using the model
    * Yourself- as the person making the model- you probably have questions you are interested in and simulations you would like to run
    * Your collaborators
    * Strangers- people who read your paper and want to use your model- potentially years after initial publication
* Making the model available to run throughout the curation process is what makes our curation "continuous", we aren't trying to finish the model before every using it, but will update the model as issues are found in use
* This means that you can curate the model in order of scientific questions- curating the pathways relevant to specific questions first, rather than in an arbitrary order
    * This means that the model will be better in regions of the metabolic network of previous interest
* This helps discover unexpected problems in the model- tests can only catch expected problems
* For tutorials on how to use a GEM to run FBA, see COBRA tutorials
    * MATLAB: https://opencobra.github.io/cobratoolbox/stable/tutorials/
    * COBRApy: https://cobrapy.readthedocs.io/en/latest/

### Step 6) Monitor
* Typically there is limited feedback after publication- someone might try to recreate your results or use your model, but if it fails, they have no where to turn
* GitHub issues can be used to plan, discuss, and track work
* anyone can open an issue
* Use issues to keep track of bugs, enhancements, or other requests
* When to open an issue
    * You find something wrong
    * Bug/weird simulation results
    * New data to add
    * Missing feature you would like the model to have
    * Documentation confusing or unclear
    * Any type of feedback
* Open an issue
    * How to open an issue
        1. Go to the main page of the repository
        2. Click Issues
        3. Click New Issue
    * GitHub issues are written in [GitHub Flavored Markdown](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax)
* What belongs in an issue
    * A concise and descriptive title
        * e.g. model does not grow on glucose, not model wrong, or "I tried to simulate growth on glucose, and got 0.00"
    * In the description
        * Detailed description
        * Provide context- including what you expected to happen versus what actually occurred
        * Step-by-step instructions for replicating the bug
            * include code, logs, or screenshots
        * Environment details
            * What OS are you using, what version of tools (e.g., COBRApy) are you using, what version of the model are you using, did you start from a release, from the main branch, from the dev branch
    * Note your issue is public, so don't include anything you don't want shared
    * Other repos (Human-GEM) have templates for reporting bugs, which can be helpful to ensure that someone gives all of the information needed to recreate and investigate the bug
* Anyone can comment on issues
* Unlike in traditional software this is a more human-dependent step- we aren't just getting crash reports, we require people to really run the model and manually open issues
* While this might seem trivial, this is a critical step, because without opening issues curation becomes a straight line, not a loop, and can't be continuous any more- so all issues are welcome!

## Why can't you just make it for me?
* Can't you just make an installable tool that makes all of this for me?
* It is very possible to make a template- i.e. Standard-GEM
* And very possible to have packages with importable tests and shared functions
* Everyone will have different data, every model has it's own quirks, its worth writing your own to really get full coverage of your model

## Develop Good Code/GitHub Habits
* If it isn't pushed, it doesn't exist
    * Commit often, push daily
    * One commit- one reasons
* Work on a branch
    * Lets you be braver, you never have to worry about "breaking" anything
* Don't let your branch live too long
* If you've put a date or _final on a version on GitHub, you've done something wrong
    * i.e. never have model_v3_final_FINAL.xml
* Write down the why, the diff already records the what
    * Use issues like a lab notebook
    * Future you will NOT remember the why
* Don't copy and paste- if you are using the same code more than once it should be a function
    * That way if there's something wring, they are wrong in the same way, and they are never slightly different
    * Make a function with arguments, don't copy and tweak code
    * And once you make a function, make a test
* No magic numbers
    * Use named constants- define them once and use them across scripts
        * e.g., `GROWTH_THRESHOLD`
* If you're doing something by hand more than twice, automate it
* Never edit data in place
    * I.e., don't download an excel file, and add a new column and save it, now you've lost the original. Instead, keep the orginal, and in a new script, read it, make the changes, and save the copy to a new file
* Assert, don't eyeball
* Don't store the same fact twice
    * Things will drift
    * If you much, have a test to ensure that they don't drift
        * e.g., my removed reactions list

## Glossary
* **Artifact**:
  * *In software engineering*:
  * *In continuous curation*:
* **Branch**: A branch is a parallel version of a repository. It is contained within the repository, but does not affect the primary or main branch allowing you to work freely without disrupting the "live" version. [^gh-glossary].
* **Commit**: A commit, or "revision", is an individual change to a file (or set of files). When you make a commit to save your work, Git creates a unique ID (a.k.a. the "SHA" or "hash") that allows you to keep record of the specific changes committed along with who made them and when. Commits usually contain a commit message which is a brief description of what changes were made. [^gh-glossary].
* **Commit Message**: Short, descriptive text that accompanies a commit and communicates the change the commit is introducing [^gh-glossary].
* **Conflict**: A situation where two branches have changes in a file that Git cannot automatically merge, requiring manual resolution [^harvard].
* **Continuous Integration (CI)**: A development practice where team members frequently integrate their code into a shared repository, often multiple times a day. Each integration is verified by automated builds and tests to detect errors early [^agile].
* **Continuous Delivery**: A software development practice where teams keep their product in a deployable state at all times, but deployment still requires a manual decision [^agile].
* **Continuous Deployment**: A software development practice where every change that passes all automated tests is released to production automatically [^agile].
* **Curation**:
  * *In continuous curation*:
* **Diff**: A diff is the difference in changes between two commits, or saved changes. The diff will visually describe what was added or removed from a file since its last commit [^gh-glossary].
* **Feature Branch**: A branch used to experiment with a new feature or fix an issue that is not in production. Also called a topic branch [^gh-glossary].
* **Git**: Git is an open source program for tracking changes in text files [^gh-glossary].
* **GitFlow**:
* **GitHub**: A web-based platform that facilitates Git's use for collaboration between individuals. Other web-based platforms include GitLab  and BitBucket [^harvard].
* **GitHub Actions**:
* **Issue**: Issues are suggested improvements, tasks or questions related to the repository. Issues can be created by anyone (for public repositories), and are moderated by repository collaborators. Each issue contains its own discussion thread. You can also categorize an issue with labels and assign it to someone [^gh-glossary].
* **JSON**:
* **Local**: 
* **Merge**: Merging takes the changes from one branch (in the same repository or from a fork), and applies them into another. This often happens as a "pull request" (which can be thought of as a request to merge), or via the command line [^harvard].
* **Monitor**:
  * *In software engineering*:
  * *In continuous curation*:
* **Pull**: The process of integrating changes from one version of a repository to another (e.g. from a fork back to the original repo, or from a branch back to the main branch). There are two general use cases: 1) When the owner of a repository makes changes to it, you pull those changes into your local copy. 2) When you make changes to a forked repository or a branch of a repository and want to incorporate the changes back to the original repo or branch, you initiate a pull request, and then whoever is in charge of the original repository can pull those changes in  [^harvard].
* **Pull Request**: Pull requests are proposed changes to a repository submitted by a user and accepted or rejected by a repository's collaborators [^gh-glossary].
* **Push**: To push means to send your committed changes to a remote repository on GitHub.com. For instance, if you change something locally, you can push those changes so that others may access them [^gh-glossary].
* **Release**:
  * *In software engineering*:
  * *In continuous curation*:
* **Remote Repository**: This is the version of a repository or branch that is hosted on a server, most likely GitHub.com [^gh-glossary].
* **Report**:
  * *In software engineering*:
  * *In continuous curation*:
* **Repository/Repo**: A repository is the most basic element of GitHub. They're easiest to imagine as a project's folder. A repository contains all of the project files (including documentation), and stores each file's revision history. Repositories can have multiple collaborators and can be either public or private [^gh-glossary].
* **Run**:
  * *In software engineering*:
  * *In continuous curation*:
* **SBML**:
* **Script**:
  * *In software engineering*:
  * *In continuous curation*:
* **Semantic Versioning**:
* **Test**:
  * *In software engineering*:
  * *In continuous curation*:
* **Trunk-Based Development**:
* **Version Control**: The process of tracking changes to files over time, allowing you to recall specific versions later [^harvard].
* **XML**:

[^harvard]: https://informatics.fas.harvard.edu/resources/glossary/#git-terms
[^agile]: https://www.agile-academy.com/en/agile-dictionary/
[^gh-glossary]: https://docs.github.com/en/get-started/learning-about-github/github-glossary

# References