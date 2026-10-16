"""The title card shown before each level, like a world screen in Super Mario.

It names the level and its topic, plays a looping picture of what the level
is about and tells the next part of the story in two short lines.
"""

import math

import pygame

from . import graphics, ui
from .config import SCREEN_HEIGHT, SCREEN_WIDTH
from .content import LEVELS
from .insight_animations import ANIMATIONS
from .scenes import CONFIRM_KEYS, INPUT_DELAY, Scene

# Story lines and the looping picture of each level.
LEVEL_INTROS = {
    "prologue": (
        ("Count Hackula has p-hacked the Archive of the Mind.", "Learn how science checks itself - and free the hidden results!"),
        "hackula",
    ),
    "level_1": (
        ("Hackula's Distractors swarm the Focus Fields.", "Find out what attention is - and keep your focus!"),
        "attention",
    ),
    "level_2": (
        ("Hackula's champion, Captain Impulse, acts before he thinks.", "Learn to stop in time - on ice, in traffic and in the volcano!"),
        "inhibition",
    ),
    "level_3": (
        ("In Mission Control, Hackula's Rule Keeper keeps changing the rules.", "Remember, plan and switch - and take back control!"),
        "executive_functions",
    ),
    "finale": (
        ("Count Hackula hides in his castle with his last p-hacked findings.", "Use everything you have learned - and let the light in!"),
        "hackula",
    ),
}


class LevelIntroScene(Scene):
    """
    The title card of a level, shown on top of it until SPACE is pressed.

    Parameters
    ----------
    game : Game
        The running game.
    key : str
        Key of the level (see ``LEVEL_INTROS``).
    """

    is_overlay = True
    stops_clock = True

    def __init__(self, game, key):
        super().__init__(game)
        self.info = next(level for level in LEVELS if level.key == key)
        self.lines, animation = LEVEL_INTROS[key]
        self.animation = ANIMATIONS[animation](game.character)
        self.number = [level.key for level in LEVELS].index(key)
        self.age = 0.0
        self.background = graphics.vertical_gradient((SCREEN_WIDTH, SCREEN_HEIGHT), (30, 26, 70), (8, 8, 24))

    def update(self, dt):
        self.age += dt

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in CONFIRM_KEYS + (pygame.K_ESCAPE,) and self.age > INPUT_DELAY:
            self.game.audio.play("select")
            self.game.pop_scene()

    def draw(self, surface):
        surface.blit(self.background, (0, 0))
        center_x = SCREEN_WIDTH // 2
        title, _, name = self.info.title.partition(": ")
        ui.draw_text(surface, title.upper(), (center_x, 70), 40, ui.SOFT_BLUE, "center", bold=True)
        bounce = math.sin(self.age * 3) * 4
        ui.draw_text(surface, name or title, (center_x, 130 + bounce), 84, ui.GOLD, "center", bold=True, shadow=True)
        ui.draw_text(surface, f"Topic: {self.info.topic}", (center_x, 190), 36, ui.WHITE, "center")
        picture = pygame.Rect(0, 0, 560, 280)
        picture.midtop = (center_x, 230)
        self.animation.draw_thumbnail(surface, picture, self.age)
        pygame.draw.rect(surface, ui.GOLD, picture, 3, border_radius=8)
        for index, line in enumerate(self.lines):
            ui.draw_text(surface, line, (center_x, 548 + index * 40), 34, ui.WHITE, "center")
        for index in range(len(LEVELS)):
            color = ui.GOLD if index == self.number else (80, 84, 120)
            pygame.draw.circle(surface, color, (center_x + (index - (len(LEVELS) - 1) / 2) * 40, 640), 10)
        if self.age > INPUT_DELAY and int(self.age * 2) % 2 == 0:
            ui.draw_text(surface, "Press SPACE to start", (center_x, 686), 32, ui.GOLD, "center", bold=True)
