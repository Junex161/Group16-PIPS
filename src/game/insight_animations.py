"""Short animations that explain attention with pictures instead of text.

Each insight of Level 1 is an animation of a few "beats". A beat shows one
idea for a few seconds and has a single caption line. Together the insights
tell one story:

1. ``attention``       What attention is: selecting from too much information.
2. ``cocktail_party``  Selective attention: tuning in to one voice.
3. ``gorilla``         Its limits: inattentional blindness.
4. ``flanker``         Distractors still interfere: the flanker effect.
5. ``spotlight``       Attention moves like a spotlight: covert attention.

``map`` ties them together in one picture before the final quiz.

All drawing happens on a ``Stage``: a 2:1 rectangle with its own
coordinates (x from 0 to 100, y from 0 to 50). The same drawing code
therefore works full screen and as a small, looping thumbnail.
"""

import math
import random
from dataclasses import dataclass, replace

import pygame

from . import graphics, ui
from .characters import CHARACTERS

GREY = (96, 100, 130)
PINK, GREEN, BLUE, YELLOW, RED = (255, 170, 200), (150, 230, 160), (170, 200, 255), (255, 214, 92), (255, 110, 110)
SKIN = (250, 214, 180)
# Re-used transparent drawing layers, one per surface size.
_layers = {}


def ease(share):
    """Smooth start and stop for a share from 0 to 1."""
    share = max(0.0, min(1.0, share))
    return share * share * (3 - 2 * share)


def lerp(start, end, share):
    """Blend two numbers or two points."""
    if isinstance(start, tuple):
        return tuple(a + (b - a) * share for a, b in zip(start, end))
    return start + (end - start) * share


def window(share, start, end):
    """Rescale ``share`` so that it runs from 0 to 1 between ``start`` and ``end``."""
    return max(0.0, min(1.0, (share - start) / (end - start)))


class Stage:
    """
    A 2:1 drawing area with its own coordinates (0..100 wide, 0..50 high).

    Parameters
    ----------
    rect : pygame.Rect
        Pixel area of the stage.
    """

    def __init__(self, rect):
        self.rect = rect
        self.unit = rect.width / 100

    def point(self, x, y):
        """Turn stage coordinates into pixels."""
        return (self.rect.left + x * self.unit, self.rect.top + y * self.unit)

    def size(self, value):
        """Turn a stage length into pixels."""
        return value * self.unit

    def text(self, surface, text, x, y, size, color=ui.WHITE, anchor="center", bold=True):
        """Write text whose size is given in stage units."""
        ui.draw_text(surface, text, self.point(x, y), max(10, int(size * self.unit)), color, anchor, bold)

    def circle(self, surface, color, x, y, radius, width=0):
        """Draw a circle in stage units."""
        pygame.draw.circle(surface, color, self.point(x, y), max(1, self.size(radius)), max(1, int(self.size(width))) if width else 0)

    def line(self, surface, color, start, end, width):
        """Draw a line in stage units."""
        pygame.draw.line(surface, color, self.point(*start), self.point(*end), max(1, int(self.size(width))))

    def translucent(self, surface, draw, alpha):
        """Call ``draw(layer)`` on a transparent layer and blend it onto the stage."""
        size = surface.get_size()
        if size not in _layers:
            _layers[size] = pygame.Surface(size, pygame.SRCALPHA)
        layer = _layers[size]
        layer.fill((0, 0, 0, 0))
        draw(layer)
        layer.set_alpha(alpha)
        surface.blit(layer, (0, 0))


def draw_character(surface, stage, character, x, y, height, facing=1, time=0.0, moving=False, punching=False):
    """Draw a hero standing on (x, y), ``height`` stage units tall."""
    image = pygame.Surface((80, 70), pygame.SRCALPHA)
    graphics.draw_hero(image, character, 20, 14, facing, time, moving, True, punching=punching)
    pixels = max(8, int(stage.size(height)))
    image = pygame.transform.smoothscale(image, (int(pixels * 80 / 70), pixels))
    surface.blit(image, image.get_rect(midbottom=stage.point(x, y)))


def draw_scaled(surface, stage, draw, size, x, y, height, angle=0.0):
    """
    Draw a game sprite on a stage at a new size.

    ``draw(image, time)`` paints the sprite onto a transparent image of
    ``size`` pixels; the result is scaled to ``height`` stage units and
    placed with its bottom centre on (x, y).
    """
    image = pygame.Surface(size, pygame.SRCALPHA)
    draw(image)
    pixels = max(4, int(stage.size(height)))
    image = pygame.transform.smoothscale(image, (int(pixels * size[0] / size[1]), pixels))
    if angle:
        image = pygame.transform.rotate(image, angle)
    surface.blit(image, image.get_rect(midbottom=stage.point(x, y)))


