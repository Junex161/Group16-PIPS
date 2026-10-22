"""Tests of the ghost races."""

import os
import tempfile
import unittest

# Must be set before pygame starts so that no real window or sound is needed.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from src.game.app import Game  # noqa: E402
from src.game.characters import CHARACTERS  # noqa: E402
from src.game.config import TILE_SIZE  # noqa: E402
from src.game.ghosts import GhostRun, ghost_path, load_ghost  # noqa: E402


class FakePlayer:
    def __init__(self, x):
        self.x, self.y, self.vx, self.facing, self.on_ground = x, 500.0, 300.0, 1, True


class GhostRunTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()

    def run_level(self, seconds, speed=100.0):
        ghost = GhostRun("level_2", "medium", folder=self.folder)
        time = 0.0
        while time < seconds:
            ghost.record(time, FakePlayer(time * speed), CHARACTERS[1])
            time += 1 / 60
        return ghost, ghost.finish(seconds)

    def test_only_a_faster_run_replaces_the_ghost(self):
        _, saved = self.run_level(10)
        self.assertTrue(saved)
        self.assertAlmostEqual(load_ghost("level_2", "medium", self.folder)["time"], 10)
        _, saved = self.run_level(12)
        self.assertFalse(saved)
        _, saved = self.run_level(8)
        self.assertTrue(saved)
        self.assertAlmostEqual(load_ghost("level_2", "medium", self.folder)["time"], 8)

    def test_ghost_position_is_interpolated_and_waits_at_the_goal(self):
        self.run_level(10)
        ghost = GhostRun("level_2", "medium", folder=self.folder)
        x = ghost.position(5.0)[0]
        self.assertAlmostEqual(x, 500, delta=6)
        self.assertEqual(ghost.position(99)[0], ghost.position(10)[0])

    def test_difficulties_have_their_own_ghosts_and_broken_files_are_ignored(self):
        self.run_level(10)
        self.assertIsNone(load_ghost("level_2", "hard", self.folder))
        ghost_path("level_3", "medium", self.folder).write_text("{not json", encoding="utf-8")
        self.assertIsNone(load_ghost("level_3", "medium", self.folder))

    def test_disabled_ghosts_record_nothing(self):
        ghost = GhostRun("level_2", "medium", enabled=False, folder=self.folder)
        ghost.record(0.0, FakePlayer(0), CHARACTERS[0])
        self.assertFalse(ghost.finish(5))


class GhostInGameTests(unittest.TestCase):
    def setUp(self):
        self.data_dir = tempfile.mkdtemp()

    def tearDown(self):
        pygame.quit()

    def finish_prologue(self, game):
        game.start_level("prologue")
        game.scenes = game.scenes[:1]
        play = game.scenes[0]
        for demo in play.level.demos:
            demo.shown = True
        for _ in range(30):
            game.step(1 / 60)
        play.player.teleport(play.level.goal_x - play.player.width / 2, 12 * TILE_SIZE)
        for _ in range(10):
            game.step(1 / 60)
        return play

    def test_a_finished_level_becomes_the_ghost_of_the_next_run(self):
        game = Game(data_dir=self.data_dir, seed=1)
        game.ghost_races = True
        play = self.finish_prologue(game)
        self.assertTrue(play.ghost.new_record)
        self.assertTrue(ghost_path("prologue", "medium", game.ghost_dir).exists())
        game.start_level("prologue")
        game.scenes = game.scenes[:1]
        self.assertIsNotNone(game.scenes[0].ghost.best_time)
        game.step(1 / 60)  # the ghost is drawn without errors

    def test_the_ghost_waits_in_minigames_and_fights_a_copy_of_the_boss(self):
        game = Game(data_dir=self.data_dir, seed=1)
        game.ghost_races = True
        game.start_level("level_2")
        game.scenes = game.scenes[:1]
        play = game.scenes[0]
        boss = play.boss
        boss.active = True
        play.ghost.record(1.0, play.player, CHARACTERS[0], boss=boss)
        play.ghost.record(2.0, play.player, CHARACTERS[0], busy=True)
        play.ghost.record(2.5, play.player, CHARACTERS[0])
        play.ghost.finish(3.0)
        game.start_level("level_2")
        game.scenes = game.scenes[:1]
        ghost = game.scenes[0].ghost
        self.assertEqual(ghost.position(2.2)[-1], 1)  # busy: the ghost waits
        self.assertEqual(ghost.position(2.7)[-1], 0)
        state = ghost.boss_state(1.0)
        self.assertIsNone(ghost.boss_state(2.5))
        self.assertEqual(state["light"], boss.light)
        fake = game.scenes[0].make_boss()
        fake.apply_ghost_state(state)
        self.assertEqual(fake.x, boss.x)

    def test_ghost_races_are_off_by_default(self):
        game = Game(data_dir=self.data_dir, seed=1)
        self.assertFalse(game.ghost_races)
        play = self.finish_prologue(game)
        self.assertFalse(play.ghost.new_record)
        self.assertFalse(ghost_path("prologue", "medium", game.ghost_dir).exists())


if __name__ == "__main__":
    unittest.main()
