"""Tests of the flanker task logic. Run with ``python -m unittest`` from the project root."""

import csv
import random
import tempfile
import unittest
from collections import Counter

from src.game.config import FlankerSettings
from src.game.flanker_task import (
    COLUMNS,
    CONDITIONS,
    DIRECTIONS,
    FLANKER_COUNTS,
    SPACINGS,
    FlankerTrial,
    TrialResult,
    has_passed,
    make_practice_trials,
    make_trials,
    save_results,
    summarise,
)


def make_result(condition="congruent", correct=True, rt_ms=500, block="test"):
    response = "left" if correct else "right"
    return TrialResult(block, 1, condition, "left", response if rt_ms is not None else None, correct, rt_ms)


class TrialListTests(unittest.TestCase):
    def test_trials_are_balanced(self):
        trials = make_trials(2, random.Random(1))
        counts = Counter((t.condition, t.target_direction) for t in trials)
        self.assertEqual(len(trials), 72)
        self.assertEqual(set(counts.values()), {12})
        self.assertEqual(len(counts), len(CONDITIONS) * len(DIRECTIONS))
        layouts = Counter((t.condition, t.target_direction, t.spacing, t.nr_flankers) for t in trials if t.condition != "neutral")
        self.assertEqual(len(layouts), 2 * 2 * len(SPACINGS) * len(FLANKER_COUNTS))
        self.assertEqual(set(layouts.values()), {2})

    def test_neutral_trials_have_no_flankers(self):
        trial = FlankerTrial("neutral", "left", 35, 8)
        self.assertEqual((trial.spacing, trial.nr_flankers), (None, 0))
        with self.assertRaises(ValueError):
            FlankerTrial("congruent", "left", 35, 5)

    def test_practice_covers_every_condition_and_direction(self):
        practice = make_practice_trials(6, random.Random(3))
        self.assertEqual(len({(t.condition, t.target_direction) for t in practice}), 6)

    def test_same_seed_gives_same_order(self):
        self.assertEqual(make_trials(3, random.Random(5)), make_trials(3, random.Random(5)))

    def test_practice_has_requested_length(self):
        for n_trials in (0, 4, 6, 9):
            self.assertEqual(len(make_practice_trials(n_trials, random.Random(2))), n_trials)

    def test_invalid_input_is_rejected(self):
        with self.assertRaises(ValueError):
            make_trials(0)
        with self.assertRaises(ValueError):
            FlankerTrial("sideways", "left")
        with self.assertRaises(ValueError):
            FlankerSettings(pass_accuracy=1.5)

    def test_flanker_direction(self):
        self.assertEqual(FlankerTrial("congruent", "left").flanker_direction, "left")
        self.assertEqual(FlankerTrial("incongruent", "left").flanker_direction, "right")
        self.assertIsNone(FlankerTrial("neutral", "left").flanker_direction)


class ScoringTests(unittest.TestCase):
    def test_summary(self):
        results = [
            make_result("congruent", rt_ms=400),
            make_result("congruent", rt_ms=500),
            make_result("incongruent", rt_ms=600),
            make_result("incongruent", correct=False, rt_ms=300),
            make_result("neutral", correct=False, rt_ms=None),
        ]
        summary = summarise(results)
        self.assertEqual(summary.n_correct, 3)
        self.assertAlmostEqual(summary.accuracy, 0.6)
        self.assertEqual(summary.mean_rt_ms["congruent"], 450)
        self.assertEqual(summary.mean_rt_ms["incongruent"], 600)  # errors are left out
        self.assertIsNone(summary.mean_rt_ms["neutral"])
        self.assertEqual(summary.flanker_effect_ms, 150)

    def test_pass_threshold(self):
        nine_of_ten = [make_result()] * 9 + [make_result(correct=False)]
        self.assertTrue(has_passed(summarise(nine_of_ten), 0.9))
        self.assertFalse(has_passed(summarise(nine_of_ten), 0.95))
        self.assertFalse(has_passed(summarise([]), 0.9))


class SavingTests(unittest.TestCase):
    def test_csv_has_one_row_per_trial(self):
        results = [make_result(), make_result("neutral", correct=False, rt_ms=None)]
        with tempfile.TemporaryDirectory() as folder:
            path = save_results(results, "p-001", attempt=2, data_dir=folder)
            with path.open(newline="", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))
        self.assertEqual(list(rows[0]), list(COLUMNS))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["participant_id"], "p-001")
        self.assertEqual(rows[0]["attempt"], "2")
        self.assertEqual(rows[1]["rt_ms"], "")  # timeout is stored as missing
        self.assertIn("spacing", rows[0])
        self.assertIn("nr_flankers", rows[0])

    def test_empty_participant_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(ValueError):
            save_results([make_result()], "???", data_dir=folder)


if __name__ == "__main__":
    unittest.main()
