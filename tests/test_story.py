"""Tests of the Prologue and Levels 2 and 3: experiments, levels, bosses and rules."""

import csv
import os
import random
import tempfile
import unittest

# Must be set before pygame starts so that no real window or sound is needed.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from src.game import nback_task, stop_signal_task, tower_task  # noqa: E402
from src.game.app import Game  # noqa: E402
from src.game.audio import TRACKS, render_track  # noqa: E402
from src.game.bosses import CaptainImpulse, FileDrawer, RuleKeeper, make_choices  # noqa: E402
from src.game.config import DIFFICULTIES, TILE_SIZE, NBackSettings, StopSignalSettings  # noqa: E402
from src.game.content import LEVELS, REFERENCES, SKILLS  # noqa: E402
from src.game.entities import ENEMY_KINDS  # noqa: E402
from src.game.experiment_scenes import NBackScene, StopSignalScene, TowerScene  # noqa: E402
from src.game.insight_animations import ANIMATIONS  # noqa: E402
from src.game.levels import LEVEL_BUILDERS, LEVEL_ORDER, next_level  # noqa: E402
from src.game.scenes import InsightScene, LevelCompleteScene  # noqa: E402
from src.game.story_content import LEVEL_INSIGHTS, STORY_INSIGHTS, STORY_SKILLS  # noqa: E402
from src.game.story_scene import EXPERIMENTS, StoryPlayScene  # noqa: E402
from src.game.worlds import STORY_THEMES  # noqa: E402

FRAME = 1 / 60
STORY_LEVELS = ("prologue", "level_2", "level_3")


def press(key):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))