def draw_bubble(surface, stage, x, y, width, color, text="", squiggle=False, scale=1.0):
    """Draw a speech bubble whose tail points at (x, y)."""
    width, height = width * scale, 8 * scale
    if text:
        # Grow the bubble if the text would not fit, also on small thumbnails.
        font = ui.get_font(max(10, int(3.6 * scale * stage.unit)), bold=True)
        width = max(width, (font.size(text)[0] + stage.size(3 * scale)) / stage.unit)
    rect = pygame.Rect(0, 0, stage.size(width), stage.size(height))
    rect.midbottom = stage.point(x, y - 2 * scale)
    pygame.draw.rect(surface, color, rect, border_radius=int(stage.size(3 * scale)))
    tail = [stage.point(x - 1.5 * scale, y - 2.3 * scale), stage.point(x + 1.5 * scale, y - 2.3 * scale), stage.point(x, y)]
    pygame.draw.polygon(surface, color, tail)
    if text:
        stage.text(surface, text, x, y - 2 * scale - height / 2, 3.6 * scale, ui.INK)
    elif squiggle:
        for row in range(2):
            points = [
                stage.point(x - width * 0.35 + step * width * 0.07, y - 2 * scale - height * (0.68 - row * 0.36) + math.sin(step * 1.7) * 0.6 * scale)
                for step in range(11)
            ]
            pygame.draw.lines(surface, ui.INK, False, points, max(1, int(stage.size(0.5))))


def draw_stimulus(surface, stage, kind, color, x, y, size):
    """Draw one piece of information: a shape, a sound or a word."""
    center = stage.point(x, y)
    radius = stage.size(size)
    if kind == "circle":
        pygame.draw.circle(surface, color, center, radius)
    elif kind == "square":
        pygame.draw.rect(surface, color, pygame.Rect(0, 0, radius * 1.8, radius * 1.8).move(center[0] - radius * 0.9, center[1] - radius * 0.9), border_radius=3)
    elif kind == "triangle":
        pygame.draw.polygon(surface, color, [(center[0], center[1] - radius), (center[0] - radius, center[1] + radius * 0.8), (center[0] + radius, center[1] + radius * 0.8)])
    elif kind == "sound":
        for ring in range(1, 4):
            arc = pygame.Rect(0, 0, radius * ring * 0.9, radius * ring * 0.9)
            arc.center = center
            pygame.draw.arc(surface, color, arc, -0.8, 0.8, max(1, int(radius * 0.25)))
    else:  # a word
        box = pygame.Rect(0, 0, radius * 2.4, radius * 1.4)
        box.center = center
        pygame.draw.rect(surface, color, box, border_radius=3)
        for row in range(2):
            y_line = box.top + box.height * (0.35 + row * 0.3)
            pygame.draw.line(surface, ui.INK, (box.left + 3, y_line), (box.right - 3, y_line), 1)


def draw_rt_bars(surface, stage, bars, left, top, width):
    """
    Draw small horizontal reaction-time bars.

    ``bars`` holds ``(label, share, color)``: share 1 fills ``width`` units.
    """
    for index, (label, share, color) in enumerate(bars):
        y = top + index * 5
        stage.text(surface, label, left, y + 1.6, 2.6, ui.WHITE, "midleft")
        bar = pygame.Rect(stage.point(left + 14, y)[0], stage.point(0, y)[1], stage.size(width * share), stage.size(3.2))
        pygame.draw.rect(surface, color, bar, border_radius=4)


@dataclass(frozen=True)
class Beat:
    """One step of an animation: a caption, a duration and a drawing method."""

    caption: str
    duration: float
    method: str


class InsightAnimation:
    """
    Base class of the animations.

    Subclasses list their ``beats`` and implement one drawing method per beat
    with the signature ``(surface, stage, share, clock)``: ``share`` runs from
    0 to 1 over the beat and ``clock`` counts seconds since it started.

    Parameters
    ----------
    character : Character, optional
        The player's hero; some animations show it or call its name.
    """

    title = ""
    beats = ()
    # The beat that is looped as a thumbnail in the notebook and the quiz.
    thumbnail_beat = 0
    background = (24, 28, 58)

    def __init__(self, character=CHARACTERS[0]):
        self.character = character
        self.hero_name = character.name.upper()

    def draw_beat(self, surface, stage, index, share, clock):
        """Draw beat ``index`` on a stage."""
        pygame.draw.rect(surface, self.background, stage.rect)
        clip = surface.get_clip()
        surface.set_clip(stage.rect)
        getattr(self, self.beats[index].method)(surface, stage, share, clock)
        surface.set_clip(clip)

    def draw_thumbnail(self, surface, rect, time):
        """Draw the thumbnail beat, looping, into ``rect`` (2:1)."""
        beat = self.beats[self.thumbnail_beat]
        clock = time % beat.duration
        self.draw_beat(surface, Stage(rect), self.thumbnail_beat, clock / beat.duration, clock)


# ---------------------------------------------------------------------------
# 1. What is attention?
# ---------------------------------------------------------------------------

_rng = random.Random(4)
STIMULI = [
    (
        _rng.choice(("circle", "square", "triangle", "sound", "word")),
        _rng.choice((PINK, GREEN, BLUE, YELLOW, (255, 170, 110))),
        (_rng.uniform(-8, 40), _rng.choice((-6, 56)) if index % 3 else _rng.uniform(4, 46)),
        _rng.random(),
    )
    for index in range(18)
]
# The hero stands on the right; information flies to the head at HEAD.
HERO_FEET = (86, 46)
HERO_HEIGHT = 30
HEAD = (83, 28)
CHOSEN = 4


