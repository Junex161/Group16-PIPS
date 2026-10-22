"""The platformer rules of the Prologue and Levels 2 and 3.

``StoryPlayScene`` is a ``PlayScene`` (see ``play_scene.py``) with the
additions these levels need:

* worlds with their own physics: slippery ice and low gravity in space,
* gates, conveyor belts, red and blue switch blocks and red-light zones,
* characters that start the experiments (stop-signal race, 2-back task,
  Tower of London) and open gates when they are passed,
* a boss fight in a closed hall,
* a final quiz: the owl shows an animation and the hero jumps into the
  answer block with the right name,
* the new skill Stop Signal (R), which freezes enemies, fire bars and bosses.
"""

import math
import random
from dataclasses import replace

import pygame

from . import graphics, ui, worlds
from .bosses import BOSS_KINDS, CARDSORT_COLUMNS, RuleKeeper
from .config import SCREEN_HEIGHT, SCREEN_WIDTH, TILE_SIZE
from .content import SKILLS
from .entities import Effect
from .experiment_scenes import NBackScene, StopSignalScene, TowerScene, draw_stop_sign, easier
from .insight_animations import ANIMATIONS
from .ghosts import ghost_stats
from .play_scene import PlayScene, format_time, make_question
from .scenes import InsightScene, LevelCompleteScene, MessageScene
from .story_content import DIALOGUES, LEVEL_INSIGHTS, STORY_INSIGHTS, STORY_SKILL_ANIMATIONS

STOP_KEY = pygame.K_r
STORY_ADMIN_ACTIONS = {
    pygame.K_1: "1: win the experiments",
    pygame.K_2: "2: pass the quiz",
    pygame.K_3: "3: learn all skills",
    pygame.K_4: "4: next checkpoint",
    pygame.K_5: "5: earn all insights",
    pygame.K_6: "6: defeat the boss",
}
CONVEYOR_SPEED = 150.0
# The red-light cycle: seconds of green, yellow and red.
LIGHT_CYCLE = (("green", 3.0), ("yellow", 0.9), ("red", 2.2))
LIGHT_GRACE = 0.25
STOP_RADIUS = 520
STOP_DURATION = 3.0
STOP_COOLDOWN = 7.0
# Which gate each experiment opens, the insight it gives and the skill it teaches.
EXPERIMENTS = {
    "signal_sam": {"gate": "city_gate", "insight": "horse_race", "skill": "stop"},
    "memory_machine": {"gate": "station_gate", "insight": "updating", "skill": None},
    "tower_gate": {"gate": "tower_gate", "insight": "planning", "skill": None},
}


class _LayeredBackdrop:
    """A backdrop that also draws the things that belong behind the tiles."""

    def __init__(self, backdrop, scene):
        self.backdrop, self.scene = backdrop, scene

    def draw(self, surface, camera, time):
        self.backdrop.draw(surface, camera, time)
        self.scene.draw_behind_tiles(surface, camera, time)


