"""Scene base class and the simple menu and text screens.

The game keeps a stack of scenes; only the top one receives input and
updates. Overlay scenes (text boxes, the notebook, pause) are drawn on top of
the scene below them.
"""

import pygame

from . import graphics, ui
from .characters import CHARACTERS
from .config import GAME_TITLE, SCREEN_HEIGHT, SCREEN_WIDTH
from .content import CUES, STORY

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


class NotebookScene(Scene):
    """The notebook: lets the player re-read all collected attention notes."""

    is_overlay = True

    def __init__(self, game, collected_keys):
        super().__init__(game)
        self.keys = list(collected_keys)
        self.selected = 0

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_TAB, pygame.K_ESCAPE):
            self.game.pop_scene()
        elif self.keys and event.key in (pygame.K_w, pygame.K_UP):
            self.selected = (self.selected - 1) % len(self.keys)
        elif self.keys and event.key in (pygame.K_s, pygame.K_DOWN):
            self.selected = (self.selected + 1) % len(self.keys)

    def draw(self, surface):
        ui.dim(surface)
        box = pygame.Rect(90, 60, SCREEN_WIDTH - 180, SCREEN_HEIGHT - 120)
        ui.draw_panel(surface, box)
        ui.draw_text(surface, f"Notebook  ({len(self.keys)}/{len(CUES)} notes)", (box.left + 40, box.top + 28), 44, ui.GOLD, bold=True)
        ui.draw_text(surface, "W/S: choose a note    TAB: close", (box.right - 40, box.top + 40), 26, ui.SOFT_BLUE, anchor="topright")
        if not self.keys:
            ui.draw_paragraph(surface, "No notes yet. Explore the level to find them!", (box.left + 40, box.top + 120), 600, 32)
            return
        for index, key in enumerate(self.keys):
            color = ui.GOLD if index == self.selected else ui.WHITE
            marker = "> " if index == self.selected else "   "
            ui.draw_text(surface, marker + CUES[key].title, (box.left + 40, box.top + 110 + index * 44), 30, color)
        cue = CUES[self.keys[self.selected]]
        text_left = box.left + 440
        ui.draw_text(surface, cue.title, (text_left, box.top + 110), 36, ui.GOLD, bold=True)
        bottom = ui.draw_paragraph(surface, cue.text, (text_left, box.top + 160), box.right - text_left - 40, 30)
        ui.draw_text(surface, cue.source, (text_left, bottom + 12), 26, ui.SOFT_BLUE)


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