class AttentionAnimation(InsightAnimation):
    """The bottleneck: too much information, attention lets a little through."""

    title = "What is attention?"
    beats = (
        Beat("Your senses take in a flood of information.", 4.5, "flood"),
        Beat("But the mind can only handle a little at a time.", 4.5, "bottleneck"),
        Beat("Attention selects what gets through - the rest is ignored.", 5.0, "selection"),
    )
    thumbnail_beat = 2

    def head(self, surface, stage, glow=0.0, clock=0.0):
        """Draw the player's hero, facing the incoming information."""
        if glow:
            stage.translucent(surface, lambda layer: pygame.draw.circle(layer, YELLOW, stage.point(*HEAD), stage.size(10)), int(120 * glow))
        draw_character(surface, stage, self.character, *HERO_FEET, HERO_HEIGHT, -1, clock)

    def flood(self, surface, stage, share, clock):
        for kind, color, start, offset in STIMULI:
            progress = (clock * 0.35 + offset) % 1
            x, y = lerp(start, (HEAD[0] - 6, HEAD[1]), progress)
            draw_stimulus(surface, stage, kind, color, x, y, 2.2)
        self.head(surface, stage, clock=clock)

    def funnel(self, surface, stage):
        stage.line(surface, ui.WHITE, (56, 6), (70, 25), 0.8)
        stage.line(surface, ui.WHITE, (56, 48), (70, 31), 0.8)

    def bottleneck(self, surface, stage, share, clock):
        passing = int(clock / 0.9) % len(STIMULI)
        for index, (kind, color, start, offset) in enumerate(STIMULI):
            # Everything waits in front of the funnel ...
            waiting = (44 + (index % 4) * 3 + math.sin(clock * 6 + index) * 0.4, 9 + (index * 7) % 33)
            if index == passing:
                # ... and one item at a time squeezes through.
                x, y = lerp(waiting, (HEAD[0] - 6, HEAD[1]), ease((clock % 0.9) / 0.9))
            else:
                x, y = lerp(start, waiting, ease(share * 2))
            draw_stimulus(surface, stage, kind, color, x, y, 2.2)
        self.funnel(surface, stage)
        self.head(surface, stage, clock=clock)

    def selection(self, surface, stage, share, clock):
        chosen_start = (40, 30)
        chosen = lerp(chosen_start, (HEAD[0] - 6, HEAD[1]), ease(window(share, 0.55, 0.9)))

        def beam(layer):
            pygame.draw.polygon(layer, YELLOW, [stage.point(HEAD[0] - 6, HEAD[1] - 2), stage.point(chosen[0], chosen[1] - 5), stage.point(chosen[0], chosen[1] + 5)])

        for index, (kind, color, start, offset) in enumerate(STIMULI):
            if index == CHOSEN:
                continue
            draw_stimulus(surface, stage, kind, GREY, 8 + (index * 13) % 46, 6 + (index * 7) % 38, 2.0)
        if share > 0.15:
            stage.translucent(surface, beam, 90)
        kind, color, _, _ = STIMULI[CHOSEN]
        draw_stimulus(surface, stage, kind, color, *chosen, 2.2 + 1.3 * ease(window(share, 0.15, 0.4)))
        self.head(surface, stage, glow=ease(window(share, 0.85, 1.0)), clock=clock)


# ---------------------------------------------------------------------------
# 2. The cocktail party
# ---------------------------------------------------------------------------

GUESTS = ((17, 31, PINK), (50, 24, GREEN), (83, 31, BLUE))
# The party guests look different from all playable heroes.
GUEST_LOOKS = (
    replace(CHARACTERS[0], fur=(150, 110, 90), jacket=(120, 90, 200)),
    replace(CHARACTERS[1], fur=(230, 190, 120), jacket=(90, 170, 200)),
    replace(CHARACTERS[2], fur=(170, 170, 175), jacket=(220, 120, 60)),
)
LISTENER = (50, 49)
WORDS = ("so then", "we went", "to Rome", "and saw")


class CocktailAnimation(InsightAnimation):
    """Selective listening at a party, and the own name breaking through."""

    title = "The cocktail party"
    beats = (
        Beat("At a party, many voices talk at once.", 4.0, "chatter"),
        Beat("You tune in to one voice ...", 4.0, "tune_in"),
        Beat("... and the rest fades into background noise.", 4.0, "fade_out"),
        Beat("But your own name still breaks through!", 4.5, "own_name"),
    )
    thumbnail_beat = 1
    background = (60, 28, 70)

    def party(self, surface, stage, clock, listener_alert=False):
        for index, (x, y, _) in enumerate(GUESTS):
            draw_character(surface, stage, GUEST_LOOKS[index], x, y + 9, 13, 1 if x < 50 else -1, clock + index)
        draw_character(surface, stage, self.character, *LISTENER, 15, 1, clock)
        if listener_alert:
            stage.text(surface, "!", LISTENER[0] + 7, LISTENER[1] - 15, 7, YELLOW)

    def beam(self, surface, stage, target, alpha=80):
        x, y = target

        def draw(layer):
            pygame.draw.polygon(layer, YELLOW, [stage.point(LISTENER[0] - 1, LISTENER[1] - 12), stage.point(x - 9, y - 6), stage.point(x + 9, y - 6)])

        stage.translucent(surface, draw, alpha)

    def chatter(self, surface, stage, share, clock):
        self.party(surface, stage, clock)
        for index, (x, y, color) in enumerate(GUESTS):
            pop = 1 + 0.08 * math.sin(clock * 5 + index * 2)
            draw_bubble(surface, stage, x, y - 2, 18, color, squiggle=True, scale=pop)

    def tune_in(self, surface, stage, share, clock):
        self.beam(surface, stage, GUESTS[1][:2])
        self.party(surface, stage, clock)
        for index, (x, y, color) in enumerate(GUESTS):
            if index == 1:
                draw_bubble(surface, stage, x, y - 2, 20, color, WORDS[int(clock / 1.0) % len(WORDS)])
            else:
                faded = lerp(color, GREY, ease(share * 1.5))
                draw_bubble(surface, stage, x, y - 2, 18, faded, squiggle=True)

    def fade_out(self, surface, stage, share, clock):
        self.beam(surface, stage, GUESTS[1][:2])
        self.party(surface, stage, clock)
        for index, (x, y, color) in enumerate(GUESTS):
            if index == 1:
                draw_bubble(surface, stage, x, y - 2, 20, color, WORDS[int(clock / 1.0) % len(WORDS)])
            else:
                draw_bubble(surface, stage, x, y - 2, 18, GREY, "bla bla", scale=1 - 0.45 * ease(share))

    def own_name(self, surface, stage, share, clock):
        broken_through = share > 0.3
        self.beam(surface, stage, GUESTS[0][:2] if share > 0.55 else GUESTS[1][:2], 90)
        self.party(surface, stage, clock, listener_alert=share > 0.45)
        x, y, color = GUESTS[1]
        draw_bubble(surface, stage, x, y - 2, 20, color if not broken_through else GREY, WORDS[int(clock) % len(WORDS)])
        draw_bubble(surface, stage, GUESTS[2][0], GUESTS[2][1] - 2, 18, GREY, "bla bla", scale=0.55)
        x, y, _ = GUESTS[0]
        if broken_through:
            bounce = 1 + 0.25 * math.sin(window(share, 0.3, 0.45) * math.pi)
            draw_bubble(surface, stage, x, y - 2, 22, YELLOW, f"{self.hero_name}!", scale=bounce)
        else:
            draw_bubble(surface, stage, x, y - 2, 18, GREY, "bla bla", scale=0.55)


