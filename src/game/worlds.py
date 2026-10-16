"""The look of the worlds of the Prologue and Levels 2 and 3.

Every level has its own worlds so that the game never repeats itself:

* Prologue: the old ``campus``, the dusty ``archive`` and the File Drawer's hall.
* Level 2: the slippery ``ice`` peaks, the neon ``city`` and the ``volcano``.
* Level 3: the clockwork ``factory`` and the low-gravity ``space`` station.

Each boss fights in its own hall (``boss_*``), which also has its own music.
This module registers the colours of the new worlds with ``graphics``, draws
their animated backdrops and the special tiles, and draws the characters and
enemies that only appear in these levels. Like the rest of the game, all
graphics are drawn from shapes in code.
"""

import math
import random

import pygame

from . import graphics, ui
from .config import SCREEN_HEIGHT, SCREEN_WIDTH, TILE_SIZE

OUTLINE = graphics.OUTLINE
# Worlds that look alike share a palette: (soil, specks, surface, highlight).
GROUND = {
    "campus": ((150, 140, 130), (120, 112, 104), (200, 180, 140), (232, 216, 172)),
    "archive": ((96, 64, 48), (72, 46, 34), (150, 100, 60), (190, 140, 90)),
    "ice": ((150, 190, 230), (120, 165, 215), (240, 250, 255), (190, 230, 255)),
    "city": ((60, 60, 76), (44, 44, 58), (90, 90, 110), (255, 80, 200)),
    "volcano": ((60, 40, 40), (200, 80, 40), (90, 60, 56), (255, 140, 60)),
    "factory": ((110, 116, 128), (80, 86, 96), (150, 156, 170), (255, 200, 60)),
    "space": ((70, 76, 110), (50, 56, 86), (120, 130, 170), (120, 230, 255)),
}
BOSS_HALLS = {"boss_drawer": "archive", "boss_impulse": "volcano", "boss_rules": "space"}
STORY_THEMES = tuple(GROUND) + tuple(BOSS_HALLS)
# Worlds with their own physics: slippery ice and low gravity.
SLIPPERY_THEMES = ("ice",)
LOW_GRAVITY_THEMES = ("space", "boss_rules")


def base_theme(theme):
    """Return the world whose look a boss hall borrows (or the theme itself)."""
    return BOSS_HALLS.get(theme, theme)


def register():
    """Add the new worlds, characters and platforms to the tables of ``graphics``."""
    graphics.NPC_DRAWERS.update(NPC_DRAWERS)
    graphics.CRUMBLE_DRAWERS.update(CRUMBLES)
    for theme in STORY_THEMES:
        soil, speck, top, highlight = GROUND[base_theme(theme)]
        graphics.GROUND_THEMES.setdefault(theme, (soil, speck, top, highlight))
        # A plain backdrop as a fallback; StoryBackdrop draws the real one.
        graphics.BACKDROP_THEMES.setdefault(theme, {"sky": (top, soil), "ridges": (speck, soil), "sun": None, "clouds": None})


# ---------------------------------------------------------------------------
# Backdrops
# ---------------------------------------------------------------------------

SKIES = {
    "campus": ((120, 180, 240), (220, 236, 250)),
    "archive": ((58, 36, 30), (90, 60, 46)),
    "ice": ((140, 190, 240), (230, 244, 255)),
    "city": ((24, 14, 56), (90, 40, 110)),
    "volcano": ((40, 10, 16), (150, 50, 30)),
    "factory": ((40, 44, 52), (86, 90, 100)),
    "space": ((4, 4, 16), (20, 16, 50)),
}


