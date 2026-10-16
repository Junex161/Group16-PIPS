"""Enemies of the Prologue and Levels 2 and 3.

They reuse the enemy classes of ``entities.py`` and only change how they
move and look. ``register()`` adds them to ``entities.ENEMY_KINDS``, so that
level layouts can place them with ``Level.add_enemy``.
"""

import math

from . import worlds
from .config import SCREEN_HEIGHT
from .entities import ENEMY_KINDS, Buzzer, Enemy, Spikeback


class Hackling(Buzzer):
    """One of Count Hackula's bats: flies back and forth (Prologue)."""

    kind = "hackling"
    SPEED = 100.0
    draw_function = staticmethod(worlds.draw_hackling)


class Slider(Enemy):
    """A penguin that slides fast and can hardly stop (Level 2, ice)."""

    kind = "slider"
    SPEED = 150.0
    draw_function = staticmethod(worlds.draw_slider)


class Ember(Enemy):
    """
    A hot-headed lava blob that leaps out of a lava pit again and again.

    It cannot be stomped, only punched or shot (Level 2, volcano).
    """

    kind = "ember"
    WIDTH, HEIGHT = 36, 36
    LEAP_SPEED = 1050.0
    GRAVITY = 1500.0
    REST_TIME = 1.4
    stompable = False
    draw_function = staticmethod(worlds.draw_ember)

    def __init__(self, x, ground_y, patrol=None):
        super().__init__(x, ground_y, patrol)
        self.base_y = SCREEN_HEIGHT + 30
        self.y = self.base_y
        # Embers start at different moments, so they do not leap in step.
        self.rest = (x / 97) % self.REST_TIME

    def update(self, dt, level):
        """Leap up, fall back into the lava, rest and leap again."""
        if not self.is_active:
            super().update(dt, level)
            return
        if self.speed_factor <= 0:
            return  # frozen by the Stop Signal
        if self.rest > 0:
            self.rest -= dt * self.speed_factor
            if self.rest <= 0:
                self.vy = -self.LEAP_SPEED
            return
        self.vy += self.GRAVITY * dt
        self.y += self.vy * dt
        if self.y >= self.base_y:
            self.y, self.vy, self.rest = self.base_y, 0.0, self.REST_TIME


class Cogbot(Spikeback):
    """A rolling gear robot: its teeth hurt, so punch it (Level 3, factory)."""

    kind = "cogbot"
    SPEED = 80.0
    draw_function = staticmethod(worlds.draw_cogbot)


class Drone(Buzzer):
    """A hovering robot that patrols the space station (Level 3)."""

    kind = "drone"
    SPEED = 110.0
    BOB_HEIGHT = 30
    draw_function = staticmethod(worlds.draw_drone)

    def update(self, dt, level):
        super().update(dt, level)
        if self.is_active:
            self.y += math.sin(self.time * 1.3) * 0.5


STORY_ENEMIES = {cls.kind: cls for cls in (Hackling, Slider, Ember, Cogbot, Drone)}


def register():
    """Add the new enemies to ``entities.ENEMY_KINDS``."""
    ENEMY_KINDS.update(STORY_ENEMIES)