# ---------------------------------------------------------------------------
# 3. The invisible gorilla
# ---------------------------------------------------------------------------

WHITE_TEAM = ((26, 34), (48, 24), (68, 38))
BLACK_TEAM = ((38, 44), (58, 18), (80, 30))
PASS_TIME = 1.4
# Share of all viewers in Simons and Chabris (1999) who did not notice the gorilla.
MISSED_GORILLA = 0.46
# The players are the game's heroes in white and in black shirts.
TEAM_LOOKS = {
    "white": [replace(character, jacket=(245, 245, 250), scarf=(210, 214, 230)) for character in CHARACTERS],
    "black": [replace(character, jacket=(40, 40, 48), scarf=(80, 80, 96)) for character in CHARACTERS],
}


class GorillaAnimation(InsightAnimation):
    """Counting passes while a gorilla walks through the scene."""

    title = "The invisible gorilla"
    beats = (
        Beat("Count how often the white team passes the ball.", 7.5, "count"),
        Beat("Your attention locks onto the ball ...", 3.5, "lock_on"),
        Beat("... while a gorilla walks right through!", 5.5, "gorilla_walks"),
        Beat("About half of the viewers never notice it.", 4.5, "reveal"),
    )
    thumbnail_beat = 3
    background = (40, 52, 80)

    def player_position(self, base, clock, index):
        return base[0] + math.sin(clock * 1.3 + index) * 3, base[1] + math.cos(clock * 1.1 + index * 2) * 2

    def ball_position(self, clock):
        throw = int(clock / PASS_TIME)
        share = (clock % PASS_TIME) / PASS_TIME
        start = self.player_position(WHITE_TEAM[throw % 3], clock, throw % 3)
        end = self.player_position(WHITE_TEAM[(throw + 1) % 3], clock, (throw + 1) % 3)
        x, y = lerp(start, end, share)
        return x, y - 8 - 7 * math.sin(share * math.pi)

    def court(self, surface, stage, clock, gorilla_x=None, thumping=False, count=True):
        pygame.draw.rect(surface, (214, 190, 150), pygame.Rect(stage.point(4, 6), (stage.size(92), stage.size(42))), border_radius=6)
        if gorilla_x is not None:
            graphics.draw_gorilla(surface, *stage.point(gorilla_x, 47), clock, thumping, scale=stage.unit / 8)
        for team, positions in (("black", BLACK_TEAM), ("white", WHITE_TEAM)):
            for index, base in enumerate(positions):
                x, y = self.player_position(base, clock + (1.7 if team == "black" else 0), index)
                facing = 1 if x < 50 else -1
                draw_character(surface, stage, TEAM_LOOKS[team][index], x, y, 12, facing, clock + index, moving=True)
        stage.circle(surface, (230, 120, 50), *self.ball_position(clock), 1.3)
        if count:
            stage.text(surface, f"Passes: {int(clock / PASS_TIME)}", 7, 3, 3.2, ui.WHITE, "midleft")

    def spotlight_on_ball(self, surface, stage, clock):
        def draw(layer):
            layer.fill((10, 12, 30, 255))
            pygame.draw.circle(layer, (0, 0, 0, 0), stage.point(*self.ball_position(clock)), stage.size(6))

        stage.translucent(surface, draw, 170)

    def count(self, surface, stage, share, clock):
        self.court(surface, stage, clock)

    def lock_on(self, surface, stage, share, clock):
        self.court(surface, stage, clock + 4.5, count=False)
        self.spotlight_on_ball(surface, stage, clock + 4.5)

    def gorilla_walks(self, surface, stage, share, clock):
        walk = ease(window(share, 0.0, 0.42)) * 0.5 + ease(window(share, 0.62, 1.0)) * 0.5
        thumping = 0.42 < share < 0.62
        self.court(surface, stage, clock + 8, gorilla_x=96 - walk * 92, thumping=thumping, count=False)
        self.spotlight_on_ball(surface, stage, clock + 8)

    def reveal(self, surface, stage, share, clock):
        self.court(surface, stage, clock, gorilla_x=50, thumping=True, count=False)
        stage.circle(surface, RED, 50, 34, 14, 0.6)
        # A pie chart: half of the viewers missed the gorilla.
        center, radius = stage.point(13, 14), stage.size(6)
        pygame.draw.circle(surface, ui.WHITE, center, radius)
        filled = MISSED_GORILLA * ease(window(share, 0.2, 0.7))
        points = [center] + [
            (center[0] + radius * math.sin(2 * math.pi * filled * step / 20), center[1] - radius * math.cos(2 * math.pi * filled * step / 20))
            for step in range(21)
        ]
        if filled > 0:
            pygame.draw.polygon(surface, RED, points)
        stage.text(surface, f"{MISSED_GORILLA:.0%} missed it", 13, 23, 2.8, ui.INK)


