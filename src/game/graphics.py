"""Procedural graphics: everything on screen is drawn from shapes in code.

No image files are needed, so the game runs right after cloning. Functions
take a target surface and pixel coordinates; ``time`` arguments are seconds
and drive small animations.
"""

import math
import random

import pygame

from .config import SCREEN_HEIGHT, SCREEN_WIDTH, TILE_SIZE
from .ui import get_font

SKY_TOP = (86, 156, 232)
SKY_BOTTOM = (206, 236, 255)
POND_TOP = (40, 130, 190)
POND_BOTTOM = (12, 52, 110)
DIRT = (134, 94, 64)
DIRT_DARK = (108, 74, 50)
GRASS = (98, 192, 86)
GRASS_LIGHT = (150, 226, 110)
BRICK = (190, 108, 76)
BRICK_DARK = (140, 74, 52)
BLOCK_GOLD = (246, 192, 62)
BLOCK_USED = (150, 132, 116)
WOOD = (166, 116, 66)
WOOD_DARK = (116, 78, 44)
FISH_YELLOW = (252, 204, 56)
FOX_ORANGE = (240, 140, 52)
OUTLINE = (40, 32, 48)


def vertical_gradient(size, top_color, bottom_color):
    """Return a surface filled with a top-to-bottom colour gradient."""
    width, height = size
    surface = pygame.Surface(size)
    for y in range(height):
        share = y / max(1, height - 1)
        color = [round(a + (b - a) * share) for a, b in zip(top_color, bottom_color)]
        pygame.draw.line(surface, color, (0, y), (width, y))
    return surface


# Look of the backdrop per theme: sky colours (top, bottom), colours of the
# far and the near ridge, sun (colour, centre, radius or None), cloud colour.
BACKDROP_THEMES = {
    "meadow": {
        "sky": (SKY_TOP, SKY_BOTTOM),
        "ridges": ((150, 180, 226), (120, 196, 150)),
        "sun": ((255, 244, 190), (1040, 130), 64),
        "clouds": (255, 255, 255),
    },
    "cave": {
        "sky": ((16, 14, 34), (40, 32, 66)),
        "ridges": ((34, 30, 62), (48, 40, 80)),
        "sun": None,
        "clouds": None,
    },
    "sunset": {
        "sky": ((240, 120, 96), (255, 216, 150)),
        "ridges": ((176, 104, 130), (128, 96, 124)),
        "sun": ((255, 226, 150), (900, 330), 90),
        "clouds": (255, 214, 196),
    },
}


