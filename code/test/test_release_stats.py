"""Tests for tools/release_stats.py, the release table that replaced fig. 2A.

These use made-up release rows, so they run without tags or a solver. The
real numbers come from code/scripts/generate_release_stats_table.py.
"""

import unittest

import pandas as pd

from tools import release_stats


def _release(version, tp, fn, fp, tn, reactions=1000, scored=None):
    return {
        "version": version,
        "tag": version,
        "reactions": reactions,
        "metabolites": 900,
        "genes": 800,
        "true_positive": tp,
        "false_negative": fn,
        "false_positive": fp,
        "true_negative": tn,
        "matches": tp + tn,
        "n_scored": scored if scored is not None else tp + fn + fp + tn,
    }


def _stats(*rows):
    return pd.DataFrame(list(rows))


class TestPaperTable(unittest.TestCase):
    def setUp(self):
        self.stats = _stats(
            _release("1.0.0", 0, 33, 0, 19, reactions=1335),
            _release("2.0.0", 24, 9, 4, 15),
            _release("4.0.1", 32, 1, 2, 17, reactions=1426),
        )
        self.table = release_stats.paper_table(self.stats).set_index(
            release_stats.STATISTIC_COLUMN
        )

    def test_columns_are_first_and_latest_release(self):
        self.assertEqual(
            list(self.table.columns), ["Draft (v1.0.0)", "Current (v4.0.1)"]
        )

    def test_values(self):
        self.assertEqual(self.table.loc["Reactions"].tolist(), ["1335", "1426"])
        self.assertEqual(self.table.loc["Matches"].tolist(), ["19 (37%)", "49 (94%)"])
        self.assertEqual(
            self.table.loc["Growth observed, no growth predicted"].tolist(),
            ["33", "1"],
        )

    def test_outcomes_add_up_to_denominator(self):
        outcomes = [label for label, col in release_stats.PAPER_ROWS
                    if col in ("true_positive", "false_negative",
                               "false_positive", "true_negative")]
        for column in self.table.columns:
            self.assertEqual(sum(int(self.table.loc[o, column]) for o in outcomes), 52)

    def test_denominator_in_heading(self):
        self.assertIn("Growth phenotypes (n = 52)", self.table.index)

    def test_section_rows_are_the_headings(self):
        table = release_stats.paper_table(self.stats)
        headings = [table.iloc[i, 0] for i in release_stats.section_rows(table)]
        self.assertEqual(headings, ["Model size", "Growth phenotypes (n = 52)"])

    def test_refuses_different_denominators(self):
        stats = _stats(
            _release("1.0.0", 0, 33, 0, 19),
            _release("4.0.1", 32, 1, 2, 16),  # one condition lost to a bad solve
        )
        with self.assertRaises(ValueError):
            release_stats.paper_table(stats)


if __name__ == "__main__":
    unittest.main()