# ---------------------------------------------------------------------------
# 4. The flanker effect
# ---------------------------------------------------------------------------


class FlankerAnimation(InsightAnimation):
    """Congruent versus incongruent fish and the tug on the response."""

    title = "The flanker effect"
    beats = (
        Beat("Which way does the middle fish swim? Easy!", 4.0, "congruent"),
        Beat("Now its neighbours swim the other way ...", 5.0, "incongruent"),
        Beat("... they pull at your answer: slower, more mistakes.", 4.5, "compare"),
    )
    thumbnail_beat = 1
    background = (16, 60, 110)

    def fish_row(self, surface, stage, y, middle, flankers, length=8):
        for offset in (-2, -1, 0, 1, 2):
            direction = middle if offset == 0 else flankers
            graphics.draw_fish(surface, stage.point(50 + offset * 10, y), direction, int(stage.size(length)))
        stage.circle(surface, ui.WHITE, 50, y, 6, 0.3)

    def needle(self, surface, stage, angle, lit=None):
        """A dial between "left" and "right"; ``angle`` -1 (left) to 1 (right)."""
        for side, label in ((-1, "LEFT"), (1, "RIGHT")):
            color = GREEN if lit == side else GREY
            stage.text(surface, label, 50 + side * 14, 44, 3, color)
        base = (50, 47)
        tip = (base[0] + math.sin(angle * 1.1) * 10, base[1] - math.cos(angle * 1.1) * 10)
        stage.line(surface, ui.WHITE, base, tip, 0.8)
        stage.circle(surface, ui.WHITE, *base, 1.2)

    def congruent(self, surface, stage, share, clock):
        self.fish_row(surface, stage, 18, "right", "right")
        answered = ease(window(share, 0.2, 0.35))
        self.needle(surface, stage, answered, lit=1 if answered > 0.95 else None)
        draw_rt_bars(surface, stage, [("same way", 0.4 * answered, GREEN)], 66, 38, 18)

    def incongruent(self, surface, stage, share, clock):
        self.fish_row(surface, stage, 18, "right", "left")
        for offset in (-2, -1, 1, 2):
            pull = math.sin(clock * 8) * 1.2
            stage.text(surface, "<", 50 + offset * 10 - 5 + pull, 25, 3, RED)
        wobble = math.sin(clock * 9) * 0.8 * (1 - ease(window(share, 0.3, 0.75)))
        angle = ease(window(share, 0.55, 0.75)) + wobble
        self.needle(surface, stage, max(-1, min(1, angle)), lit=1 if share > 0.75 else None)
        draw_rt_bars(surface, stage, [("same way", 0.4, GREEN), ("other way", 0.75 * ease(window(share, 0.2, 0.75)), RED)], 66, 34, 18)

    def compare(self, surface, stage, share, clock):
        self.fish_row(surface, stage, 10, "right", "right", 6)
        self.fish_row(surface, stage, 26, "right", "left", 6)
        draw_rt_bars(surface, stage, [("same way", 0.4, GREEN), ("other way", 0.75, RED)], 30, 38, 34)


# ---------------------------------------------------------------------------
# 5. The spotlight
# ---------------------------------------------------------------------------

EYE = (50, 22)
BOX_X = (18, 82)


