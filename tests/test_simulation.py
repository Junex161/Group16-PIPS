"""Tests of the data loading, the bootstrap and the simulation."""

import os
import tempfile
import unittest
from pathlib import Path

# Must be set before pygame starts so that no real window or sound is needed.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src import bootstrap, data, simulation  # noqa: E402
from src.game import flanker_task, nback_task, stop_signal_task  # noqa: E402
from src.game.config import FlankerSettings, NBackSettings, StopSignalSettings  # noqa: E402


def results_from(trials, cls):
    """Turn simulated rows into the game's result objects."""
    rows = trials.drop(columns=["participant_id", "attempt"]).astype(object).where(trials.notna(), None)
    return [cls(**row) for row in rows.to_dict("records")]


class DataTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        sim = simulation.simulate_participants(n=1, seed=1)
        flanker = sim.flanker.assign(participant_id="p_1")
        for timestamp, attempt in (("20261020-100000", 1), ("20261021-100000", 1), ("20261021-100500", 2)):
            flanker.assign(attempt=attempt).to_csv(self.folder / f"flanker_p_1_{timestamp}_attempt-{attempt}.csv", index=False)

    def test_file_names_with_underscores_are_parsed(self):
        self.assertEqual(data.parse_file_name("flanker_p_1_20261021-100000_attempt-2.csv"), ("flanker", "p_1", "20261021-100000", 2))

    def test_session_uses_the_first_attempt_of_the_newest_session(self):
        self.assertEqual(data.latest_participant(self.folder), "p_1")
        session = data.load_session(data_dir=self.folder, example_dir=None)
        self.assertEqual(set(session), {"participant_id", "source", "flanker"})
        self.assertEqual(session["source"], self.folder)
        self.assertTrue((session["flanker"]["attempt"] == 1).all())
        self.assertEqual(len(data.load_task("flanker", self.folder)), 3 * len(session["flanker"]))

    def test_player_with_only_a_questionnaire_is_not_chosen(self):
        sim = simulation.simulate_participants(n=1, seed=1)
        sim.questionnaire.assign(participant_id="p-late").to_csv(self.folder / "questionnaire_p-late_20261022-090000_attempt-1.csv", index=False)
        self.assertEqual(data.latest_participant(self.folder), "p_1")
        self.assertEqual(data.latest_participant(self.folder, tasks=data.TASKS), "p-late")

    def test_example_playthrough_is_used_without_any_experiment_data(self):
        empty = Path(tempfile.mkdtemp())
        session = data.load_session(data_dir=empty, example_dir=self.folder)
        self.assertEqual((session["participant_id"], session["source"]), ("p_1", self.folder))
        self.assertIn("flanker", session)
        # A real player always takes precedence over the example.
        other = Path(tempfile.mkdtemp())
        (self.folder / "flanker_p_1_20261021-100000_attempt-1.csv").rename(other / "flanker_p-real_20261022-100000_attempt-1.csv")
        self.assertEqual(data.load_session(data_dir=other, example_dir=self.folder)["participant_id"], "p-real")

    def test_empty_folder_gives_no_participant(self):
        empty = tempfile.mkdtemp()
        self.assertIsNone(data.latest_participant(empty))
        self.assertTrue(data.load_task("nback", empty).empty)
        self.assertEqual(data.load_session(data_dir=empty, example_dir=None), {"participant_id": None, "source": None})
        self.assertEqual(data.load_session(data_dir=empty, example_dir=tempfile.mkdtemp())["participant_id"], None)

    def test_unknown_task_is_rejected(self):
        with self.assertRaises(ValueError):
            data.load_task("stroop", self.folder)


class BootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sim = simulation.simulate_participants(n=1, seed=3, nback_settings=NBackSettings(n_test_trials=120, n_test_targets=40))
        cls.session = {"participant_id": "sim-001", **sim.tasks()}

    def test_measures_match_the_game(self):
        flanker = flanker_task.summarise(results_from(self.session["flanker"], flanker_task.TrialResult))
        measures = bootstrap.flanker_measures(self.session["flanker"])
        self.assertAlmostEqual(measures["flanker_effect_ms"], flanker.flanker_effect_ms)
        stop = stop_signal_task.summarise(results_from(self.session["stopsignal"], stop_signal_task.StopResult), 1250)
        self.assertAlmostEqual(bootstrap.stop_signal_measures(self.session["stopsignal"])["ssrt_ms"], stop.ssrt_ms)
        nback = nback_task.summarise(results_from(self.session["nback"], nback_task.NBackResult))
        self.assertAlmostEqual(bootstrap.nback_measures(self.session["nback"])["d_prime"], nback.d_prime)

    def test_same_seed_gives_same_distribution_and_ci_holds_estimate(self):
        first = bootstrap.bootstrap_task("flanker", self.session["flanker"], n_resamples=300, seed=5)
        second = bootstrap.bootstrap_task("flanker", self.session["flanker"], n_resamples=300, seed=5)
        effect = first["flanker_effect_ms"]
        np.testing.assert_array_equal(effect.samples, second["flanker_effect_ms"].samples)
        lower, upper = effect.ci()
        self.assertLess(lower, effect.estimate)
        self.assertLess(effect.estimate, upper)
        self.assertGreater(effect.sd, 0)

    def test_session_skips_missing_tasks_and_summarises(self):
        results = bootstrap.bootstrap_session({"participant_id": "x", "flanker": self.session["flanker"]}, n_resamples=50)
        self.assertEqual(set(results), {"flanker"})
        table = bootstrap.summary_table(results)
        self.assertEqual(list(table.index.get_level_values("measure")), list(bootstrap.MEASURES["flanker"]))

    def test_results_are_saved(self):
        results = bootstrap.bootstrap_session(self.session, n_resamples=20)
        summary_path, samples_path = bootstrap.save_bootstrap(results, "sim-001", tempfile.mkdtemp())
        summary, samples = pd.read_csv(summary_path), pd.read_csv(samples_path)
        n_measures = sum(len(measures) for measures in bootstrap.MEASURES.values())
        self.assertEqual(len(summary), n_measures)
        self.assertEqual(len(samples), 20 * n_measures)
        self.assertTrue((summary["participant_id"] == "sim-001").all())
        self.assertEqual(bootstrap.save_bootstrap({}), [])

    def test_invalid_input_is_rejected(self):
        with self.assertRaises(ValueError):
            bootstrap.bootstrap_task("flanker", self.session["flanker"].iloc[0:0])
        with self.assertRaises(ValueError):
            bootstrap.bootstrap_task("tower", self.session["flanker"])


