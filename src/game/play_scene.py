"""The platformer itself: the hero running through a level.

``PlayScene`` connects the level, the player, the enemies, the insight orbs,
the flanker mini boss and the quiz pipes, and applies the rules of the game
(hearts, checkpoints, skills, rewards).
"""

import math
import random
from dataclasses import dataclass, replace

import pygame

from . import graphics, ui
from .config import SCREEN_HEIGHT, SCREEN_WIDTH, TILE_SIZE
from .content import INSIGHTS, QRP_SHOTS, QUIZ_TOPICS, SKILL_ANIMATIONS, SKILLS
from .entities import ENEMY_KINDS, CrumblePlatform, Effect, FireBar, MovingPlatform, Player, PowerUp, Projectile
from .flanker_scene import FlankerScene
from .level import GROUND_ROW, LEVEL_ROWS, cell_rect
from .level_one import build_level_one
from .insight_animations import ANIMATIONS
from .scenes import GameOverScene, InsightScene, LevelCompleteScene, MessageScene, NotebookScene, PauseScene, Scene, TransitionScene

JUMP_KEYS = (pygame.K_SPACE, pygame.K_w)
PUNCH_KEY = pygame.K_f
SHOOT_KEY = pygame.K_g
FEAR_KEY = pygame.K_q
ENTER_PIPE_KEY = pygame.K_s
# P is offered as well because many laptops need Fn for the F keys.
ADMIN_KEYS = (pygame.K_F1, pygame.K_p)
# Keys that only work in admin mode, with the text shown in the admin panel.
ADMIN_ACTIONS = {
    pygame.K_1: "1: win Pond Challenge",
    pygame.K_2: "2: pass the owl's quiz",
    pygame.K_3: "3: learn all skills",
    pygame.K_4: "4: next checkpoint",
    pygame.K_5: "5: earn all insights",
}
TALK_DISTANCE = 100
PICKUP_DISTANCE = 30
ORB_PICKUP_DISTANCE = 44
SPARKS_PER_INSIGHT = 5
# Enemies further away than this from the player stand still.
ACTIVE_DISTANCE = SCREEN_WIDTH
# Share of the screen width that is kept between the hero and the left edge.
CAMERA_LEAD = 0.4
# Colour of the cave darkness (RGBA) and the radius of light around things.
DARKNESS = (6, 6, 20, 240)
N_ANSWERS = 3
ITEMS = ("mushroom", "star", "shield")
ITEM_MESSAGES = {"mushroom": "Zoom!", "star": "Focus Star!", "shield": "Shield!"}
# The celebration at the goal: its length, how often a firework goes off,
# and the colours of the fireworks.
CELEBRATION_TIME = 3.2
FIREWORK_INTERVAL = 0.35
FIREWORK_COLORS = ((255, 214, 92), (255, 120, 140), (130, 220, 255), (150, 240, 150), (220, 160, 255))
FIREWORK_GRAVITY = 260.0
SPOTLIGHT_RADIUS = 300
DIM_LIGHT_RADIUS = 150
GLOW_RADIUS = 80


@dataclass(frozen=True)
class Question:
    """
    A quiz question: which phenomenon does the animation show?

    ``options`` are insight keys, one per answer pipe; ``correct_index``
    points at ``topic``.
    """

    topic: str
    options: tuple
    correct_index: int


def make_question(topic, rng, n_options=N_ANSWERS, topics=QUIZ_TOPICS):
    """
    Build a question about ``topic`` with wrong answers from the other topics.

    Parameters
    ----------
    topic : str
        The insight key the animation shows.
    rng : random.Random
        Random number generator for the wrong answers and their order.
    n_options : int, optional
        Number of answers.
    topics : sequence of str, optional
        All possible answers.

    Returns
    -------
    Question
        The question with shuffled answers.
    """
    wrong = rng.sample([other for other in topics if other != topic], n_options - 1)
    options = [topic] + wrong
    rng.shuffle(options)
    return Question(topic, tuple(options), options.index(topic))


def format_time(seconds):
    """Format a duration in seconds as "m:ss"."""
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes}:{seconds:02d}"