class SpotlightAnimation(InsightAnimation):
    """Spatial cueing: attention moves to the cued side without the eyes."""

    title = "The spotlight of attention"
    beats = (
        Beat("Your eyes stay on the centre ...", 3.5, "fixate"),
        Beat("... but an arrow sends your attention to the right.", 4.5, "cue"),
        Beat("A star in the spotlight: spotted fast!", 4.0, "valid"),
        Beat("A star elsewhere: the spotlight must move first - slower.", 5.0, "invalid"),
    )
    thumbnail_beat = 1
    background = (12, 14, 34)

    def scene(self, surface, stage, light_x, arrow=False, star=None, clock=0.0):
        stage.translucent(surface, lambda layer: pygame.draw.circle(layer, (255, 244, 170), stage.point(light_x, EYE[1]), stage.size(10)), 110)
        for x in BOX_X:
            box = pygame.Rect(0, 0, stage.size(14), stage.size(14))
            box.center = stage.point(x, EYE[1])
            pygame.draw.rect(surface, (110, 120, 170), box, max(1, int(stage.size(0.6))), border_radius=6)
        eye = pygame.Rect(0, 0, stage.size(10), stage.size(6))
        eye.center = stage.point(*EYE)
        pygame.draw.ellipse(surface, ui.WHITE, eye)
        stage.circle(surface, (60, 110, 200), *EYE, 2.2)
        stage.circle(surface, ui.INK, *EYE, 1.1)
        if arrow:
            stage.line(surface, YELLOW, (EYE[0] - 4, EYE[1] - 8), (EYE[0] + 4, EYE[1] - 8), 1)
            pygame.draw.polygon(surface, YELLOW, [stage.point(EYE[0] + 6, EYE[1] - 8), stage.point(EYE[0] + 3, EYE[1] - 10.5), stage.point(EYE[0] + 3, EYE[1] - 5.5)])
        if star is not None:
            graphics.draw_spark(surface, *stage.point(star, EYE[1]), clock, radius=stage.size(4))

    def fixate(self, surface, stage, share, clock):
        self.scene(surface, stage, 50 + math.sin(clock * 2) * 1.5)
        stage.text(surface, "eyes here", EYE[0], EYE[1] + 6, 2.6, ui.SOFT_BLUE)

    def cue(self, surface, stage, share, clock):
        self.scene(surface, stage, lerp(50, BOX_X[1], ease(window(share, 0.3, 0.8))), arrow=share > 0.15)
        stage.text(surface, "eyes still here", EYE[0], EYE[1] + 6, 2.6, ui.SOFT_BLUE)

    def valid(self, surface, stage, share, clock):
        star = BOX_X[1] if share > 0.2 else None
        self.scene(surface, stage, BOX_X[1], arrow=True, star=star, clock=clock)
        draw_rt_bars(surface, stage, [("fast", 0.35 * ease(window(share, 0.2, 0.45)), GREEN)], 30, 38, 40)

    def invalid(self, surface, stage, share, clock):
        star = BOX_X[0] if share > 0.15 else None
        light_x = lerp(BOX_X[1], BOX_X[0], ease(window(share, 0.25, 0.65)))
        self.scene(surface, stage, light_x, arrow=True, star=star, clock=clock)
        draw_rt_bars(surface, stage, [("fast", 0.35, GREEN), ("slow", 0.6 * ease(window(share, 0.15, 0.7)), RED)], 30, 36, 40)


# ---------------------------------------------------------------------------
# The big picture
# ---------------------------------------------------------------------------

MAP_NODES = (
    ("cocktail_party", "selects one source", (20, 11)),
    ("gorilla", "has limits", (80, 11)),
    ("flanker", "can be disturbed", (20, 39)),
    ("spotlight", "moves like a spotlight", (80, 39)),
)


class AttentionMapAnimation(InsightAnimation):
    """Connects the four phenomena to one picture of attention."""

    title = "The big picture"
    beats = (
        Beat("Attention SELECTS what we focus on ...", 3.5, "node_1"),
        Beat("... but it has LIMITS: we miss what we ignore ...", 3.5, "node_2"),
        Beat("... DISTRACTORS still get in ...", 3.5, "node_3"),
        Beat("... and it MOVES like a spotlight, even without the eyes.", 4.5, "node_4"),
    )
    thumbnail_beat = 3

    def __init__(self, character=CHARACTERS[0]):
        super().__init__(character)
        self.parts = {key: ANIMATIONS[key](character) for key, _, _ in MAP_NODES}

    def draw_map(self, surface, stage, n_nodes, share, clock):
        for index, (key, label, (x, y)) in enumerate(MAP_NODES[:n_nodes]):
            grow = 1.0 if index < n_nodes - 1 else ease(window(share, 0.0, 0.4))
            stage.line(surface, YELLOW, (50, 25), lerp((50, 25), (x, y), grow), 0.6)
            if grow >= 1:
                thumb = pygame.Rect(0, 0, stage.size(26), stage.size(13))
                thumb.center = stage.point(x, y - 1)
                self.parts[key].draw_thumbnail(surface, thumb, clock)
                pygame.draw.rect(surface, YELLOW, thumb, max(1, int(stage.size(0.3))), border_radius=4)
                stage.text(surface, label, x, y + 7.3, 2.6, ui.WHITE)
        stage.circle(surface, (60, 70, 140), 50, 25, 8)
        stage.circle(surface, YELLOW, 50, 25, 8, 0.4)
        stage.text(surface, "ATTENTION", 50, 25, 2.6, YELLOW)

    def node_1(self, surface, stage, share, clock):
        self.draw_map(surface, stage, 1, share, clock)

    def node_2(self, surface, stage, share, clock):
        self.draw_map(surface, stage, 2, share, clock)

    def node_3(self, surface, stage, share, clock):
        self.draw_map(surface, stage, 3, share, clock)

    def node_4(self, surface, stage, share, clock):
        self.draw_map(surface, stage, 4, share, clock)


# ---------------------------------------------------------------------------
# The QRP Blaster (shown when it is unlocked at the end of the level)
# ---------------------------------------------------------------------------

P_VALUES = (0.41, 0.22, 0.67, 0.13, 0.35, 0.09, 0.03)


