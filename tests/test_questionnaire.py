"""Tests of the questionnaire at the start of the game."""

import csv
import os
import tempfile
import unittest

# Must be set before pygame starts so that no real window or sound is needed.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from src.game.app import Game  # noqa: E402
from src.game.menu_scenes import HomeScene  # noqa: E402
from src.game.questionnaire import COLUMNS, QUESTIONS, QuestionnaireScene  # noqa: E402
from src.game.scenes import TitleScene  # noqa: E402


def press(key):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))


class QuestionnaireTests(unittest.TestCase):
    def setUp(self):
        self.game = Game(data_dir=tempfile.mkdtemp(), seed=1)
        self.game.scenes = [TitleScene(self.game)]

    def tearDown(self):
        pygame.quit()

    def step(self, n=1):
        for _ in range(n):
            self.game.step(1 / 60)

    def answer(self, key, n_times=1):
        for _ in range(n_times):
            self.step(30)
            press(key)
        self.step(2)

    def test_title_leads_to_the_questionnaire_and_saves_the_answers(self):
        press(pygame.K_SPACE)
        self.step(2)
        self.assertIsInstance(self.game.scenes[-1], QuestionnaireScene)
        self.answer(pygame.K_d, 2)  # screen time: 3 -> 4 hours
        self.answer(pygame.K_SPACE)
        self.answer(pygame.K_a)  # short videos: 3 -> 2
        self.answer(pygame.K_SPACE, len(QUESTIONS) - 1)
        self.assertIsInstance(self.game.scenes[-1], HomeScene)
        path = self.game.saved_files[-1]
        self.assertTrue(path.name.startswith("questionnaire_"))
        with path.open(newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(list(rows[0]), list(COLUMNS))
        self.assertEqual(float(rows[0]["screen_time_hours"]), 4.0)
        self.assertEqual(float(rows[0]["short_video_frequency"]), 2)

    def test_answers_stay_on_the_scale(self):
        scene = QuestionnaireScene(self.game, lambda: None)
        self.game.scenes = [scene]
        self.answer(pygame.K_a, 20)
        self.assertEqual(scene.answers[0], QUESTIONS[0].minimum)

    def test_questionnaire_can_be_skipped_and_is_asked_only_once(self):
        press(pygame.K_SPACE)
        self.step(2)
        self.answer(pygame.K_ESCAPE)
        self.assertIsInstance(self.game.scenes[-1], HomeScene)
        self.assertEqual(self.game.saved_files, [])
        self.game.after_title()
        self.assertIsInstance(self.game.scenes[-1], HomeScene)

    def test_questionnaire_can_be_switched_off(self):
        self.game.ask_questionnaire = False
        self.game.after_title()
        self.assertIsInstance(self.game.scenes[-1], HomeScene)


if __name__ == "__main__":
    unittest.main()
