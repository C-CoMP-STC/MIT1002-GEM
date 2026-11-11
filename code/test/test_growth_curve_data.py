"""Schema tests for data/growth_curves/MIT1002_growth_curves.csv.

No model needed. These guard what the supplement promises in its header and
README, and that the committed CSV is what the cleaning script produces from the
committed raw export -- so nobody can hand-edit the supplement unnoticed.
"""

import importlib.util
import unittest

import pandas as pd

from tools.paths import DATA_DIR

GROWTH_DIR = DATA_DIR / "growth_curves"
TIDY_CSV = GROWTH_DIR / "MIT1002_growth_curves.csv"
RAW_CSV = GROWTH_DIR / "raw" / "MIT1002_growth_tests_ALL_raw.csv"
EXPECTED_COLUMNS = ["substrate", "carbon_mM_C", "replicate", "time_h", "OD600"]


def _load_cleaner():
    spec = importlib.util.spec_from_file_location(
        "clean_growth_curves", GROWTH_DIR / "clean_growth_curves.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestGrowthCurveData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = pd.read_csv(TIDY_CSV, comment="#", dtype={"carbon_mM_C": "Int64"})

    def test_header_is_documented(self):
        with TIDY_CSV.open(encoding="utf-8") as handle:
            first = handle.readline()
        self.assertTrue(first.startswith("# Supplementary File"))

    def test_columns(self):
        self.assertEqual(list(self.data.columns), EXPECTED_COLUMNS)

    def test_no_missing_readings(self):
        self.assertFalse(self.data[["substrate", "replicate", "time_h", "OD600"]].isna().any().any())

    def test_concentrations_are_known_values(self):
        known = set(self.data["carbon_mM_C"].dropna().unique())
        self.assertLessEqual(known, {6, 8, 12})

    def test_one_reading_per_well_per_time(self):
        keys = ["substrate", "carbon_mM_C", "replicate", "time_h"]
        self.assertFalse(self.data.duplicated(keys).any())

    def test_at_least_three_replicates(self):
        n = self.data.groupby(["substrate", "carbon_mM_C"], dropna=False)["replicate"].nunique()
        self.assertTrue((n >= 3).all(), n[n < 3].to_dict())

    def test_expected_substrates_present(self):
        for substrate in ["Glucose", "Mannuronic acid", "Phenylalanine"]:
            self.assertIn(substrate, set(self.data["substrate"]))

    def test_matches_cleaning_script(self):
        """The committed CSV is exactly what the script makes from the raw export."""
        cleaner = _load_cleaner()
        rebuilt = cleaner.tidy(pd.read_csv(RAW_CSV, header=None, dtype=object))
        pd.testing.assert_frame_equal(rebuilt.reset_index(drop=True), self.data,
                                      check_dtype=False)


if __name__ == "__main__":
    unittest.main()