class QrpAnimation(InsightAnimation):
    """What questionable research practices are, and why they are a problem."""

    title = "The QRP Blaster"
    beats = (
        Beat("p-hacking: test again and again until one result is 'significant'.", 11.0, "p_hacking"),
        Beat("HARKing: write the hypothesis AFTER seeing the results.", 9.0, "harking"),
        Beat("Both make chance look like a finding that often fails to replicate.", 8.0, "blaster"),
    )
    thumbnail_beat = 2

    def p_hacking(self, surface, stage, share, clock):
        baseline, top = 42, 8
        stage.line(surface, ui.WHITE, (12, baseline), (88, baseline), 0.4)
        line_y = baseline - (baseline - top) * 0.05 / 0.7
        stage.line(surface, RED, (12, line_y), (88, line_y), 0.35)
        stage.text(surface, "p = .05", 90, line_y, 2.4, RED, "midleft")
        n_shown = min(len(P_VALUES), int(share * 1.1 * len(P_VALUES)) + 1)
        for index, p_value in enumerate(P_VALUES[:n_shown]):
            height = (baseline - top) * p_value / 0.7
            significant = p_value < 0.05
            bar = pygame.Rect(stage.point(16 + index * 10, baseline - height), (stage.size(6), stage.size(height)))
            pygame.draw.rect(surface, GREEN if significant else GREY, bar, border_radius=3)
            stage.text(surface, f"test {index + 1}", 19 + index * 10, baseline + 2.5, 2.2, ui.WHITE)
            if significant:
                stage.text(surface, "Significant!", 19 + index * 10, 10, 3.4, GREEN)

    def harking(self, surface, stage, share, clock):
        results = pygame.Rect(stage.point(10, 14), (stage.size(32), stage.size(22)))
        pygame.draw.rect(surface, (40, 46, 90), results, border_radius=8)
        for index, height in enumerate((6, 10, 16)):
            bar = pygame.Rect(stage.point(15 + index * 8, 33 - height), (stage.size(5), stage.size(height)))
            pygame.draw.rect(surface, BLUE, bar, border_radius=3)
        stage.text(surface, "1. Results", 26, 11, 3, ui.WHITE)
        slide = ease(window(share, 0.35, 0.6))
        x = lerp(60, 58, slide)
        if share > 0.35:
            note = pygame.Rect(stage.point(x, 14), (stage.size(32), stage.size(22)))
            pygame.draw.rect(surface, YELLOW, note, border_radius=8)
            stage.text(surface, "2. Hypothesis:", x + 16, 19, 2.8, ui.INK)
            stage.text(surface, "'We predicted", x + 16, 25, 2.6, ui.INK)
            stage.text(surface, "this!'", x + 16, 29, 2.6, ui.INK)
            stage.line(surface, YELLOW, (44, 25), (56, 25), 0.6)
        if share > 0.65:
            stage.text(surface, "Written AFTER the results", 50, 44, 3, RED)

    def blaster(self, surface, stage, share, clock):
        graphics.draw_blaster(surface, *stage.point(16, 25), scale=stage.unit / 6)
        for index, word in enumerate(("p-hacking", "HARKing", "cherry-picking")):
            travel = (clock * 0.3 + index / 3) % 1
            rect = pygame.Rect(0, 0, stage.size(16), stage.size(4.4))
            rect.center = stage.point(24 + travel * 50, 25 + (index - 1) * 7 * travel)
            graphics.draw_projectile(surface, rect, word, 1) if stage.unit > 6 else pygame.draw.rect(surface, YELLOW, rect, border_radius=4)
        sign = pygame.Rect(stage.point(78, 14), (stage.size(16), stage.size(22)))
        pygame.draw.rect(surface, (40, 46, 90), sign, border_radius=8)
        stage.text(surface, "Repeat the", 86, 19, 2.4, ui.WHITE)
        stage.text(surface, "study", 86, 23, 2.4, ui.WHITE)
        failed = share > 0.5
        stage.text(surface, "X" if failed else "?", 86, 30, 6, RED if failed else ui.WHITE)


# ---------------------------------------------------------------------------
# Skills: punch and fear conditioning
# ---------------------------------------------------------------------------

_tile_images = {}


def tile_image(name):
    """Return a tile picture from graphics.make_tile_images (made once)."""
    if not _tile_images:
        _tile_images.update(graphics.make_tile_images())
    return _tile_images[name]


class PunchAnimation(InsightAnimation):
    """How to punch: crates break, enemies fly away."""

    title = "Punch!"
    beats = (
        Beat("Press F to punch: cracked crates break apart.", 5.0, "crates"),
        Beat("Punches knock out enemies - even spiky ones.", 5.0, "enemy"),
    )
    background = (40, 60, 110)

    def ground(self, surface, stage):
        pygame.draw.rect(surface, (98, 192, 86), pygame.Rect(stage.point(0, 40), (stage.size(100), stage.size(10))))

    def crates(self, surface, stage, share, clock):
        self.ground(surface, stage)
        walk = ease(window(share, 0.0, 0.4))
        punching = 0.45 < share < 0.6
        draw_character(surface, stage, self.character, lerp(18, 44, walk), 40, 14, 1, clock, moving=walk < 1, punching=punching)
        size = stage.size(8)
        if share < 0.5:
            for row in range(2):
                crate = pygame.transform.smoothscale(tile_image("crate"), (int(size), int(size)))
                surface.blit(crate, stage.point(54, 32 - row * 8))
        else:
            burst = ease(window(share, 0.5, 0.85))
            for index in range(8):
                angle = index * math.pi / 4 + 0.3
                x = 58 + math.cos(angle) * 14 * burst
                y = 32 + math.sin(angle) * 10 * burst + 12 * burst**2
                piece = pygame.Rect(stage.point(x, y), (stage.size(2.2), stage.size(2.2)))
                pygame.draw.rect(surface, graphics.WOOD, piece)
        if punching:
            stage.text(surface, "F", 50, 18, 6, YELLOW)

    def enemy(self, surface, stage, share, clock):
        self.ground(surface, stage)
        punching = 0.45 < share < 0.6
        draw_character(surface, stage, self.character, 40, 40, 14, 1, clock, punching=punching)
        if share < 0.5:
            x = lerp(80, 52, ease(window(share, 0.0, 0.5)))
            draw_scaled(surface, stage, lambda image: graphics.draw_spikeback(image, 4, 14, clock), (50, 50), x, 40.5, 8)
        else:
            fly = window(share, 0.5, 0.9)
            x, y = lerp(52, 95, fly), 40 - 30 * math.sin(fly * math.pi * 0.7)
            draw_scaled(surface, stage, lambda image: graphics.draw_spikeback(image, 4, 14, clock), (50, 50), x, y, 8, angle=-fly * 540)
        if punching:
            stage.text(surface, "F", 46, 18, 6, YELLOW)