class PlayScene(Scene):
    """
    One run through a level, from the start until the goal or game over.

    Parameters
    ----------
    game : Game
        The running game.
    build_level : callable, optional
        Function that returns a fresh ``Level``.
    """

    # Keys of the admin mode and their labels; later levels have their own.
    admin_actions = ADMIN_ACTIONS

    def __init__(self, game, build_level=build_level_one):
        super().__init__(game)
        self.difficulty = difficulty = game.difficulty
        self.level = build_level()
        self.level.narrow_pits(difficulty.pit_narrowing)
        self.player = Player(*self.level.player_start, difficulty.apply_to(game.player_settings))
        self.flanker_settings = game.flanker_settings
        if difficulty.flanker_pass_accuracy is not None:
            self.flanker_settings = replace(game.flanker_settings, pass_accuracy=difficulty.flanker_pass_accuracy)
        self.enemies = self._make_enemies()
        self.platforms = [
            MovingPlatform(start.x, start.y, start.width, start.travel_x, start.travel_y, start.period)
            for start in self.level.platform_starts
        ] + [CrumblePlatform(start.x, start.y, start.width) for start in self.level.crumble_starts]
        self.firebars = [
            FireBar(start.x, start.y, start.n_balls, start.speed * difficulty.enemy_speed_factor, start.angle)
            for start in self.level.firebar_starts
        ]
        # Seconds that each spring stays squashed after a jump.
        self.spring_squash = [0.0] * len(self.level.springs)
        self.powerups = []
        # Each firework spark: [x, y, vx, vy, colour, seconds left].
        self.fireworks = []
        self.celebration_time = None
        self.next_firework = 0.0
        self.firework_rng = random.Random(7)
        self.projectiles = []
        self.n_shots = 0
        self.effects = []
        self.insights = []
        self.n_insights_total = len(self.level.orbs) + 1  # one more comes from Professor Fin
        self.respawn_point = self.level.player_start
        self.quiz_topics = list(QUIZ_TOPICS)
        game.rng.shuffle(self.quiz_topics)
        self.active_question = None
        self.map_shown = False
        self.quiz_animations = {key: ANIMATIONS[key](game.character) for key in QUIZ_TOPICS}
        self.quiz_passed = False
        self.flanker_passed = False
        self.flanker_accuracy = None
        self.admin = False
        self.falls = 0
        # ``time`` drives animations; ``total_time`` also runs during the
        # experiments and text boxes and is shown to the player.
        self.time = 0.0
        self.total_time = 0.0
        self.camera_x = 0.0
        self.held_keys = set()
        self.tile_images = graphics.make_tile_images()
        self.backdrops = {zone.theme: graphics.Backdrop(zone.theme) for zone in self.level.zones}
        self.darkness = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.lights = {radius: graphics.make_light(radius, DARKNESS) for radius in (SPOTLIGHT_RADIUS, DIM_LIGHT_RADIUS, GLOW_RADIUS)}

    def _make_enemies(self):
        """Create the enemies of the level as the difficulty asks for."""
        difficulty = self.difficulty
        enemies, n_ordinary = [], 0
        for start in self.level.enemy_starts:
            # Brutes always stay: they are a puzzle, not just an obstacle.
            if start.kind != "brute":
                n_ordinary += 1
                if int(n_ordinary * difficulty.enemy_share) == int((n_ordinary - 1) * difficulty.enemy_share):
                    continue
            enemy = ENEMY_KINDS[start.kind](start.x, start.ground_y, start.patrol)
            enemy.speed_factor = difficulty.enemy_speed_factor
            enemies.append(enemy)
        return enemies

    # ----- input ----------------------------------------------------------

    def on_resume(self):
        """Forget keys that may have been released while an overlay was open."""
        pressed = pygame.key.get_pressed()
        self.held_keys = {key for key in (pygame.K_a, pygame.K_d, pygame.K_s) if pressed[key]}
        self.player.release_jump()

    def update_in_background(self, dt):
        if not self.game.scenes[-1].stops_clock and self.celebration_time is None:
            self.total_time += dt
        if self.celebration_time is not None:
            self._update_celebration(dt)  # the fireworks go on behind the end screen

    def handle_event(self, event):
        if event.type == pygame.KEYUP:
            self.held_keys.discard(event.key)
            if event.key in JUMP_KEYS:
                self.player.release_jump()
        elif event.type == pygame.KEYDOWN:
            self.held_keys.add(event.key)
            if event.key in ADMIN_KEYS and self.game.allow_admin:
                self.admin = not self.admin
                self._say("Admin mode ON" if self.admin else "Admin mode OFF", ui.GOLD)
            elif self.admin and event.key in self.admin_actions:
                self._admin_action(event.key)
            elif event.key in JUMP_KEYS:
                self.player.press_jump()
            elif event.key == PUNCH_KEY:
                self._punch()
            elif event.key == SHOOT_KEY:
                self._shoot()
            elif event.key == FEAR_KEY:
                self._use_fear()
            elif event.key == ENTER_PIPE_KEY:
                self._enter_pipe()
            elif event.key == pygame.K_e:
                self._interact()
            elif event.key == pygame.K_TAB:
                self.game.push_scene(NotebookScene(self.game, self.insights, self.n_insights_total))
            elif event.key == pygame.K_ESCAPE:
                self.game.push_scene(PauseScene(self.game))

    def _nearby(self, things):
        """Return the first of ``things`` that the hero stands next to, or None."""
        for thing in things:
            close = abs(thing.x - self.player.center_x) < TALK_DISTANCE
            if close and abs(thing.ground_y - (self.player.y + self.player.height)) < TILE_SIZE * 2:
                return thing
        return None

    def _interact(self):
        npc = self._nearby(self.level.npcs)
        sign = self._nearby(self.level.signs)
        if npc and npc.kind == "professor_fin":
            self._talk_to_professor_fin()
        elif npc and npc.kind == "owl":
            self._talk_to_owl()
        elif sign:
            self.game.push_scene(MessageScene(self.game, sign.title, sign.pages))

    # ----- admin mode (for testing) ---------------------------------------

    def _admin_action(self, key):
        """Skip a challenge or move on without playing; only in admin mode."""
        player, level = self.player, self.level
        if key == pygame.K_1 and not self.flanker_passed:
            self._win_pond_challenge()
            self._earn_insight("flanker")
        elif key == pygame.K_2:
            self.quiz_passed = True
            self._arrive_at(next(pipe for pipe in level.pipes.values() if pipe.kind == "quiz").target)
        elif key == pygame.K_3:
            player.skills.update(SKILLS)
            for shrine in level.shrines:
                shrine.used = True
            self._say("All skills learned", ui.GOLD)
        elif key == pygame.K_4:
            here = level.progress_of(player.center_x + TILE_SIZE)
            ahead = sorted((c for c in level.checkpoints if level.progress_of(c.x) > here), key=lambda c: level.progress_of(c.x))
            if ahead:
                player.respawn(ahead[0].x - player.width / 2, ahead[0].ground_y)
                self._snap_camera()
        elif key == pygame.K_5:
            for orb in level.orbs:
                orb.collected = True
            self.insights = list(INSIGHTS)
            self._say("All insights earned", ui.GOLD)

    def _win_pond_challenge(self):
        """Hand out everything a passed flanker task gives; return True if a heart was gained."""
        self.flanker_passed = True
        self.level.build_bridge()
        self.player.has_spotlight = True
        self.game.audio.play("powerup")
        return self.player.heal()

    # ----- skills ---------------------------------------------------------

    def _punch(self):
        player = self.player
        if not player.start_punch():
            return
        self.game.audio.play("punch")
        fist = player.punch_rect
        for enemy in self.enemies:
            if enemy.is_active and enemy.rect.colliderect(fist):
                self._strike(enemy, player.facing)
        for cell, content in self.level.break_crates(fist):
            self._smash_crate(cell, content)

    def _shoot(self):
        player = self.player
        if not player.start_shot():
            return
        settings = player.settings
        text = QRP_SHOTS[self.n_shots % len(QRP_SHOTS)]
        self.n_shots += 1
        self.game.audio.play("shoot")
        muzzle_x = player.center_x + player.facing * (player.width / 2 + 10)
        self.projectiles.append(Projectile(muzzle_x, player.y + 24, player.facing, text, settings.shot_speed, settings.shot_lifetime))

    def _update_projectiles(self, dt):
        """Move the shots; they stop at the first wall, crate or enemy."""
        level = self.level
        for shot in self.projectiles:
            shot.update(dt)
            tip_x, tip_y = shot.tip
            tip_cell = (int(tip_x // TILE_SIZE), int(tip_y // TILE_SIZE))
            if level.is_solid(*tip_cell):
                shot.used_up = True
                for cell, content in level.break_crates(pygame.Rect(tip_x - 2, tip_y - 2, 4, 4)):
                    self._smash_crate(cell, content)
                continue
            for enemy in self.enemies:
                if enemy.is_active and enemy.rect.colliderect(shot.rect):
                    shot.used_up = True
                    self._strike(enemy, shot.direction)
                    break
        self.projectiles = [shot for shot in self.projectiles if not shot.is_gone]

    def _strike(self, enemy, direction):
        """Hit an enemy with a punch or a shot."""
        if enemy.punchable:
            enemy.knock_out(direction)
            self._add_sparks()
        else:
            self.effects.append(Effect("text", enemy.center_x, enemy.y - 10, "Too tough! Scare it away.", ui.SOFT_BLUE))

    def _smash_crate(self, cell, content):
        self.effects.append(Effect("burst", *cell_rect(cell).center, color=graphics.WOOD, lifetime=0.5))
        self.game.audio.play("break")
        if content == "spark":
            self._add_sparks()

    def _use_fear(self):
        player = self.player
        if "fear" not in player.skills:
            return
        if not player.start_fear():
            self._say("Recharging...", ui.SOFT_BLUE)
            return
        settings = player.settings
        self.game.audio.play("fear")
        self.effects.append(Effect("ring", *player.rect.center, color=(120, 200, 255), lifetime=0.5))
        for enemy in self.enemies:
            if enemy.is_active and math.dist(enemy.rect.center, player.rect.center) < settings.fear_radius:
                enemy.frighten(settings.fear_duration, player.center_x)

    def _learn_skill(self, key):
        skill = SKILLS[key]
        self.player.skills.add(key)
        self.game.audio.play("powerup")
        title = f"New skill: {skill.name}  [{skill.button}]"
        message = MessageScene(self.game, title, skill.pages, footer=skill.source)
        if key in SKILL_ANIMATIONS:
            # First show what the skill is about, then how to use it.
            self.game.push_scene(InsightScene(self.game, SKILL_ANIMATIONS[key], on_close=lambda: self.game.push_scene(message)))
        else:
            self.game.push_scene(message)

    # ----- pipes ----------------------------------------------------------

    def _pipe_below(self):
        """Return the pipe the hero stands on, or None."""
        player = self.player
        if not player.on_ground:
            return None
        return self.level.pipe_under(player.center_x, player.y + player.height)

    def _enter_pipe(self):
        pipe = self._pipe_below()
        if pipe is None or pipe.kind == "exit":
            return
        if pipe.kind == "quiz":
            self._answer_quiz(pipe)
        else:
            self._travel(pipe)

    def _travel(self, pipe):
        """Go down a pipe and come out of its target pipe."""
        self.game.audio.play("double_jump")
        self.game.push_scene(TransitionScene(self.game, lambda: self._arrive_at(pipe.target), pipe.label))

    def _arrive_at(self, pipe_name):
        """Put the hero on top of a pipe; it becomes the new respawn point."""
        pipe = self.level.pipes[pipe_name]
        self.respawn_point = (pipe.x - self.player.width / 2, pipe.ground_y)
        self.player.teleport(*self.respawn_point)  # items such as the star stay active
        self.projectiles = []
        self._snap_camera()

    # ----- insights, mini boss and quiz -----------------------------------

    def _show_insight(self, key):
        """Play the animation of an insight; the insight is earned afterwards."""
        self.game.audio.play("note")
        self.game.push_scene(InsightScene(self.game, key, on_close=lambda: self._earn_insight(key)))

    def _earn_insight(self, key):
        """Add an insight to the notebook and give the reward."""
        if key in self.insights:
            return
        self.insights.append(key)
        self._add_sparks(SPARKS_PER_INSIGHT)
        self._say(f"Insight {len(self.insights)}/{self.n_insights_total}: +{SPARKS_PER_INSIGHT}", ui.GOLD)

    def _talk_to_professor_fin(self):
        game = self.game
        if self.flanker_passed:
            game.push_scene(MessageScene(game, "Professor Fin", ["Take the pipe behind the pond!"]))
            return

        def start_task():
            scene = FlankerScene(game, self._on_flanker_finished, self.flanker_settings, game.rng, show_tutorial=not game.flanker_tutorial_seen)
            game.flanker_tutorial_seen = True
            game.audio.play_music("pond")  # calm music that is the same in every condition
            game.push_scene(scene)

        pages = ["Blub! Win my fish challenge and I will build you a bridge."]
        game.push_scene(MessageScene(game, "Professor Fin", pages, on_close=start_task))

    def _on_flanker_finished(self, passed, summary, results):
        game = self.game
        if summary is None:
            game.push_scene(MessageScene(game, "Professor Fin", ["Talk to me again (E) when you are ready."]))
            return
        self.flanker_accuracy = summary.accuracy
        if not passed:
            text = f"{summary.accuracy:.0%} - you need {self.flanker_settings.pass_accuracy:.0%}. Talk to me again (E) to retry."
            game.push_scene(MessageScene(game, "Professor Fin", [text]))
            return
        gained_heart = self._win_pond_challenge()
        reward = "+1 heart and the SPOTLIGHT for the dark cave" if gained_heart else "the SPOTLIGHT for the dark cave"
        pages = [f"Wonderful focus! The bridge is ready. Reward: {reward}. Now watch what happened in your head ..."]
        game.push_scene(MessageScene(game, "Professor Fin", pages, on_close=lambda: self._show_insight("flanker")))

    def _next_question(self):
        topic = self.quiz_topics.pop(0)
        self.quiz_topics.append(topic)
        self.active_question = make_question(topic, self.game.rng)

    def _talk_to_owl(self):
        game = self.game
        if self.quiz_passed:
            game.push_scene(MessageScene(game, "The Owl", ["The goal is behind the wall!"]))
            return
        if not self.map_shown:
            # First the big picture, then the quiz.
            self.map_shown = True
            game.push_scene(InsightScene(game, "map", on_close=self._talk_to_owl))
            return
        if self.active_question is None:
            self._next_question()
        game.push_scene(MessageScene(game, "The Owl", ["Which effect do you see on my board? Stand on the right pipe and press S."]))

    def _answer_quiz(self, pipe):
        game, question = self.game, self.active_question
        if self.quiz_passed:
            self._travel(pipe)
        elif question is None:
            self._say("Talk to the owl first (E)", ui.SOFT_BLUE)
        elif pipe.answer_index == question.correct_index:
            self.quiz_passed = True
            self.active_question = None
            game.audio.play("correct")
            self._travel(replace(pipe, label="Correct!"))
        else:
            game.audio.play("wrong")
            if self.difficulty.wrong_answer_costs_heart:
                self.player.hearts -= 1
                if self._check_game_over():
                    return
            right = INSIGHTS[question.topic].short_name
            game.push_scene(MessageScene(game, "The Owl", [f"Dead end! That was the {right}. Here is a new one."], on_close=self._next_question))

    # ----- rules ----------------------------------------------------------

    def _check_game_over(self):
        if self.player.hearts > 0:
            return False
        self.game.push_scene(GameOverScene(self.game))
        return True

    def _say(self, text, color=ui.WHITE):
        """Show a short floating text above the hero."""
        self.effects.append(Effect("text", self.player.center_x, self.player.y - 10, text, color))

    def _add_sparks(self, amount=1):
        self.game.audio.play("spark")
        if self.player.add_sparks(amount):
            self._say("+1 heart!", ui.RED)

    def _release_block_content(self, content, cell):
        if content == "spark":
            self._add_sparks()
            self._say("+1")
        elif content in ITEMS:
            self.powerups.append(PowerUp(content, cell))
        elif content == "heart":
            self.game.audio.play("powerup")
            self._say("+1 heart!" if self.player.heal() else "Hearts full!", ui.RED)

    def _hurt(self, from_x):
        """Take a hit from pixel column ``from_x``; return True if the game is over."""
        if not self.player.take_hit(from_x):
            return False
        self.game.audio.play("hurt")
        return self._check_game_over()

    def _lose_heart_by_falling(self):
        self.falls += 1
        if self.difficulty.falling_costs_heart:
            self.player.hearts -= 1
        self.game.audio.play("hurt")
        if not self._check_game_over():
            self.player.respawn(*self.respawn_point)
            self._snap_camera()

    def _start_celebration(self):
        """Reach the goal: fireworks first, then the end screen."""
        self.celebration_time = 0.0
        self.player.vx = 0.0
        self.game.audio.play("win")

    def _update_celebration(self, dt):
        """Launch and move fireworks; open the end screen after a while."""
        self.celebration_time += dt
        self.next_firework -= dt
        rng = self.firework_rng
        if self.next_firework <= 0:
            self.next_firework = FIREWORK_INTERVAL
            x = self.camera_x + rng.uniform(150, SCREEN_WIDTH - 150)
            y = rng.uniform(90, 330)
            color = rng.choice(FIREWORK_COLORS)
            for index in range(36):
                angle = 2 * math.pi * index / 36
                speed = rng.uniform(160, 340)
                self.fireworks.append([x, y, math.cos(angle) * speed, math.sin(angle) * speed, color, rng.uniform(0.9, 1.4)])
            self.game.audio.play("firework")
        for spark in self.fireworks:
            spark[0] += spark[2] * dt
            spark[1] += spark[3] * dt
            spark[3] += FIREWORK_GRAVITY * dt
            spark[5] -= dt
        self.fireworks = [spark for spark in self.fireworks if spark[5] > 0]
        if self.celebration_time >= CELEBRATION_TIME and self.game.scenes[-1] is self:
            self._finish_level()

    def _finish_level(self):
        accuracy = "-" if self.flanker_accuracy is None else f"{self.flanker_accuracy:.0%}"
        stats = [
            ("Difficulty", self.difficulty.name),
            ("Total time", format_time(self.total_time)),
            ("Sparks", str(self.player.sparks)),
            ("Insights", f"{len(self.insights)}/{self.n_insights_total}"),
            ("Pond Challenge accuracy", accuracy),
            ("Hearts left", str(self.player.hearts)),
        ]
        self.game.push_scene(LevelCompleteScene(self.game, stats))

    # ----- update ---------------------------------------------------------

    def update(self, dt):
        self.time += dt
        player, level = self.player, self.level
        if self.celebration_time is not None:
            self._update_celebration(dt)
            return
        self.total_time += dt
        # The Focus Star has its own music, like the star in Super Mario.
        self.game.audio.play_music("star" if player.has_star else level.zone_at(player.center_x).theme)

        for platform in self.platforms:
            platform.update(dt)
        direction = (pygame.K_d in self.held_keys) - (pygame.K_a in self.held_keys)
        if self.admin:
            rising = any(key in self.held_keys for key in JUMP_KEYS)
            player.fly(dt, direction, (pygame.K_s in self.held_keys) - rising, level)
            player.invulnerable_timer = 0.2  # nothing hurts in admin mode
            bumped_cell = None
        else:
            bumped_cell = player.update(dt, direction, pygame.K_s in self.held_keys, level)
            for platform in self.platforms:
                if platform.carry(player):
                    break
            self._use_springs(dt)
        if player.jump_started:
            self.game.audio.play(player.jump_started)
        if bumped_cell:
            content = level.hit_block(bumped_cell)
            if content:
                self._release_block_content(content, bumped_cell)

        for firebar in self.firebars:
            firebar.update(dt)
        if any(firebar.hits(player.rect) for firebar in self.firebars):
            if self._hurt(player.center_x + (1 if player.vx >= 0 else -1)):
                return
        if level.spike_hits(player.rect):
            # Knock the hero back the way they came from.
            if self._hurt(player.center_x + (1 if player.vx >= 0 else -1)):
                return
        if self._update_enemies(dt):
            return
        self._update_projectiles(dt)
        self._update_pickups(dt)
        for effect in self.effects:
            effect.update(dt)
        self.effects = [effect for effect in self.effects if not effect.is_gone]
        self.camera_x += (self._camera_target() - self.camera_x) * min(1.0, 10 * dt)

        if player.y > SCREEN_HEIGHT + TILE_SIZE:
            self._lose_heart_by_falling()
        elif abs(player.center_x - level.goal_x) < TILE_SIZE and (player.on_ground or self.admin):
            self._start_celebration()

    def _use_springs(self, dt):
        """Launch the hero who lands on a spring."""
        player = self.player
        self.spring_squash = [max(0.0, squash - dt) for squash in self.spring_squash]
        for index, spring in enumerate(self.level.springs):
            over = player.x + player.width > spring.left and player.x < spring.right
            landing = player.vy >= 0 and player.previous_bottom <= spring.top + 6 and player.y + player.height >= spring.top
            if over and landing:
                player.y = spring.top - player.height
                player.spring()
                self.spring_squash[index] = 0.25
                self.game.audio.play("jump")

    def _camera_target(self):
        """Where the camera wants to be: ahead of the hero, inside the hero's zone."""
        zone = self.level.zone_at(self.player.center_x)
        left = zone.first_col * TILE_SIZE
        right = (zone.last_col + 1) * TILE_SIZE - SCREEN_WIDTH
        return min(max(self.player.center_x - SCREEN_WIDTH * CAMERA_LEAD, left), max(left, right))

    def _snap_camera(self):
        self.camera_x = self._camera_target()

    def _update_enemies(self, dt):
        """Move the enemies and handle contact; return True if the game is over."""
        player = self.player
        for enemy in self.enemies:
            if abs(enemy.x - player.x) < ACTIVE_DISTANCE or not enemy.is_active:
                enemy.update(dt, self.level)
            if not enemy.is_active or not enemy.rect.colliderect(player.rect):
                continue
            if player.has_star:
                if enemy.kind != "brute":  # the Brute stays a puzzle, even for a star
                    enemy.knock_out(1 if enemy.center_x > player.center_x else -1)
                    self.game.audio.play("stomp")
                    self._add_sparks()
                continue
            # A stomp: the hero was above the enemy a moment ago and is moving down.
            stomp = player.vy > 0 and player.previous_bottom <= enemy.y + enemy.height * 0.5
            if stomp and enemy.stompable:
                enemy.squish()
                player.bounce()
                self.game.audio.play("stomp")
                self._add_sparks()
            elif self._hurt(enemy.center_x):
                return True
        self.enemies = [enemy for enemy in self.enemies if not enemy.is_gone]
        return False

    def _update_pickups(self, dt):
        player, level = self.player, self.level
        center = player.rect.center
        for spark in level.sparks:
            if not spark.collected and math.dist(center, (spark.x, spark.y)) < PICKUP_DISTANCE:
                spark.collected = True
                self._add_sparks()
        for demo in level.demos:
            if not demo.shown and player.center_x > demo.x:
                demo.shown = True
                self.game.push_scene(InsightScene(self.game, demo.key))
        for orb in level.orbs:
            if not orb.collected and math.dist(center, (orb.x, orb.y)) < ORB_PICKUP_DISTANCE:
                orb.collected = True
                self._show_insight(orb.key)
        for item in self.powerups:
            item.update(dt, level)
            if item.rect.colliderect(player.rect):
                item.collected = True
                player.collect(item.kind)
                self.game.audio.play("powerup")
                self._say(ITEM_MESSAGES[item.kind], ui.GOLD)
        self.powerups = [item for item in self.powerups if not item.is_gone]
        for checkpoint in level.checkpoints:
            if not checkpoint.active and abs(checkpoint.x - player.center_x) < TILE_SIZE and player.on_ground:
                checkpoint.active = True
                self.respawn_point = (checkpoint.x - player.width / 2, checkpoint.ground_y)
                self.game.audio.play("checkpoint")
                self._say("Checkpoint!", ui.GREEN)
        shrine = self._nearby([s for s in level.shrines if not s.used])
        if shrine and abs(shrine.x - player.center_x) < TILE_SIZE:
            shrine.used = True
            self._learn_skill(shrine.skill)

    # ----- drawing --------------------------------------------------------

    def draw(self, surface):
        camera = round(self.camera_x)
        level, player, time = self.level, self.player, self.time
        zone = level.zone_at(player.center_x)
        self.backdrops[zone.theme].draw(surface, camera, time)
        for first_col, last_col in level.water_spans:
            top = GROUND_ROW * TILE_SIZE + 22
            water = pygame.Rect(first_col * TILE_SIZE - camera, top, (last_col - first_col + 1) * TILE_SIZE, SCREEN_HEIGHT - top)
            graphics.draw_water(surface, water, time)
        self._draw_tiles(surface, camera)
        for pipe in level.pipes.values():
            graphics.draw_pipe(surface, pipe.rect.move(-camera, 0), pipe.kind)
        for platform in self.platforms:
            if isinstance(platform, CrumblePlatform):
                if platform.state != "gone":
                    rect = platform.rect.move(round(platform.shake_offset) - camera, 0)
                    graphics.draw_crumble(surface, rect, level.zone_at(platform.x).theme, platform.state == "shaking")
            else:
                graphics.draw_moving_platform(surface, platform.rect.move(-camera, 0))
        for index, spring in enumerate(level.springs):
            graphics.draw_spring(surface, spring.move(-camera, 0), self.spring_squash[index] / 0.25)
        for firebar in self.firebars:
            if -200 < firebar.x - camera < SCREEN_WIDTH + 200:
                for x, y in firebar.balls:
                    graphics.draw_fireball(surface, x - camera, y, time)

        for checkpoint in level.checkpoints:
            graphics.draw_checkpoint(surface, checkpoint.x - camera, checkpoint.ground_y, checkpoint.active, time)
        for sign in level.signs:
            graphics.draw_sign(surface, sign.x - camera, sign.ground_y)
        for shrine in level.shrines:
            graphics.draw_shrine(surface, shrine.x - camera, shrine.ground_y, time, shrine.used, shrine.skill)
        for orb in level.orbs:
            graphics.draw_orb(surface, orb.x - camera, orb.y, time, orb.collected)
        for npc in level.npcs:
            draw_npc = graphics.NPC_DRAWERS.get(npc.kind, graphics.draw_owl)
            draw_npc(surface, npc.x - camera, npc.ground_y, time)
        graphics.draw_goal(surface, level.goal_x - camera, level.player_start[1], time)
        for spark in level.sparks:
            if not spark.collected and -20 < spark.x - camera < SCREEN_WIDTH + 20:
                graphics.draw_spark(surface, spark.x - camera, spark.y, time)
        for item in self.powerups:
            graphics.draw_powerup(surface, item.kind, item.rect.x - camera, item.rect.y, time)
        for enemy in self.enemies:
            if -100 < enemy.x - camera < SCREEN_WIDTH + 100:
                graphics.draw_enemy(surface, enemy, enemy.rect.x - camera, enemy.rect.y, time)

        if player.has_star:
            glow = pygame.Surface((110, 110), pygame.SRCALPHA)
            color = FIREWORK_COLORS[int(time * 10) % len(FIREWORK_COLORS)]
            pygame.draw.circle(glow, (*color, 110), (55, 55), 44)
            surface.blit(glow, glow.get_rect(center=player.rect.move(-camera, 0).center))
        blinking = player.is_invulnerable and not self.admin and int(time * 12) % 2 == 0
        if not blinking:
            graphics.draw_hero(
                surface, self.game.character, player.rect.x - camera, player.rect.y, player.facing, time,
                abs(player.vx) > 20, player.on_ground, player.is_boosted, player.is_punching, player.is_shooting,
            )
        if player.has_shield:
            graphics.draw_shield_bubble(surface, player.rect.move(-camera, 0), time)
        for shot in self.projectiles:
            graphics.draw_projectile(surface, shot.rect.move(-camera, 0), shot.text, shot.direction)
        self._draw_fireworks(surface, camera)
        if zone.dark:
            self._draw_darkness(surface, camera)
        self._draw_effects(surface, camera)
        self._draw_pipe_labels(surface, camera)
        self._draw_hint(surface, camera)
        self._draw_hud(surface)

    def _draw_fireworks(self, surface, camera):
        """Draw the firework sparks with short glowing trails, and a cheer."""
        for x, y, vx, vy, color, left in self.fireworks:
            size = max(2, int(6 * min(1.0, left)))
            tail = (x - camera - vx * 0.06, y - vy * 0.06)
            pygame.draw.line(surface, color, tail, (x - camera, y), max(1, size - 2))
            pygame.draw.circle(surface, (255, 255, 255), (x - camera, y), size // 2 + 1)
            pygame.draw.circle(surface, color, (x - camera, y), size, 2)
        if self.celebration_time is not None:
            bounce = abs(math.sin(self.celebration_time * 4)) * 10
            ui.draw_text(surface, "LEVEL COMPLETE!", (SCREEN_WIDTH // 2, 200 - bounce), 110, ui.GOLD, "center", bold=True, shadow=True)

    def _draw_tiles(self, surface, camera):
        level, images = self.level, self.tile_images
        first_col = camera // TILE_SIZE
        for col in range(first_col, first_col + SCREEN_WIDTH // TILE_SIZE + 2):
            theme = level.zone_at(col * TILE_SIZE).theme
            for row in range(LEVEL_ROWS):
                kind = level.tiles.get((col, row))
                if kind == "ground":
                    kind = f"{theme}_fill" if level.tiles.get((col, row - 1)) == "ground" else f"{theme}_top"
                if kind is not None and kind != "pipe":  # pipes are drawn as a whole
                    surface.blit(images[kind], (col * TILE_SIZE - camera, row * TILE_SIZE))
                pointing = level.spikes.get((col, row))
                if pointing:
                    surface.blit(images[f"spikes_{pointing}"], (col * TILE_SIZE - camera, row * TILE_SIZE))
        if self.player.has_spotlight:
            shimmer = 150 + int(math.sin(self.time * 6) * 90)
            for cell in level.hidden_blocks:
                outline = cell_rect(cell).move(-camera, 0)
                pygame.draw.rect(surface, (255, 250, shimmer), outline, 3, border_radius=8)
                ui.draw_text(surface, "?", outline.center, 36, (255, 250, shimmer), "center", bold=True)

    def _draw_darkness(self, surface, camera):
        """Darken a cave except around the hero and around glowing things."""
        level, player = self.level, self.player
        self.darkness.fill(DARKNESS)

        def light_up(radius, x, y):
            light = self.lights[radius]
            self.darkness.blit(light, (x - camera - radius, y - radius), special_flags=pygame.BLEND_RGBA_MIN)

        light_up(SPOTLIGHT_RADIUS if player.has_spotlight else DIM_LIGHT_RADIUS, *player.rect.center)
        for thing in level.shrines + level.checkpoints + list(level.pipes.values()):
            light_up(GLOW_RADIUS, thing.x, thing.ground_y - 60)
        for orb in level.orbs:
            if not orb.collected:
                light_up(GLOW_RADIUS, orb.x, orb.y)
        surface.blit(self.darkness, (0, 0))

    def _draw_effects(self, surface, camera):
        for effect in self.effects:
            x, y, progress = effect.x - camera, effect.y, effect.progress
            if effect.kind == "text":
                ui.draw_text(surface, effect.text, (x, y), 30, effect.color, "midbottom", bold=True, shadow=True)
            elif effect.kind == "ring":
                radius = int(self.player.settings.fear_radius * progress)
                pygame.draw.circle(surface, effect.color, (int(x), int(y)), max(4, radius), 5)
            else:
                for index in range(8):
                    angle = math.pi / 4 * index + 0.4
                    distance = 50 * progress
                    piece = pygame.Rect(0, 0, 10, 10)
                    piece.center = (x + math.cos(angle) * distance, y + math.sin(angle) * distance + 60 * progress**2)
                    pygame.draw.rect(surface, effect.color, piece)

    def _draw_pipe_labels(self, surface, camera):
        """Write the destinations above the pipes and the answers above the quiz pipes."""
        question = self.active_question
        zone = self.level.zone_at(self.player.center_x)
        on_screen = False
        for pipe in self.level.pipes.values():
            x = pipe.x - camera
            if not -150 < x < SCREEN_WIDTH + 150 or self.level.zone_at(pipe.x) is not zone:
                continue
            text = pipe.label
            if pipe.kind == "quiz":
                on_screen = True
                text = INSIGHTS[question.options[pipe.answer_index]].short_name if question else "?"
            if not text:
                continue
            lines = ui.wrap_text(text, ui.get_font(26), 180)
            box = pygame.Rect(0, 0, 196, 20 + len(lines) * 26)
            box.midbottom = (x, pipe.ground_y - 70)
            box.clamp_ip(pygame.Rect(8, 0, SCREEN_WIDTH - 16, SCREEN_HEIGHT))  # keep it readable at the edge
            ui.draw_panel(surface, box, radius=10)
            for index, line in enumerate(lines):
                ui.draw_text(surface, line, (box.centerx, box.top + 10 + index * 26), 26, ui.WHITE, "midtop")
        if question and on_screen:
            board = pygame.Rect(0, 0, 400, 236)
            board.midtop = (SCREEN_WIDTH // 2, 96)
            ui.draw_panel(surface, board)
            ui.draw_text(surface, "Which effect is this?", (board.centerx, board.top + 14), 30, ui.GOLD, "midtop", bold=True)
            picture = pygame.Rect(0, 0, 360, 180)
            picture.midbottom = (board.centerx, board.bottom - 12)
            self.quiz_animations[question.topic].draw_thumbnail(surface, picture, self.time)

    def _draw_hint(self, surface, camera):
        """Show which key works at the place where the hero stands."""
        pipe = self._pipe_below()
        thing = self._nearby(self.level.npcs) or self._nearby(self.level.signs)
        if pipe is not None and pipe.kind != "exit":
            label, x, y = "S: enter", pipe.x, pipe.ground_y - 150
        elif thing is None:
            return
        else:
            label = "E: read" if thing in self.level.signs else "E: talk"
            x, y = thing.x, thing.ground_y - 180
        bubble = pygame.Rect(0, 0, ui.get_font(28, bold=True).size(label)[0] + 40, 40)
        bubble.midbottom = (x - camera, y + math.sin(self.time * 4) * 4)
        ui.draw_panel(surface, bubble, radius=12)
        ui.draw_text(surface, label, bubble.center, 28, ui.GOLD, "center", bold=True)

    def _draw_hud(self, surface):
        player = self.player
        for index in range(max(player.hearts, player.settings.start_hearts)):
            graphics.draw_heart(surface, 24 + index * 40, 20, 32, filled=index < player.hearts)
        graphics.draw_spark(surface, 40, 80, 0)
        ui.draw_text(surface, f"x {player.sparks}", (62, 68), 34, ui.WHITE, bold=True, shadow=True)
        pygame.draw.circle(surface, ui.GOLD, (40, 124), 15)
        ui.draw_text(surface, "i", (40, 124), 30, ui.INK, "center", bold=True)
        ui.draw_text(surface, f"{len(self.insights)}/{self.n_insights_total} insights   TAB: notebook", (62, 112), 30, ui.WHITE, shadow=True)
        ui.draw_text(surface, f"{self.level.name}  ({self.difficulty.name})", (SCREEN_WIDTH - 24, 20), 30, ui.WHITE, "topright", shadow=True)
        ui.draw_text(surface, f"Time {format_time(self.total_time)}", (SCREEN_WIDTH - 24, 52), 30, ui.WHITE, "topright", shadow=True)
        if player.has_spotlight:
            ui.draw_text(surface, "Spotlight active", (SCREEN_WIDTH - 24, 84), 28, ui.GOLD, "topright", bold=True, shadow=True)
        self._draw_item_bars(surface)
        self._draw_skill_bar(surface)
        if self.game.allow_admin and not self.admin:
            ui.draw_text(surface, "P: admin mode", (SCREEN_WIDTH - 24, SCREEN_HEIGHT - 40), 24, ui.WHITE, "topright", shadow=True)
        if self.admin:
            lines = ["ADMIN MODE  (P: off)", "Fly: A/D, W or SPACE up, S down"] + list(self.admin_actions.values())
            box = pygame.Rect(SCREEN_WIDTH - 330, 130, 310, 24 + len(lines) * 26)
            ui.draw_panel(surface, box, border=ui.RED, radius=12)
            for index, line in enumerate(lines):
                ui.draw_text(surface, line, (box.left + 16, box.top + 12 + index * 26), 24, ui.RED if index == 0 else ui.WHITE, bold=index == 0)

    def _draw_item_bars(self, surface):
        """Show how long the active items last, at the top of the screen."""
        player, settings = self.player, self.player.settings
        bars = [
            ("ZOOM", player.boost_timer / settings.boost_duration, (90, 170, 250)),
            ("STAR", player.star_timer / settings.star_duration, (255, 214, 92)),
            ("SHIELD", 1.0 if player.has_shield else 0.0, (130, 220, 255)),
        ]
        active = [bar for bar in bars if bar[1] > 0]
        for index, (label, share, color) in enumerate(active):
            bar = pygame.Rect(0, 0, 180, 16)
            bar.midtop = (SCREEN_WIDTH // 2 + (index - (len(active) - 1) / 2) * 200, 24)
            pygame.draw.rect(surface, ui.INK, bar, border_radius=8)
            pygame.draw.rect(surface, color, (bar.x, bar.y, int(bar.width * share), bar.height), border_radius=8)
            pygame.draw.rect(surface, ui.WHITE, bar, 2, border_radius=8)
            ui.draw_text(surface, label, (bar.centerx, bar.bottom + 4), 24, ui.WHITE, "midtop", bold=True, shadow=True)

    def _draw_skill_bar(self, surface):
        """List the known skills with their keys in the bottom-left corner."""
        player = self.player
        x = 20
        for key, skill in SKILLS.items():
            if key not in player.skills:
                continue
            label = f"{skill.button}: {skill.name}"
            box = pygame.Rect(x, SCREEN_HEIGHT - 52, ui.get_font(26).size(label)[0] + 28, 36)
            ready = key != "fear" or player.fear_cooldown <= 0
            ui.draw_panel(surface, box, border=ui.GOLD if ready else (120, 124, 150), radius=10)
            ui.draw_text(surface, label, box.center, 26, ui.WHITE if ready else (150, 154, 180), "center")
            if not ready:
                share = player.fear_cooldown / player.settings.fear_cooldown
                pygame.draw.rect(surface, ui.SOFT_BLUE, (box.x + 6, box.bottom - 7, int((box.width - 12) * (1 - share)), 4))
            x = box.right + 10
