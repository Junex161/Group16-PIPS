"""Scene base class and the simple menu and text screens.

The game keeps a stack of scenes; only the top one receives input and
updates. Overlay scenes (text boxes, the notebook, pause) are drawn on top of
the scene below them.
"""

import pygame

from . import graphics, ui
from .characters import CHARACTERS
from .config import GAME_TITLE, SCREEN_HEIGHT, SCREEN_WIDTH
from .content import INSIGHTS, SKILL_CARDS, STORY
from .insight_animations import ANIMATIONS, Stage

CONFIRM_KEYS = (pygame.K_SPACE, pygame.K_RETURN, pygame.K_e)
# Ignore key presses right after a text box opens, so a jump does not skip it.
INPUT_DELAY = 0.35


class Scene:
    """One screen of the game. Subclasses override the methods they need."""

    is_overlay = False
    # True for scenes during which the level timer stands still.
    stops_clock = False

    def __init__(self, game):
        self.game = game

    def handle_event(self, event):
        """React to one pygame event."""

    def update(self, dt):
        """Advance the scene by ``dt`` seconds."""

    def draw(self, surface):
        """Draw the scene."""

    def on_resume(self):
        """Called when the scene above this one was closed."""

    def update_in_background(self, dt):
        """Called every frame while another scene is on top of this one."""


class MessageScene(Scene):
    """
    A text box with one or more pages, shown on top of the current scene.

    Parameters
    ----------
    game : Game
        The running game.
    title : str
        Heading of the box.
    pages : sequence of str
        Texts shown one after the other.
    on_close : callable or None, optional
        Called without arguments after the last page was confirmed.
    footer : str, optional
        Small line below the text, for example a source.
    """

    is_overlay = True

    def __init__(self, game, title, pages, on_close=None, footer=""):
        super().__init__(game)
        self.title, self.pages, self.on_close, self.footer = title, list(pages), on_close, footer
        self.page = 0
        self.age = 0.0

    def update(self, dt):
        self.age += dt

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or event.key not in CONFIRM_KEYS or self.age < INPUT_DELAY:
            return
        self.page += 1
        self.age = 0.0
        if self.page >= len(self.pages):
            self.game.pop_scene()
            if self.on_close:
                self.on_close()

    def draw(self, surface):
        ui.dim(surface, 110)
        box = pygame.Rect(0, 0, 900, 330)
        box.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        ui.draw_panel(surface, box)
        ui.draw_text(surface, self.title, (box.left + 40, box.top + 30), 44, ui.GOLD, bold=True)
        page = self.pages[min(self.page, len(self.pages) - 1)]
        ui.draw_paragraph(surface, page, (box.left + 40, box.top + 90), box.width - 80, 32)
        if self.footer:
            ui.draw_text(surface, self.footer, (box.left + 40, box.bottom - 44), 26, ui.SOFT_BLUE)
        counter = f"{self.page + 1}/{len(self.pages)}  " if len(self.pages) > 1 else ""
        ui.draw_text(surface, counter + "SPACE to continue", (box.right - 40, box.bottom - 44), 26, ui.GOLD, anchor="topright")


