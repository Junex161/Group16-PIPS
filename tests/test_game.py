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
from src.game.config import DIFFICULTIES, TILE_SIZE, FlankerSettings, PlayerSettings  # noqa: E402
import random  # noqa: E402

from src.game.content import INSIGHTS, QUIZ_TOPICS, REFERENCES, SKILLS  # noqa: E402
from src.game.entities import Brute, CrumblePlatform, FireBar, MovingPlatform, Player  # noqa: E402
from src.game.flanker_scene import FlankerScene  # noqa: E402
from src.game.level import GROUND_ROW  # noqa: E402
from src.game.level_one import CAVE, N_QUIZ_PIPES, POND, build_level_one  # noqa: E402
from src.game.menu_scenes import HomeScene  # noqa: E402
from src.game.play_scene import PlayScene  # noqa: E402
from src.game.scenes import GameOverScene, MessageScene, TransitionScene  # noqa: E402
from src.game.insight_animations import ANIMATIONS, Stage  # noqa: E402
from src.game.play_scene import make_question  # noqa: E402
from src.game.scenes import InsightScene, NotebookScene  # noqa: E402

FRAME = 1 / 60
START_HEARTS = PlayerSettings().start_hearts


def press(key):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))


def release(key):
    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=key))


class _SilentSound:
    """Stands in for a pygame Sound in tests."""


class _SilentChannel:
    """Stands in for a pygame Channel in tests."""

    def play(self, sound, loops=0, fade_ms=0):
        pass

    def pause(self):
        pass

    def unpause(self):
        pass


class ContentTests(unittest.TestCase):
    def test_every_insight_has_an_animation(self):
        self.assertTrue(set(INSIGHTS) <= set(ANIMATIONS))
        self.assertTrue(set(QUIZ_TOPICS) <= set(INSIGHTS))

    def test_questions_have_one_right_answer_per_quiz_pipe(self):
        rng = random.Random(3)
        for topic in QUIZ_TOPICS:
            question = make_question(topic, rng, N_QUIZ_PIPES)
            self.assertEqual(len(set(question.options)), N_QUIZ_PIPES)
            self.assertEqual(question.options[question.correct_index], topic)

    def test_captions_stay_short(self):
        for animation in ANIMATIONS.values():
            for beat in animation.beats:
                self.assertLessEqual(len(beat.caption.split()), 12, beat.caption)

    def test_every_cited_author_is_in_the_reference_list(self):
        sources = [insight.source for insight in INSIGHTS.values()] + [skill.source for skill in SKILLS.values()]
        for source in sources:
            for citation in filter(None, source.split("; ")):
                first_author = citation.split()[0].rstrip(",")
                year = citation[citation.index("(") + 1:citation.index(")")]
                self.assertTrue(
                    any(ref.startswith(first_author) and f"({year})" in ref for ref in REFERENCES),
                    f"{citation} is missing from REFERENCES",
                )


class AudioTests(unittest.TestCase):
    def test_every_part_fills_its_track(self):
        for name, track in audio.TRACKS.items():
            for text, _, _ in track["parts"]:
                self.assertAlmostEqual(audio.total_beats(audio.parse(text)), track["bars"] * audio.BEATS_PER_BAR, msg=name)

    def test_melodies_stay_in_a_comfortable_range(self):
        for name, track in audio.TRACKS.items():
            for text, _, _ in track["parts"]:
                notes = [note for names, _ in audio.parse(text) for note in names]
                self.assertLess(max(audio.note_frequency(note) for note in notes), 800, name)  # nothing shrill

    def test_music_loops_without_clicks(self):
        for name in audio.TRACKS:
            samples = audio.render_track(name)
            self.assertLessEqual(abs(samples).max(), 1.0)
            # The end of the loop flows into its start without a jump.
            self.assertLess(abs(samples[-1] - samples[0]), 0.05, name)

    def test_notes_start_and_end_silently(self):
        for instrument in audio.INSTRUMENTS:
            note = audio.render_note(440.0, 0.3, instrument)
            self.assertLess(abs(note[0]), 0.01, instrument)
            self.assertLess(abs(note[-1]), 0.01, instrument)

    def test_note_frequencies(self):
        self.assertAlmostEqual(audio.note_frequency("A4"), 440.0)
        self.assertAlmostEqual(audio.note_frequency("A5"), 880.0)
        with self.assertRaises(ValueError):
            audio.note_frequency("H4")


