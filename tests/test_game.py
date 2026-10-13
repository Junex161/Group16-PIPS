"""Tests of the content, the level layout and the game without a visible window."""

import os
import tempfile
import unittest

# Must be set before pygame starts so that no real window or sound is needed.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from src.game import audio  # noqa: E402
from src.game.app import Game  # noqa: E402
from src.game.characters import CHARACTERS  # noqa: E402
from src.game.config import TILE_SIZE, FlankerSettings, PlayerSettings  # noqa: E402
from src.game.content import CUES, QUESTIONS, REFERENCES, SKILLS  # noqa: E402
from src.game.entities import Brute, MovingPlatform, Player  # noqa: E402
from src.game.flanker_scene import FlankerScene  # noqa: E402
from src.game.level import GROUND_ROW  # noqa: E402
from src.game.level_one import CAVE, POND, build_level_one  # noqa: E402
from src.game.menu_scenes import HomeScene  # noqa: E402
from src.game.play_scene import PlayScene  # noqa: E402
from src.game.scenes import GameOverScene, MessageScene  # noqa: E402

FRAME = 1 / 60
START_HEARTS = PlayerSettings().start_hearts


def press(key):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))


def release(key):
    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=key))


class ContentTests(unittest.TestCase):
    def test_every_note_has_one_question(self):
        self.assertEqual(sorted(q.cue_key for q in QUESTIONS), sorted(CUES))

    def test_questions_have_a_valid_answer(self):
        for question in QUESTIONS:
            self.assertEqual(len(question.options), 4)
            self.assertIn(question.correct_index, range(4))

    def test_every_cited_author_is_in_the_reference_list(self):
        sources = [cue.source for cue in CUES.values()] + [skill.source for skill in SKILLS.values()]
        for source in sources:
            for citation in filter(None, source.split("; ")):
                first_author = citation.split()[0].rstrip(",")
                year = citation[citation.index("(") + 1:citation.index(")")]
                self.assertTrue(
                    any(ref.startswith(first_author) and f"({year})" in ref for ref in REFERENCES),
                    f"{citation} is missing from REFERENCES",
                )


class AudioTests(unittest.TestCase):
    def test_melody_and_bass_have_the_same_length(self):
        for name, track in audio.TRACKS.items():
            melody = audio.render_voice(track["melody"], track["tempo"])
            bass = audio.render_voice(track["bass"], track["tempo"], "triangle")
            self.assertEqual(len(melody), len(bass), name)

    def test_note_frequencies(self):
        self.assertAlmostEqual(audio.note_frequency("A4"), 440.0)
        self.assertAlmostEqual(audio.note_frequency("A5"), 880.0)
        with self.assertRaises(ValueError):
            audio.note_frequency("H4")


class LevelTests(unittest.TestCase):
    def test_all_notes_can_be_found(self):
        level = build_level_one()
        contents = list(level.block_contents.values()) + list(level.hidden_blocks.values())
        keys = [note.key for note in level.notes] + [c.split(":")[1] for c in contents if c.startswith("note:")]
        # Professor Fin hands out the note about the flanker effect.
        self.assertEqual(sorted(keys + ["flanker"]), sorted(CUES))

    def test_pond_needs_the_bridge(self):
        level = build_level_one()
        self.assertFalse(any(level.is_solid(col, GROUND_ROW) for col in range(POND[0], POND[1] + 1)))
        level.build_bridge()
        self.assertTrue(all(level.is_solid(col, GROUND_ROW) for col in range(POND[0], POND[1] + 1)))

    def test_only_the_cave_is_dark(self):
        level = build_level_one()
        middle_of_cave = (CAVE[0] + CAVE[1]) / 2 * TILE_SIZE
        self.assertEqual(level.darkness_at(10 * TILE_SIZE), 0.0)
        self.assertEqual(level.darkness_at(middle_of_cave), 1.0)
        self.assertEqual(level.zone_at(middle_of_cave).theme, "cave")
        self.assertEqual(level.zone_at((CAVE[1] + 5) * TILE_SIZE).theme, "sunset")

    def test_skills_are_taught_in_the_level(self):
        level = build_level_one()
        self.assertEqual([shrine.skill for shrine in level.shrines], ["double_jump", "fear"])