class InsightScene(Scene):
    """
    Play an insight animation (see insight_animations.py) full screen.

    The beats run one after the other, each with one caption line. For an
    insight a final card shows its key term, a one-sentence definition and
    the source. SPACE skips to the next beat, ESC closes.

    Parameters
    ----------
    game : Game
        The running game.
    key : str
        Key in ``insight_animations.ANIMATIONS``.
    on_close : callable or None, optional
        Called without arguments when the scene closes.
    """

    STAGE = pygame.Rect(190, 100, 900, 450)

    def __init__(self, game, key, on_close=None):
        super().__init__(game)
        self.animation = ANIMATIONS[key](game.character)
        self.insight = INSIGHTS.get(key) or SKILL_CARDS.get(key)
        self.on_close = on_close
        self.n_steps = len(self.animation.beats) + (1 if self.insight else 0)
        self.step = 0
        self.clock = 0.0
        self.background = graphics.vertical_gradient((SCREEN_WIDTH, SCREEN_HEIGHT), (34, 30, 70), (10, 10, 28))

    @property
    def on_card(self):
        """True while the final card of an insight is shown."""
        return self.step >= len(self.animation.beats)

    def next_step(self):
        """Go to the next beat, or close after the last one."""
        if self.step >= self.n_steps - 1:
            self.close()
        else:
            self.step += 1
            self.clock = 0.0

    def close(self):
        """Leave the animation."""
        self.game.pop_scene()
        if self.on_close:
            self.on_close()

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.close()
        elif event.key in CONFIRM_KEYS and self.clock >= INPUT_DELAY:
            self.next_step()

    def update(self, dt):
        self.clock += dt
        if not self.on_card and self.step == self.n_steps - 1 and self.clock >= self.animation.beats[self.step].duration:
            self.clock = self.animation.beats[self.step].duration  # the last beat waits
        elif not self.on_card and self.clock >= self.animation.beats[self.step].duration:
            self.next_step()

    def draw(self, surface):
        surface.blit(self.background, (0, 0))
        ui.draw_text(surface, self.animation.title, (SCREEN_WIDTH // 2, 54), 52, ui.GOLD, "center", bold=True)
        stage = Stage(self.STAGE)
        if self.on_card:
            self._draw_card(surface, stage)
            caption = "Press TAB in the level to watch it again."
        else:
            beat = self.animation.beats[self.step]
            self.animation.draw_beat(surface, stage, self.step, min(1.0, self.clock / beat.duration), self.clock)
            caption = beat.caption
        pygame.draw.rect(surface, ui.GOLD, self.STAGE, 3, border_radius=8)
        ui.draw_text(surface, caption, (SCREEN_WIDTH // 2, 596), 38, ui.WHITE, "center")
        for index in range(self.n_steps):
            color = ui.GOLD if index == self.step else (90, 94, 130)
            pygame.draw.circle(surface, color, (SCREEN_WIDTH // 2 + (index - (self.n_steps - 1) / 2) * 28, 646), 7)
        ui.draw_text(surface, "SPACE: next      ESC: close", (SCREEN_WIDTH // 2, 690), 24, ui.SOFT_BLUE, "center")

    def _draw_card(self, surface, stage):
        insight = self.insight
        pygame.draw.rect(surface, (24, 28, 58), stage.rect)
        thumbnail = pygame.Rect(stage.rect.left + 30, stage.rect.top + 120, 380, 190)
        self.animation.draw_thumbnail(surface, thumbnail, self.clock)
        pygame.draw.rect(surface, ui.GOLD, thumbnail, 2, border_radius=6)
        left = thumbnail.right + 30
        width = stage.rect.right - left - 30
        y = ui.draw_paragraph(surface, insight.term, (left, stage.rect.top + 110), width, 56, ui.GOLD)
        y = ui.draw_paragraph(surface, insight.definition, (left, y + 10), width, 34)
        ui.draw_text(surface, insight.source, (left, y + 14), 28, ui.SOFT_BLUE)


class NotebookScene(Scene):
    """The notebook: the earned insights with a looping picture each."""

    is_overlay = True

    def __init__(self, game, earned_keys):
        super().__init__(game)
        self.keys = list(earned_keys)
        self.selected = 0
        self.time = 0.0
        self.animations = {key: ANIMATIONS[key](game.character) for key in self.keys}

    def update(self, dt):
        self.time += dt

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_TAB, pygame.K_ESCAPE):
            self.game.pop_scene()
        elif self.keys and event.key in (pygame.K_w, pygame.K_UP):
            self.selected = (self.selected - 1) % len(self.keys)
        elif self.keys and event.key in (pygame.K_s, pygame.K_DOWN):
            self.selected = (self.selected + 1) % len(self.keys)
        elif self.keys and event.key in CONFIRM_KEYS:
            self.game.push_scene(InsightScene(self.game, self.keys[self.selected]))

    def draw(self, surface):
        ui.dim(surface)
        box = pygame.Rect(90, 60, SCREEN_WIDTH - 180, SCREEN_HEIGHT - 120)
        ui.draw_panel(surface, box)
        ui.draw_text(surface, f"Insights  ({len(self.keys)}/{len(INSIGHTS)})", (box.left + 40, box.top + 28), 44, ui.GOLD, bold=True)
        ui.draw_text(surface, "W/S: choose    SPACE: watch again    TAB: close", (box.right - 40, box.top + 40), 26, ui.SOFT_BLUE, "topright")
        if not self.keys:
            ui.draw_paragraph(surface, "Touch the glowing orbs to collect insights.", (box.left + 40, box.top + 120), 800, 32)
            return
        for index, key in enumerate(self.keys):
            color = ui.GOLD if index == self.selected else ui.WHITE
            marker = "> " if index == self.selected else "   "
            ui.draw_text(surface, marker + INSIGHTS[key].short_name, (box.left + 40, box.top + 110 + index * 44), 30, color)
        key = self.keys[self.selected]
        insight = INSIGHTS[key]
        picture = pygame.Rect(box.left + 420, box.top + 100, 520, 260)
        self.animations[key].draw_thumbnail(surface, picture, self.time)
        pygame.draw.rect(surface, ui.GOLD, picture, 2, border_radius=6)
        ui.draw_text(surface, insight.term, (picture.left, picture.bottom + 20), 40, ui.GOLD, bold=True)
        bottom = ui.draw_paragraph(surface, insight.definition, (picture.left, picture.bottom + 66), box.right - picture.left - 40, 30)
        ui.draw_text(surface, insight.source, (picture.left, bottom + 8), 26, ui.SOFT_BLUE)


class TransitionScene(Scene):
    """
    The trip through a pipe: fade to black, a short loading screen, fade in.

    Parameters
    ----------
    game : Game
        The running game.
    on_dark : callable
        Called once when the loading screen appears; it should move the player.
    label : str, optional
        Name of the destination, shown on the loading screen.
    """

    is_overlay = True
    FADE_TIME = 0.3
    LOADING_TIME = 1.4

    def __init__(self, game, on_dark, label=""):
        super().__init__(game)
        self.on_dark, self.label = on_dark, label
        self.age = 0.0
        self.moved = False

    @property
    def total_time(self):
        """Length of the whole trip in seconds."""
        return 2 * self.FADE_TIME + self.LOADING_TIME

    def update(self, dt):
        self.age += dt
        if not self.moved and self.age >= self.FADE_TIME:
            self.moved = True
            self.on_dark()
        if self.age >= self.total_time:
            self.game.pop_scene()

    def draw(self, surface):
        loading_start, loading_end = self.FADE_TIME, self.FADE_TIME + self.LOADING_TIME
        if self.age < loading_start:
            ui.dim(surface, int(255 * self.age / self.FADE_TIME))
            return
        if self.age > loading_end:
            ui.dim(surface, int(255 * max(0.0, 1 - (self.age - loading_end) / self.FADE_TIME)))
            return
        share = (self.age - loading_start) / self.LOADING_TIME
        surface.fill((10, 10, 26))
        center_x = SCREEN_WIDTH // 2
        # The hero slides down a pipe ...
        pipe = pygame.Rect(0, 0, 96, 150)
        pipe.midtop = (center_x, 250)
        hero_y = 150 + 170 * min(1.0, share * 1.3)
        graphics.draw_hero(surface, self.game.character, center_x - 17, int(hero_y), 1, 0.0, False, False)
        pygame.draw.rect(surface, (10, 10, 26), (0, pipe.bottom, SCREEN_WIDTH, SCREEN_HEIGHT - pipe.bottom))
        graphics.draw_pipe(surface, pipe)
        # ... while a bar fills up.
        ui.draw_text(surface, self.label or "Off we go!", (center_x, 470), 52, ui.GOLD, "center", bold=True)
        bar = pygame.Rect(0, 0, 420, 22)
        bar.center = (center_x, 540)
        pygame.draw.rect(surface, (40, 44, 80), bar, border_radius=11)
        pygame.draw.rect(surface, ui.GOLD, (bar.x, bar.y, int(bar.width * share), bar.height), border_radius=11)
        pygame.draw.rect(surface, ui.WHITE, bar, 2, border_radius=11)
        ui.draw_text(surface, "Loading" + "." * (int(self.age * 4) % 4), (center_x, 580), 30, ui.SOFT_BLUE, "midtop")


class TitleScene(Scene):
    """Title screen: the logo, the story in one paragraph and the three heroes."""

    def __init__(self, game):
        super().__init__(game)
        self.backdrop = graphics.Backdrop()
        self.time = 0.0

    def update(self, dt):
        self.time += dt
        self.game.audio.play_music("title")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.game.audio.play("select")
            self.game.show_home()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.quit()

    def draw(self, surface):
        self.backdrop.draw(surface, self.time * 40, self.time)
        center_x = SCREEN_WIDTH // 2
        ui.draw_text(surface, GAME_TITLE, (center_x, 150), 150, ui.GOLD, "center", bold=True, shadow=True)
        ui.draw_text(surface, "A jump-and-run adventure through psychology", (center_x, 240), 40, ui.WHITE, "center", shadow=True)
        box = pygame.Rect(0, 0, 900, 150)
        box.midtop = (center_x, 300)
        ui.draw_panel(surface, box)
        ui.draw_paragraph(surface, STORY, (box.left + 30, box.top + 24), box.width - 60, 30, centered=True)
        for index, character in enumerate(CHARACTERS):
            graphics.draw_hero(surface, character, center_x - 110 + index * 100, 526, 1, self.time + index * 0.3, True, True)
        pygame.draw.rect(surface, graphics.GRASS, (0, 576, SCREEN_WIDTH, SCREEN_HEIGHT - 576))
        pygame.draw.rect(surface, graphics.GRASS_LIGHT, (0, 576, SCREEN_WIDTH, 6))
        if int(self.time * 2) % 2 == 0:
            ui.draw_text(surface, "Press SPACE to start", (center_x, 640), 44, ui.WHITE, "center", shadow=True)


class PauseScene(Scene):
    """Pause menu."""

    is_overlay = True
    stops_clock = True

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_ESCAPE, pygame.K_SPACE):
            self.game.pop_scene()
        elif event.key == pygame.K_q:
            self.game.show_home()

    def draw(self, surface):
        ui.dim(surface)
        center_x = SCREEN_WIDTH // 2
        ui.draw_text(surface, "Paused", (center_x, 260), 90, ui.GOLD, "center", bold=True)
        ui.draw_text(surface, "SPACE or ESC: continue      Q: back to the home screen", (center_x, 360), 34, ui.WHITE, "center")
        ui.draw_text(surface, "M: sound on / off (works at any time)", (center_x, 410), 30, ui.SOFT_BLUE, "center")


class GameOverScene(Scene):
    """Shown when all hearts are lost; restarts the game from the beginning."""

    is_overlay = True

    def __init__(self, game):
        super().__init__(game)
        self.age = 0.0

    def update(self, dt):
        self.age += dt

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in CONFIRM_KEYS and self.age > INPUT_DELAY * 2:
            self.game.start_level()

    def draw(self, surface):
        ui.dim(surface, 200)
        center_x = SCREEN_WIDTH // 2
        ui.draw_text(surface, "Out of hearts!", (center_x, 270), 90, ui.RED, "center", bold=True)
        ui.draw_text(surface, "You are sent back to the very beginning.", (center_x, 360), 36, ui.WHITE, "center")
        ui.draw_text(surface, "Press SPACE to try again", (center_x, 430), 36, ui.GOLD, "center")


class LevelCompleteScene(Scene):
    """
    End screen with the statistics of the run.

    Parameters
    ----------
    game : Game
        The running game.
    stats : list of tuple
        ``(label, value)`` pairs of strings to list on the screen.
    """

    is_overlay = True

    def __init__(self, game, stats):
        super().__init__(game)
        self.stats = stats
        self.age = 0.0

    def update(self, dt):
        self.age += dt

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or self.age < INPUT_DELAY * 2:
            return
        if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
            self.game.show_home()

    def draw(self, surface):
        ui.dim(surface, 180)
        box = pygame.Rect(0, 0, 760, 540)
        box.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        ui.draw_panel(surface, box)
        ui.draw_text(surface, "Level complete!", (box.centerx, box.top + 60), 72, ui.GOLD, "center", bold=True)
        for index, (label, value) in enumerate(self.stats):
            y = box.top + 120 + index * 46
            ui.draw_text(surface, label, (box.left + 90, y), 34)
            ui.draw_text(surface, value, (box.right - 90, y), 34, ui.GOLD, "topright", bold=True)
        ui.draw_text(surface, "More levels are coming soon.", (box.centerx, box.bottom - 100), 30, ui.SOFT_BLUE, "center")
        ui.draw_text(surface, "SPACE: back to the home screen", (box.centerx, box.bottom - 50), 32, ui.WHITE, "center")