PAIRINGS = (0.12, 0.42, 0.72)


class FearAnimation(InsightAnimation):
    """Classical conditioning: bell plus scare, until the bell alone scares."""

    title = "Fear conditioning"
    beats = (
        Beat("At first the bell means nothing - the enemy ignores it.", 6.0, "before"),
        Beat("Bell plus a scary flash, again and again ...", 9.0, "pairing"),
        Beat("Now the bell alone scares it away!", 6.0, "after"),
    )
    background = (36, 30, 66)

    def bell(self, surface, stage, ringing):
        x, y = 22, 22
        swing = math.sin(pygame.time.get_ticks() * 0.02) * 8 if ringing else 0
        body = [stage.point(x - 6, y + 6), stage.point(x - 4, y - 4), stage.point(x, y - 7), stage.point(x + 4, y - 4), stage.point(x + 6, y + 6)]
        pygame.draw.polygon(surface, YELLOW, body)
        stage.circle(surface, (200, 140, 30), x + swing * 0.05, y + 7, 1.6)
        if ringing:
            for ring in range(1, 4):
                arc = pygame.Rect(0, 0, stage.size(8 + ring * 5), stage.size(8 + ring * 5))
                arc.center = stage.point(x, y)
                pygame.draw.arc(surface, ui.WHITE, arc, -0.7, 0.7, max(1, int(stage.size(0.4))))
        stage.text(surface, "CS: bell", x, y + 13, 2.6, ui.SOFT_BLUE)

    def enemy(self, surface, stage, x, clock, scared=False):
        jitter = math.sin(clock * 40) * 0.8 if scared else 0
        draw_scaled(surface, stage, lambda image: graphics.draw_distractor(image, 5, 14, clock), (50, 50), x + jitter, 42, 9)
        if scared:
            stage.text(surface, "!", x, 25, 6, (120, 200, 255))

    def ground(self, surface, stage):
        pygame.draw.rect(surface, (60, 52, 100), pygame.Rect(stage.point(0, 42), (stage.size(100), stage.size(8))))

    def before(self, surface, stage, share, clock):
        self.ground(surface, stage)
        ringing = 0.3 < share < 0.6
        self.bell(surface, stage, ringing)
        self.enemy(surface, stage, 62 + math.sin(clock * 1.2) * 8, clock)
        if ringing:
            stage.text(surface, "...", 62, 26, 4, ui.WHITE)

    def pairing(self, surface, stage, share, clock):
        self.ground(surface, stage)
        active = [start for start in PAIRINGS if start <= share < start + 0.18]
        count = sum(share >= start for start in PAIRINGS)
        flashing = bool(active) and (share - active[0]) < 0.08
        if flashing:
            stage.translucent(surface, lambda layer: layer.fill((255, 255, 255, 255)), 120)
            bolt = [(48, 4), (42, 18), (48, 18), (40, 34), (54, 14), (47, 14), (52, 4)]
            pygame.draw.polygon(surface, YELLOW, [stage.point(*point) for point in bolt])
            stage.text(surface, "US: scary flash", 47, 38, 2.6, YELLOW)
        self.bell(surface, stage, bool(active))
        self.enemy(surface, stage, 66, clock, scared=bool(active))
        stage.text(surface, f"Pairing {max(1, count)} of {len(PAIRINGS)}", 84, 8, 3, ui.WHITE)

    def after(self, surface, stage, share, clock):
        self.ground(surface, stage)
        self.bell(surface, stage, 0.15 < share < 0.45)
        if share < 0.25:
            self.enemy(surface, stage, 62, clock)
        else:
            run = ease(window(share, 0.3, 0.9))
            self.enemy(surface, stage, lerp(62, 112, run), clock, scared=True)
            stage.text(surface, "CR: fear", 50, 12, 3.2, (120, 200, 255))


ANIMATIONS = {
    "attention": AttentionAnimation,
    "cocktail_party": CocktailAnimation,
    "gorilla": GorillaAnimation,
    "flanker": FlankerAnimation,
    "spotlight": SpotlightAnimation,
    "map": AttentionMapAnimation,
    "qrp": QrpAnimation,
    "punch": PunchAnimation,
    "fear": FearAnimation,
}
