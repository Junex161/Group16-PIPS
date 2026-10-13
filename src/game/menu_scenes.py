"""The home screen and its sub-pages (how to play, references)."""

import pygame

from . import graphics, ui
from .characters import CHARACTERS
from .config import GAME_TITLE, SCREEN_HEIGHT, SCREEN_WIDTH
from .content import LEVELS, REFERENCES, SKILLS
from .scenes import Scene

LEFT_KEYS = (pygame.K_a, pygame.K_LEFT)
RIGHT_KEYS = (pygame.K_d, pygame.K_RIGHT)
UP_KEYS = (pygame.K_w, pygame.K_UP)
DOWN_KEYS = (pygame.K_s, pygame.K_DOWN)
CONFIRM_KEYS = (pygame.K_SPACE, pygame.K_RETURN)

CONTROLS = (
    ("A / D", "walk left and right"),
    ("SPACE or W", "jump (hold for a higher jump)"),
    ("S", "fall faster"),
    ("F", "punch enemies and crates"),
    ("E", "talk and read signs"),
    ("TAB", "open your notebook"),
    ("M", "sound on / off"),
    ("ESC", "pause"),
)
RULES = (
    "You have three hearts. Enemies and spikes cost one heart.",
    "Falling down costs a heart and sends you back to the last checkpoint flag.",
    "Without hearts you start again from the very beginning.",
    "Collect the notes: the owl at the end asks a question about them.",
    "Glowing shrines teach new skills such as the Double Jump.",
)


