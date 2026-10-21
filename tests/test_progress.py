"""Tests of the level locking and the level previews."""

import os
import tempfile
import unittest

# Must be set before pygame starts so that no real window or sound is needed.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from src.game.app import Game  # noqa: E402
from src.game.levels import LEVEL_ORDER  # noqa: E402
from src.game.menu_scenes import HomeScene  # noqa: E402
from src.game.previews import PREVIEW_SIZE, level_preview  # noqa: E402
from src.game.progress import Progress  # noqa: E402


def press(key):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))


class ProgressTests(unittest.TestCase):
    def test_levels_open_one_after_the_other_and_progress_is_saved(self):
        path = os.path.join(tempfile.mkdtemp(), "progress.json")
        progress = Progress(path, LEVEL_ORDER)
        self.assertEqual([progress.is_unlocked(key) for key in LEVEL_ORDER], [True, False, False, False, False])
        progress.complete("prologue")
        self.assertTrue(progress.is_unlocked("level_1"))
        self.assertFalse(progress.is_unlocked("level_2"))
        self.assertEqual(Progress(path, LEVEL_ORDER).completed, {"prologue"})
        self.assertEqual(Progress(path, LEVEL_ORDER).next_open(), "level_1")


class HomeLockTests(unittest.TestCase):
    def setUp(self):
        self.game = Game(data_dir=tempfile.mkdtemp(), seed=1)
        self.game.show_home()
        self.home = self.game.scenes[0]

    def tearDown(self):
        pygame.quit()

    def step(self, n=2):
        for _ in range(n):
            self.game.step(1 / 60)

    def test_a_locked_level_cannot_be_started(self):
        self.home.selected = LEVEL_ORDER.index("level_2")
        press(pygame.K_SPACE)
        self.step()
        self.assertIsInstance(self.game.scenes[-1], HomeScene)
        self.assertIn("Locked", self.home.hint)

    def test_admin_mode_opens_every_level(self):
        press(pygame.K_p)
        self.step()
        self.assertTrue(self.game.all_levels_open)
        self.home.selected = LEVEL_ORDER.index("finale")
        press(pygame.K_SPACE)
        self.step()
        self.assertEqual(self.game.level_key, "finale")

    def test_finishing_a_level_unlocks_the_next(self):
        self.game.start_level("prologue")
        play = self.game.scenes[0]
        play._start_celebration()
        self.assertTrue(self.game.is_unlocked("level_1"))

    def test_every_level_has_a_preview(self):
        for key in LEVEL_ORDER:
            self.assertEqual(level_preview(self.game, key).get_size(), PREVIEW_SIZE)


if __name__ == "__main__":
    unittest.main()