class SimulationTests(unittest.TestCase):
    def test_tables_have_the_game_columns_and_design(self):
        sim = simulation.simulate_participants(n=4, seed=1)
        self.assertEqual(tuple(sim.flanker.columns), flanker_task.COLUMNS)
        self.assertEqual(tuple(sim.stopsignal.columns), stop_signal_task.COLUMNS)
        self.assertEqual(tuple(sim.nback.columns), nback_task.COLUMNS)
        self.assertEqual(len(sim.questionnaire), 4)
        trials = sim.flanker.groupby("participant_id").size()
        self.assertTrue((trials == 36 * FlankerSettings().n_test_repetitions).all())
        self.assertTrue((sim.stopsignal.groupby("participant_id").size() == StopSignalSettings().n_test_trials).all())
        self.assertTrue((sim.nback.groupby("participant_id").size() == NBackSettings().n_test_trials).all())

    def test_same_seed_same_players(self):
        first, second = simulation.simulate_participants(n=3, seed=7), simulation.simulate_participants(n=3, seed=7)
        for task in first.tasks():
            pd.testing.assert_frame_equal(first.tasks()[task], second.tasks()[task])
        other = simulation.simulate_participants(n=3, seed=8)
        self.assertFalse(first.flanker["rt_ms"].equals(other.flanker["rt_ms"]))

    def test_without_bootstrap_the_literature_is_used(self):
        parameters = simulation.simulate_participants(n=2, seed=1).parameters
        self.assertAlmostEqual(parameters.loc[("flanker", "flanker_effect_ms"), "mean"], 117.29)
        self.assertIn("Kaufman", parameters.loc[("flanker", "flanker_effect_ms"), "source"])

    def test_player_and_literature_are_weighted_by_precision(self):
        sim = simulation.simulate_participants(n=1, seed=2)
        results = bootstrap.bootstrap_session({"participant_id": "sim-001", **sim.tasks()}, n_resamples=200)
        parameters = simulation.simulate_participants(n=2, bootstrap=results, participant_id="p-real").parameters
        row = parameters.loc[("flanker", "flanker_effect_ms")]
        effect = results["flanker"]["flanker_effect_ms"]
        weight = 22.3**2 / (22.3**2 + effect.sd**2)
        self.assertAlmostEqual(row["player_weight"], weight)
        self.assertAlmostEqual(row["mean"], weight * effect.estimate + (1 - weight) * 117.29)
        self.assertEqual(row["between_person_sd"], 22.3)
        self.assertIn("p-real", row["source"])
        # Values without a between-person SD take the player's own estimate.
        noise = parameters.loc[("flanker", "trial_sd_ms")]
        self.assertAlmostEqual(noise["mean"], results["flanker"]["trial_sd_ms"].estimate)

    def test_precise_players_count_more_than_noisy_ones(self):
        population = simulation.Value(100.0, 20.0, "test")
        precise, precise_weight = simulation.precision_weighted_mean(50.0, 5.0, population)
        noisy, noisy_weight = simulation.precision_weighted_mean(50.0, 100.0, population)
        self.assertGreater(precise_weight, 0.9)
        self.assertLess(noisy_weight, 0.05)
        self.assertLess(precise, 55)
        self.assertGreater(noisy, 95)
        self.assertEqual(simulation.precision_weighted_mean(50.0, 0.0, population), (50.0, 1.0))
        with self.assertRaises(ValueError):
            simulation.precision_weighted_mean(50.0, 5.0, simulation.Value(100.0, 0.0, "no SD"))

    def test_built_in_values_are_recovered(self):
        sim = simulation.simulate_participants(n=300, seed=11, effects=simulation.Effects(screen_time_on_flanker_ms=10))
        truth = sim.true_values.merge(sim.questionnaire, on="participant_id")
        slope = np.polyfit(truth["screen_time_hours"], truth["flanker_effect_ms"], 1)[0]
        self.assertAlmostEqual(slope, 10, delta=3)
        effects = [bootstrap.flanker_measures(trials)["flanker_effect_ms"] for _, trials in sim.flanker.groupby("participant_id")]
        self.assertAlmostEqual(np.mean(effects), truth["flanker_effect_ms"].mean(), delta=10)
        stop_success = sim.stopsignal.loc[sim.stopsignal["trial_type"] == "stop", "correct"].mean()
        self.assertAlmostEqual(stop_success, 0.5, delta=0.1)

    def test_questionnaire_answers_are_in_range(self):
        questionnaire = simulation.simulate_participants(n=200, seed=4).questionnaire
        self.assertTrue(questionnaire["screen_time_hours"].between(0, 16).all())
        for column in simulation.ANSWER_SHARES:
            self.assertTrue(questionnaire[column].between(1, 5).all())
        self.assertGreater(questionnaire["screen_time_hours"].corr(questionnaire["short_video_frequency"]), 0.2)

    def test_saved_files_can_be_loaded_again(self):
        folder = tempfile.mkdtemp()
        sim = simulation.simulate_participants(n=2, seed=1)
        paths = sim.save(folder)
        self.assertEqual(len(paths), 6)
        reloaded = data.load_task("flanker", folder)
        self.assertEqual(len(reloaded), len(sim.flanker))

    def test_invalid_input_is_rejected(self):
        with self.assertRaises(ValueError):
            simulation.simulate_participants(n=0)
        with self.assertRaises(ValueError):
            simulation.Effects(short_video_screen_time_correlation=2)



if __name__ == "__main__":
    unittest.main()