class Backdrop:
    """
    Sky, sun, clouds and two ridge layers that scroll slower than the level.

    Parameters
    ----------
    theme : str, optional
        "meadow", "cave" or "sunset" (see ``BACKDROP_THEMES``).
    seed : int, optional
        Seed for the shape of the ridges and the cloud positions.
    """

    LAYER_WIDTH = 2048

    def __init__(self, theme="meadow", seed=7):
        look = BACKDROP_THEMES[theme]
        rng = random.Random(seed)
        self.sun = look["sun"]
        self.cloud_color = look["clouds"]
        self.sky = vertical_gradient((SCREEN_WIDTH, SCREEN_HEIGHT), *look["sky"])
        far, near = look["ridges"]
        self.layers = [
            (self._ridge(rng, far, base=430, height=120), 0.15),
            (self._ridge(rng, near, base=540, height=70), 0.35),
        ]
        if theme == "cave":
            self._add_crystals(rng, self.layers[1][0])
        self.clouds = [
            (rng.uniform(0, self.LAYER_WIDTH), rng.uniform(40, 260), rng.uniform(0.7, 1.4))
            for _ in range(9)
        ]

    def _ridge(self, rng, color, base, height):
        """Draw a seamless, wavy ridge line as one scrolling layer."""
        layer = pygame.Surface((self.LAYER_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        # Whole numbers of sine waves fit the layer, so its two ends match up.
        waves = [(rng.randint(2, 4), rng.uniform(0, 6.28), 0.6), (rng.randint(6, 9), rng.uniform(0, 6.28), 0.4)]
        points = [(0, SCREEN_HEIGHT)]
        for x in range(0, self.LAYER_WIDTH + 1, 8):
            angle = 2 * math.pi * x / self.LAYER_WIDTH
            wave = sum(weight * math.sin(count * angle + shift) for count, shift, weight in waves)
            points.append((x, base - height * 0.5 * (wave + 1)))
        points.append((self.LAYER_WIDTH, SCREEN_HEIGHT))
        pygame.draw.polygon(layer, color, points)
        return layer

    def _add_crystals(self, rng, layer):
        """Scatter glowing crystals over a cave layer."""
        for _ in range(26):
            x, y, size = rng.randrange(40, self.LAYER_WIDTH - 40), rng.randrange(200, 560), rng.randrange(8, 20)
            color = rng.choice(((120, 220, 255), (190, 140, 255), (140, 255, 200)))
            pygame.draw.polygon(layer, color, [(x, y - size), (x + size // 2, y), (x, y + size), (x - size // 2, y)])

    def draw(self, surface, camera_x, time):
        """Draw the backdrop for the given camera position."""
        surface.blit(self.sky, (0, 0))
        if self.sun:
            color, center, radius = self.sun
            pygame.draw.circle(surface, color, center, radius)
            pygame.draw.circle(surface, tuple(min(255, c + 12) for c in color), center, radius - 14)
        if self.cloud_color:
            for x, y, scale in self.clouds:
                cloud_x = (x - camera_x * 0.08 + time * 10 * scale) % self.LAYER_WIDTH - 200
                draw_cloud(surface, cloud_x, y, scale, self.cloud_color)
        for layer, speed in self.layers:
            offset = -(camera_x * speed) % self.LAYER_WIDTH
            surface.blit(layer, (offset - self.LAYER_WIDTH, 0))
            surface.blit(layer, (offset, 0))


def draw_cloud(surface, x, y, scale=1.0, color=(255, 255, 255)):
    """Draw a puffy cloud with its left edge near ``x``."""
    for dx, dy, radius in ((0, 12, 26), (30, 0, 34), (66, 10, 28), (34, 20, 30)):
        pygame.draw.circle(surface, color, (int(x + dx * scale), int(y + dy * scale)), int(radius * scale))


# Ground colours per theme: soil, dark soil specks, surface, surface highlight.
GROUND_THEMES = {
    "meadow": (DIRT, DIRT_DARK, GRASS, GRASS_LIGHT),
    "cave": ((84, 80, 112), (62, 58, 88), (116, 112, 150), (150, 146, 186)),
    "sunset": ((140, 88, 70), (110, 66, 54), (232, 150, 60), (255, 200, 96)),
}


def make_tile_images():
    """Return a dict that maps tile names to pre-drawn tile surfaces.

    Ground tiles exist per theme as "<theme>_top" and "<theme>_fill".
    """
    size = TILE_SIZE
    rng = random.Random(3)
    images = {}

    for theme, (soil, speck, top, highlight) in GROUND_THEMES.items():
        fill = pygame.Surface((size, size))
        fill.fill(soil)
        for _ in range(9):
            spot = (rng.randrange(4, size - 6), rng.randrange(4, size - 6), rng.randrange(3, 7), 3)
            pygame.draw.ellipse(fill, speck, spot)
        images[f"{theme}_fill"] = fill
        surface_tile = fill.copy()
        pygame.draw.rect(surface_tile, top, (0, 0, size, 14))
        pygame.draw.rect(surface_tile, highlight, (0, 0, size, 4))
        for x in range(0, size, 12):
            pygame.draw.polygon(surface_tile, top, [(x, 13), (x + 6, 21), (x + 12, 13)])
        images[f"{theme}_top"] = surface_tile

    crate = pygame.Surface((size, size))
    crate.fill((196, 150, 92))
    pygame.draw.rect(crate, WOOD_DARK, crate.get_rect(), 4)
    pygame.draw.line(crate, WOOD_DARK, (4, 4), (size - 4, size - 4), 4)
    pygame.draw.line(crate, WOOD_DARK, (size - 4, 4), (4, size - 4), 4)
    pygame.draw.lines(crate, OUTLINE, False, [(14, 6), (20, 16), (15, 24), (22, 34)], 2)  # crack
    images["crate"] = crate

    for pointing in ("up", "down"):
        spikes = pygame.Surface((size, size), pygame.SRCALPHA)
        for x in range(0, size, 16):
            points = [(x, size), (x + 8, 14), (x + 16, size)]
            pygame.draw.polygon(spikes, (214, 218, 232), points)
            pygame.draw.polygon(spikes, (110, 114, 140), points, 2)
        images[f"spikes_{pointing}"] = spikes if pointing == "up" else pygame.transform.flip(spikes, False, True)

    brick = pygame.Surface((size, size))
    brick.fill(BRICK)
    for row in range(3):
        y = row * 16
        pygame.draw.line(brick, BRICK_DARK, (0, y + 15), (size, y + 15), 2)
        for x in range(24 if row % 2 else 0, size + 1, 24):
            pygame.draw.line(brick, BRICK_DARK, (x, y), (x, y + 15), 2)
    pygame.draw.rect(brick, BRICK_DARK, brick.get_rect(), 2)
    images["brick"] = brick

    for name, color, label in (("question", BLOCK_GOLD, "?"), ("used", BLOCK_USED, "")):
        block = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(block, color, block.get_rect(), border_radius=8)
        pygame.draw.rect(block, OUTLINE, block.get_rect(), 3, border_radius=8)
        for corner in ((7, 7), (size - 8, 7), (7, size - 8), (size - 8, size - 8)):
            pygame.draw.circle(block, OUTLINE, corner, 2)
        if label:
            text = get_font(44, bold=True).render(label, True, (255, 252, 230))
            block.blit(text, text.get_rect(center=(size // 2, size // 2 + 2)))
        images[name] = block

    bridge = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(bridge, WOOD, (0, 0, size, 18), border_radius=4)
    pygame.draw.rect(bridge, WOOD_DARK, (0, 0, size, 18), 2, border_radius=4)
    pygame.draw.line(bridge, WOOD_DARK, (size // 2, 2), (size // 2, 16), 2)
    pygame.draw.rect(bridge, WOOD_DARK, (4, 18, 6, size - 18))
    images["bridge"] = bridge

    gate = pygame.Surface((size, size))
    gate.fill((66, 62, 96))
    for x in (8, 24, 40):
        pygame.draw.rect(gate, (226, 184, 80), (x - 3, 0, 6, size))
    pygame.draw.rect(gate, (40, 36, 64), (0, size // 2 - 3, size, 6))
    images["gate"] = gate
    return images


def draw_hero(surface, character, x, y, facing, time, moving, on_ground, boosted=False, punching=False):
    """
    Draw the player character with the top-left of the hitbox at (x, y).

    Parameters
    ----------
    surface : pygame.Surface
        Target surface.
    character : Character
        Looks of the hero (see ``characters.py``).
    x, y : int
        Top-left corner of the 34 x 50 hitbox.
    facing : int
        1 (right) or -1 (left).
    time : float
        Seconds, drives the walking animation.
    moving, on_ground, boosted, punching : bool
        State of the player, selects the pose.
    """
    image = pygame.Surface((64, 60), pygame.SRCALPHA)
    fur, white = character.fur, (255, 250, 240)
    inner = tuple(max(0, channel - 110) for channel in fur)
    if character.tail == "bushy":
        pygame.draw.polygon(image, fur, [(12, 48), (0, 32), (5, 28), (16, 40)])
        pygame.draw.circle(image, white, (3, 31), 4)
    elif character.tail == "thin":
        pygame.draw.lines(image, fur, False, [(13, 46), (5, 44), (2, 34), (6, 26)], 4)
    else:
        pygame.draw.circle(image, white, (10, 44), 6)
    step = int(time * 12) % 2 if moving and on_ground else 0
    leg_y = 50 if on_ground else 47
    for index, leg_x in enumerate((14, 26)):
        lift = 4 if moving and on_ground and index == step else 0
        pygame.draw.rect(image, (92, 52, 34), (leg_x, leg_y - lift, 9, 10), border_radius=3)
    jacket = (250, 214, 70) if boosted else character.jacket
    pygame.draw.rect(image, jacket, (12, 31, 24, 22), border_radius=8)
    pygame.draw.rect(image, character.scarf, (11, 30, 26, 7), border_radius=3)
    if character.ears == "long":
        for ear_x in (16, 28):
            pygame.draw.rect(image, fur, (ear_x, 0, 8, 20), border_radius=4)
            pygame.draw.rect(image, (240, 170, 180), (ear_x + 2, 3, 4, 12), border_radius=2)
    else:
        pygame.draw.polygon(image, fur, [(14, 16), (16, 4), (24, 11)])
        pygame.draw.polygon(image, fur, [(26, 10), (34, 4), (37, 16)])
        pygame.draw.polygon(image, inner, [(17, 13), (17, 7), (21, 11)])
        pygame.draw.polygon(image, inner, [(29, 11), (33, 7), (34, 13)])
    pygame.draw.circle(image, fur, (26, 21), 13)
    pygame.draw.ellipse(image, white, (29, 21, 14, 10))
    pygame.draw.circle(image, OUTLINE, (42, 24), 2)
    pygame.draw.circle(image, (255, 255, 255), (30, 18), 4)
    pygame.draw.circle(image, OUTLINE, (31, 18), 2)
    if punching:
        pygame.draw.line(image, jacket, (32, 40), (52, 38), 7)
        pygame.draw.circle(image, white, (56, 38), 7)
        pygame.draw.circle(image, OUTLINE, (56, 38), 7, 2)
    if facing < 0:
        image = pygame.transform.flip(image, True, False)
        surface.blit(image, (x - 23, y - 10))
    else:
        surface.blit(image, (x - 7, y - 10))


def draw_distractor(surface, x, y, time, squished=False):
    """Draw a Distractor enemy (40 x 34 hitbox) with its top-left at (x, y)."""
    purple, dark = (146, 86, 206), (92, 48, 140)
    if squished:
        pygame.draw.ellipse(surface, purple, (x - 2, y + 22, 44, 12))
        return
    wobble = int(math.sin(time * 10) * 2)
    pygame.draw.ellipse(surface, dark, (x + 4 + wobble, y + 26, 13, 8))
    pygame.draw.ellipse(surface, dark, (x + 23 - wobble, y + 26, 13, 8))
    pygame.draw.ellipse(surface, purple, (x, y + 2, 40, 28))
    pygame.draw.ellipse(surface, dark, (x, y + 2, 40, 28), 2)
    for eye_x in (x + 13, x + 27):
        pygame.draw.circle(surface, (255, 255, 255), (eye_x, y + 15), 5)
        pygame.draw.circle(surface, OUTLINE, (eye_x, y + 16), 2)
    pygame.draw.line(surface, OUTLINE, (x + 7, y + 7), (x + 17, y + 11), 3)
    pygame.draw.line(surface, OUTLINE, (x + 33, y + 7), (x + 23, y + 11), 3)
    pygame.draw.line(surface, dark, (x + 20, y + 3), (x + 20, y - 6), 2)
    pygame.draw.circle(surface, (255, 220, 80), (x + 20, y - 8), 4)


def draw_spark(surface, center_x, center_y, time):
    """Draw a collectible focus spark (a pulsing four-pointed star)."""
    radius = 11 + math.sin(time * 6 + center_x * 0.05) * 2
    points = []
    for index in range(8):
        length = radius if index % 2 == 0 else radius * 0.4
        angle = math.pi / 4 * index
        points.append((center_x + math.cos(angle) * length, center_y + math.sin(angle) * length))
    pygame.draw.polygon(surface, (255, 226, 92), points)
    pygame.draw.polygon(surface, (220, 150, 30), points, 2)


def draw_mushroom(surface, x, y):
    """Draw a Zoom-shroom (36 x 36 hitbox) with its top-left at (x, y)."""
    pygame.draw.rect(surface, (250, 238, 214), (x + 10, y + 18, 16, 18), border_radius=5)
    pygame.draw.ellipse(surface, (60, 150, 240), (x, y, 36, 26))
    pygame.draw.ellipse(surface, (26, 78, 160), (x, y, 36, 26), 2)
    bolt = [(x + 20, y + 3), (x + 12, y + 14), (x + 18, y + 14), (x + 15, y + 23), (x + 25, y + 10), (x + 19, y + 10)]
    pygame.draw.polygon(surface, (255, 236, 110), bolt)


def draw_heart(surface, x, y, size=30, filled=True):
    """Draw a heart whose bounding box starts at (x, y)."""
    color = (236, 64, 86) if filled else (70, 74, 100)
    quarter = size // 4
    pygame.draw.circle(surface, color, (x + quarter, y + quarter), quarter)
    pygame.draw.circle(surface, color, (x + 3 * quarter, y + quarter), quarter)
    pygame.draw.polygon(surface, color, [(x, y + quarter + 2), (x + size, y + quarter + 2), (x + size // 2, y + size)])
    if filled:
        pygame.draw.circle(surface, (255, 190, 200), (x + quarter - 2, y + quarter - 2), max(2, size // 10))


def draw_note(surface, center_x, center_y, time, glow=False):
    """Draw an attention note (a floating scroll) centred on the given point."""
    y = center_y + math.sin(time * 3) * 4
    if glow:
        halo = pygame.Surface((90, 90), pygame.SRCALPHA)
        pygame.draw.circle(halo, (255, 244, 150, 90), (45, 45), 34 + int(math.sin(time * 5) * 6))
        surface.blit(halo, (center_x - 45, y - 45))
    paper = pygame.Rect(0, 0, 30, 36)
    paper.center = (center_x, y)
    pygame.draw.rect(surface, (252, 240, 204), paper, border_radius=5)
    pygame.draw.rect(surface, (150, 110, 60), paper, 2, border_radius=5)
    for line in range(3):
        line_y = paper.top + 10 + line * 8
        pygame.draw.line(surface, (150, 110, 60), (paper.left + 6, line_y), (paper.right - 6, line_y), 2)


def draw_checkpoint(surface, x, ground_y, active, time):
    """Draw a checkpoint flag standing on the ground at pixel column ``x``."""
    pygame.draw.rect(surface, (230, 230, 240), (x - 3, ground_y - 110, 6, 110))
    pygame.draw.circle(surface, (255, 220, 80), (x, ground_y - 112), 7)
    color = (90, 210, 110) if active else (170, 174, 190)
    wave = math.sin(time * 5) * 5 if active else 0
    flag = [(x + 3, ground_y - 106), (x + 50, ground_y - 90 + wave), (x + 3, ground_y - 72)]
    pygame.draw.polygon(surface, color, flag)
    pygame.draw.polygon(surface, OUTLINE, flag, 2)


def draw_sign(surface, x, ground_y):
    """Draw a wooden sign post standing on the ground at pixel column ``x``."""
    pygame.draw.rect(surface, WOOD_DARK, (x - 4, ground_y - 50, 8, 50))
    board = pygame.Rect(x - 30, ground_y - 84, 60, 40)
    pygame.draw.rect(surface, WOOD, board, border_radius=6)
    pygame.draw.rect(surface, WOOD_DARK, board, 3, border_radius=6)
    for line in range(3):
        pygame.draw.line(surface, WOOD_DARK, (board.left + 10, board.top + 10 + line * 9), (board.right - 10, board.top + 10 + line * 9), 2)


def draw_fish(surface, center, direction, length=110, color=FISH_YELLOW):
    """
    Draw a fish that swims left or right, the stimulus of the flanker task.

    Parameters
    ----------
    surface : pygame.Surface
        Target surface.
    center : tuple of float
        Pixel position of the middle of the fish.
    direction : str
        "left" or "right": the side the head points to.
    length : int, optional
        Total length of the fish in pixels.
    color : tuple of int, optional
        RGB body colour.
    """
    center_x, center_y = center
    sign = 1 if direction == "right" else -1
    height = length * 0.5
    darker = tuple(max(0, channel - 60) for channel in color)
    tail = [
        (center_x - sign * length * 0.22, center_y),
        (center_x - sign * length * 0.5, center_y - height * 0.45),
        (center_x - sign * length * 0.5, center_y + height * 0.45),
    ]
    pygame.draw.polygon(surface, darker, tail)
    body = pygame.Rect(0, 0, length * 0.76, height)
    body.center = (center_x + sign * length * 0.12, center_y)
    pygame.draw.ellipse(surface, color, body)
    pygame.draw.ellipse(surface, darker, body, 3)
    fin = [
        (center_x + sign * length * 0.05, center_y + height * 0.05),
        (center_x - sign * length * 0.12, center_y + height * 0.3),
        (center_x + sign * length * 0.12, center_y + height * 0.22),
    ]
    pygame.draw.polygon(surface, darker, fin)
    eye = (int(center_x + sign * length * 0.32), int(center_y - height * 0.14))
    pygame.draw.circle(surface, (255, 255, 255), eye, max(3, int(length * 0.06)))
    pygame.draw.circle(surface, OUTLINE, (eye[0] + sign, eye[1]), max(2, int(length * 0.03)))


def draw_professor_fin(surface, x, ground_y, time):
    """Draw Professor Fin, a fish with glasses in a glass bowl on a barrel."""
    barrel = pygame.Rect(x - 34, ground_y - 56, 68, 56)
    pygame.draw.rect(surface, WOOD, barrel, border_radius=8)
    pygame.draw.rect(surface, WOOD_DARK, barrel, 3, border_radius=8)
    pygame.draw.line(surface, WOOD_DARK, (barrel.left, barrel.top + 16), (barrel.right, barrel.top + 16), 3)
    pygame.draw.line(surface, WOOD_DARK, (barrel.left, barrel.bottom - 16), (barrel.right, barrel.bottom - 16), 3)
    bowl_center = (x, ground_y - 108)
    bowl = pygame.Surface((120, 120), pygame.SRCALPHA)
    pygame.draw.circle(bowl, (150, 214, 255, 150), (60, 60), 56)
    surface.blit(bowl, (bowl_center[0] - 60, bowl_center[1] - 60))
    pygame.draw.circle(surface, (236, 248, 255), bowl_center, 56, 3)
    bob = math.sin(time * 2) * 4
    fish_center = (x, bowl_center[1] + 4 + bob)
    draw_fish(surface, fish_center, "left", length=74, color=(255, 150, 70))
    glasses = (int(fish_center[0] - 23), int(fish_center[1] - 5))
    pygame.draw.circle(surface, OUTLINE, glasses, 9, 2)
    pygame.draw.line(surface, OUTLINE, (glasses[0] + 9, glasses[1]), (glasses[0] + 22, glasses[1] - 3), 2)


def draw_owl(surface, x, ground_y, time):
    """Draw the gatekeeper owl sitting on a tree stump."""
    stump = pygame.Rect(x - 26, ground_y - 40, 52, 40)
    pygame.draw.rect(surface, WOOD, stump, border_radius=6)
    pygame.draw.rect(surface, WOOD_DARK, stump, 3, border_radius=6)
    body = pygame.Rect(x - 30, ground_y - 112, 60, 76)
    pygame.draw.ellipse(surface, (134, 96, 70), body)
    pygame.draw.ellipse(surface, (226, 200, 160), body.inflate(-22, -30).move(0, 10))
    pygame.draw.polygon(surface, (134, 96, 70), [(x - 26, ground_y - 98), (x - 20, ground_y - 124), (x - 8, ground_y - 106)])
    pygame.draw.polygon(surface, (134, 96, 70), [(x + 26, ground_y - 98), (x + 20, ground_y - 124), (x + 8, ground_y - 106)])
    blink = math.sin(time * 1.3) > 0.97
    for eye_x in (x - 12, x + 12):
        pygame.draw.circle(surface, (255, 255, 255), (eye_x, ground_y - 90), 11)
        if blink:
            pygame.draw.line(surface, OUTLINE, (eye_x - 8, ground_y - 90), (eye_x + 8, ground_y - 90), 3)
        else:
            pygame.draw.circle(surface, OUTLINE, (eye_x, ground_y - 90), 5)
    pygame.draw.polygon(surface, (250, 180, 60), [(x - 5, ground_y - 82), (x + 5, ground_y - 82), (x, ground_y - 72)])


def draw_goal(surface, x, ground_y, time):
    """Draw the goal arch that ends the level."""
    for post_x in (x - 44, x + 36):
        pygame.draw.rect(surface, (236, 236, 246), (post_x, ground_y - 170, 8, 170))
    banner = pygame.Rect(x - 50, ground_y - 190, 100, 34)
    pygame.draw.rect(surface, (236, 80, 100), banner, border_radius=8)
    pygame.draw.rect(surface, OUTLINE, banner, 3, border_radius=8)
    text = get_font(28, bold=True).render("GOAL", True, (255, 255, 255))
    surface.blit(text, text.get_rect(center=banner.center))
    draw_spark(surface, x, ground_y - 214 + math.sin(time * 3) * 4, time)


def draw_water(surface, rect, time):
    """Fill ``rect`` with pond water and a moving wave line on top."""
    pygame.draw.rect(surface, (44, 132, 200), rect)
    for x in range(rect.left, rect.right, 24):
        wave_y = rect.top + math.sin(time * 3 + x * 0.05) * 3
        pygame.draw.arc(surface, (190, 230, 255), (x, wave_y - 6, 24, 12), 0, math.pi, 3)


def draw_spikeback(surface, x, y, time):
    """Draw a Spikeback enemy (42 x 34 hitbox) with its top-left at (x, y)."""
    shell, dark = (70, 150, 120), (36, 90, 72)
    wobble = int(math.sin(time * 8) * 2)
    pygame.draw.ellipse(surface, dark, (x + 4 + wobble, y + 26, 13, 8))
    pygame.draw.ellipse(surface, dark, (x + 25 - wobble, y + 26, 13, 8))
    for spike_x in (x + 4, x + 15, x + 26):
        spike = [(spike_x, y + 10), (spike_x + 6, y - 8), (spike_x + 12, y + 10)]
        pygame.draw.polygon(surface, (236, 238, 246), spike)
        pygame.draw.polygon(surface, OUTLINE, spike, 2)
    pygame.draw.ellipse(surface, shell, (x, y + 4, 42, 26))
    pygame.draw.ellipse(surface, dark, (x, y + 4, 42, 26), 2)
    for eye_x in (x + 14, x + 28):
        pygame.draw.circle(surface, (255, 255, 255), (eye_x, y + 18), 4)
        pygame.draw.circle(surface, OUTLINE, (eye_x, y + 19), 2)


def draw_buzzer(surface, x, y, time):
    """Draw a flying Buzzer enemy (40 x 30 hitbox) with its top-left at (x, y)."""
    flap = int(abs(math.sin(time * 30)) * 6)
    for wing_x in (x + 2, x + 22):
        pygame.draw.ellipse(surface, (220, 240, 255), (wing_x, y - 10 + flap, 16, 16 - flap))
    pygame.draw.ellipse(surface, (250, 196, 50), (x, y, 40, 30))
    pygame.draw.rect(surface, OUTLINE, (x + 12, y + 2, 5, 26))
    pygame.draw.rect(surface, OUTLINE, (x + 23, y + 2, 5, 26))
    pygame.draw.ellipse(surface, OUTLINE, (x, y, 40, 30), 2)
    for eye_x in (x + 8, x + 32):
        pygame.draw.circle(surface, (255, 255, 255), (eye_x, y + 12), 5)
        pygame.draw.circle(surface, (200, 40, 40), (eye_x, y + 12), 2)


def draw_brute(surface, x, y, time):
    """Draw a Brute enemy (64 x 100 hitbox) with its top-left at (x, y)."""
    body, dark = (176, 80, 70), (110, 44, 44)
    sway = int(math.sin(time * 4) * 2)
    pygame.draw.rect(surface, dark, (x + 8 + sway, y + 86, 20, 14), border_radius=5)
    pygame.draw.rect(surface, dark, (x + 36 - sway, y + 86, 20, 14), border_radius=5)
    pygame.draw.rect(surface, body, (x, y + 6, 64, 84), border_radius=18)
    pygame.draw.rect(surface, dark, (x, y + 6, 64, 84), 3, border_radius=18)
    pygame.draw.polygon(surface, (240, 236, 220), [(x + 8, y + 10), (x + 14, y - 8), (x + 22, y + 8)])
    pygame.draw.polygon(surface, (240, 236, 220), [(x + 42, y + 8), (x + 50, y - 8), (x + 56, y + 10)])
    for eye_x in (x + 20, x + 44):
        pygame.draw.circle(surface, (255, 255, 255), (eye_x, y + 36), 8)
        pygame.draw.circle(surface, OUTLINE, (eye_x, y + 38), 4)
    pygame.draw.line(surface, OUTLINE, (x + 10, y + 22), (x + 28, y + 28), 4)
    pygame.draw.line(surface, OUTLINE, (x + 54, y + 22), (x + 36, y + 28), 4)
    pygame.draw.rect(surface, (250, 244, 230), (x + 18, y + 58, 28, 10), border_radius=3)
    for tooth_x in range(x + 24, x + 46, 7):
        pygame.draw.line(surface, OUTLINE, (tooth_x, y + 58), (tooth_x, y + 68), 2)


def draw_enemy(surface, enemy, x, y, time):
    """
    Draw any enemy with the top-left of its hitbox at screen position (x, y).

    A frightened enemy gets a blue exclamation mark above its head.
    """
    if enemy.squish_timer is not None:
        draw_distractor(surface, x, y, time, squished=True)
        return
    draw = {"spikeback": draw_spikeback, "buzzer": draw_buzzer, "brute": draw_brute}.get(enemy.kind, draw_distractor)
    draw(surface, x, y, time)
    if enemy.is_afraid:
        mark = get_font(40, bold=True).render("!", True, (120, 200, 255))
        surface.blit(mark, mark.get_rect(midbottom=(x + enemy.width // 2, y - 10 + math.sin(time * 20) * 3)))


def draw_moving_platform(surface, rect):
    """Draw a moving platform: a wooden board with two glowing ends."""
    pygame.draw.rect(surface, WOOD, rect, border_radius=6)
    pygame.draw.rect(surface, WOOD_DARK, rect, 3, border_radius=6)
    for x in range(rect.left + 24, rect.right - 12, 24):
        pygame.draw.line(surface, WOOD_DARK, (x, rect.top + 3), (x, rect.bottom - 3), 2)
    for end_x in (rect.left + 8, rect.right - 8):
        pygame.draw.circle(surface, (130, 230, 255), (end_x, rect.centery), 4)


def draw_shrine(surface, x, ground_y, time, used=False):
    """Draw a skill shrine: a stone with a floating, glowing star above it."""
    stone = pygame.Rect(x - 26, ground_y - 46, 52, 46)
    pygame.draw.rect(surface, (128, 130, 156), stone, border_radius=10)
    pygame.draw.rect(surface, (78, 80, 104), stone, 3, border_radius=10)
    pygame.draw.circle(surface, (78, 80, 104), stone.center, 10, 3)
    if used:
        return
    star_y = ground_y - 86 + math.sin(time * 3) * 6
    halo = pygame.Surface((110, 110), pygame.SRCALPHA)
    pygame.draw.circle(halo, (130, 230, 255, 80), (55, 55), 38 + int(math.sin(time * 5) * 6))
    surface.blit(halo, (x - 55, star_y - 55))
    points = []
    for index in range(10):
        length = 20 if index % 2 == 0 else 9
        angle = math.pi / 5 * index - math.pi / 2 + time
        points.append((x + math.cos(angle) * length, star_y + math.sin(angle) * length))
    pygame.draw.polygon(surface, (150, 240, 255), points)
    pygame.draw.polygon(surface, (40, 120, 190), points, 2)


def make_light(radius, darkness):
    """
    Create a round "hole" that is cut out of the cave darkness.

    Parameters
    ----------
    radius : int
        Radius of the lit area in pixels.
    darkness : tuple of int
        RGBA colour of full darkness; the light fades into it at its edge.

    Returns
    -------
    pygame.Surface
        Square surface to blit onto the darkness with ``BLEND_RGBA_MIN``.
    """
    light = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    light.fill(darkness)
    for step in range(radius, 0, -3):
        alpha = int(darkness[3] * (step / radius) ** 3)
        pygame.draw.circle(light, (*darkness[:3], alpha), (radius, radius), step)
    return light
