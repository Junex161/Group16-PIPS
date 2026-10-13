"""The platformer itself: the hero running through a level.

``PlayScene`` connects the level, the player, the enemies, the flanker mini
boss and the quiz gate, and applies the rules of the game (hearts,
checkpoints, skills, rewards).
"""

import math

import pygame

from . import graphics, ui
from .config import SCREEN_HEIGHT, SCREEN_WIDTH, TILE_SIZE
from .content import CUES, QUESTIONS, SKILLS
from .entities import ENEMY_KINDS, Effect, MovingPlatform, Mushroom, Player
from .flanker_scene import FlankerScene
from .level import GROUND_ROW, LEVEL_ROWS, cell_rect
from .level_one import build_level_one
from .quiz_scene import QuizScene
from .scenes import GameOverScene, LevelCompleteScene, MessageScene, NotebookScene, PauseScene, Scene

JUMP_KEYS = (pygame.K_SPACE, pygame.K_w)
PUNCH_KEY = pygame.K_f
FEAR_KEY = pygame.K_q
TALK_DISTANCE = 100
PICKUP_DISTANCE = 30
# Enemies further away than this from the player stand still.
ACTIVE_DISTANCE = SCREEN_WIDTH
# Share of the screen width that is kept between the hero and the left edge.
CAMERA_LEAD = 0.4
# Colour of the cave darkness (RGBA) and the radius of light around things.
DARKNESS = (6, 6, 20, 240)
SPOTLIGHT_RADIUS = 300
DIM_LIGHT_RADIUS = 150
GLOW_RADIUS = 80
BACKDROP_FADE_TIME = 0.6


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

    def __init__(self, game, build_level=build_level_one):
        super().__init__(game)
        self.level = build_level()
        self.player = Player(*self.level.player_start, game.player_settings)
        self.enemies = [ENEMY_KINDS[start.kind](start.x, start.ground_y, start.patrol) for start in self.level.enemy_starts]
        self.platforms = [
            MovingPlatform(start.x, start.y, start.width, start.travel_x, start.travel_y, start.period)
            for start in self.level.platform_starts
        ]
        self.mushrooms = []
        self.effects = []
        self.collected_notes = []
        self.n_notes_total = self.level.n_notes + 1  # one more note comes from Professor Fin
        self.respawn_point = self.level.player_start
        self.questions = list(QUESTIONS)
        game.rng.shuffle(self.questions)
        self.flanker_passed = False
        self.flanker_accuracy = None
        self.gate_open = False
        self.falls = 0
        # ``time`` drives animations; ``total_time`` also runs during the
        # flanker task, the quiz and text boxes and is shown to the player.
        self.time = 0.0
        self.total_time = 0.0
        self.camera_x = 0.0
        self.held_keys = set()
        self.tile_images = graphics.make_tile_images()
        self.backdrops = {zone.theme: graphics.Backdrop(zone.theme) for zone in self.level.zones}
        self.backdrop_theme = self.level.zones[0].theme
        self.previous_theme = None
        self.backdrop_fade = 0.0
        self.fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.darkness = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.lights = {radius: graphics.make_light(radius, DARKNESS) for radius in (SPOTLIGHT_RADIUS, DIM_LIGHT_RADIUS, GLOW_RADIUS)}

    # ----- input ----------------------------------------------------------

    def on_resume(self):
        """Forget keys that may have been released while an overlay was open."""
        pressed = pygame.key.get_pressed()
        self.held_keys = {key for key in (pygame.K_a, pygame.K_d, pygame.K_s) if pressed[key]}
        self.player.release_jump()

    def update_in_background(self, dt):
        if not self.game.scenes[-1].stops_clock:
            self.total_time += dt

    def handle_event(self, event):
        if event.type == pygame.KEYUP:
            self.held_keys.discard(event.key)
            if event.key in JUMP_KEYS:
                self.player.release_jump()
        elif event.type == pygame.KEYDOWN:
            self.held_keys.add(event.key)
            if event.key in JUMP_KEYS:
                self.player.press_jump()
            elif event.key == PUNCH_KEY:
                self._punch()
            elif event.key == FEAR_KEY:
                self._use_fear()
            elif event.key == pygame.K_e:
                self._interact()
            elif event.key == pygame.K_TAB:
                self.game.push_scene(NotebookScene(self.game, self.collected_notes))
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

    # ----- skills ---------------------------------------------------------

    def _punch(self):
        player = self.player
        if not player.start_punch():
            return
        self.game.audio.play("punch")
        fist = player.punch_rect
        for enemy in self.enemies:
            if not enemy.is_active or not enemy.rect.colliderect(fist):
                continue
            if enemy.punchable:
                enemy.knock_out(player.facing)
                self._add_sparks()
            else:
                self._say("Too tough! Scare it away.", ui.SOFT_BLUE)
        for cell, content in self.level.break_crates(fist):
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
        self.game.push_scene(MessageScene(self.game, title, skill.pages, footer=skill.source))

    # ----- mini boss and quiz ---------------------------------------------

    def _talk_to_professor_fin(self):
        game = self.game
        if self.flanker_passed:
            text = "The bridge is yours. Your Spotlight will light the cave on the other side!"
            game.push_scene(MessageScene(game, "Professor Fin", [text]))
            return

        def start_task():
            scene = FlankerScene(game, self._on_flanker_finished, game.flanker_settings, game.rng, show_tutorial=not game.flanker_tutorial_seen)
            game.flanker_tutorial_seen = True
            game.audio.pause_music()  # no distraction during the experiment
            game.push_scene(scene)

        pages = [
            "Blub! I am Professor Fin and this is my pond. It is far too wide to jump.",
            "Show me that you can FOCUS your attention and I will build you a bridge. "
            "Ready for my Pond Challenge?",
        ]
        game.push_scene(MessageScene(game, "Professor Fin", pages, on_close=start_task))

    def _on_flanker_finished(self, passed, summary, results):
        game = self.game
        game.audio.resume_music()
        if summary is None:
            game.push_scene(MessageScene(game, "Professor Fin", ["Come back when you are ready. Just talk to me again (E)."]))
            return
        self.flanker_accuracy = summary.accuracy
        if not passed:
            text = (
                f"You fed {summary.accuracy:.0%} of the fish correctly, but you need "
                f"{game.flanker_settings.pass_accuracy:.0%}. Take a breath and talk to me again (E) to retry."
            )
            game.push_scene(MessageScene(game, "Professor Fin", [text]))
            return
        self.flanker_passed = True
        self.level.build_bridge()
        self.player.has_spotlight = True
        game.audio.play("powerup")
        gained_heart = self.player.heal()
        reward = "an extra heart and the SPOTLIGHT" if gained_heart else "the SPOTLIGHT"
        pages = [
            f"Wonderful focus! The bridge is ready. As a reward you get {reward}.",
            "The Spotlight lights up the dark cave ahead and makes hidden blocks shimmer. "
            "I also added a note about what you just experienced to your notebook.",
        ]
        game.push_scene(MessageScene(game, "Professor Fin", pages, on_close=lambda: self._collect_note("flanker")))

    def _talk_to_owl(self):
        game = self.game
        if self.gate_open:
            game.push_scene(MessageScene(game, "The Owl", ["The gate is open. The goal is just ahead!"]))
            return

        def ask():
            question = self.questions.pop(0)
            self.questions.append(question)
            game.push_scene(QuizScene(game, question, self._on_quiz_finished))

        pages = [
            "Hoo! Nobody passes my gate without knowing about ATTENTION.",
            f"You found {len(self.collected_notes)} of {self.n_notes_total} notes. Answer one question "
            "correctly and I open the gate. But careful: a wrong answer costs you a heart!",
        ]
        game.push_scene(MessageScene(game, "The Owl", pages, on_close=ask))

    def _on_quiz_finished(self, correct):
        game = self.game
        if correct:
            self.gate_open = True
            self.level.open_gate()
            game.push_scene(MessageScene(game, "The Owl", ["Well done! You paid attention. The gate is open."]))
            return
        self.player.hearts -= 1
        if self._check_game_over():
            return
        text = "You lose a heart. Read your notes (TAB) and talk to me again for another question."
        game.push_scene(MessageScene(game, "The Owl", [text]))

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

    def _collect_note(self, key):
        if key in self.collected_notes:
            return
        self.collected_notes.append(key)
        self.game.audio.play("note")
        cue = CUES[key]
        title = f"Note {len(self.collected_notes)}/{self.n_notes_total}: {cue.title}"
        self.game.push_scene(MessageScene(self.game, title, [cue.text], footer=cue.source))

    def _release_block_content(self, content, cell):
        if content == "spark":
            self._add_sparks()
            self._say("+1")
        elif content == "mushroom":
            self.mushrooms.append(Mushroom(cell))
        elif content == "heart":
            self.game.audio.play("powerup")
            self._say("+1 heart!" if self.player.heal() else "Hearts full!", ui.RED)
        elif content.startswith("note:"):
            self._collect_note(content.split(":", 1)[1])

    def _hurt(self, from_x):
        """Take a hit from pixel column ``from_x``; return True if the game is over."""
        if not self.player.take_hit(from_x):
            return False
        self.game.audio.play("hurt")
        return self._check_game_over()

    def _lose_heart_by_falling(self):
        self.falls += 1
        self.player.hearts -= 1
        self.game.audio.play("hurt")
        if not self._check_game_over():
            self.player.respawn(*self.respawn_point)

    def _finish_level(self):
        accuracy = "-" if self.flanker_accuracy is None else f"{self.flanker_accuracy:.0%}"
        stats = [
            ("Total time", format_time(self.total_time)),
            ("Sparks", str(self.player.sparks)),
            ("Attention notes", f"{len(self.collected_notes)}/{self.n_notes_total}"),
            ("Pond Challenge accuracy", accuracy),
            ("Hearts left", str(self.player.hearts)),
        ]
        self.game.audio.play("win")
        self.game.push_scene(LevelCompleteScene(self.game, stats))

    # ----- update ---------------------------------------------------------

    def update(self, dt):
        self.time += dt
        self.total_time += dt
        player, level = self.player, self.level
        self.game.audio.play_music(level.zone_at(player.center_x).theme)

        for platform in self.platforms:
            platform.update(dt)
        direction = (pygame.K_d in self.held_keys) - (pygame.K_a in self.held_keys)
        bumped_cell = player.update(dt, direction, pygame.K_s in self.held_keys, level)
        for platform in self.platforms:
            if platform.carry(player):
                break
        if player.jump_started:
            self.game.audio.play(player.jump_started)
        if bumped_cell:
            content = level.hit_block(bumped_cell)
            if content:
                self._release_block_content(content, bumped_cell)

        if level.spike_hits(player.rect):
            # Knock the hero back the way they came from.
            if self._hurt(player.center_x + (1 if player.vx >= 0 else -1)):
                return
        if self._update_enemies(dt):
            return
        self._update_pickups(dt)
        for effect in self.effects:
            effect.update(dt)
        self.effects = [effect for effect in self.effects if not effect.is_gone]

        target = player.center_x - SCREEN_WIDTH * CAMERA_LEAD
        target = min(max(target, 0), level.pixel_width - SCREEN_WIDTH)
        self.camera_x += (target - self.camera_x) * min(1.0, 10 * dt)
        self._update_backdrop(dt)

        if player.y > SCREEN_HEIGHT + TILE_SIZE:
            self._lose_heart_by_falling()
        elif abs(player.center_x - level.goal_x) < TILE_SIZE and player.on_ground:
            self._finish_level()

    def _update_backdrop(self, dt):
        theme = self.level.zone_at(self.camera_x + SCREEN_WIDTH / 2).theme
        if theme != self.backdrop_theme:
            self.previous_theme, self.backdrop_theme = self.backdrop_theme, theme
            self.backdrop_fade = 1.0
        self.backdrop_fade = max(0.0, self.backdrop_fade - dt / BACKDROP_FADE_TIME)

    def _update_enemies(self, dt):
        """Move the enemies and handle contact; return True if the game is over."""
        player = self.player
        for enemy in self.enemies:
            if abs(enemy.x - player.x) < ACTIVE_DISTANCE or not enemy.is_active:
                enemy.update(dt, self.level)
            if not enemy.is_active or not enemy.rect.colliderect(player.rect):
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
        for note in level.notes:
            if not note.collected and math.dist(center, (note.x, note.y)) < PICKUP_DISTANCE + 10:
                note.collected = True
                self._collect_note(note.key)
        for mushroom in self.mushrooms:
            mushroom.update(dt, level)
            if mushroom.rect.colliderect(player.rect):
                mushroom.y = SCREEN_HEIGHT * 2  # removed below
                player.boost_timer = player.settings.boost_duration
                self.game.audio.play("powerup")
                self._say("Zoom!", ui.GOLD)
        self.mushrooms = [m for m in self.mushrooms if m.y < SCREEN_HEIGHT + TILE_SIZE]
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
        self._draw_backdrop(surface, camera)
        for first_col, last_col in level.water_spans:
            top = GROUND_ROW * TILE_SIZE + 22
            water = pygame.Rect(first_col * TILE_SIZE - camera, top, (last_col - first_col + 1) * TILE_SIZE, SCREEN_HEIGHT - top)
            graphics.draw_water(surface, water, time)
        self._draw_tiles(surface, camera)
        for platform in self.platforms:
            graphics.draw_moving_platform(surface, platform.rect.move(-camera, 0))

        for checkpoint in level.checkpoints:
            graphics.draw_checkpoint(surface, checkpoint.x - camera, checkpoint.ground_y, checkpoint.active, time)
        for sign in level.signs:
            graphics.draw_sign(surface, sign.x - camera, sign.ground_y)
        for shrine in level.shrines:
            graphics.draw_shrine(surface, shrine.x - camera, shrine.ground_y, time, shrine.used)
        for npc in level.npcs:
            draw_npc = graphics.draw_professor_fin if npc.kind == "professor_fin" else graphics.draw_owl
            draw_npc(surface, npc.x - camera, npc.ground_y, time)
        graphics.draw_goal(surface, level.goal_x - camera, level.player_start[1], time)
        for spark in level.sparks:
            if not spark.collected and -20 < spark.x - camera < SCREEN_WIDTH + 20:
                graphics.draw_spark(surface, spark.x - camera, spark.y, time)
        for note in level.notes:
            if not note.collected:
                graphics.draw_note(surface, note.x - camera, note.y, time, glow=True)
        for mushroom in self.mushrooms:
            graphics.draw_mushroom(surface, mushroom.rect.x - camera, mushroom.rect.y)
        for enemy in self.enemies:
            if -100 < enemy.x - camera < SCREEN_WIDTH + 100:
                graphics.draw_enemy(surface, enemy, enemy.rect.x - camera, enemy.rect.y, time)

        blinking = player.is_invulnerable and int(time * 12) % 2 == 0
        if not blinking:
            graphics.draw_hero(
                surface, self.game.character, player.rect.x - camera, player.rect.y, player.facing, time,
                abs(player.vx) > 20, player.on_ground, player.is_boosted, player.is_punching,
            )
        self._draw_darkness(surface, camera)
        self._draw_effects(surface, camera)
        self._draw_talk_hint(surface, camera)
        self._draw_hud(surface)

    def _draw_backdrop(self, surface, camera):
        self.backdrops[self.backdrop_theme].draw(surface, camera, self.time)
        if self.backdrop_fade > 0 and self.previous_theme:
            self.backdrops[self.previous_theme].draw(self.fade_surface, camera, self.time)
            self.fade_surface.set_alpha(int(255 * self.backdrop_fade))
            surface.blit(self.fade_surface, (0, 0))

    def _draw_tiles(self, surface, camera):
        level, images = self.level, self.tile_images
        first_col = camera // TILE_SIZE
        for col in range(first_col, first_col + SCREEN_WIDTH // TILE_SIZE + 2):
            theme = level.zone_at(col * TILE_SIZE).theme
            for row in range(LEVEL_ROWS):
                kind = level.tiles.get((col, row))
                if kind == "ground":
                    kind = f"{theme}_fill" if level.tiles.get((col, row - 1)) == "ground" else f"{theme}_top"
                if kind is not None:
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
        strength = level.darkness_at(player.center_x)
        if strength <= 0:
            return
        self.darkness.fill(DARKNESS)

        def light_up(radius, x, y):
            light = self.lights[radius]
            self.darkness.blit(light, (x - camera - radius, y - radius), special_flags=pygame.BLEND_RGBA_MIN)

        light_up(SPOTLIGHT_RADIUS if player.has_spotlight else DIM_LIGHT_RADIUS, *player.rect.center)
        for note in level.notes:
            if not note.collected:
                light_up(GLOW_RADIUS, note.x, note.y)
        for thing in level.shrines + level.checkpoints:
            light_up(GLOW_RADIUS, thing.x, thing.ground_y - 70)
        self.darkness.set_alpha(int(255 * strength))
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

    def _draw_talk_hint(self, surface, camera):
        thing = self._nearby(self.level.npcs) or self._nearby(self.level.signs)
        if thing is None:
            return
        bubble = pygame.Rect(0, 0, 150, 40)
        bubble.midbottom = (thing.x - camera, thing.ground_y - 180 + math.sin(self.time * 4) * 4)
        ui.draw_panel(surface, bubble, radius=12)
        label = "E: read" if thing in self.level.signs else "E: talk"
        ui.draw_text(surface, label, bubble.center, 28, ui.GOLD, "center", bold=True)

    def _draw_hud(self, surface):
        player = self.player
        for index in range(max(player.hearts, player.settings.start_hearts)):
            graphics.draw_heart(surface, 24 + index * 40, 20, 32, filled=index < player.hearts)
        graphics.draw_spark(surface, 40, 80, 0)
        ui.draw_text(surface, f"x {player.sparks}", (62, 68), 34, ui.WHITE, bold=True, shadow=True)
        graphics.draw_note(surface, 40, 124, 0)
        ui.draw_text(surface, f"{len(self.collected_notes)}/{self.n_notes_total}   TAB: notebook", (62, 112), 30, ui.WHITE, shadow=True)
        ui.draw_text(surface, self.level.name, (SCREEN_WIDTH - 24, 20), 30, ui.WHITE, "topright", shadow=True)
        ui.draw_text(surface, f"Time {format_time(self.total_time)}", (SCREEN_WIDTH - 24, 52), 30, ui.WHITE, "topright", shadow=True)
        if player.has_spotlight:
            ui.draw_text(surface, "Spotlight active", (SCREEN_WIDTH - 24, 84), 28, ui.GOLD, "topright", bold=True, shadow=True)
        if player.is_boosted:
            share = player.boost_timer / player.settings.boost_duration
            bar = pygame.Rect(SCREEN_WIDTH // 2 - 120, 24, 240, 18)
            pygame.draw.rect(surface, ui.INK, bar, border_radius=9)
            pygame.draw.rect(surface, (90, 170, 250), (bar.x, bar.y, int(bar.width * share), bar.height), border_radius=9)
            pygame.draw.rect(surface, ui.WHITE, bar, 2, border_radius=9)
            ui.draw_text(surface, "ZOOM", (bar.centerx, bar.bottom + 4), 24, ui.WHITE, "midtop", bold=True, shadow=True)
        self._draw_skill_bar(surface)

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