class HomeScene(Scene):
    """
    The home screen: choose a hero, pick a level or open an info page.

    A/D switches the hero, W/S moves through the menu, SPACE confirms.
    """

    EXTRA_ENTRIES = ("How to play", "References", "Quit")

    def __init__(self, game):
        super().__init__(game)
        self.backdrop = graphics.Backdrop()
        self.time = 0.0
        self.entries = [level.title for level in LEVELS] + list(self.EXTRA_ENTRIES)
        self.selected = next(index for index, level in enumerate(LEVELS) if level.playable)
        self.hint = ""

    def update(self, dt):
        self.time += dt
        self.game.audio.play_music("meadow")

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        game = self.game
        characters = list(CHARACTERS)
        if event.key in LEFT_KEYS + RIGHT_KEYS:
            step = 1 if event.key in RIGHT_KEYS else -1
            game.character = characters[(characters.index(game.character) + step) % len(characters)]
            game.audio.play("select")
        elif event.key in UP_KEYS + DOWN_KEYS:
            step = 1 if event.key in DOWN_KEYS else -1
            self.selected = (self.selected + step) % len(self.entries)
            self.hint = ""
            game.audio.play("select")
        elif event.key in CONFIRM_KEYS:
            self._confirm()
        elif event.key == pygame.K_ESCAPE:
            game.quit()

    def _confirm(self):
        game = self.game
        entry = self.entries[self.selected]
        if self.selected < len(LEVELS):
            if LEVELS[self.selected].playable:
                game.audio.play("powerup")
                game.start_level()
            else:
                game.audio.play("wrong")
                self.hint = "This level is still under construction."
        elif entry == "How to play":
            game.push_scene(HowToPlayScene(game))
        elif entry == "References":
            game.push_scene(ReferencesScene(game))
        else:
            game.quit()

    def draw(self, surface):
        self.backdrop.draw(surface, self.time * 30, self.time)
        ui.draw_text(surface, GAME_TITLE, (SCREEN_WIDTH // 2, 64), 96, ui.GOLD, "center", bold=True, shadow=True)
        self._draw_hero_panel(surface)
        self._draw_menu(surface)
        self._draw_info(surface)

    def _draw_hero_panel(self, surface):
        box = pygame.Rect(60, 130, 380, 400)
        ui.draw_panel(surface, box)
        ui.draw_text(surface, "Choose your hero", (box.centerx, box.top + 24), 36, ui.GOLD, "midtop", bold=True)
        character = self.game.character
        portrait = pygame.Surface((80, 70), pygame.SRCALPHA)
        graphics.draw_hero(portrait, character, 20, 14, 1, self.time, True, True)
        portrait = pygame.transform.scale(portrait, (240, 210))
        surface.blit(portrait, portrait.get_rect(center=(box.centerx, box.top + 180)))
        ui.draw_text(surface, "<  A", (box.left + 24, box.top + 170), 34, ui.SOFT_BLUE)
        ui.draw_text(surface, "D  >", (box.right - 24, box.top + 170), 34, ui.SOFT_BLUE, "topright")
        ui.draw_text(surface, character.name, (box.centerx, box.top + 296), 44, ui.WHITE, "midtop", bold=True)
        ui.draw_paragraph(surface, character.description, (box.left + 24, box.top + 344), box.width - 48, 26, ui.SOFT_BLUE, centered=True)

    def _draw_menu(self, surface):
        box = pygame.Rect(480, 130, 740, 400)
        ui.draw_panel(surface, box)
        for index, entry in enumerate(self.entries):
            y = box.top + 26 + index * 50 + (16 if index >= len(LEVELS) else 0)
            is_level = index < len(LEVELS)
            locked = is_level and not LEVELS[index].playable
            color = ui.GOLD if index == self.selected else (150, 154, 180) if locked else ui.WHITE
            marker = ">" if index == self.selected else " "
            ui.draw_text(surface, f"{marker}  {entry}", (box.left + 30, y), 34, color, bold=index == self.selected)
            if is_level:
                label = "under construction" if locked else LEVELS[index].topic
                ui.draw_text(surface, label, (box.right - 30, y + 4), 26, color, "topright")

    def _draw_info(self, surface):
        box = pygame.Rect(60, 550, SCREEN_WIDTH - 120, 140)
        ui.draw_panel(surface, box)
        if self.selected < len(LEVELS):
            level = LEVELS[self.selected]
            ui.draw_text(surface, f"{level.title}  -  Topic: {level.topic}", (box.left + 30, box.top + 18), 32, ui.GOLD, bold=True)
            ui.draw_paragraph(surface, self.hint or level.description, (box.left + 30, box.top + 56), box.width - 60, 28)
        else:
            texts = {
                "How to play": "The controls, the rules and the skills you can learn.",
                "References": "The scientific sources behind the notes, the flanker task and the skills.",
                "Quit": "Close the game.",
            }
            ui.draw_paragraph(surface, texts[self.entries[self.selected]], (box.left + 30, box.top + 40), box.width - 60, 30)
        ui.draw_text(surface, "W/S: menu    A/D: hero    SPACE: select", (box.right - 30, box.bottom - 36), 24, ui.SOFT_BLUE, "topright")


class InfoScene(Scene):
    """Base class of the info pages: a panel that closes on any confirm key."""

    is_overlay = True
    title = ""

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in CONFIRM_KEYS + (pygame.K_ESCAPE,):
            self.game.pop_scene()

    def draw(self, surface):
        ui.dim(surface, 190)
        box = pygame.Rect(50, 30, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 60)
        ui.draw_panel(surface, box)
        ui.draw_text(surface, self.title, (box.left + 36, box.top + 22), 44, ui.GOLD, bold=True)
        ui.draw_text(surface, "SPACE: back", (box.right - 36, box.top + 34), 26, ui.SOFT_BLUE, "topright")
        self.draw_content(surface, box)

    def draw_content(self, surface, box):
        """Draw the page content inside ``box``."""


class HowToPlayScene(InfoScene):
    """Controls, rules and skills on one page."""

    title = "How to play"

    def draw_content(self, surface, box):
        for index, (key, action) in enumerate(CONTROLS):
            y = box.top + 90 + index * 36
            ui.draw_text(surface, key, (box.left + 36, y), 28, ui.GOLD, bold=True)
            ui.draw_text(surface, action, (box.left + 220, y), 28)
        right = box.left + 620
        ui.draw_text(surface, "Skills", (right, box.top + 90), 32, ui.GOLD, bold=True)
        y = box.top + 130
        for skill in SKILLS.values():
            ui.draw_text(surface, f"{skill.name}  [{skill.button}]", (right, y), 28, ui.SOFT_BLUE, bold=True)
            y = ui.draw_paragraph(surface, skill.pages[-1], (right, y + 30), box.right - right - 36, 22, line_gap=3) + 10
        y = box.top + 400
        ui.draw_text(surface, "Rules", (box.left + 36, y), 32, ui.GOLD, bold=True)
        for index, rule in enumerate(RULES):
            ui.draw_text(surface, f"-  {rule}", (box.left + 36, y + 40 + index * 32), 24)


class ReferencesScene(InfoScene):
    """The reference list of the game."""

    title = "References"

    def draw_content(self, surface, box):
        y = box.top + 84
        for reference in REFERENCES:
            y = ui.draw_paragraph(surface, reference, (box.left + 36, y), box.width - 72, 26, line_gap=2) + 8