class PhysicsTests(unittest.TestCase):
    """Checks of single game objects in the real level, without a Game."""

    def setUp(self):
        self.level = build_level_one()

    def jump_height(self, skills, n_presses):
        """Return how many pixels a player rises with the given jump presses."""
        player = Player(2 * TILE_SIZE, GROUND_ROW * TILE_SIZE, skills=skills)
        for _ in range(3):
            player.update(FRAME, 0, False, self.level)
        start_y, top_y, presses = player.y, player.y, 0
        for _ in range(240):
            if presses < n_presses and (player.on_ground or player.vy >= 0):
                player.press_jump()
                presses += 1
            player.update(FRAME, 0, False, self.level)
            top_y = min(top_y, player.y)
        return start_y - top_y

    def test_double_jump_needs_the_skill(self):
        single = self.jump_height(("punch",), 2)
        double = self.jump_height(("punch", "double_jump"), 2)
        self.assertLess(single, 4 * TILE_SIZE)
        self.assertGreater(double, 6 * TILE_SIZE)

    def test_double_jump_clears_the_wall_with_any_timing(self):
        wall_top = 8 * TILE_SIZE
        for delay in (2, 6, 12, 22, 30, 38):  # frames between the two presses
            player = Player(60 * TILE_SIZE, GROUND_ROW * TILE_SIZE, skills=("double_jump",))
            for _ in range(3):
                player.update(FRAME, 0, False, self.level)
            player.press_jump()
            lowest_bottom = player.y + player.height
            for frame in range(120):
                if frame == delay:
                    player.press_jump()
                player.update(FRAME, 0, False, self.level)
                lowest_bottom = min(lowest_bottom, player.y + player.height)
            self.assertLess(lowest_bottom, wall_top, f"second press after {delay} frames")

    def test_moving_platform_carries_the_player(self):
        platform = MovingPlatform(159 * TILE_SIZE, GROUND_ROW * TILE_SIZE, 3 * TILE_SIZE, travel_x=5 * TILE_SIZE, period=5.0)
        player = Player(160 * TILE_SIZE, GROUND_ROW * TILE_SIZE)
        offset = player.x - platform.x
        for _ in range(150):  # half a period: the platform is at its far end
            platform.update(FRAME)
            player.update(FRAME, 0, False, self.level)
            self.assertTrue(platform.carry(player))
        self.assertAlmostEqual(player.x - platform.x, offset, delta=1)
        self.assertAlmostEqual(platform.x, 164 * TILE_SIZE, delta=2)

    def test_lift_carries_the_player_up_and_down(self):
        lift = MovingPlatform(194 * TILE_SIZE, 11 * TILE_SIZE, 2 * TILE_SIZE, travel_y=-5 * TILE_SIZE, period=4.0)
        player = Player(194 * TILE_SIZE + 20, 11 * TILE_SIZE)
        for _ in range(240):
            lift.update(FRAME)
            player.update(FRAME, 0, False, self.level)
            self.assertTrue(lift.carry(player))
            self.assertAlmostEqual(player.y + player.height, lift.y, delta=0.01)

    def test_frightened_brute_runs_into_the_pit(self):
        brute = Brute(181 * TILE_SIZE, GROUND_ROW * TILE_SIZE, patrol=(177 * TILE_SIZE, 186 * TILE_SIZE))
        for _ in range(600):
            brute.update(FRAME, self.level)
        self.assertFalse(brute.is_gone)  # it stays in its tunnel by itself
        brute.frighten(PlayerSettings().fear_duration, from_x=175 * TILE_SIZE)
        for _ in range(300):
            brute.update(FRAME, self.level)
        self.assertTrue(brute.is_gone)


class GameTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        fast = FlankerSettings(n_practice_trials=2, n_test_repetitions=1, fixation_min=0.01, fixation_max=0.02, practice_feedback_time=0.02, test_feedback_time=0.02)
        self.game = Game("test", self.folder.name, seed=1, flanker_settings=fast)
        self.game.start_level()
        self.play = self.game.scenes[0]
        self.player = self.play.player

    def tearDown(self):
        pygame.quit()
        self.folder.cleanup()

    def step(self, n_frames=1):
        for _ in range(n_frames):
            self.game.step(FRAME)

    def place(self, col, surface_row=GROUND_ROW):
        """Put the player on a surface, standing still."""
        self.player.x, self.player.y = col * TILE_SIZE, surface_row * TILE_SIZE - self.player.height
        self.player.vx = self.player.vy = 0.0

    def close_text_boxes(self):
        while isinstance(self.game.scenes[-1], MessageScene):
            self.step(30)
            press(pygame.K_SPACE)
            self.step(2)

    def test_walking_and_jumping(self):
        self.step(5)
        self.assertTrue(self.player.on_ground)
        start_x, ground_y = self.player.x, self.player.y
        press(pygame.K_d)
        self.step(30)
        self.assertGreater(self.player.x, start_x + 50)
        press(pygame.K_SPACE)
        self.step(10)
        self.assertLess(self.player.y, ground_y - 50)

    def test_falling_costs_a_heart_and_respawns(self):
        self.player.x, self.player.y = 30 * TILE_SIZE, 800  # below the first pit
        self.step(2)
        self.assertEqual(self.player.hearts, START_HEARTS - 1)
        self.assertLess(self.player.x, 5 * TILE_SIZE)

    def test_losing_all_hearts_restarts_from_the_beginning(self):
        self.player.hearts = 1
        self.player.y = 2000
        self.step(2)
        self.assertIsInstance(self.game.scenes[-1], GameOverScene)
        self.step(60)
        press(pygame.K_SPACE)
        self.step(2)
        self.assertIsInstance(self.game.scenes[-1], PlayScene)
        self.assertIsNot(self.game.scenes[-1], self.play)
        self.assertEqual(self.game.scenes[-1].player.hearts, START_HEARTS)

    def test_stomping_an_enemy(self):
        enemy = self.play.enemies[0]
        self.player.x, self.player.y = enemy.x, enemy.y - 120
        self.step(60)
        self.assertNotIn(enemy, self.play.enemies)
        self.assertEqual(self.player.hearts, START_HEARTS)

    def test_touching_an_enemy_costs_a_heart(self):
        enemy = self.play.enemies[0]
        self.player.x, self.player.y = enemy.x + 20, enemy.y + enemy.height - self.player.height
        self.step(3)
        self.assertEqual(self.player.hearts, START_HEARTS - 1)

    def test_spikes_cost_a_heart(self):
        self.place(40)  # on the first spikes
        self.step(3)
        self.assertEqual(self.player.hearts, START_HEARTS - 1)

    def test_spikeback_cannot_be_stomped_but_punched(self):
        spikeback = next(enemy for enemy in self.play.enemies if enemy.kind == "spikeback")
        self.player.x, self.player.y = spikeback.x, spikeback.y - 60
        self.step(20)
        self.assertEqual(self.player.hearts, START_HEARTS - 1)
        self.assertTrue(spikeback.is_active)
        self.player.invulnerable_timer = 0.0
        self.player.x, self.player.y = spikeback.x - self.player.width - 20, spikeback.y + spikeback.height - self.player.height
        self.player.vx, self.player.facing = 0.0, 1
        press(pygame.K_f)
        self.step(2)
        self.assertFalse(spikeback.is_active)

    def test_punch_breaks_the_crates_in_the_way(self):
        self.place(18)
        self.player.facing = 1
        press(pygame.K_d)
        self.step(40)
        self.assertLess(self.player.x, 19 * TILE_SIZE)  # blocked by the crates
        press(pygame.K_f)
        self.step(60)
        self.assertGreater(self.player.x, 20 * TILE_SIZE)

    def test_shrine_teaches_the_double_jump(self):
        self.assertNotIn("double_jump", self.player.skills)
        self.place(58)
        self.step(3)
        self.assertIn("double_jump", self.player.skills)
        self.assertIsInstance(self.game.scenes[-1], MessageScene)

    def test_fear_conditioning_scares_the_brute_away(self):
        brute = next(enemy for enemy in self.play.enemies if enemy.kind == "brute")
        self.place(175)
        press(pygame.K_q)
        self.step(2)
        self.assertFalse(brute.is_afraid)  # the skill has not been learned yet
        self.player.skills.add("fear")
        press(pygame.K_q)
        self.step(2)
        self.assertTrue(brute.is_afraid)
        self.step(300)
        self.assertNotIn(brute, self.play.enemies)

    def test_admin_mode_flies_and_skips_challenges(self):
        self.step(5)
        ground_y = self.player.y
        press(pygame.K_p)
        press(pygame.K_w)
        self.step(30)
        self.assertTrue(self.play.admin)
        self.assertLess(self.player.y, ground_y - 200)  # flying up
        release(pygame.K_w)
        self.step(30)
        self.assertLess(self.player.y, ground_y - 200)  # and not falling down again
        self.place(40)  # on spikes
        self.step(5)
        self.assertEqual(self.player.hearts, START_HEARTS)
        press(pygame.K_1)
        self.step(2)
        self.close_text_boxes()
        self.assertTrue(self.play.flanker_passed)
        self.assertIn("flanker", self.play.collected_notes)
        self.assertEqual(self.game.saved_files, [])  # skipping writes no data
        press(pygame.K_2)
        press(pygame.K_3)
        self.step(2)
        self.assertTrue(self.play.gate_open)
        self.assertIn("fear", self.player.skills)

    def test_admin_mode_can_be_switched_off_for_data_collection(self):
        self.game.allow_admin = False
        press(pygame.K_F1)
        self.step(2)
        self.assertFalse(self.play.admin)

    def test_timer_keeps_running_during_text_boxes(self):
        self.step(60)
        self.game.push_scene(MessageScene(self.game, "Test", ["Text"]))
        self.step(60)
        self.assertAlmostEqual(self.play.total_time, 2.0, delta=0.05)

    def test_home_screen_switches_the_hero_and_starts_the_level(self):
        self.game.show_home()
        self.assertIsInstance(self.game.scenes[-1], HomeScene)
        press(pygame.K_d)
        self.step(2)
        self.assertIs(self.game.character, CHARACTERS[1])
        press(pygame.K_SPACE)
        self.step(2)
        self.assertIsInstance(self.game.scenes[-1], PlayScene)

    def test_perfect_flanker_run_builds_the_bridge(self):
        outcome = {}

        def on_finish(*args):
            outcome["args"] = args
            self.play._on_flanker_finished(*args)

        scene = FlankerScene(self.game, on_finish, self.game.flanker_settings, self.game.rng)
        self.game.push_scene(scene)
        keys = {"left": pygame.K_a, "right": pygame.K_d}
        for _ in range(4000):
            if self.game.scenes[-1] is not scene:
                break
            if scene.phase == "trials" and scene.trial_phase == "target" and scene.target_onset is not None:
                press(keys[scene.trials[scene.trial_index].target_direction])
            elif scene.phase != "trials":
                press(pygame.K_SPACE)
            self.step()
        passed, summary, results = outcome["args"]
        self.assertTrue(passed)
        self.assertEqual(summary.accuracy, 1.0)
        self.assertEqual(len(results), 2 + 6)
        self.assertTrue(self.play.flanker_passed)
        self.assertTrue(self.player.has_spotlight)
        self.assertEqual(len(self.game.saved_files), 1)
        self.assertTrue(self.game.saved_files[0].exists())
        self.assertIsInstance(self.game.scenes[-1], MessageScene)


if __name__ == "__main__":
    unittest.main()