class StoryPlayScene(PlayScene):
    """
    One run through the Prologue, Level 2 or Level 3.

    Parameters
    ----------
    game : Game
        The running game.
    build_level : callable
        Function that returns a fresh ``StoryLevel``.
    """

    admin_actions = STORY_ADMIN_ACTIONS

    def __init__(self, game, build_level):
        super().__init__(game, build_level)
        level, player = self.level, self.player
        player.skills = set(level.start_skills)
        self.topics = LEVEL_INSIGHTS[level.key]
        self.n_insights_total = len(self.topics)
        self.phase_banner = None  # (text, end time) when a boss starts a new phase
        self.base_settings = player.settings
        self.ice_settings = replace(self.base_settings, ground_acceleration=380.0, air_acceleration=1100.0, walk_speed=self.base_settings.walk_speed * 1.1)
        self.space_settings = replace(
            self.base_settings,
            gravity=self.base_settings.gravity * 0.45,
            max_fall_speed=560.0,
            jump_speed=self.base_settings.jump_speed * 0.75,
            spring_speed=self.base_settings.spring_speed * 0.7,
        )
        worlds.add_tile_images(self.tile_images)
        self.backdrops = {
            zone.theme: _LayeredBackdrop(worlds.StoryBackdrop(zone.theme) if zone.theme in worlds.STORY_THEMES else graphics.Backdrop(zone.theme), self)
            for zone in level.zones
        }
        self.rng = random.Random(game.rng.random())
        self.passed_experiments = set()
        self.experiment_results = {}
        self.stop_cooldown = 0.0
        self.frozen = {}
        self.frozen_firebars = {}
        self.light_damage_cooldown = 0.0
        self.previous_vy = 0.0
        self.story_flags = set()
        self.boss = self.make_boss()
        if self.boss:
            level.open_gate(level.boss.gate_in)
        self.quiz_animations = {key: ANIMATIONS[key](game.character) for key in self.topics}

    def make_boss(self, rng=None):
        """Create the boss of the level (None if it has none); the ghost race uses a second one."""
        rng = rng or self.rng
        spec = self.level.boss
        if spec is None:
            return None
        arena = (spec.first_col * TILE_SIZE, (spec.last_col + 1) * TILE_SIZE)
        boss_class = BOSS_KINDS[spec.kind]
        ground_y = self.level.player_start[1]
        if spec.card_cells:  # the Rule Keeper's cards and Count Hackula's windows
            return boss_class(arena, ground_y, spec.card_cells, self.difficulty.key, rng)
        return boss_class(arena, ground_y, self.difficulty.key, rng)

    # ----- input ----------------------------------------------------------

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == STOP_KEY and not self.admin:
            self._use_stop()
            return
        super().handle_event(event)

    def _interact(self):
        npc = self._nearby(self.level.npcs)
        if npc is None:
            super()._interact()
            return
        handler = getattr(self, f"_talk_to_{npc.kind}", None)
        if handler:
            handler()
        else:
            super()._interact()

    # ----- skills ---------------------------------------------------------

    def _use_stop(self):
        """The Stop Signal: freeze nearby enemies, fire bars and the boss."""
        player = self.player
        if "stop" not in player.skills:
            return
        if self.stop_cooldown > 0:
            self._say("Recharging...", ui.SOFT_BLUE)
            return
        self.stop_cooldown = STOP_COOLDOWN
        self.game.audio.play("whistle")
        self.effects.append(Effect("ring", *player.rect.center, color=(255, 110, 110), lifetime=0.5))
        center = player.rect.center
        for enemy in self.enemies:
            if enemy.is_active and math.dist(enemy.rect.center, center) < STOP_RADIUS:
                if enemy not in self.frozen:
                    self.frozen[enemy] = [STOP_DURATION, enemy.speed_factor]
                    enemy.speed_factor = 0.0
                else:
                    self.frozen[enemy][0] = STOP_DURATION
        for firebar in self.firebars:
            if math.dist((firebar.x, firebar.y), center) < STOP_RADIUS:
                if firebar not in self.frozen_firebars:
                    self.frozen_firebars[firebar] = [STOP_DURATION, firebar.speed]
                    firebar.speed = 0.0
                else:
                    self.frozen_firebars[firebar][0] = STOP_DURATION
        if self.boss and self.boss.active and math.dist(self._boss_center(), center) < STOP_RADIUS * 1.5:
            self.boss.freeze(STOP_DURATION * 0.8)

    def _update_frozen(self, dt):
        """Thaw enemies and fire bars after the Stop Signal wears off."""
        self.stop_cooldown = max(0.0, self.stop_cooldown - dt)
        for table, attribute in ((self.frozen, "speed_factor"), (self.frozen_firebars, "speed")):
            for thing, entry in list(table.items()):
                entry[0] -= dt
                if entry[0] <= 0:
                    setattr(thing, attribute, entry[1])
                    del table[thing]

    def _learn_skill(self, key):
        if key in STORY_SKILL_ANIMATIONS:
            skill = SKILLS[key]
            self.player.skills.add(key)
            self.game.audio.play("powerup")
            message = MessageScene(self.game, f"New skill: {skill.name}  [{skill.button}]", skill.pages, footer=skill.source)
            self.game.push_scene(InsightScene(self.game, STORY_SKILL_ANIMATIONS[key], on_close=lambda: self.game.push_scene(message)))
        else:
            super()._learn_skill(key)

    def _punch(self):
        super()._punch()
        player = self.player
        if self.boss and player.punch_timer == player.settings.punch_time:  # a punch started just now
            self._strike_boss(player.punch_rect, "punch")

    # ----- characters and experiments -------------------------------------

    def _say_lines(self, title, key, on_close=None):
        self.game.push_scene(MessageScene(self.game, title, DIALOGUES[key], on_close=on_close))

    def _talk_to_professor_shell(self):
        if self.level.quiz and self.player.center_x > self.level.quiz.cells[0][0] * TILE_SIZE - 20 * TILE_SIZE:
            self._say_lines("Professor Shell", "shell_end")
        elif "shell_intro" in self.story_flags:
            self._say_lines("Professor Shell", "shell_again")
        else:
            self.story_flags.add("shell_intro")
            self._say_lines("Professor Shell", "shell_intro", on_close=lambda: self._show_story_animation("hackula"))

    def _show_story_animation(self, key, on_close=None):
        self.game.audio.play("note")
        self.game.push_scene(InsightScene(self.game, key, on_close=on_close))

    def _talk_to_signal_sam(self):
        self._start_experiment("signal_sam", "Signal Sam", "sam_intro", "sam_done", StopSignalScene, self.game.stop_signal_settings)

    def _talk_to_memory_machine(self):
        self._start_experiment("memory_machine", "The Memory Machine", "machine_intro", "machine_done", NBackScene, self.game.nback_settings)

    def _talk_to_tower_gate(self):
        self._start_experiment("tower_gate", "Tower of London", "tower_intro", "tower_done", TowerScene, self.game.tower_settings)

    def _start_experiment(self, key, title, intro, done, scene_class, settings):
        game = self.game
        if key in self.passed_experiments:
            self._say_lines(title, done)
            return
        settings = easier(settings, self.difficulty.key)

        def start():
            if scene_class is TowerScene:
                scene = TowerScene(game, lambda *result: self._on_experiment_finished(key, title, *result), settings, game.rng)
            else:
                first_time = key not in game.tutorials_seen
                scene = scene_class(game, lambda *result: self._on_experiment_finished(key, title, *result), settings, game.rng, show_tutorial=first_time)
            game.tutorials_seen.add(key)
            game.audio.play_music("lab")  # calm music that is the same in every condition
            game.push_scene(scene)

        self._say_lines(title, intro, on_close=start)

    def _on_experiment_finished(self, key, title, passed, summary, results):
        game = self.game
        if summary is None:
            game.push_scene(MessageScene(game, title, ["Talk to me again (E) when you are ready."]))
            return
        self.experiment_results[key] = summary
        if not passed:
            game.push_scene(MessageScene(game, title, ["Not quite - talk to me again (E) to retry."]))
            return
        self._win_experiment(key, title)

    def _win_experiment(self, key, title, announce=True):
        """Open the gate and hand out the rewards of a passed experiment."""
        info = EXPERIMENTS[key]
        self.passed_experiments.add(key)
        self.level.open_gate(info["gate"])
        gained = self.player.heal()
        self.game.audio.play("powerup")
        if not announce:
            self._earn_insight(info["insight"])
            if info["skill"]:
                self.player.skills.add(info["skill"])
            return
        reward = "The gate is open" + (" and you got a heart!" if gained else "!")

        def after_insight():
            self._earn_insight(info["insight"])
            if info["skill"]:
                self._learn_skill(info["skill"])

        def show_insight():
            self.game.audio.play("note")
            self.game.push_scene(InsightScene(self.game, info["insight"], on_close=after_insight))

        self.game.push_scene(MessageScene(self.game, title, [f"{reward} Now watch what happened in your head ..."], on_close=show_insight))

    # ----- the quiz -------------------------------------------------------

    def _talk_to_quiz_owl(self):
        game = self.game
        if self.quiz_passed:
            game.push_scene(MessageScene(game, "The Owl", ["The way is open!"]))
            return
        if not self.map_shown:
            self.map_shown = True
            map_key = {"prologue": "prologue_map", "level_2": "inhibition_map", "level_3": "control_map"}[self.level.key]
            game.push_scene(InsightScene(game, map_key, on_close=self._talk_to_quiz_owl))
            return
        if self.active_question is None:
            self._next_story_question()
        self._say_lines("The Owl", "owl_quiz")

    def _next_story_question(self):
        if not hasattr(self, "_quiz_order"):
            self._quiz_order = list(self.topics)
            self.rng.shuffle(self._quiz_order)
        topic = self._quiz_order.pop(0)
        self._quiz_order.append(topic)
        self.active_question = make_question(topic, self.rng, len(self.level.quiz.cells), self.topics)

    def _answer(self, index):
        game, question = self.game, self.active_question
        if self.quiz_passed:
            return
        if question is None:
            self._say("Talk to the owl first (E)", ui.SOFT_BLUE)
            return
        if index == question.correct_index:
            self.quiz_passed = True
            self.active_question = None
            self.level.open_gate(self.level.quiz.gate)
            game.audio.play("correct")
            self._say("Correct! The way is open!", ui.GREEN)
            return
        game.audio.play("wrong")
        if self.difficulty.wrong_answer_costs_heart:
            self.player.hearts -= 1
            if self._check_game_over():
                return
        right = STORY_INSIGHTS[question.topic].short_name
        game.push_scene(MessageScene(game, "The Owl", [f"No - that was: {right}. Here is a new one."], on_close=self._next_story_question))

    # ----- admin mode -----------------------------------------------------

    def _admin_action(self, key):
        level = self.level
        if key == pygame.K_1:
            npc_kinds = {npc.kind for npc in level.npcs}
            for experiment in EXPERIMENTS:
                if experiment in npc_kinds and experiment not in self.passed_experiments:
                    self._win_experiment(experiment, "", announce=False)
            self._say("Experiments won", ui.GOLD)
        elif key == pygame.K_2 and level.quiz:
            self.quiz_passed = True
            self.active_question = None
            level.open_gate(level.quiz.gate)
            self._say("Quiz passed", ui.GOLD)
        elif key == pygame.K_5:
            for orb in level.orbs:
                orb.collected = True
            self.insights = list(self.topics)
            self._say("All insights earned", ui.GOLD)
        elif key == pygame.K_6 and self.boss and not self.boss.defeated:
            self.boss.active = True
            self.boss.damage(self.boss.hp)
        elif key in (pygame.K_3, pygame.K_4):
            super()._admin_action(key)

    # ----- the boss -------------------------------------------------------

    def _boss_center(self):
        boss = self.boss
        body = boss.body_rect
        return body.center if body else (boss.x, boss.y)

    def _start_boss(self):
        spec = self.level.boss
        self.level.close_gate(spec.gate_in)
        intro = {"file_drawer": "drawer_intro", "captain_impulse": "impulse_intro", "rule_keeper": "rules_intro", "count_hackula": "hackula_intro"}[spec.kind]
        guide = {"file_drawer": "drawer_how", "captain_impulse": "impulse_how", "rule_keeper": "rules_how", "count_hackula": "hackula_how"}[spec.kind]

        def fight():
            self.boss.active = True

        # A taunt, then a short animation that shows how to beat the boss.
        self._say_lines(self.boss.name, intro, on_close=lambda: self._show_story_animation(guide, on_close=fight))

    def _strike_boss(self, rect, kind):
        """Pass an attack on to the boss and react to the result."""
        boss = self.boss
        if not boss or not boss.active or boss.defeated:
            return None
        result = boss.strike(rect, kind)
        shown = any(effect.text == "No effect!" and effect.age < 0.6 for effect in self.effects)
        if result == "blocked" and kind != "stomp" and not shown:  # one at a time, not a pile
            self.effects.append(Effect("text", rect.centerx, rect.top - 10, "No effect!", ui.SOFT_BLUE))
        return result

    def _update_boss(self, dt):
        """Move the boss, check hits and contact; return True if the game is over."""
        boss, player, spec = self.boss, self.player, self.level.boss
        if not boss.active and not boss.defeated:
            if player.center_x > (spec.first_col + 5) * TILE_SIZE and player.on_ground:
                self._start_boss()
            return False
        boss.update(dt, player)
        for shot in self.projectiles:
            if not shot.used_up and self._strike_boss(shot.rect, "shot"):
                shot.used_up = True
        self._handle_boss_events()
        if boss.defeated:
            return False
        body = boss.body_rect
        if body is not None and player.rect.colliderect(body):
            falling_on_top = player.vy > 0 and player.previous_bottom <= body.top + 14
            touch = self._strike_boss(player.rect, "touch") if getattr(boss, "touch_hits", False) else None
            if touch in ("hit", "blocked"):
                player.vy = max(player.vy, 150.0)  # bounce off him
            elif falling_on_top and self._strike_boss(player.rect, "stomp"):
                player.bounce()
                self.game.audio.play("stomp")
            elif not falling_on_top and self._hurt(body.centerx):
                return True
        for hazard in boss.hazards:
            if hazard.harmful and hazard.rect.colliderect(player.rect) and self._hurt(hazard.x):
                return True
        return False

    def _handle_boss_events(self):
        boss = self.boss
        x, y = self._boss_center()
        for event, value in boss.events:
            if event == "hit":
                self.game.audio.play("stomp")
                self.effects.append(Effect("burst", x, y, color=ui.GOLD, lifetime=0.6))
            elif event == "heal":
                self.game.audio.play("wrong")
                self.effects.append(Effect("text", x, y - 90, "Commission error! It heals!", ui.RED, lifetime=1.6))
            elif event == "stop_signal":
                self.game.audio.play("whistle")
                self.effects.append(Effect("text", x, y - 90, "STOP SIGNAL!", ui.RED, lifetime=1.4))
            elif event in ("hop", "bump"):
                self.game.audio.play("break")
            elif event == "phase":
                self.game.audio.play("powerup")
                text = {"swoop": "He swoops! GREEN eyes: jump into him. RED eyes: stay down!", "sunlight": "Let the light in: open the windows in his order!"}.get(boss.phase, "")
                self.phase_banner = (text, self.time + 3.0)
            elif event == "rattle":
                self.game.audio.play("break")
            elif event == "window":
                self.game.audio.play("correct")
            elif event == "sequence":
                self.game.audio.play("note")
            elif event == "defeated":
                self._on_boss_defeated()
        boss.events.clear()

    def _on_boss_defeated(self):
        spec, game = self.level.boss, self.game
        for cell in spec.card_cells:
            self.level.tiles[cell] = "used"
        self.level.open_gate(spec.gate_out)
        self.level.open_gate(spec.gate_in)
        game.audio.play("win")
        self._add_sparks(10)
        if isinstance(self.boss, RuleKeeper) and self.boss.trials:
            game.save_task_results("cardsort", self.boss.trials, CARDSORT_COLUMNS)
        text = {
            "file_drawer": "The drawer bursts open - the hidden null results are free, and Hackula's bats flee!",
            "captain_impulse": "Captain Impulse runs out of steam: stopping in time wins! But Count Hackula has one trick left ...",
            "rule_keeper": "The Rule Keeper runs out of rules - you stayed flexible! Count Hackula flees to his castle ...",
            "count_hackula": "The sunlight of open science pours in - Count Hackula turns to dust!",
        }[spec.kind]
        follow_up = {"file_drawer": "file_drawer", "captain_impulse": None, "rule_keeper": "card_sorting", "count_hackula": None}[spec.kind]

        def after():
            if follow_up and follow_up not in self.insights:
                self._show_insight(follow_up)

        game.push_scene(MessageScene(game, f"{self.boss.name} defeated!", [text], on_close=after))

    # ----- update ---------------------------------------------------------

    def update(self, dt):
        player, level = self.player, self.level
        zone = level.zone_at(player.center_x)
        if zone.theme in worlds.SLIPPERY_THEMES:
            player.settings = self.ice_settings
        elif zone.theme in worlds.LOW_GRAVITY_THEMES:
            player.settings = self.space_settings
        else:
            player.settings = self.base_settings
        self.previous_vy = player.vy
        hearts_before = player.hearts
        self._update_frozen(dt)
        super().update(dt)
        if self.game.scenes[-1] is not self or self.celebration_time is not None or player.hearts <= 0:
            return
        if player.hearts < hearts_before and player.hearts <= 0:
            return
        self._move_on_conveyor(dt)
        self._check_head_bump()
        self._update_red_lights(dt)
        if self.boss and self._update_boss(dt):
            return

    def _move_on_conveyor(self, dt):
        player, level = self.player, self.level
        if not player.on_ground:
            return
        below = (int(player.center_x // TILE_SIZE), int((player.y + player.height + 2) // TILE_SIZE))
        direction = level.conveyors.get(below)
        if not direction:
            return
        new_x = player.x + direction * CONVEYOR_SPEED * dt
        if not level.solid_cells_in(new_x, player.y, player.width, player.height):
            player.x = new_x

    def _check_head_bump(self):
        """React when the hero hits an answer, switch or card block from below."""
        player, level = self.player, self.level
        if self.previous_vy >= 0 or player.vy != 0 or player.on_ground or self.admin:
            return
        row = int((player.y - 1) // TILE_SIZE)
        cols = range(int(player.x // TILE_SIZE), int((player.x + player.width - 1) // TILE_SIZE) + 1)
        candidates = [(col, row) for col in cols if level.tiles.get((col, row)) in ("answer", "card", "switch_red", "switch_blue")]
        if not candidates:
            return
        cell = min(candidates, key=lambda c: abs((c[0] + 0.5) * TILE_SIZE - player.center_x))
        kind = level.tiles[cell]
        if kind == "answer" and level.quiz:
            self._answer(level.quiz.cells.index(cell))
        elif kind == "card" and self.boss:
            choice = self.boss.choose(level.boss.card_cells.index(cell))
            if choice is not None:
                self.game.audio.play("correct" if choice else "wrong")
                self._handle_boss_events()
        elif kind.startswith("switch"):
            color = level.toggle_switches()
            self.game.audio.play("select")
            self._say(f"{color.upper()} blocks!", worlds.BLOCK_COLORS[color])
            self._unstick_player()

    def _unstick_player(self):
        """If a block appeared inside the hero, put the hero on top of it."""
        player, level = self.player, self.level
        cells = level.solid_cells_in(player.x, player.y, player.width, player.height)
        if cells:
            top = min(row for _, row in cells)
            player.y = top * TILE_SIZE - player.height
            player.vy = 0.0

    def _light_state(self, light):
        cycle = sum(seconds for _, seconds in LIGHT_CYCLE)
        moment = (self.time + light.offset) % cycle
        for state, seconds in LIGHT_CYCLE:
            if moment < seconds:
                return state, moment
            moment -= seconds
        return "green", 0.0

    def _update_red_lights(self, dt):
        """Moving inside a red-light zone while the light is red hurts."""
        player = self.player
        self.light_damage_cooldown = max(0.0, self.light_damage_cooldown - dt)
        for light in self.level.red_lights:
            light.state, moment = self._light_state(light)
            inside = light.first_x <= player.center_x <= light.last_x
            moving = abs(player.vx) > 40 or abs(player.vy) > 80
            if inside and light.state == "red" and moment > LIGHT_GRACE and moving and self.light_damage_cooldown <= 0 and not self.admin:
                self.light_damage_cooldown = 1.0
                self.effects.append(Effect("text", player.center_x, player.y - 30, "You moved on RED!", ui.RED, lifetime=1.3))
                if self._hurt(light.light_x):
                    return

    # ----- drawing --------------------------------------------------------

    def draw_behind_tiles(self, surface, camera, time):
        """Draw lava, red-light towers, switched-off blocks and the boss behind the tiles."""
        level = self.level
        bottom = SCREEN_HEIGHT // TILE_SIZE - 1
        for first_col, last_col in level.lava_spans:
            for col in range(first_col, last_col + 1):
                if (col, bottom) not in level.tiles:
                    rect = pygame.Rect(col * TILE_SIZE - camera, (bottom - 1) * TILE_SIZE + 20, TILE_SIZE, 2 * TILE_SIZE)
                    if -TILE_SIZE < rect.x < SCREEN_WIDTH:
                        worlds.draw_lava(surface, rect, time)
        for light in level.red_lights:
            self._draw_red_light(surface, light, camera, time)
        inactive = "blue" if level.active_color == "red" else "red"
        for col, row in level.color_blocks[inactive]:
            rect = pygame.Rect(col * TILE_SIZE - camera, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if -TILE_SIZE < rect.x < SCREEN_WIDTH:
                worlds.draw_block_outline(surface, rect, inactive)
        if self.boss and not self.boss.defeated and level.zone_at(self.player.center_x) is level.zone_at(self.boss.arena[0] + TILE_SIZE):
            self.boss.draw(surface, camera, time)

    def _draw_red_light(self, surface, light, camera, time):
        x = light.light_x - camera
        if not -200 < x < SCREEN_WIDTH + 200:
            return
        ground_y = self.level.player_start[1]
        pygame.draw.rect(surface, (50, 50, 64), (x - 6, ground_y - 230, 12, 230))
        box = pygame.Rect(0, 0, 44, 110)
        box.midbottom = (x, ground_y - 220)
        pygame.draw.rect(surface, (30, 30, 40), box, border_radius=10)
        pygame.draw.rect(surface, ui.GOLD, box, 2, border_radius=10)
        colors = {"red": (240, 60, 60), "yellow": (255, 200, 60), "green": (70, 220, 100)}
        for index, name in enumerate(("red", "yellow", "green")):
            on = light.state == name
            pygame.draw.circle(surface, colors[name] if on else tuple(c // 4 for c in colors[name]), (box.centerx, box.top + 20 + index * 35), 14)
        if light.state == "red":
            beam = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            left, right = light.first_x - camera, light.last_x - camera
            pygame.draw.polygon(beam, (255, 60, 60, 45), [(x, box.top + 20), (left, ground_y), (right, ground_y)])
            surface.blit(beam, (0, 0))
            ui.draw_text(surface, "FREEZE!", (x, box.top - 8), 30, colors["red"], "midbottom", bold=True, shadow=True)

    def _draw_fireworks(self, surface, camera):
        # Things on top of the level (drawn before darkness, labels and HUD).
        self._draw_on_top(surface, camera, self.time)
        super()._draw_fireworks(surface, camera)

    def _draw_on_top(self, surface, camera, time):
        level = self.level
        for (col, row), direction in level.conveyors.items():
            rect = pygame.Rect(col * TILE_SIZE - camera, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if -TILE_SIZE < rect.x < SCREEN_WIDTH:
                worlds.draw_conveyor_arrows(surface, rect, direction, time)
        for enemy in self.frozen:
            rect = enemy.rect.move(-camera, 0).inflate(12, 12)
            ice = pygame.Surface(rect.size, pygame.SRCALPHA)
            ice.fill((170, 220, 255, 110))
            surface.blit(ice, rect)
        for firebar in self.frozen_firebars:
            draw_stop_sign(surface, (firebar.x - camera, firebar.y), 14)
        if self.boss and not self.boss.defeated:
            self.boss.draw_front(surface, camera, time)
            for hazard in self.boss.hazards:
                hazard.draw(surface, camera, time)
        if level.quiz:
            self._draw_quiz(surface, camera)

    def _draw_quiz(self, surface, camera):
        level, question = self.level, self.active_question
        cells = level.quiz.cells
        # After the quiz the answer blocks need no labels any more.
        if self.quiz_passed or abs((cells[0][0] + 1) * TILE_SIZE - self.player.center_x) > SCREEN_WIDTH:
            return
        for index, (col, row) in enumerate(cells):
            x = (col + 0.5) * TILE_SIZE - camera
            text = STORY_INSIGHTS[question.options[index]].short_name if question else "?"
            lines = ui.wrap_text(text, ui.get_font(24), 150)
            box = pygame.Rect(0, 0, 164, 16 + len(lines) * 24)
            box.midbottom = (x, row * TILE_SIZE - 8)
            ui.draw_panel(surface, box, radius=10)
            for line_index, line in enumerate(lines):
                ui.draw_text(surface, line, (box.centerx, box.top + 8 + line_index * 24), 24, ui.WHITE, "midtop")
        if question and not self.quiz_passed:
            # Small enough to stay above the answer labels, also the ones with two lines.
            board = pygame.Rect(0, 0, 380, 212)
            board.midtop = (SCREEN_WIDTH // 2, 90)
            ui.draw_panel(surface, board)
            ui.draw_text(surface, "Which idea is this?", (board.centerx, board.top + 12), 30, ui.GOLD, "midtop", bold=True)
            picture = pygame.Rect(0, 0, 320, 160)
            picture.midbottom = (board.centerx, board.bottom - 12)
            self.quiz_animations[question.topic].draw_thumbnail(surface, picture, self.time)

    def _draw_hud(self, surface):
        super()._draw_hud(surface)
        banner = self.phase_banner
        if banner and self.time < banner[1]:
            # A new boss phase is announced below the fight, where nothing else is written.
            ui.draw_text(surface, banner[0], (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 116), 30, ui.GOLD, "midtop", bold=True, shadow=True)
        if self.boss and self.boss.active and not self.boss.defeated:
            self.boss.draw_health(surface)
        if "stop" in self.player.skills and self.stop_cooldown > 0:
            share = self.stop_cooldown / STOP_COOLDOWN
            bar = pygame.Rect(20, SCREEN_HEIGHT - 70, 160, 8)
            pygame.draw.rect(surface, ui.INK, bar, border_radius=4)
            pygame.draw.rect(surface, (255, 110, 110), (bar.x, bar.y, int(bar.width * (1 - share)), bar.height), border_radius=4)

    # ----- the end --------------------------------------------------------

    def _finish_level(self):
        stats = [
            ("Difficulty", self.difficulty.name),
            ("Total time", format_time(self.total_time)),
            ("Sparks", str(self.player.sparks)),
        ]
        if self.n_insights_total:
            stats.append(("Insights", f"{len(self.insights)}/{self.n_insights_total}"))
        stop = self.experiment_results.get("signal_sam")
        if stop is not None and stop.ssrt_ms is not None:
            stats.append(("Your stopping time (SSRT)", f"{stop.ssrt_ms:.0f} ms"))
        nback = self.experiment_results.get("memory_machine")
        if nback is not None:
            stats.append(("2-back accuracy", f"{nback.accuracy:.0%}"))
        if self.boss:
            stats.append((self.boss.name, "defeated" if self.boss.defeated else "-"))
        stats.append(("Hearts left", str(self.player.hearts)))
        stats += ghost_stats(self.ghost)
        if self.level.key == "finale":
            # The end of the story comes before the statistics.
            self._show_story_animation("finale", on_close=lambda: self.game.push_scene(LevelCompleteScene(self.game, stats)))
        else:
            self.game.push_scene(LevelCompleteScene(self.game, stats))