class LevelTests(unittest.TestCase):
    def test_every_insight_can_be_earned(self):
        level = build_level_one()
        keys = [orb.key for orb in level.orbs]
        self.assertEqual(keys[0], "attention")  # the level starts with what attention is
        # Professor Fin hands out the insight about the flanker effect.
        self.assertEqual(sorted(keys + ["flanker"]), sorted(INSIGHTS))

    def test_pipes_lead_to_existing_pipes(self):
        level = build_level_one()
        for pipe in level.pipes.values():
            if pipe.kind != "exit":
                self.assertIn(pipe.target, level.pipes, pipe.name)
        answers = sorted(pipe.answer_index for pipe in level.pipes.values() if pipe.kind == "quiz")
        self.assertEqual(answers, list(range(N_QUIZ_PIPES)))

    def test_worlds_are_closed_off_and_wide_enough_for_the_camera(self):
        level = build_level_one()
        for zone in level.zones:
            self.assertGreaterEqual((zone.last_col - zone.first_col + 1) * TILE_SIZE, 1280)
        # The cave can only be left through its pipe: walls at both ends.
        for col in (CAVE[0], CAVE[1]):
            self.assertTrue(all(level.is_solid(col, row) for row in range(GROUND_ROW)))

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
        self.assertEqual(level.darkness_at((level.n_cols - 5) * TILE_SIZE), 0.0)  # the bonus room is lit

    def test_skills_are_taught_in_the_level(self):
        level = build_level_one()
        self.assertEqual([shrine.skill for shrine in level.shrines], ["double_jump", "fear", "blaster"])


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