class StoryBackdrop:
    """
    An animated backdrop for one of the new worlds.

    Parameters
    ----------
    theme : str
        One of ``STORY_THEMES``.
    seed : int, optional
        Seed for the scenery.
    """

    LAYER_WIDTH = 2048

    def __init__(self, theme, seed=11):
        self.theme = base_theme(theme)
        self.boss_hall = theme in BOSS_HALLS
        self.rng = random.Random(seed)
        self.sky = graphics.vertical_gradient((SCREEN_WIDTH, SCREEN_HEIGHT), *SKIES[self.theme])
        self.layers = []
        self.particles = [(self.rng.uniform(0, SCREEN_WIDTH), self.rng.uniform(0, SCREEN_HEIGHT), self.rng.uniform(0.5, 1.5)) for _ in range(60)]
        getattr(self, f"_build_{self.theme}")()

    def _layer(self):
        return pygame.Surface((self.LAYER_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    def _build_campus(self):
        far, near = self._layer(), self._layer()
        for x in range(0, self.LAYER_WIDTH, 260):
            # Old university halls with towers and arched windows.
            hall = pygame.Rect(x + 20, 300, 200, 200)
            pygame.draw.rect(far, (176, 160, 196), hall)
            pygame.draw.polygon(far, (150, 132, 172), [(hall.left - 10, hall.top), (hall.centerx, hall.top - 70), (hall.right + 10, hall.top)])
            tower = pygame.Rect(hall.centerx - 22, hall.top - 150, 44, 110)
            pygame.draw.rect(far, (160, 144, 182), tower)
            pygame.draw.polygon(far, (130, 112, 156), [(tower.left - 6, tower.top), (tower.centerx, tower.top - 50), (tower.right + 6, tower.top)])
            pygame.draw.circle(far, (240, 236, 220), (tower.centerx, tower.top + 30), 12)
            for wx in range(hall.left + 20, hall.right - 20, 40):
                pygame.draw.rect(far, (110, 96, 140), (wx, hall.top + 40, 20, 40), border_top_left_radius=10, border_top_right_radius=10)
        for x in range(0, self.LAYER_WIDTH, 120):
            pygame.draw.circle(near, (90, 160, 90), (x + 60, 520), 50)
            pygame.draw.rect(near, (110, 80, 60), (x + 54, 540, 12, 60))
        pygame.draw.rect(near, (120, 180, 100), (0, 560, self.LAYER_WIDTH, SCREEN_HEIGHT))
        self.layers = [(far, 0.15), (near, 0.35)]

    def _build_archive(self):
        far, near = self._layer(), self._layer()
        colors = ((150, 50, 50), (60, 90, 150), (60, 120, 70), (190, 150, 60), (110, 70, 130))
        for x in range(0, self.LAYER_WIDTH, 220):
            shelf = pygame.Rect(x + 10, 120, 200, 460)
            pygame.draw.rect(far, (70, 44, 32), shelf)
            for board_y in range(shelf.top + 90, shelf.bottom, 90):
                pygame.draw.rect(far, (110, 74, 50), (shelf.left, board_y, shelf.width, 10))
                bx = shelf.left + 8
                while bx < shelf.right - 16:
                    width = self.rng.randint(10, 18)
                    height = self.rng.randint(50, 78)
                    pygame.draw.rect(far, self.rng.choice(colors), (bx, board_y - height, width, height))
                    bx += width + 2
        for x in range(0, self.LAYER_WIDTH, 512):
            pygame.draw.rect(near, (50, 30, 24), (x + 40, 0, 50, SCREEN_HEIGHT))
            pygame.draw.rect(near, (50, 30, 24), (x, 0, 512, 30))
        self.layers = [(far, 0.2), (near, 0.4)]

    def _build_ice(self):
        far, near = self._layer(), self._layer()
        for layer, color, base, height, step in ((far, (200, 220, 245), 470, 300, 340), (near, (170, 205, 240), 560, 200, 220)):
            points = [(0, SCREEN_HEIGHT)]
            for x in range(0, self.LAYER_WIDTH + step, step):
                points += [(x, base), (x + step // 2, base - height * self.rng.uniform(0.6, 1.0))]
            points.append((self.LAYER_WIDTH, SCREEN_HEIGHT))
            pygame.draw.polygon(layer, color, points)
            # Snow caps.
            for index in range(2, len(points) - 1, 2):
                peak = points[index]
                pygame.draw.polygon(layer, (255, 255, 255), [peak, (peak[0] - 40, peak[1] + 50), (peak[0] + 40, peak[1] + 50)])
        self.layers = [(far, 0.12), (near, 0.3)]

    def _build_city(self):
        far, near = self._layer(), self._layer()
        neon = ((255, 80, 200), (80, 230, 255), (255, 220, 80), (140, 255, 140))
        for layer, base, low, high, color in ((far, 560, 200, 380, (50, 30, 90)), (near, 600, 120, 260, (34, 22, 64))):
            x = 0
            while x < self.LAYER_WIDTH:
                width = self.rng.randint(70, 140)
                height = self.rng.randint(low, high)
                building = pygame.Rect(x, base - height, width, height + 200)
                pygame.draw.rect(layer, color, building)
                for wy in range(building.top + 14, base - 10, 22):
                    for wx in range(building.left + 8, building.right - 12, 18):
                        if self.rng.random() < 0.55:
                            pygame.draw.rect(layer, (255, 230, 150) if layer is far else (255, 200, 120), (wx, wy, 8, 10))
                if layer is near and self.rng.random() < 0.6:
                    sign = pygame.Rect(building.left + 10, building.top + 20, width - 20, 26)
                    pygame.draw.rect(layer, self.rng.choice(neon), sign, 3, border_radius=8)
                x += width + self.rng.randint(4, 20)
        self.layers = [(far, 0.12), (near, 0.3)]

    def _build_volcano(self):
        far, near = self._layer(), self._layer()
        for x in range(0, self.LAYER_WIDTH, 1024):
            cone = [(x + 120, 600), (x + 420, 230), (x + 520, 230), (x + 820, 600)]
            pygame.draw.polygon(far, (36, 14, 20), cone)
            pygame.draw.ellipse(far, (255, 120, 40, 90), (x + 390, 170, 160, 90))
            pygame.draw.ellipse(far, (255, 150, 50), (x + 420, 222, 100, 20))
        points = [(0, SCREEN_HEIGHT)] + [(x, 540 - 60 * abs(math.sin(x * 0.006))) for x in range(0, self.LAYER_WIDTH + 1, 16)] + [(self.LAYER_WIDTH, SCREEN_HEIGHT)]
        pygame.draw.polygon(near, (40, 20, 22), points)
        self.layers = [(far, 0.12), (near, 0.3)]

    def _build_factory(self):
        far, near = self._layer(), self._layer()
        for x in range(0, self.LAYER_WIDTH, 256):
            pygame.draw.rect(far, (66, 70, 80), (x, 0, 30, SCREEN_HEIGHT))
            pygame.draw.rect(far, (76, 80, 92), (x, 200, 256, 22))
            pygame.draw.rect(far, (76, 80, 92), (x, 420, 256, 22))
            for rivet_x in range(x + 10, x + 256, 32):
                pygame.draw.circle(far, (100, 104, 118), (rivet_x, 211), 4)
        for x in range(0, self.LAYER_WIDTH, 400):
            pygame.draw.rect(near, (90, 70, 50), (x + 60, 0, 26, SCREEN_HEIGHT))
            pygame.draw.rect(near, (130, 100, 60), (x + 56, 330, 34, 18))
        self.gears = [(x + 160, self.rng.randint(150, 480), self.rng.randint(40, 90)) for x in range(0, self.LAYER_WIDTH, 300)]
        self.layers = [(far, 0.15), (near, 0.35)]

    def _build_space(self):
        far = self._layer()
        for _ in range(220):
            x, y = self.rng.randrange(self.LAYER_WIDTH), self.rng.randrange(SCREEN_HEIGHT)
            pygame.draw.circle(far, (255, 255, 255, self.rng.randint(80, 255)), (x, y), self.rng.choice((1, 1, 2)))
        pygame.draw.circle(far, (70, 120, 220), (500, 220), 90)
        pygame.draw.circle(far, (90, 180, 110), (470, 200), 40)
        pygame.draw.circle(far, (90, 180, 110), (540, 260), 30)
        pygame.draw.circle(far, (220, 180, 140), (1500, 160), 50)
        pygame.draw.ellipse(far, (240, 210, 170), (1430, 150, 140, 20), 3)
        near = self._layer()
        for x in range(0, self.LAYER_WIDTH, 512):
            pygame.draw.rect(near, (60, 66, 96), (x, 560, 512, 200))
            pygame.draw.rect(near, (90, 96, 130), (x + 100, 500, 140, 70), border_radius=12)
            pygame.draw.circle(near, (120, 230, 255), (x + 170, 535), 14)
        self.layers = [(far, 0.05), (near, 0.3)]

    def draw(self, surface, camera_x, time):
        """Draw the backdrop for the given camera position."""
        surface.blit(self.sky, (0, 0))
        theme = self.theme
        if theme == "campus":
            pygame.draw.circle(surface, (255, 246, 200), (1040, 120), 60)
            for index in range(5):
                graphics.draw_cloud(surface, (index * 330 - camera_x * 0.05 + time * 8) % (SCREEN_WIDTH + 300) - 150, 60 + index * 30 % 120, 1.0)
        elif theme == "space":
            pass
        for layer, speed in self.layers:
            offset = -(camera_x * speed) % self.LAYER_WIDTH
            surface.blit(layer, (offset - self.LAYER_WIDTH, 0))
            surface.blit(layer, (offset, 0))
        if theme == "factory":
            for x, y, radius in self.gears:
                gear_x = (x - camera_x * 0.25) % self.LAYER_WIDTH - 100
                if -150 < gear_x < SCREEN_WIDTH + 150:
                    draw_gear(surface, (gear_x, y), radius, time * (1.2 if radius % 2 else -1.2), (96, 100, 112))
        self._draw_particles(surface, time)
        if self.boss_hall:
            # A boss hall is darker at the edges.
            shade = pygame.Surface((SCREEN_WIDTH, 90), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 70))
            surface.blit(shade, (0, 0))

    def _draw_particles(self, surface, time):
        theme = self.theme
        for x, y, speed in self.particles:
            if theme == "ice":
                px = (x + math.sin(time + y) * 30) % SCREEN_WIDTH
                py = (y + time * 40 * speed) % SCREEN_HEIGHT
                pygame.draw.circle(surface, (255, 255, 255), (px, py), 2 + int(speed))
            elif theme == "volcano":
                px = (x + math.sin(time * 2 + y) * 10) % SCREEN_WIDTH
                py = (y - time * 50 * speed) % SCREEN_HEIGHT
                pygame.draw.circle(surface, (255, 150 + int(speed * 60), 60), (px, py), 2)
            elif theme == "space" and speed > 1.3:
                if math.sin(time * 3 + x) > 0.6:
                    pygame.draw.circle(surface, (255, 255, 220), (x, y), 2)
            elif theme == "archive" and speed > 1.0:
                px = (x + time * 6 * speed) % SCREEN_WIDTH
                py = (y + math.sin(time + x) * 20) % SCREEN_HEIGHT
                pygame.draw.circle(surface, (240, 220, 170), (px, py), 1)


def draw_gear(surface, center, radius, angle, color):
    """Draw a cog wheel."""
    x, y = center
    for tooth in range(10):
        a = angle + tooth * math.pi / 5
        pygame.draw.circle(surface, color, (x + math.cos(a) * radius, y + math.sin(a) * radius), max(3, radius // 5))
    pygame.draw.circle(surface, color, (x, y), radius)
    pygame.draw.circle(surface, tuple(max(0, c - 30) for c in color), (x, y), radius // 3)


# ---------------------------------------------------------------------------
# Special tiles
# ---------------------------------------------------------------------------

BLOCK_COLORS = {"red": (230, 70, 80), "blue": (70, 130, 240)}


def _stone(tile, size):
    tile.fill((214, 196, 156))
    pygame.draw.line(tile, (176, 158, 120), (0, size // 2), (size, size // 2), 3)
    pygame.draw.line(tile, (176, 158, 120), (size // 2, 0), (size // 2, size // 2), 3)
    pygame.draw.line(tile, (176, 158, 120), (size // 4, size // 2), (size // 4, size), 3)
    pygame.draw.rect(tile, (140, 124, 92), tile.get_rect(), 2)


def _shelf(tile, size):
    tile.fill((80, 50, 34))
    for index, x in enumerate(range(4, size - 4, 8)):
        color = ((170, 60, 60), (60, 100, 160), (70, 130, 80), (200, 160, 70))[index % 4]
        pygame.draw.rect(tile, color, (x, 6 + (index % 2) * 4, 7, size - 16))
    pygame.draw.rect(tile, (130, 90, 56), (0, size - 8, size, 8))
    pygame.draw.rect(tile, (50, 30, 20), tile.get_rect(), 2)


def _ice(tile, size):
    tile.fill((180, 226, 250))
    pygame.draw.polygon(tile, (230, 248, 255), [(4, 4), (size - 12, 4), (6, size - 14)])
    pygame.draw.rect(tile, (110, 170, 220), tile.get_rect(), 3, border_radius=6)


def _neon(tile, size):
    tile.fill((40, 34, 70))
    pygame.draw.line(tile, (255, 80, 200), (0, 4), (size, 4), 4)
    for x in range(0, size, 16):
        pygame.draw.line(tile, (90, 80, 140), (x, 8), (x + 16, size), 3)
    pygame.draw.rect(tile, (80, 230, 255), tile.get_rect(), 2)


def _basalt(tile, size):
    tile.fill((60, 40, 40))
    pygame.draw.lines(tile, (255, 120, 40), False, [(6, 0), (14, 16), (10, 30), (20, size)], 3)
    pygame.draw.lines(tile, (255, 120, 40), False, [(size - 4, 6), (size - 16, 22), (size - 8, size - 6)], 2)
    pygame.draw.rect(tile, (30, 20, 22), tile.get_rect(), 2)


def _metal(tile, size):
    tile.fill((150, 156, 170))
    pygame.draw.rect(tile, (110, 116, 128), tile.get_rect().inflate(-10, -10), 2)
    for corner in ((6, 6), (size - 7, 6), (6, size - 7), (size - 7, size - 7)):
        pygame.draw.circle(tile, (90, 94, 106), corner, 3)
    pygame.draw.rect(tile, (255, 200, 60), (0, 0, size, 5))
    pygame.draw.rect(tile, (70, 74, 86), tile.get_rect(), 2)


def _hull(tile, size):
    tile.fill((96, 104, 150))
    pygame.draw.rect(tile, (70, 76, 116), (4, 4, size - 8, size - 8), 2, border_radius=6)
    pygame.draw.circle(tile, (120, 230, 255), (size // 2, size // 2), 5)
    pygame.draw.rect(tile, (50, 56, 90), tile.get_rect(), 2)


# Platform tiles by world: stone, book shelves, ice, neon girders, basalt,
# metal plates and hull panels.
PLATFORM_STYLES = {
    "campus": _stone,
    "archive": _shelf,
    "ice": _ice,
    "city": _neon,
    "volcano": _basalt,
    "factory": _metal,
    "space": _hull,
}


def add_tile_images(images):
    """Add the tiles of the new levels to a dict from ``graphics.make_tile_images``."""
    size = TILE_SIZE
    gate = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(gate, (60, 60, 76), (0, 0, size, size))
    for x in range(4, size, 12):
        pygame.draw.rect(gate, (150, 154, 176), (x, 0, 6, size))
    pygame.draw.rect(gate, (110, 114, 136), (0, size // 2 - 4, size, 8))
    images["gate"] = gate

    answer = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(answer, (150, 110, 230), answer.get_rect(), border_radius=8)
    pygame.draw.rect(answer, OUTLINE, answer.get_rect(), 3, border_radius=8)
    text = ui.get_font(40, bold=True).render("!", True, (255, 255, 255))
    answer.blit(text, text.get_rect(center=(size // 2, size // 2 + 2)))
    images["answer"] = answer

    conveyor = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(conveyor, (50, 52, 60), (0, 0, size, size))
    pygame.draw.rect(conveyor, (30, 30, 36), (0, 0, size, 14))
    pygame.draw.circle(conveyor, (120, 124, 136), (size // 2, 30), 10)
    images["conveyor"] = conveyor

    for color, rgb in BLOCK_COLORS.items():
        block = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(block, rgb, block.get_rect(), border_radius=6)
        pygame.draw.rect(block, OUTLINE, block.get_rect(), 3, border_radius=6)
        pygame.draw.line(block, (255, 255, 255), (8, 8), (size - 16, 8), 3)
        images[f"{color}_block"] = block
        switch = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(switch, (240, 240, 250), switch.get_rect(), border_radius=8)
        pygame.draw.rect(switch, rgb, switch.get_rect().inflate(-10, -10), border_radius=6)
        pygame.draw.rect(switch, OUTLINE, switch.get_rect(), 3, border_radius=8)
        label = ui.get_font(22, bold=True).render("SWITCH", True, (255, 255, 255))
        switch.blit(pygame.transform.smoothscale(label, (size - 14, 16)), (7, size // 2 - 8))
        images[f"switch_{color}"] = switch

    for theme, draw in PLATFORM_STYLES.items():
        tile = pygame.Surface((size, size), pygame.SRCALPHA)
        draw(tile, size)
        images[f"plat_{theme}"] = tile

    card = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(card, (250, 246, 230), card.get_rect(), border_radius=6)
    pygame.draw.rect(card, OUTLINE, card.get_rect(), 3, border_radius=6)
    images["card"] = card
    return images


def draw_block_outline(surface, rect, color):
    """Draw a switched-off colour block as a dashed outline."""
    rgb = BLOCK_COLORS[color]
    for index in range(0, rect.width, 12):
        pygame.draw.line(surface, rgb, (rect.left + index, rect.top), (rect.left + index + 6, rect.top), 3)
        pygame.draw.line(surface, rgb, (rect.left + index, rect.bottom - 2), (rect.left + index + 6, rect.bottom - 2), 3)
        pygame.draw.line(surface, rgb, (rect.left, rect.top + index), (rect.left, rect.top + index + 6), 3)
        pygame.draw.line(surface, rgb, (rect.right - 2, rect.top + index), (rect.right - 2, rect.top + index + 6), 3)


def draw_conveyor_arrows(surface, rect, direction, time):
    """Draw moving arrows on a conveyor belt tile."""
    shift = (time * 60 * direction) % 24
    for x in range(-24, rect.width + 24, 24):
        ax = rect.left + x + shift
        if rect.left <= ax <= rect.right - 10:
            tip = ax + 8 * direction
            pygame.draw.polygon(surface, (255, 200, 60), [(ax, rect.top + 3), (tip, rect.top + 7), (ax, rect.top + 11)])


def draw_lava(surface, rect, time):
    """Fill ``rect`` with glowing lava and bubbles."""
    pygame.draw.rect(surface, (230, 80, 30), rect)
    for x in range(rect.left, rect.right, 24):
        wave_y = rect.top + math.sin(time * 3 + x * 0.05) * 4
        pygame.draw.arc(surface, (255, 200, 80), (x, wave_y - 6, 24, 12), 0, math.pi, 4)
        if math.sin(time * 2 + x) > 0.9:
            pygame.draw.circle(surface, (255, 220, 120), (x + 12, rect.top + 20), 5)


def draw_book_crumble(surface, rect, shaking=False):
    """A crumbling platform in the archive: a wobbly stack of 'shaky findings'."""
    colors = ((180, 60, 60), (70, 110, 170), (200, 160, 70))
    for index, x in enumerate(range(rect.left, rect.right - 4, 24)):
        book = pygame.Rect(x + 1, rect.top + (index % 2) * 2, 22, rect.height - 2)
        pygame.draw.rect(surface, colors[index % 3], book, border_radius=3)
        pygame.draw.rect(surface, OUTLINE, book, 2, border_radius=3)
        pygame.draw.line(surface, (250, 240, 210), (book.left + 4, book.centery), (book.right - 4, book.centery), 2)
    if shaking:
        ui.draw_text(surface, "?", (rect.centerx, rect.top - 18), 28, (255, 220, 120), "center", bold=True)


def draw_ice_crumble(surface, rect, shaking=False):
    """A crumbling platform on the ice peaks: a cracking ice floe."""
    pygame.draw.rect(surface, (200, 236, 255), rect, border_radius=8)
    pygame.draw.rect(surface, (120, 180, 230), rect, 3, border_radius=8)
    if shaking:
        pygame.draw.lines(surface, (90, 140, 200), False, [(rect.left + 12, rect.top + 3), (rect.centerx, rect.bottom - 3), (rect.right - 12, rect.top + 4)], 2)


def draw_metal_crumble(surface, rect, shaking=False):
    """A crumbling platform in the factory and in space: a loose metal grate."""
    pygame.draw.rect(surface, (130, 136, 150), rect, border_radius=4)
    for x in range(rect.left + 6, rect.right - 4, 10):
        pygame.draw.line(surface, (80, 84, 96), (x, rect.top + 3), (x, rect.bottom - 3), 2)
    pygame.draw.rect(surface, (255, 200, 60) if shaking else (60, 64, 76), rect, 3, border_radius=4)


CRUMBLES = {
    "archive": draw_book_crumble,
    "boss_drawer": draw_book_crumble,
    "ice": draw_ice_crumble,
    "factory": draw_metal_crumble,
    "space": draw_metal_crumble,
    "boss_rules": draw_metal_crumble,
    "city": draw_metal_crumble,
    "volcano": draw_metal_crumble,
    "boss_impulse": draw_metal_crumble,
}


# ---------------------------------------------------------------------------
# Characters
# ---------------------------------------------------------------------------


def draw_professor_shell(surface, x, ground_y, time):
    """Draw Professor Shell, the old tortoise of slow and careful science."""
    bob = math.sin(time * 2) * 2
    shell = pygame.Rect(0, 0, 90, 64)
    shell.midbottom = (x - 6, ground_y - 10)
    pygame.draw.ellipse(surface, (110, 150, 80), shell)
    pygame.draw.ellipse(surface, (70, 100, 50), shell, 3)
    for dx, dy in ((-20, 18), (0, 12), (20, 18), (-10, 34), (10, 34)):
        pygame.draw.circle(surface, (150, 190, 100), (shell.centerx + dx, shell.top + dy), 9, 3)
    for foot_x in (x - 36, x + 16):
        pygame.draw.ellipse(surface, (170, 200, 130), (foot_x, ground_y - 16, 22, 16))
    head = (x + 44, ground_y - 50 + bob)
    pygame.draw.line(surface, (170, 200, 130), (x + 26, ground_y - 30), head, 16)
    pygame.draw.circle(surface, (170, 200, 130), head, 18)
    for eye_x in (head[0] - 2, head[0] + 10):
        pygame.draw.circle(surface, OUTLINE, (eye_x, head[1] - 4), 7, 2)
        pygame.draw.circle(surface, OUTLINE, (eye_x, head[1] - 4), 2)
    pygame.draw.arc(surface, OUTLINE, (head[0] - 4, head[1] + 2, 16, 8), math.pi, 2 * math.pi, 2)
    # A graduation cap.
    pygame.draw.polygon(surface, (40, 40, 60), [(head[0] - 20, head[1] - 18), (head[0] + 4, head[1] - 28), (head[0] + 28, head[1] - 18), (head[0] + 4, head[1] - 10)])
    pygame.draw.line(surface, ui.GOLD, (head[0] + 4, head[1] - 19), (head[0] + 22, head[1] - 6), 2)


def draw_signal_sam(surface, x, ground_y, time):
    """Draw Signal Sam, the friendly traffic-light robot of Neon City."""
    pygame.draw.rect(surface, (80, 84, 100), (x - 6, ground_y - 60, 12, 60))
    body = pygame.Rect(0, 0, 54, 120)
    body.midbottom = (x, ground_y - 50)
    pygame.draw.rect(surface, (40, 44, 56), body, border_radius=14)
    pygame.draw.rect(surface, (255, 220, 80), body, 3, border_radius=14)
    lit = int(time / 1.2) % 3
    for index, color in enumerate(((240, 60, 60), (255, 200, 60), (70, 220, 100))):
        center = (body.centerx, body.top + 22 + index * 38)
        pygame.draw.circle(surface, color if index == lit else tuple(c // 4 for c in color), center, 15)
    for side in (-1, 1):
        arm = (x + side * 27, body.centery)
        pygame.draw.line(surface, (80, 84, 100), arm, (arm[0] + side * 16, arm[1] - 20 + math.sin(time * 3) * 6), 5)
    pygame.draw.arc(surface, ui.WHITE, (body.centerx - 12, body.bottom - 18, 24, 12), math.pi, 2 * math.pi, 2)


def draw_memory_machine(surface, x, ground_y, time):
    """Draw the Memory Machine, a robot with a letter screen for a head."""
    for side in (-1, 1):
        pygame.draw.rect(surface, (90, 96, 110), (x + side * 18 - 7, ground_y - 40, 14, 40))
    body = pygame.Rect(0, 0, 80, 60)
    body.midbottom = (x, ground_y - 36)
    pygame.draw.rect(surface, (150, 156, 170), body, border_radius=10)
    pygame.draw.rect(surface, OUTLINE, body, 3, border_radius=10)
    draw_gear(surface, body.center, 14, time * 2, (110, 116, 130))
    screen = pygame.Rect(0, 0, 100, 70)
    screen.midbottom = (x, body.top - 4)
    letters = "KBKDBD"
    pygame.draw.rect(surface, (90, 96, 110), screen.inflate(12, 12), border_radius=10)
    pygame.draw.rect(surface, (20, 40, 30), screen, border_radius=8)
    ui.draw_text(surface, letters[int(time * 1.5) % len(letters)], screen.center, 56, (120, 255, 160), "center", bold=True)
    pygame.draw.line(surface, (90, 96, 110), (x, screen.top - 6), (x, screen.top - 22), 3)
    pygame.draw.circle(surface, (255, 80, 80) if int(time * 2) % 2 else (120, 30, 30), (x, screen.top - 24), 6)


def draw_tower_gate(surface, x, ground_y, time):
    """Draw the Tower of London puzzle stand next to the factory gate."""
    stand = pygame.Rect(0, 0, 130, 20)
    stand.midbottom = (x, ground_y)
    pygame.draw.rect(surface, graphics.WOOD, stand, border_radius=6)
    pygame.draw.rect(surface, graphics.WOOD_DARK, stand, 3, border_radius=6)
    for peg, (height, balls) in enumerate(((66, ("red", "green")), (46, ("blue",)), (26, ()))):
        peg_x = x - 42 + peg * 42
        pygame.draw.rect(surface, graphics.WOOD_DARK, (peg_x - 3, stand.top - height, 6, height))
        for index, ball in enumerate(balls):
            color = {"red": (230, 70, 80), "green": (90, 200, 110), "blue": (80, 140, 240)}[ball]
            pygame.draw.circle(surface, color, (peg_x, stand.top - 10 - index * 20), 10)
    ui.draw_text(surface, "?", (x, stand.top - 100 + math.sin(time * 3) * 4), 40, ui.GOLD, "center", bold=True)


NPC_DRAWERS = {
    "professor_shell": draw_professor_shell,
    "signal_sam": draw_signal_sam,
    "memory_machine": draw_memory_machine,
    "tower_gate": draw_tower_gate,
    "quiz_owl": graphics.draw_owl,
}


# ---------------------------------------------------------------------------
# Enemies of the new levels
# ---------------------------------------------------------------------------


def draw_hackling(surface, x, y, time):
    """A Hackling: one of Count Hackula's bats, with a 'p' on its belly (40 x 30)."""
    flap = math.sin(time * 18) * 10
    body = (x + 20, y + 15)
    for side in (-1, 1):
        wing = [(body[0] + side * 8, body[1] - 4), (body[0] + side * 30, body[1] - 12 + flap), (body[0] + side * 22, body[1] + 6), (body[0] + side * 12, body[1] + 2)]
        pygame.draw.polygon(surface, (90, 50, 110), wing)
    pygame.draw.circle(surface, (120, 70, 150), body, 14)
    for side in (-1, 1):
        pygame.draw.polygon(surface, (120, 70, 150), [(body[0] + side * 4, body[1] - 10), (body[0] + side * 10, body[1] - 22), (body[0] + side * 12, body[1] - 8)])
        pygame.draw.circle(surface, (255, 230, 90), (body[0] + side * 5, body[1] - 3), 3)
    ui.draw_text(surface, "p", (body[0], body[1] + 6), 18, (255, 230, 90), "center", bold=True)


def draw_slider(surface, x, y, time):
    """A Slider: a penguin that cannot stop sliding (40 x 34)."""
    pygame.draw.ellipse(surface, (40, 44, 60), (x, y + 2, 40, 32))
    pygame.draw.ellipse(surface, (250, 250, 255), (x + 8, y + 10, 24, 22))
    for eye_x in (x + 14, x + 26):
        pygame.draw.circle(surface, (255, 255, 255), (eye_x, y + 10), 4)
        pygame.draw.circle(surface, OUTLINE, (eye_x, y + 11), 2)
    pygame.draw.polygon(surface, (255, 170, 50), [(x + 16, y + 15), (x + 24, y + 15), (x + 20, y + 21)])
    pygame.draw.line(surface, (200, 230, 255), (x - 8, y + 30), (x - 20, y + 30), 3)


def draw_ember(surface, x, y, time):
    """An Ember: a hot-headed lava blob that leaps out of the lava (36 x 36)."""
    flicker = int(math.sin(time * 20) * 3)
    pygame.draw.circle(surface, (240, 90, 30), (x + 18, y + 20), 18 + flicker // 2)
    pygame.draw.polygon(surface, (255, 160, 50), [(x + 6, y + 14), (x + 12, y - 6 + flicker), (x + 18, y + 8), (x + 24, y - 8 - flicker), (x + 30, y + 14)])
    pygame.draw.circle(surface, (255, 220, 120), (x + 18, y + 22), 10)
    for eye_x in (x + 13, x + 23):
        pygame.draw.line(surface, OUTLINE, (eye_x - 3, y + 16), (eye_x + 3, y + 19), 3)


def draw_cogbot(surface, x, y, time):
    """A Cogbot: a rolling gear robot of the factory (42 x 34)."""
    draw_gear(surface, (x + 21, y + 20), 14, time * 6, (150, 156, 170))
    pygame.draw.circle(surface, (90, 96, 110), (x + 21, y + 20), 10)
    pygame.draw.circle(surface, (255, 80, 80), (x + 21, y + 20), 4)


def draw_drone(surface, x, y, time):
    """A Drone: a hovering robot of the space station (40 x 30)."""
    pygame.draw.ellipse(surface, (180, 190, 220), (x, y + 8, 40, 18))
    pygame.draw.ellipse(surface, OUTLINE, (x, y + 8, 40, 18), 2)
    pygame.draw.circle(surface, (120, 230, 255), (x + 20, y + 10), 9)
    pygame.draw.circle(surface, (255, 255, 255), (x + 17, y + 7), 3)
    for side in (x + 4, x + 36):
        pygame.draw.line(surface, (120, 230, 255, 120), (side, y + 26), (side, y + 32 + math.sin(time * 20) * 3), 3)


def draw_card(surface, rect, card, scale=1.0):
    """
    Draw a sorting card: 1 to 3 shapes of one colour.

    Parameters
    ----------
    rect : pygame.Rect
        Area of the card.
    card : tuple
        ``(number, colour, shape)`` with colour "red", "green" or "blue" and
        shape "circle", "triangle" or "star".
    """
    number, color, shape = card
    rgb = {"red": (230, 70, 80), "green": (70, 190, 100), "blue": (70, 130, 240)}[color]
    pygame.draw.rect(surface, (250, 246, 230), rect, border_radius=int(8 * scale))
    pygame.draw.rect(surface, OUTLINE, rect, max(2, int(3 * scale)), border_radius=int(8 * scale))
    size = rect.height * 0.18
    for index in range(number):
        cx = rect.centerx + (index - (number - 1) / 2) * rect.width * 0.3
        cy = rect.centery
        if shape == "circle":
            pygame.draw.circle(surface, rgb, (cx, cy), size)
        elif shape == "triangle":
            pygame.draw.polygon(surface, rgb, [(cx, cy - size), (cx - size, cy + size * 0.8), (cx + size, cy + size * 0.8)])
        else:
            points = []
            for corner in range(10):
                length = size * 1.15 if corner % 2 == 0 else size * 0.5
                angle = math.pi / 5 * corner - math.pi / 2
                points.append((cx + math.cos(angle) * length, cy + math.sin(angle) * length))
            pygame.draw.polygon(surface, rgb, points)