class StopSignalLogicTests(unittest.TestCase):
    def test_trials_have_the_right_share_of_stop_trials_and_start_with_go(self):
        trials = stop_signal_task.make_trials(64, 0.25, random.Random(1))
        self.assertEqual(sum(t.trial_type == "stop" for t in trials), 16)
        self.assertEqual(trials[0].trial_type, "go")
        go = [t for t in trials if t.trial_type == "go"]
        self.assertEqual(sum(t.direction == "left" for t in go), len(go) // 2)

    def test_staircase_moves_in_steps_and_stays_within_limits(self):
        staircase = stop_signal_task.Staircase(0.25, 0.05, 0.05, 0.9)
        self.assertAlmostEqual(staircase.update(stopped=True), 0.30)
        self.assertAlmostEqual(staircase.update(stopped=False), 0.25)
        for _ in range(20):
            staircase.update(stopped=False)
        self.assertAlmostEqual(staircase.value, 0.05)

    def test_ssrt_by_integration(self):
        # Ten go RTs of 100 ... 1000 ms; responding on 30% of stop trials picks the 3rd fastest.
        rts = [100 * i for i in range(1, 11)]
        self.assertEqual(stop_signal_task.ssrt_integration(rts, 0.3, 150), 300 - 150)

    def test_summary_replaces_missed_go_trials_and_scores_stops(self):
        result = stop_signal_task.StopResult
        results = [
            result("test", 1, "go", "left", None, "left", True, 400),
            result("test", 2, "go", "right", None, None, False, None),
            result("test", 3, "stop", "left", 200, None, True, None),
            result("test", 4, "stop", "left", 250, "left", False, 380),
        ]
        summary = stop_signal_task.summarise(results, 1250)
        self.assertEqual(summary.go_accuracy, 0.5)
        self.assertEqual(summary.go_omissions, 1)
        self.assertEqual(summary.stop_success, 0.5)
        self.assertEqual(summary.mean_ssd_ms, 225)
        # The missed go trial counts as the slowest RT (400 ms): rank 1 of [400, 400].
        self.assertEqual(summary.ssrt_ms, 400 - 225)
        self.assertTrue(stop_signal_task.has_passed(summary, 0.5, 0.25))
        self.assertFalse(stop_signal_task.has_passed(summary, 0.85, 0.25))

    def test_settings_are_checked(self):
        with self.assertRaises(ValueError):
            StopSignalSettings(ssd_max=2.0)


class NBackLogicTests(unittest.TestCase):
    def test_sequence_has_exactly_the_requested_targets(self):
        for seed in range(20):
            sequence = nback_task.make_sequence(2, 36, 12, "BCDFGHKL", random.Random(seed))
            letters = [letter for letter, _ in sequence]
            for index, (letter, is_target) in enumerate(sequence):
                repeats = index >= 2 and letters[index - 2] == letter
                self.assertEqual(repeats, is_target)
            self.assertEqual(sum(t for _, t in sequence), 12)

    def test_summary_and_d_prime(self):
        result = nback_task.NBackResult
        results = [result("test", 2, 1, "K", True, True, True, 500), result("test", 2, 2, "B", False, True, False, 600)]
        results += [result("test", 2, 3, "D", False, False, True, None)] * 2
        summary = nback_task.summarise(results)
        self.assertEqual((summary.hits, summary.false_alarms, summary.correct_rejections), (1, 1, 2))
        self.assertAlmostEqual(summary.accuracy, 0.75)
        self.assertGreater(nback_task.d_prime(10, 0, 0, 20), nback_task.d_prime(5, 5, 10, 10))
        self.assertAlmostEqual(nback_task.d_prime(5, 5, 5, 5), 0.0)

    def test_settings_are_checked(self):
        with self.assertRaises(ValueError):
            NBackSettings(n_test_trials=10, n_test_targets=12)


class TowerLogicTests(unittest.TestCase):
    def test_moves_respect_capacities(self):
        state = tower_task.START
        self.assertFalse(tower_task.can_move(state, 2, 0))  # the third peg is empty
        state = tower_task.move(state, 0, 2)
        self.assertFalse(tower_task.can_move(state, 0, 2))  # the third peg holds one ball
        self.assertEqual(state, (("red",), ("blue",), ("green",)))

    def test_problems_need_the_requested_number_of_moves(self):
        for problem in tower_task.make_problems((3, 4, 5), random.Random(2)):
            self.assertEqual(tower_task.min_moves(problem.start, problem.goal), problem.min_moves)
        self.assertEqual(max(tower_task.distances_from(tower_task.START).values()), 8)


class BossTests(unittest.TestCase):
    class Hero:
        center_x = 100.0

    def test_file_drawer_only_takes_damage_through_an_open_drawer(self):
        boss = FileDrawer((0, 30 * TILE_SIZE), 576, "medium", random.Random(1))
        boss.active = True
        self.assertEqual(boss.strike(boss.body_rect, "punch"), "blocked")
        boss.open_drawer = 2
        self.assertEqual(boss.strike(boss.drawer_rect(2), "punch"), "hit")
        self.assertEqual(boss.hp, boss.max_hp - 1)

    def test_captain_impulse_heals_after_attacks_on_red(self):
        boss = CaptainImpulse((0, 30 * TILE_SIZE), 576, "medium", random.Random(1))
        boss.active = True
        boss.light = "green"
        self.assertEqual(boss.strike(boss.body_rect, "punch"), "hit")
        boss.light = "red"
        self.assertEqual(boss.strike(boss.body_rect, "punch"), "heal")
        self.assertEqual(boss.hp, boss.max_hp)
        boss.light = "yellow"
        self.assertEqual(boss.strike(boss.body_rect, "punch"), "blocked")

    def test_captain_impulse_sometimes_turns_red_without_warning(self):
        boss = CaptainImpulse((0, 30 * TILE_SIZE), 576, "medium", random.Random(4))
        boss.active = True
        sudden = 0
        for _ in range(60 * 60):
            boss.update(FRAME, self.Hero())
            sudden += any(event == "stop_signal" for event, _ in boss.events)
            boss.events.clear()
        self.assertGreater(sudden, 0)

    def test_every_choice_matches_the_target_on_exactly_one_dimension(self):
        rng = random.Random(3)
        for _ in range(50):
            target = (rng.choice((1, 2, 3)), rng.choice(("red", "green", "blue")), rng.choice(("circle", "triangle", "star")))
            cards, dimensions = make_choices(target, rng)
            self.assertEqual(sorted(dimensions), ["color", "number", "shape"])
            for card, dimension in zip(cards, dimensions):
                matches = [name for name, a, b in zip(("number", "color", "shape"), card, target) if a == b]
                self.assertEqual(matches, [dimension])

    def test_rule_keeper_switches_rules_and_logs_perseveration(self):
        boss = RuleKeeper((0, 30 * TILE_SIZE), 576, [(5, 8), (10, 8), (15, 8)], "medium", random.Random(5))
        boss.active = True
        for _ in range(boss.switch_after):
            self.assertTrue(boss.choose(boss.choice_dimensions.index("color")))
            boss.feedback = None
            boss._new_round()
        self.assertEqual(boss.rule, "shape")
        self.assertFalse(boss.choose(boss.choice_dimensions.index("color")))
        self.assertTrue(boss.trials[-1]["perseverative"])


class CountHackulaTests(unittest.TestCase):
    class Hero:
        center_x = 400.0

    def make(self, difficulty="medium"):
        from src.game.hackula_boss import CountHackula

        boss = CountHackula((0, 24 * TILE_SIZE), 576, [(4, 9), (11, 9), (18, 9)], difficulty, random.Random(2))
        boss.active = True
        return boss

    def test_the_count_is_one_opponent_hidden_in_the_dark(self):
        boss = self.make()
        self.assertEqual(boss.phase, "shadow")
        body = boss.body_rect
        self.assertIsNone(boss.strike(body.move(300, 0), "punch"))
        self.assertEqual(boss.strike(body, "punch"), "hit")
        self.assertEqual(boss.hp, boss.max_hp - 1)

    def test_copies_are_distractions_and_p_hacking_feeds_him(self):
        boss = self.make()
        boss.move_timer = 0.0  # he has landed
        copies = boss.copy_rects()
        self.assertEqual(len(copies), 2)
        self.assertFalse(any(copy.colliderect(boss.body_rect) for copy in copies))
        self.assertEqual(boss.strike(copies[0], "punch"), "decoy")
        self.assertTrue(any(hazard.kind == "bat" for hazard in boss.hazards))
        self.assertEqual(boss.hp, boss.max_hp)
        boss.move_timer = 0.0
        boss.flash = 0
        boss.strike(boss.body_rect, "punch")
        boss.flash = 0
        self.assertEqual(boss.strike(boss.body_rect, "shot"), "fed")
        self.assertEqual(boss.hp, boss.max_hp)  # the QRP shot healed him again

    def test_phases_follow_each_other(self):
        boss = self.make()
        self.assertEqual(boss.phase, "shadow")
        for _ in range(boss.hits_per_phase):
            boss.flash = 0
            boss.damage()
        self.assertEqual(boss.phase, "swoop")
        boss.eyes = "red"
        boss.flash = 0
        self.assertEqual(boss.strike(boss.body_rect, "touch"), "heal")
        boss.eyes = "green"
        for _ in range(boss.hits_per_phase):
            boss.flash = 0
            self.assertEqual(boss.strike(boss.body_rect, "touch"), "hit")
        self.assertEqual(boss.phase, "sunlight")

    def test_windows_in_the_right_order_end_the_fight(self):
        from src.game.hackula_boss import WINDOWS

        boss = self.make("easy")
        boss.hp = 1
        boss._start_sunlight()
        self.assertIsNone(boss.choose(0))  # still showing the order
        boss.time = boss.shown_until
        wrong = next(index for index, window in enumerate(WINDOWS) if window != boss.sequence[0])
        self.assertFalse(boss.choose(wrong))
        boss.reset_timer = 0.0
        boss.time = boss.shown_until
        for window in boss.sequence:
            self.assertTrue(boss.choose(WINDOWS.index(window)))
        self.assertTrue(boss.defeated)

    def test_he_swoops_above_a_standing_hero(self):
        boss = self.make()
        lowest = boss.ground_y - 260 + boss.SWOOP_DEPTH
        self.assertLess(lowest + boss.RADIUS, boss.ground_y - 50)


class StoryContentTests(unittest.TestCase):
    def test_every_level_is_listed_and_playable(self):
        self.assertEqual([level.key for level in LEVELS], list(LEVEL_ORDER))
        self.assertTrue(all(level.playable for level in LEVELS))
        self.assertEqual(next_level("prologue"), "level_1")
        self.assertEqual(next_level("level_3"), "finale")
        self.assertIsNone(next_level("finale"))

    def test_every_story_insight_has_an_animation_and_a_cited_source(self):
        sources = [insight.source for insight in STORY_INSIGHTS.values()] + [skill.source for skill in STORY_SKILLS.values()]
        for key in STORY_INSIGHTS:
            self.assertIn(key, ANIMATIONS)
        for source in sources:
            for citation in filter(None, source.split("; ")):
                first_author = citation.split()[0].rstrip(",")
                year = citation[citation.index("(") + 1:citation.index(")")]
                self.assertTrue(any(ref.startswith(first_author) and f"({year})" in ref for ref in REFERENCES), citation)

    def test_references_are_sorted(self):
        self.assertEqual(list(REFERENCES), sorted(REFERENCES, key=str.lower))

    def test_every_track_of_a_new_world_renders(self):
        for theme in STORY_THEMES + ("lab",):
            self.assertIn(theme, TRACKS)
        render_track("lab")


class StoryLevelTests(unittest.TestCase):
    def test_layouts_are_consistent(self):
        for key in STORY_LEVELS:
            level = LEVEL_BUILDERS[key]()
            with self.subTest(level=key):
                for pipe in level.pipes.values():
                    if pipe.target:
                        self.assertIn(pipe.target, level.pipes)
                for zone in level.zones:
                    self.assertIn(zone.theme, STORY_THEMES)
                for start in level.enemy_starts:
                    self.assertIn(start.kind, ENEMY_KINDS)
                for npc in level.npcs:
                    if npc.kind in EXPERIMENTS:
                        self.assertIn(EXPERIMENTS[npc.kind]["gate"], level.gates)
                self.assertIn(level.quiz.gate, level.gates)
                self.assertEqual(set(level.quiz.topics), set(LEVEL_INSIGHTS[key]))
                self.assertEqual(level.zone_at(level.goal_x), level.zones[-1])

    def test_every_insight_can_be_earned(self):
        follow_ups = {"file_drawer": "file_drawer", "rule_keeper": "card_sorting", "captain_impulse": None}
        for key in STORY_LEVELS:
            level = LEVEL_BUILDERS[key]()
            earned = {orb.key for orb in level.orbs}
            earned |= {EXPERIMENTS[npc.kind]["insight"] for npc in level.npcs if npc.kind in EXPERIMENTS}
            earned.add(follow_ups[level.boss.kind])
            self.assertEqual(earned - {None}, set(LEVEL_INSIGHTS[key]), key)


class StoryPlayTests(unittest.TestCase):
    def setUp(self):
        self.data_dir = tempfile.mkdtemp()
        self.game = Game(data_dir=self.data_dir, seed=4)

    def tearDown(self):
        pygame.quit()

    def step(self, n=1):
        for _ in range(n):
            self.game.step(FRAME)

    def start(self, key):
        self.game.start_level(key)
        self.game.scenes = self.game.scenes[:1]  # skip the title card of the level
        play = self.game.scenes[0]
        for demo in play.level.demos:
            demo.shown = True  # tests that teleport the hero skip the demos
        return play

    def close_overlays(self):
        while len(self.game.scenes) > 1:
            scene = self.game.scenes[-1]
            self.game.pop_scene()
            if getattr(scene, "on_close", None):
                scene.on_close()

    def test_every_level_starts_in_every_difficulty(self):
        for difficulty in DIFFICULTIES:
            self.game.difficulty = difficulty
            for key in STORY_LEVELS:
                play = self.start(key)
                self.step(5)
                if play.boss:
                    self.assertGreater(play.boss.max_hp, 0)

    def test_prologue_needs_single_jumps_only(self):
        play = self.start("prologue")
        level, player = play.level, play.player
        jump_height = player.settings.jump_speed**2 / (2 * player.settings.gravity)
        # The QRP orb: hit the block below it, stand on it and jump.
        orb = next(orb for orb in level.orbs if orb.key == "qrps")
        col = int(orb.x // TILE_SIZE)
        block_row = next(row for row in range(int(orb.y // TILE_SIZE) + 1, 13) if level.is_solid(col, row))
        self.assertLessEqual((12 - block_row) * TILE_SIZE, jump_height)
        player.respawn(orb.x - player.width / 2, block_row * TILE_SIZE)
        self.step(2)
        press(pygame.K_SPACE)
        self.step(40)
        self.assertTrue(orb.collected)
        # Spikes under a platform: the platform must be a single jump high.
        for (spike_col, spike_row) in level.spikes:
            above = [row for row in range(spike_row - 5, spike_row) if level.is_solid(spike_col, row)]
            if above:
                self.assertLessEqual((spike_row + 1 - max(above)) * TILE_SIZE, jump_height, (spike_col, spike_row))

    def test_every_level_runs_and_draws(self):
        for key in STORY_LEVELS:
            play = self.start(key)
            self.assertIsInstance(play, StoryPlayScene)
            self.assertEqual(play.player.skills, set(play.level.start_skills))
            press(pygame.K_d)
            self.step(60)
            self.assertGreater(play.total_time, 0.5)

    def test_start_skills_grow_from_level_to_level(self):
        skills = [set(LEVEL_BUILDERS[key]().start_skills) for key in STORY_LEVELS]
        self.assertLess(skills[0], skills[1])
        self.assertLess(skills[1], skills[2])
        self.assertIn("stop", SKILLS)

    def test_ice_is_slippery_and_space_has_low_gravity(self):
        play = self.start("level_2")
        self.step(2)
        self.assertLess(play.player.settings.ground_acceleration, play.base_settings.ground_acceleration)
        play = self.start("level_3")
        station = next(zone for zone in play.level.zones if zone.theme == "space")
        play.player.teleport((station.first_col + 6) * TILE_SIZE, 12 * TILE_SIZE)
        self.step(2)
        self.assertLess(play.player.settings.gravity, play.base_settings.gravity)

    def test_moving_on_red_hurts(self):
        play = self.start("level_2")
        light = play.level.red_lights[0]
        play.player.teleport(light.first_x + 3 * TILE_SIZE, 12 * TILE_SIZE)
        play.time = 3.0 + 0.9 + 1.0 - light.offset  # in the middle of a red phase
        play.player.invulnerable_timer = 0.0
        hearts = play.player.hearts
        play.player.vx = 200.0
        play._update_red_lights(FRAME)
        self.assertEqual(play.player.hearts, hearts - 1)

    def test_switch_blocks_swap(self):
        play = self.start("level_3")
        level = play.level
        wall = next(iter(level.color_blocks["red"]))
        self.assertTrue(level.is_solid(*wall))
        level.toggle_switches()
        self.assertFalse(level.is_solid(*wall))
        self.assertTrue(all(level.is_solid(*cell) for cell in level.color_blocks["blue"]))

    def test_stop_signal_freezes_enemies(self):
        play = self.start("level_3")
        enemy = play.enemies[0]
        play.player.teleport(enemy.x - 100, 12 * TILE_SIZE)
        press(pygame.K_r)
        self.step(1)
        self.assertEqual(enemy.speed_factor, 0.0)
        self.step(int(4 / FRAME))
        self.assertGreater(enemy.speed_factor, 0.0)

    def test_winning_an_experiment_opens_its_gate_and_teaches_the_skill(self):
        play = self.start("level_2")
        play.player.skills.discard("stop")
        self.assertFalse(play.level.gate_is_open("city_gate"))
        play._win_experiment("signal_sam", "Signal Sam")
        self.assertTrue(play.level.gate_is_open("city_gate"))
        self.close_overlays()
        self.close_overlays()
        self.assertIn("stop", play.player.skills)
        self.assertIn("horse_race", play.insights)

    def test_quiz_blocks_open_the_last_gate(self):
        play = self.start("prologue")
        play.map_shown = True
        play._talk_to_quiz_owl()
        self.close_overlays()
        question = play.active_question
        wrong = (question.correct_index + 1) % len(question.options)
        hearts = play.player.hearts
        play._answer(wrong)
        self.assertEqual(play.player.hearts, hearts - 1)
        self.close_overlays()
        play._answer(play.active_question.correct_index)
        self.assertTrue(play.quiz_passed)
        self.assertTrue(play.level.gate_is_open(play.level.quiz.gate))

    def test_boss_fight_closes_and_opens_the_hall(self):
        for key in STORY_LEVELS:
            play = self.start(key)
            spec = play.level.boss
            play.player.teleport((spec.first_col + 6) * TILE_SIZE, 12 * TILE_SIZE)
            self.step(3)
            self.close_overlays()
            self.assertTrue(play.boss.active, key)
            self.assertFalse(play.level.gate_is_open(spec.gate_out))
            play.boss.damage(play.boss.hp)
            play._handle_boss_events()
            self.assertTrue(play.level.gate_is_open(spec.gate_out), key)

    def test_reaching_the_goal_offers_the_next_level(self):
        play = self.start("prologue")
        play.player.teleport(play.level.goal_x - play.player.width / 2, 12 * TILE_SIZE)
        self.step(int(4 / FRAME))
        self.assertIsInstance(self.game.scenes[-1], LevelCompleteScene)
        press(pygame.K_SPACE)
        self.step(2)
        self.assertEqual(self.game.level_key, "level_1")

    def test_game_over_restarts_the_current_level(self):
        play = self.start("level_3")
        play.player.hearts = 1
        play._lose_heart_by_falling()
        self.step(int(1 / FRAME))
        press(pygame.K_SPACE)
        self.step(2)
        self.assertEqual(self.game.level_key, "level_3")
        self.assertIsNot(self.game.scenes[0], play)

    def test_admin_mode_skips_the_story_challenges(self):
        play = self.start("level_3")
        press(pygame.K_p)
        self.step(1)
        for key in (pygame.K_1, pygame.K_2, pygame.K_5, pygame.K_6):
            press(key)
            self.step(1)
            self.close_overlays()
        self.assertTrue(all(play.level.gate_is_open(name) for name in play.level.gates))
        self.assertEqual(set(play.insights), set(LEVEL_INSIGHTS["level_3"]))

    def test_title_card_is_shown_once_per_level(self):
        from src.game.intro_scene import LevelIntroScene

        self.game.start_level("level_2")
        self.assertIsInstance(self.game.scenes[-1], LevelIntroScene)
        press(pygame.K_SPACE)
        self.step(30)
        press(pygame.K_SPACE)
        self.step(2)
        self.assertIsInstance(self.game.scenes[-1], StoryPlayScene)
        self.game.start_level("level_2")
        self.assertIsInstance(self.game.scenes[-1], StoryPlayScene)

    def test_each_world_has_its_own_platforms(self):
        for key in STORY_LEVELS:
            level = LEVEL_BUILDERS[key]()
            self.assertNotIn("brick", level.tiles.values(), key)
            for kind in set(level.tiles.values()):
                if kind.startswith("plat_"):
                    self.assertIn(kind, self.start(key).tile_images)

    def test_the_story_ends_with_the_finale(self):
        play = self.start("finale")
        play._finish_level()
        finale = self.game.scenes[-1]
        self.assertIsInstance(finale, InsightScene)
        finale.close()
        self.assertIsInstance(self.game.scenes[-1], LevelCompleteScene)
        self.assertIsNone(self.game.next_level_key())

    def test_story_animations_play(self):
        self.start("prologue")
        for key in ("hackula", "finale", "drawer_how", "impulse_how", "rules_how", "red_light_how", "switch_how", "prologue_map", "stop_skill"):
            scene = InsightScene(self.game, key)
            self.game.push_scene(scene)
            for _ in range(len(scene.animation.beats) + 1):
                self.step(30)
                press(pygame.K_SPACE)
            self.step(2)
            self.assertNotIn(scene, self.game.scenes)


class ExperimentSceneTests(unittest.TestCase):
    def setUp(self):
        self.game = Game(data_dir=tempfile.mkdtemp(), seed=6)
        self.game.start_level("level_2")
        self.outcome = None

    def tearDown(self):
        pygame.quit()

    def finish(self, passed, summary, results):
        self.outcome = (passed, summary, results)

    def run_scene(self, scene, answer, max_frames=60 * 60 * 10):
        self.game.push_scene(scene)
        for _ in range(max_frames):
            if self.outcome:
                return
            if scene.phase in ("tutorial", "practice_done", "reminder", "results", "solved") and scene.phase_age > 0.5:
                press(pygame.K_SPACE)
            elif scene.phase in ("trials", "puzzle"):
                answer(scene)
            self.game.step(FRAME)
        self.fail("the experiment did not finish")

    def test_stop_signal_task_saves_its_trials(self):
        settings = StopSignalSettings(n_practice_trials=4, n_test_trials=12)

        def answer(scene):
            trial = scene.trials[scene.trial_index]
            if scene.trial_phase == "target" and scene.target_onset is not None and trial.trial_type == "go":
                press(pygame.K_a if trial.direction == "left" else pygame.K_d)

        self.run_scene(StopSignalScene(self.game, self.finish, settings, random.Random(1)), answer)
        passed, summary, results = self.outcome
        self.assertTrue(passed)
        self.assertEqual(summary.n_go + summary.n_stop, 12)
        path = self.game.saved_files[-1]
        self.assertTrue(path.name.startswith("stopsignal_"))
        with path.open() as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(len(rows), 16)
        self.assertEqual(set(rows[0]), set(stop_signal_task.COLUMNS))

    def test_nback_task_saves_its_trials(self):
        settings = NBackSettings(n_practice_trials=6, n_practice_targets=2, n_test_trials=10, n_test_targets=3, blank_time=0.3)
        answered = set()

        def answer(scene):
            letter, is_target = scene.sequence[scene.trial_index]
            key = (scene.block, scene.trial_index)
            if is_target and scene.onset is not None and key not in answered:
                answered.add(key)
                press(pygame.K_SPACE)

        self.run_scene(NBackScene(self.game, self.finish, settings, random.Random(2)), answer)
        passed, summary, _ = self.outcome
        self.assertTrue(passed)
        self.assertEqual(summary.hits, 3)
        self.assertTrue(self.game.saved_files[-1].name.startswith("nback_"))

    def test_tower_puzzles_can_be_solved(self):
        scene = TowerScene(self.game, self.finish, rng=random.Random(3))
        plan = []

        def answer(scene):
            if not plan:
                problem = scene.problems[scene.problem_index]
                distances = tower_task.distances_from(problem.goal)
                state = scene.state
                if distances[state] == 0:
                    return
                for source in range(3):
                    for target in range(3):
                        if tower_task.can_move(state, source, target) and distances[tower_task.move(state, source, target)] == distances[state] - 1:
                            plan.extend([source, "lift", target, "drop"])
                            break
                    if plan:
                        break
            step = plan.pop(0)
            if isinstance(step, int):
                scene.cursor = step
            else:
                press(pygame.K_SPACE)

        self.run_scene(scene, answer)
        passed, summary, _ = self.outcome
        self.assertTrue(passed)
        self.assertEqual([r.moves for r in summary], [r.min_moves for r in summary])
        self.assertTrue(self.game.saved_files[-1].name.startswith("tower_"))


if __name__ == "__main__":
    unittest.main()