class NewObstacleTests(unittest.TestCase):
    """Springs, crumbling platforms and fire bars."""

    def setUp(self):
        self.level = build_level_one()

    def test_spring_launches_higher_than_a_double_jump(self):
        player = Player(334 * TILE_SIZE, GROUND_ROW * TILE_SIZE)
        player.spring()
        lowest = player.y
        for _ in range(90):
            player.update(FRAME, 0, False, self.level)
            player.release_jump()  # letting go does not cut a spring jump short
            lowest = min(lowest, player.y)
        self.assertLess(lowest + player.height, 4 * TILE_SIZE)  # above the high ledge in the woods

    def test_crumbling_platform_falls_and_comes_back(self):
        platform = CrumblePlatform(337 * TILE_SIZE, 9 * TILE_SIZE, 2 * TILE_SIZE)
        player = Player(337 * TILE_SIZE + 10, 9 * TILE_SIZE)
        player.previous_bottom = player.y + player.height
        self.assertTrue(platform.carry(player))
        self.assertEqual(platform.state, "shaking")
        for _ in range(120):
            platform.update(FRAME)
        self.assertIn(platform.state, ("falling", "gone"))
        for _ in range(400):
            platform.update(FRAME)
        self.assertEqual(platform.state, "solid")
        self.assertEqual(platform.y, 9 * TILE_SIZE)

    def test_fire_bar_turns_and_hurts_on_touch(self):
        bar = FireBar(100, 100, n_balls=4, speed=2.0)
        first = bar.balls[-1]
        bar.update(0.5)
        self.assertNotEqual(first, bar.balls[-1])
        x, y = bar.balls[2]
        self.assertTrue(bar.hits(pygame.Rect(x - 5, y - 5, 10, 10)))
        self.assertFalse(bar.hits(pygame.Rect(400, 400, 10, 10)))

    def test_sky_brute_can_be_scared_into_the_void(self):
        brute = Brute(489 * TILE_SIZE, GROUND_ROW * TILE_SIZE, patrol=(486 * TILE_SIZE, 495 * TILE_SIZE))
        brute.frighten(PlayerSettings().fear_duration, from_x=483 * TILE_SIZE)
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
        # Most tests are about movement; keep the insight animations out of the way.
        for orb in self.play.level.orbs:
            orb.collected = True
        for demo in self.play.level.demos:
            demo.shown = True

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

    def test_blaster_is_the_reward_at_the_end(self):
        self.assertNotIn("blaster", self.player.skills)
        press(pygame.K_g)
        self.step(2)
        self.assertEqual(self.play.projectiles, [])
        shrine = next(shrine for shrine in self.play.level.shrines if shrine.skill == "blaster")
        self.assertGreater(shrine.x, self.play.level.pipes["goal_entry"].x)
        self.player.x, self.player.y = shrine.x - self.player.width / 2, shrine.ground_y - self.player.height
        self.step(3)
        self.assertIn("blaster", self.player.skills)
        self.assertIsInstance(self.game.scenes[-1], InsightScene)  # the QRP animation
        self.assertIsNotNone(self.game.scenes[-1].insight)  # with its own card

    def test_blaster_knocks_out_enemies_and_breaks_crates(self):
        self.player.skills.add("blaster")
        enemy = self.play.enemies[0]
        self.player.x, self.player.y = enemy.x - 250, enemy.y + enemy.height - self.player.height
        self.player.facing = 1
        press(pygame.K_g)
        self.step(30)
        self.assertFalse(enemy.is_active)
        self.assertEqual(self.player.hearts, START_HEARTS)
        self.place(14)
        self.assertTrue(self.play.level.is_solid(19, 11))
        self.player.shot_cooldown = 0.0
        press(pygame.K_g)
        self.step(30)
        self.assertFalse(self.play.level.is_solid(19, 11))

    def test_blaster_does_not_hurt_a_brute(self):
        self.player.skills.add("blaster")
        brute = next(enemy for enemy in self.play.enemies if enemy.kind == "brute")
        self.place(175)
        self.player.facing = 1
        press(pygame.K_g)
        self.step(40)
        self.assertTrue(brute.is_active)
        self.assertEqual(self.play.projectiles, [])

    def release_item(self, kind):
        """Let an item come out of a block right next to the hero and pick it up."""
        self.place(10)
        self.play._release_block_content(kind, (10, GROUND_ROW - 1))
        self.step(10)

    def test_items_do_what_they_promise(self):
        self.release_item("mushroom")
        self.assertTrue(self.player.is_boosted)
        self.release_item("shield")
        self.assertTrue(self.player.has_shield)
        self.assertFalse(self.player.take_hit(0))  # the shield takes the hit ...
        self.assertEqual(self.player.hearts, START_HEARTS)
        self.assertFalse(self.player.has_shield)  # ... and is gone
        self.release_item("star")
        self.assertTrue(self.player.has_star)

    def test_star_has_its_own_music(self):
        self.game.audio.enabled = True  # track names are recorded even without a sound device
        self.game.audio._music = {name: _SilentSound() for name in audio.TRACKS}
        self.game.audio._music_channel = _SilentChannel()
        self.step(2)
        self.assertEqual(self.game.audio.current_track, "meadow")
        self.player.star_timer = 2.0
        self.step(2)
        self.assertEqual(self.game.audio.current_track, "star")
        self.player.star_timer = 0.0
        self.step(2)
        self.assertEqual(self.game.audio.current_track, "meadow")

    def test_star_defeats_enemies_on_touch(self):
        self.player.star_timer = 5.0
        enemy = self.play.enemies[0]
        self.player.x, self.player.y = enemy.x + 5, enemy.y + enemy.height - self.player.height
        self.step(3)
        self.assertFalse(enemy.is_active)
        self.assertEqual(self.player.hearts, START_HEARTS)

    def test_items_stay_active_after_a_pipe(self):
        self.player.star_timer = 5.0
        self.player.has_shield = True
        self.play._arrive_at("cave_entry")
        self.assertTrue(self.player.has_star)
        self.assertTrue(self.player.has_shield)

    def test_pipe_trip_shows_a_loading_screen(self):
        self.play._travel(self.play.level.pipes["woods_exit"])
        scene = self.game.scenes[-1]
        self.assertIsInstance(scene, TransitionScene)
        self.step(int(scene.total_time * 60) + 5)
        self.assertIsInstance(self.game.scenes[-1], PlayScene)
        self.assertTrue(self.play.level.zone_at(self.player.center_x).dark)

    def test_punch_demo_plays_once_near_the_first_crates(self):
        demo = self.play.level.demos[0]
        demo.shown = False
        self.place(int(demo.x // TILE_SIZE) + 1)
        self.step(2)
        self.assertIsInstance(self.game.scenes[-1], InsightScene)
        self.assertEqual(self.game.scenes[-1].animation.title, ANIMATIONS["punch"].title)
        press(pygame.K_ESCAPE)
        self.step(5)
        self.assertIsInstance(self.game.scenes[-1], PlayScene)

    def test_fear_shrine_plays_its_animation_first(self):
        shrine = next(shrine for shrine in self.play.level.shrines if shrine.skill == "fear")
        self.player.x, self.player.y = shrine.x - self.player.width / 2, shrine.ground_y - self.player.height
        self.step(3)
        self.assertIn("fear", self.player.skills)
        self.assertIsInstance(self.game.scenes[-1], InsightScene)
        self.assertEqual(self.game.scenes[-1].insight.term, "FEAR CONDITIONING")

    def test_goal_starts_fireworks_and_then_the_end_screen(self):
        goal_x = self.play.level.goal_x
        self.player.x, self.player.y = goal_x - self.player.width / 2, GROUND_ROW * TILE_SIZE - self.player.height
        self.step(30)
        self.assertIsNotNone(self.play.celebration_time)
        self.assertTrue(self.play.fireworks)
        self.assertIsInstance(self.game.scenes[-1], PlayScene)
        self.step(200)
        self.assertEqual(type(self.game.scenes[-1]).__name__, "LevelCompleteScene")

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
        self.assertIn("flanker", self.play.insights)
        self.assertEqual(self.game.saved_files, [])  # skipping writes no data
        press(pygame.K_3)
        press(pygame.K_5)
        press(pygame.K_2)
        self.step(2)
        self.assertIn("fear", self.player.skills)
        self.assertEqual(sorted(self.play.insights), sorted(INSIGHTS))
        self.assertTrue(self.play.quiz_passed)
        self.assertGreater(self.player.x, 278 * TILE_SIZE)  # behind the wall

    def test_admin_mode_can_be_switched_off_for_data_collection(self):
        self.game.allow_admin = False
        press(pygame.K_F1)
        self.step(2)
        self.assertFalse(self.play.admin)

    def enter_pipe(self, name):
        """Stand on a pipe, press S and wait for the trip to end."""
        pipe = self.play.level.pipes[name]
        self.player.x, self.player.y = pipe.x - self.player.width / 2, pipe.ground_y - self.player.height
        self.player.vx = self.player.vy = 0.0
        self.step(3)
        press(pygame.K_s)
        self.step(2)

    def test_pipe_leads_to_the_cave_and_back_from_the_bonus_room(self):
        self.enter_pipe("to_woods")
        self.step(130)
        self.assertEqual(self.play.level.zone_at(self.player.center_x).theme, "forest")
        self.enter_pipe("woods_exit")
        self.assertIsInstance(self.game.scenes[-1], TransitionScene)
        self.step(130)  # wait until the loading screen is over
        self.assertEqual(self.play.level.zone_at(self.player.center_x).theme, "cave")
        self.assertTrue(self.play.level.zone_at(self.player.center_x).dark)
        self.assertGreaterEqual(self.play.camera_x, CAVE[0] * TILE_SIZE)  # the camera stays in the cave
        self.enter_pipe("to_bonus_room")
        self.step(130)  # wait until the loading screen is over
        self.assertGreater(self.player.x, 294 * TILE_SIZE)
        self.enter_pipe("bonus_room_exit")
        self.step(130)  # wait until the loading screen is over
        self.assertAlmostEqual(self.player.center_x, self.play.level.pipes["from_bonus_room"].x, delta=2)

    def test_only_the_right_quiz_pipe_leads_to_the_goal(self):
        self.enter_pipe("answer_0")
        self.assertFalse(self.play.quiz_passed)  # the owl has not asked yet
        self.assertIsInstance(self.game.scenes[-1], PlayScene)
        self.play._next_question()
        question = self.play.active_question
        wrong = next(index for index in range(N_QUIZ_PIPES) if index != question.correct_index)
        self.enter_pipe(f"answer_{wrong}")
        self.assertEqual(self.player.hearts, START_HEARTS - 1)
        self.assertFalse(self.play.quiz_passed)
        self.close_text_boxes()
        self.assertIsNot(self.play.active_question, question)  # a new question
        self.enter_pipe(f"answer_{self.play.active_question.correct_index}")
        self.step(60)
        self.assertTrue(self.play.quiz_passed)
        self.assertGreater(self.player.x, 278 * TILE_SIZE)

    def test_orb_plays_its_animation_and_then_earns_the_insight(self):
        orb = self.play.level.orbs[0]
        orb.collected = False
        self.player.x, self.player.y = orb.x - self.player.width / 2, orb.y - self.player.height / 2
        self.step(2)
        scene = self.game.scenes[-1]
        self.assertIsInstance(scene, InsightScene)
        self.assertEqual(self.play.insights, [])
        for _ in range(1500):  # the beats advance on their own ...
            self.step()
        self.assertTrue(scene.on_card)  # ... until the final card
        press(pygame.K_SPACE)
        self.step(2)
        self.assertIsInstance(self.game.scenes[-1], PlayScene)
        self.assertEqual(self.play.insights, [orb.key])
        self.assertTrue(orb.collected)

    def test_notebook_replays_an_animation(self):
        self.play.insights = ["attention", "gorilla"]
        press(pygame.K_TAB)
        self.step(2)
        self.assertIsInstance(self.game.scenes[-1], NotebookScene)
        press(pygame.K_s)
        press(pygame.K_SPACE)
        self.step(2)
        self.assertIsInstance(self.game.scenes[-1], InsightScene)
        self.assertEqual(self.game.scenes[-1].animation.title, ANIMATIONS["gorilla"].title)

    def test_every_beat_and_thumbnail_can_be_drawn(self):
        surface = pygame.Surface((1280, 720))
        for key, animation_class in ANIMATIONS.items():
            animation = animation_class(CHARACTERS[2])
            for index in range(len(animation.beats)):
                for share in (0.0, 0.5, 1.0):
                    animation.draw_beat(surface, Stage(pygame.Rect(190, 100, 900, 450)), index, share, share * 4)
            animation.draw_thumbnail(surface, pygame.Rect(0, 0, 240, 120), 1.3)

    def test_owl_shows_the_big_picture_before_the_quiz(self):
        owl = next(npc for npc in self.play.level.npcs if npc.kind == "owl")
        self.player.x, self.player.y = owl.x - 60, owl.ground_y - self.player.height
        self.step(2)
        press(pygame.K_e)
        self.step(2)
        self.assertIsInstance(self.game.scenes[-1], InsightScene)
        self.assertEqual(self.game.scenes[-1].animation.title, ANIMATIONS["map"].title)
        press(pygame.K_ESCAPE)
        self.step(2)
        self.assertIsNotNone(self.play.active_question)
        self.assertIn(self.play.active_question.topic, QUIZ_TOPICS)

    def start_with(self, difficulty_key):
        self.game.difficulty = next(d for d in DIFFICULTIES if d.key == difficulty_key)
        self.game.start_level()
        self.play = self.game.scenes[0]
        self.player = self.play.player

    def test_easy_mode_is_more_forgiving(self):
        n_enemies_medium = len(self.play.enemies)
        self.start_with("easy")
        self.assertEqual(self.player.hearts, 5)
        self.assertLess(len(self.play.enemies), n_enemies_medium)
        self.assertTrue(any(enemy.kind == "brute" for enemy in self.play.enemies))
        self.assertEqual(self.play.flanker_settings.pass_accuracy, 0.75)
        # Pits are narrower: the first one (columns 29 to 31) lost a tile,
        # the wide one (71 to 76) lost one on each side.
        self.assertIn((30, 31), self.play.level.pits())
        self.assertIn((72, 75), self.play.level.pits())
        self.assertFalse(self.play.level.is_solid(POND[0], GROUND_ROW))  # the pond stays
        self.player.y = 2000  # falling is free
        self.step(2)
        self.assertEqual(self.player.hearts, 5)

    def test_hard_mode_has_faster_enemies(self):
        medium_speed = abs(self.play.enemies[0].SPEED * self.play.enemies[0].speed_factor)
        self.start_with("hard")
        enemy = self.play.enemies[0]
        self.assertGreater(enemy.SPEED * enemy.speed_factor, medium_speed)
        self.assertEqual(self.player.settings.max_hearts, 4)

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
        self.assertIsInstance(self.game.scenes[0], PlayScene)

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
        self.assertEqual(len(results), 2 + 36)  # 2 practice trials and one balanced set of 36
        self.assertTrue(self.play.flanker_passed)
        self.assertTrue(self.player.has_spotlight)
        self.assertEqual(len(self.game.saved_files), 1)
        self.assertTrue(self.game.saved_files[0].exists())
        self.assertIsInstance(self.game.scenes[-1], MessageScene)


if __name__ == "__main__":
    unittest.main()
