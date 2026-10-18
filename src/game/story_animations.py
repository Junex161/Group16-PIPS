"""Animations that explain the Prologue and Levels 2 and 3 with pictures.

They work exactly like the attention animations of Level 1 (see
``insight_animations.py``): a few beats with one caption line each, drawn on
a 2:1 ``Stage`` with coordinates from 0 to 100 (x) and 0 to 50 (y), so the
same code draws the full-screen version and the small looping thumbnail.

``register()`` adds them to ``insight_animations.ANIMATIONS``.
"""

import math
import random

import pygame

from . import graphics, insight_animations, ui
from .characters import CHARACTERS
from .experiment_scenes import draw_race_car, draw_stop_sign, draw_tower
from .insight_animations import (
    BLUE,
    GREEN,
    GREY,
    PINK,
    RED,
    YELLOW,
    Beat,
    InsightAnimation,
    draw_bubble,
    draw_character,
    draw_scaled,
    ease,
    lerp,
    window,
)
from .worlds import draw_card

ORANGE = (255, 170, 90)
PAPER = (250, 246, 230)


def ground(surface, stage, color=(98, 192, 86), top=42):
    """Draw a strip of ground at the bottom of a stage."""
    pygame.draw.rect(surface, color, pygame.Rect(stage.point(0, top), (stage.size(100) + 2, stage.size(50 - top) + 2)))


def draw_paper(surface, stage, x, y, color=PAPER, label="", label_color=ui.INK, size=1.0):
    """Draw a sheet of paper (a study) centred on (x, y)."""
    rect = pygame.Rect(0, 0, stage.size(6 * size), stage.size(8 * size))
    rect.center = stage.point(x, y)
    pygame.draw.rect(surface, color, rect, border_radius=max(1, int(stage.size(0.6))))
    pygame.draw.rect(surface, graphics.OUTLINE, rect, max(1, int(stage.size(0.25))), border_radius=max(1, int(stage.size(0.6))))
    if label:
        stage.text(surface, label, x, y, 1.9 * size, label_color)
    else:
        for row in range(3):
            line_y = y - 2 * size + row * 1.6 * size
            stage.line(surface, GREY, (x - 2 * size, line_y), (x + 2 * size, line_y), 0.3)


def draw_cabinet(surface, stage, x, y, open_share=0.0, height=24):
    """Draw a filing cabinet whose top drawer opens by ``open_share`` (0 to 1)."""
    body = pygame.Rect(0, 0, stage.size(16), stage.size(height))
    body.midbottom = stage.point(x, y)
    pygame.draw.rect(surface, (110, 120, 140), body, border_radius=int(stage.size(1)))
    pygame.draw.rect(surface, graphics.OUTLINE, body, max(1, int(stage.size(0.3))), border_radius=int(stage.size(1)))
    for index in range(3):
        drawer = pygame.Rect(0, 0, stage.size(13), stage.size(height / 3 - 2))
        drawer.midtop = (body.centerx, body.top + stage.size(1 + index * height / 3))
        if index == 0:
            drawer.x -= stage.size(8 * open_share)
        pygame.draw.rect(surface, (140, 150, 170), drawer, border_radius=int(stage.size(0.6)))
        pygame.draw.rect(surface, graphics.OUTLINE, drawer, max(1, int(stage.size(0.25))), border_radius=int(stage.size(0.6)))
        pygame.draw.rect(surface, (220, 200, 120), pygame.Rect(drawer.centerx - stage.size(2), drawer.centery - stage.size(0.5), stage.size(4), stage.size(1)))


def draw_check(surface, stage, x, y, size=3.0, ok=True):
    """Draw a green tick or a red cross."""
    if ok:
        points = [stage.point(x - size, y), stage.point(x - size * 0.3, y + size * 0.7), stage.point(x + size, y - size * 0.8)]
        pygame.draw.lines(surface, GREEN, False, points, max(2, int(stage.size(size * 0.3))))
    else:
        stage.line(surface, RED, (x - size, y - size), (x + size, y + size), size * 0.3)
        stage.line(surface, RED, (x - size, y + size), (x + size, y - size), size * 0.3)


def draw_value_bars(surface, stage, bars, left, bottom, width, height):
    """Draw vertical bars with labels: ``bars`` holds (label, share, colour, value text)."""
    slot = width / len(bars)
    stage.line(surface, ui.WHITE, (left, bottom), (left + width, bottom), 0.4)
    for index, (label, share, color, text) in enumerate(bars):
        x = left + slot * (index + 0.5)
        bar_height = height * share
        rect = pygame.Rect(0, 0, stage.size(slot * 0.5), max(2, stage.size(bar_height)))
        rect.midbottom = stage.point(x, bottom)
        pygame.draw.rect(surface, color, rect, border_radius=int(stage.size(0.8)))
        stage.text(surface, text, x, bottom - bar_height - 2.5, 3.0, ui.WHITE)
        stage.text(surface, label, x, bottom + 3, 2.4, ui.WHITE)


# ---------------------------------------------------------------------------
# Prologue: Open Science
# ---------------------------------------------------------------------------

STATIONS = (("PLAN", 14), ("DATA", 38), ("ANALYSIS", 62), ("PAPER", 86))


class OpenScienceIntroAnimation(InsightAnimation):
    """What Open Science is: every step of research becomes see-through."""

    title = "What is Open Science?"
    beats = (
        Beat("Research has many steps - usually hidden in a black box.", 4.5, "closed"),
        Beat("Open Science opens every step: plan, data, analysis, paper.", 5.5, "opening"),
        Beat("So anyone can check the work - and build on it.", 5.0, "checking"),
    )
    thumbnail_beat = 2
    background = (24, 50, 70)

    def stations(self, surface, stage, opened, clock):
        for index, (label, x) in enumerate(STATIONS):
            box = pygame.Rect(0, 0, stage.size(18), stage.size(16))
            box.center = stage.point(x, 22)
            is_open = index < opened
            pygame.draw.rect(surface, (230, 240, 250) if is_open else (40, 40, 56), box, border_radius=int(stage.size(1.2)))
            pygame.draw.rect(surface, YELLOW if is_open else GREY, box, max(1, int(stage.size(0.4))), border_radius=int(stage.size(1.2)))
            stage.text(surface, label, x, 34, 2.6, ui.WHITE)
            if is_open:
                for row in range(3):
                    stage.line(surface, GREY, (x - 6, 18 + row * 3), (x + 6, 18 + row * 3), 0.4)
            else:
                stage.text(surface, "?", x, 22, 6, GREY)
            if index < len(STATIONS) - 1:
                stage.line(surface, ui.WHITE, (x + 10, 22), (x + 14, 22), 0.5)

    def closed(self, surface, stage, share, clock):
        self.stations(surface, stage, 0, clock)
        stage.text(surface, "'Trust me, it works!'", 50, 44, 3.2, ui.SOFT_BLUE)

    def opening(self, surface, stage, share, clock):
        self.stations(surface, stage, int(share * 4.4), clock)

    def checking(self, surface, stage, share, clock):
        self.stations(surface, stage, 4, clock)
        for index in range(3):
            x = 26 + index * 24
            draw_character(surface, stage, CHARACTERS[index], x, 48, 10, 1, clock + index, moving=False)
            if share > 0.3 + index * 0.15:
                draw_check(surface, stage, x + 6, 38, 1.6)


def grid_positions():
    """Positions of 100 small squares in a 20 x 5 grid."""
    return [(14 + (index % 20) * 3.8, 16 + (index // 20) * 4.4) for index in range(100)]


class ReproducibilityAnimation(InsightAnimation):
    """The Reproducibility Project: 100 studies repeated (Open Science Collaboration, 2015)."""

    title = "The Reproducibility Project"
    beats = (
        Beat("Many labs repeated 100 published psychology studies.", 4.5, "hundred"),
        Beat("In the originals, 97 of 100 results were significant.", 4.5, "originals"),
        Beat("Repeated, only 35 of these 97 were significant again.", 5.0, "repeats"),
        Beat("And the effects were only about half as large.", 5.0, "effects"),
    )
    thumbnail_beat = 2
    background = (40, 30, 70)
    # Which of the 100 studies were significant: 97 originals, 36 replications.
    _rng = random.Random(5)
    ORIGINAL = set(_rng.sample(range(100), 97))
    REPLICATED = set(_rng.sample(sorted(ORIGINAL), 35))

    def squares(self, surface, stage, shown, colored, color, share=1.0):
        for index, (x, y) in enumerate(grid_positions()[:shown]):
            fill = color if index in colored else GREY
            rect = pygame.Rect(0, 0, stage.size(3), stage.size(3.6))
            rect.center = stage.point(x, y)
            pygame.draw.rect(surface, fill, rect, border_radius=max(1, int(stage.size(0.4))))

    def hundred(self, surface, stage, share, clock):
        shown = int(100 * ease(window(share, 0.0, 0.8)))
        self.squares(surface, stage, shown, set(), GREY)
        stage.text(surface, f"{shown} studies", 50, 44, 4, ui.WHITE)

    def originals(self, surface, stage, share, clock):
        colored = {index for index in self.ORIGINAL if index / 100 < ease(window(share, 0.1, 0.8))}
        self.squares(surface, stage, 100, colored, GREEN)
        stage.text(surface, f"Original studies: {len(colored)} of 100 significant", 50, 44, 3.6, GREEN)

    def repeats(self, surface, stage, share, clock):
        fade = ease(window(share, 0.1, 0.7))
        keep = {index for index in self.ORIGINAL if index in self.REPLICATED or fade < (index % 10) / 10}
        self.squares(surface, stage, 100, keep, GREEN)
        stage.text(surface, "Replications: 35 of 97 significant (36%)", 50, 44, 3.6, YELLOW)

    def effects(self, surface, stage, share, clock):
        grow = ease(window(share, 0.0, 0.5))
        bars = [
            ("original studies", 0.403 / 0.45 * grow, BLUE, "r = .40"),
            ("replications", 0.197 / 0.45 * grow, YELLOW, "r = .20"),
        ]
        draw_value_bars(surface, stage, bars, 25, 40, 50, 28)
        stage.text(surface, "Average effect size", 50, 6, 3.4, ui.WHITE)


LAB_RESULTS = ["n.s."] * 13 + ["p<.05"] + ["n.s."] * 6


class FileDrawerAnimation(InsightAnimation):
    """Publication bias: chance hits get published, null results stay hidden."""

    title = "The file drawer"
    beats = (
        Beat("Twenty labs test an effect that does not exist.", 4.5, "labs"),
        Beat("By chance alone, about 1 in 20 finds 'p < .05'.", 4.5, "lucky"),
        Beat("Only that one is published - the rest go in the drawer.", 5.5, "drawer"),
        Beat("Readers only see the lucky hit - and believe it.", 4.5, "readers"),
    )
    thumbnail_beat = 2
    background = (50, 34, 30)

    def paper_position(self, index):
        return (12 + (index % 10) * 7, 14 + (index // 10) * 11)

    def labs(self, surface, stage, share, clock):
        shown = int(20 * ease(window(share, 0.0, 0.7))) + 1
        for index in range(min(20, shown)):
            draw_paper(surface, stage, *self.paper_position(index))
        stage.text(surface, "true effect: none", 50, 44, 3.4, ui.SOFT_BLUE)

    def lucky(self, surface, stage, share, clock):
        for index, result in enumerate(LAB_RESULTS):
            lucky = result != "n.s."
            pop = 1 + 0.4 * math.sin(window(share, 0.2, 0.5) * math.pi) if lucky else 1
            draw_paper(surface, stage, *self.paper_position(index), color=YELLOW if lucky and share > 0.2 else PAPER, label=result, label_color=ui.INK if lucky else GREY, size=pop)

    def drawer(self, surface, stage, share, clock):
        open_share = ease(window(share, 0.0, 0.2)) * (1 - ease(window(share, 0.8, 1.0)))
        draw_cabinet(surface, stage, 18, 46, open_share)
        journal = pygame.Rect(0, 0, stage.size(16), stage.size(22))
        journal.midbottom = stage.point(80, 44)
        pygame.draw.rect(surface, (180, 60, 60), journal, border_radius=int(stage.size(1)))
        stage.text(surface, "JOURNAL", 80, 26, 2.6, ui.WHITE)
        for index, result in enumerate(LAB_RESULTS):
            start = self.paper_position(index)
            if result == "n.s.":
                travel = ease(window(share, 0.15 + index * 0.025, 0.45 + index * 0.025))
                if travel < 1:
                    draw_paper(surface, stage, *lerp(start, (14, 24), travel), label=result, label_color=GREY, size=1 - 0.5 * travel)
            else:
                travel = ease(window(share, 0.1, 0.4))
                draw_paper(surface, stage, *lerp(start, (80, 34), travel), color=YELLOW, label=result)

    def readers(self, surface, stage, share, clock):
        draw_cabinet(surface, stage, 18, 46, 0.0)
        stage.text(surface, "19 hidden", 18, 18, 2.8, GREY)
        draw_paper(surface, stage, 56, 22, color=YELLOW, label="p<.05", size=1.6)
        for index in range(3):
            draw_character(surface, stage, CHARACTERS[index], 70 + index * 9, 46, 11, -1, clock + index)
        if share > 0.4:
            draw_bubble(surface, stage, 79, 32, 20, ui.WHITE, "It works!")


class OpenPracticesAnimation(InsightAnimation):
    """The Open Science toolbox: preregistration, Registered Reports, open data and replications."""

    title = "The Open Science toolbox"
    beats = (
        Beat("Preregister: fix hypotheses and analyses BEFORE collecting data.", 5.5, "prereg"),
        Beat("Registered Report: the journal accepts the plan, whatever the result.", 5.5, "registered"),
        Beat("Share data, materials and analysis scripts, so anyone can check.", 5.0, "share"),
        Beat("Replicate - and publish null results, too.", 5.0, "publish"),
    )
    thumbnail_beat = 0

    def registered(self, surface, stage, share, clock):
        draw_paper(surface, stage, 26, 24, label="PLAN", size=2.0)
        journal = pygame.Rect(0, 0, stage.size(20), stage.size(24))
        journal.center = stage.point(72, 24)
        pygame.draw.rect(surface, (60, 140, 90), journal, border_radius=int(stage.size(1)))
        stage.text(surface, "JOURNAL", 72, 16, 2.6, ui.WHITE)
        if share > 0.3:
            stamp = lerp(72, 30, ease(window(share, 0.3, 0.6)))
            stage.text(surface, "ACCEPTED", stamp, 26, 3.4, GREEN)
        if share > 0.7:
            stage.text(surface, "no data yet - results can't decide it", 50, 45, 2.8, YELLOW)
    background = (24, 60, 70)

    def prereg(self, surface, stage, share, clock):
        draw_paper(surface, stage, 26, 24, label="PLAN", size=2.0)
        lock_x = lerp(70, 34, ease(window(share, 0.2, 0.55)))
        body = pygame.Rect(0, 0, stage.size(7), stage.size(6))
        body.center = stage.point(lock_x, 29)
        pygame.draw.arc(surface, (200, 200, 210), pygame.Rect(body.left + stage.size(1), body.top - stage.size(4), stage.size(5), stage.size(7)), 0, math.pi, max(2, int(stage.size(0.8))))
        pygame.draw.rect(surface, YELLOW, body, border_radius=int(stage.size(1)))
        if share > 0.6:
            stage.text(surface, "timestamp: before the data", 62, 14, 3, GREEN)
            for index in range(5):
                draw_paper(surface, stage, 56 + index * 6, 30 + math.sin(clock * 3 + index) * 0.6, label="data", size=0.8)

    def share(self, surface, stage, share, clock):
        box = pygame.Rect(0, 0, stage.size(20), stage.size(12))
        box.midbottom = stage.point(50, 42)
        pygame.draw.rect(surface, graphics.WOOD, box, border_radius=int(stage.size(1)))
        stage.text(surface, "OPEN DATA", 50, 37, 2.6, ui.WHITE)
        for index in range(4):
            fly = ease(window(share, 0.1 + index * 0.12, 0.5 + index * 0.12))
            target = (14 + index * 24, 12)
            draw_paper(surface, stage, *lerp((50, 32), target, fly), label="csv")
        for index in range(4):
            draw_character(surface, stage, CHARACTERS[index % 3], 14 + index * 24, 30, 9, 1, clock + index)
        if share > 0.75:
            stage.text(surface, "Anyone can check!", 50, 46, 3, GREEN)

    def publish(self, surface, stage, share, clock):
        draw_cabinet(surface, stage, 18, 46, ease(window(share, 0.0, 0.3)))
        journal = pygame.Rect(0, 0, stage.size(22), stage.size(26))
        journal.midbottom = stage.point(78, 46)
        pygame.draw.rect(surface, (60, 140, 90), journal, border_radius=int(stage.size(1)))
        stage.text(surface, "ALL RESULTS", 78, 24, 2.6, ui.WHITE)
        for index in range(5):
            fly = ease(window(share, 0.25 + index * 0.1, 0.55 + index * 0.1))
            label = "p<.05" if index == 2 else "n.s."
            draw_paper(surface, stage, *lerp((20, 26), (70 + (index % 3) * 6, 32 + (index // 3) * 7), fly), color=YELLOW if index == 2 else PAPER, label=label, size=0.8)


class QrpsAnimation(insight_animations.QrpAnimation):
    """Questionable research practices: what they are and why they happen."""

    title = "Questionable research practices"
    beats = (
        Beat("p-hacking: test again and again until something is 'significant'.", 8.0, "p_hacking"),
        Beat("HARKing: write the hypothesis AFTER seeing the results.", 7.0, "harking"),
        Beat("Cherry-picking: report only the results that look good.", 5.5, "cherry"),
        Beat("Rarely evil - mostly pressure to publish 'exciting' results.", 5.5, "pressure"),
    )
    thumbnail_beat = 2
    background = (50, 30, 40)

    def cherry(self, surface, stage, share, clock):
        points = ((20, 30), (28, 18), (36, 34), (44, 22), (52, 38), (60, 16), (68, 28), (76, 20))
        keep = {1, 5, 7}
        for index, (x, y) in enumerate(points):
            hidden = index not in keep and share > 0.4
            stage.circle(surface, GREY if hidden else RED, x, y, 1.8)
            if hidden and share > 0.6:
                stage.line(surface, ui.WHITE, (x - 2, y - 2), (x + 2, y + 2), 0.4)
        if share > 0.7:
            stage.text(surface, "'Look, a clear effect!'", 50, 44, 3.2, YELLOW)

    def pressure(self, surface, stage, share, clock):
        draw_character(surface, stage, self.character, 30, 46, 14, 1, clock)
        journal = pygame.Rect(0, 0, stage.size(18), stage.size(22))
        journal.center = stage.point(72, 24)
        pygame.draw.rect(surface, (180, 60, 60), journal, border_radius=int(stage.size(1)))
        stage.text(surface, "JOURNAL", 72, 18, 2.6, ui.WHITE)
        stage.text(surface, "only p<.05!", 72, 28, 2.6, YELLOW)
        bob = math.sin(clock * 4) * 1
        draw_bubble(surface, stage, 34, 26 + bob, 26, ui.WHITE, "Publish or perish ...")


class MapAnimation(InsightAnimation):
    """
    The big picture before a quiz: four insights connected to one idea.

    Subclasses set ``nodes`` (insight key, label, position), ``center`` and
    the four beats.
    """

    nodes = ()
    center = ""
    thumbnail_beat = 3

    def __init__(self, character=CHARACTERS[0]):
        super().__init__(character)
        self.parts = {key: insight_animations.ANIMATIONS[key](character) for key, _, _ in self.nodes}

    def draw_map(self, surface, stage, n_nodes, share, clock):
        for index, (key, label, (x, y)) in enumerate(self.nodes[:n_nodes]):
            grow = 1.0 if index < n_nodes - 1 else ease(window(share, 0.0, 0.4))
            stage.line(surface, YELLOW, (50, 25), lerp((50, 25), (x, y), grow), 0.6)
            if grow >= 1:
                thumb = pygame.Rect(0, 0, stage.size(26), stage.size(13))
                thumb.center = stage.point(x, y - 1)
                self.parts[key].draw_thumbnail(surface, thumb, clock)
                pygame.draw.rect(surface, YELLOW, thumb, max(1, int(stage.size(0.3))), border_radius=4)
                stage.text(surface, label, x, y + 7.3, 2.6, ui.WHITE)
        stage.circle(surface, (60, 70, 140), 50, 25, 9)
        stage.circle(surface, YELLOW, 50, 25, 9, 0.4)
        for line_index, line in enumerate(self.center.split("\n")):
            stage.text(surface, line, 50, 25 + (line_index - (self.center.count("\n")) / 2) * 3, 2.4, YELLOW)

    def node_1(self, surface, stage, share, clock):
        self.draw_map(surface, stage, 1, share, clock)

    def node_2(self, surface, stage, share, clock):
        self.draw_map(surface, stage, 2, share, clock)

    def node_3(self, surface, stage, share, clock):
        self.draw_map(surface, stage, 3, share, clock)

    def node_4(self, surface, stage, share, clock):
        self.draw_map(surface, stage, 4, share, clock)


class PrologueMapAnimation(MapAnimation):
    """How Open Science fits together."""

    title = "The big picture"
    center = "OPEN\nSCIENCE"
    nodes = (
        ("qrps", "questionable practices", (20, 11)),
        ("reproducibility", "many findings failed", (80, 11)),
        ("file_drawer", "null results hidden", (20, 39)),
        ("open_practices", "the toolbox", (80, 39)),
    )
    beats = (
        Beat("QUESTIONABLE PRACTICES inflate results ...", 3.5, "node_1"),
        Beat("... so many findings did NOT replicate ...", 3.5, "node_2"),
        Beat("... and null results stayed HIDDEN.", 3.5, "node_3"),
        Beat("OPEN SCIENCE makes every step checkable.", 4.5, "node_4"),
    )


# ---------------------------------------------------------------------------
# Level 2: Response inhibition
# ---------------------------------------------------------------------------


class InhibitionAnimation(InsightAnimation):
    """Running towards an edge and stopping just in time."""

    title = "Stop!"
    beats = (
        Beat("The hero runs full speed towards the edge ...", 4.0, "run"),
        Beat("STOP! The brain cancels the running action.", 4.0, "brake"),
        Beat("Stopping in time: that is response inhibition.", 4.5, "safe"),
    )
    thumbnail_beat = 1
    background = (40, 70, 110)
    EDGE = 72

    def scene(self, surface, stage):
        pygame.draw.rect(surface, (220, 236, 250), pygame.Rect(stage.point(0, 40), (stage.size(self.EDGE), stage.size(10) + 2)))
        stage.text(surface, "!", self.EDGE + 8, 46, 4, RED)

    def run(self, surface, stage, share, clock):
        self.scene(surface, stage)
        draw_character(surface, stage, self.character, lerp(8, 50, share), 40, 13, 1, clock, moving=True)

    def brake(self, surface, stage, share, clock):
        self.scene(surface, stage)
        slide = ease(window(share, 0.15, 0.8))
        x = lerp(50, 66, slide)
        draw_character(surface, stage, self.character, x, 40, 13, 1, clock, moving=slide < 1)
        if share > 0.1:
            draw_stop_sign(surface, stage.point(30, 16), int(stage.size(7)))
        for index in range(4):
            stage.circle(surface, ui.WHITE, x - 4 - index * 3, 39 - index * 0.5, max(0.3, 1.2 - index * 0.25) * (1 - slide))

    def safe(self, surface, stage, share, clock):
        self.scene(surface, stage)
        wobble = math.sin(clock * 10) * 1.5 * (1 - ease(window(share, 0.0, 0.5)))
        draw_character(surface, stage, self.character, 66 + wobble, 40, 13, 1, clock)
        if share > 0.4:
            stage.text(surface, "Phew!", 66, 20, 4, YELLOW)


def draw_fruit(surface, stage, x, y, color, size=3.0):
    """Draw a round fruit with a leaf."""
    stage.circle(surface, color, x, y, size)
    stage.circle(surface, ui.WHITE, x - size * 0.35, y - size * 0.35, size * 0.25)
    pygame.draw.ellipse(surface, (60, 160, 70), pygame.Rect(stage.point(x, y - size * 1.4), (stage.size(size * 0.9), stage.size(size * 0.5))))


FRUIT_SEQUENCE = ("go", "go", "go", "go", "nogo")


class GoNoGoAnimation(InsightAnimation):
    """Grabbing frequent green fruit and holding back on a rare red one."""

    title = "Go / No-Go"
    beats = (
        Beat("GREEN fruit: grab it! Most fruit is green ...", 5.0, "go"),
        Beat("RED fruit: hands off!", 4.0, "nogo"),
        Beat("After many GOs, holding back is hard: oops!", 5.0, "oops"),
    )
    thumbnail_beat = 2
    background = (40, 60, 50)

    def belt(self, surface, stage, clock, colors, grab_index=None, share=0.0):
        pygame.draw.rect(surface, (60, 60, 70), pygame.Rect(stage.point(0, 36), (stage.size(100), stage.size(4))))
        speed = 12
        for index, color in enumerate(colors):
            x = 100 - ((clock * speed + index * 16) % 110)
            if grab_index == index and 40 < x < 60:
                continue
            draw_fruit(surface, stage, x, 33, color)

    def go(self, surface, stage, share, clock):
        punching = (clock % 1.33) < 0.25
        self.belt(surface, stage, clock, [GREEN] * 7)
        draw_character(surface, stage, self.character, 50, 26, 12, 1, clock, punching=punching)
        stage.text(surface, "GO!", 50, 8, 4, GREEN)

    def nogo(self, surface, stage, share, clock):
        self.belt(surface, stage, clock, [GREEN, GREEN, RED, GREEN, GREEN, GREEN, GREEN])
        draw_character(surface, stage, self.character, 50, 26, 12, 1, clock)
        stage.text(surface, "NO-GO: hold still!", 50, 8, 4, RED)
        jitter = math.sin(clock * 30) * 0.6
        stage.text(surface, "...", 56 + jitter, 15, 3, ui.WHITE)

    def oops(self, surface, stage, share, clock):
        ground(surface, stage, (40, 60, 50), 36)
        for index in range(5):
            kind = FRUIT_SEQUENCE[index]
            x = 14 + index * 15
            arrived = share > index * 0.16
            if arrived:
                draw_fruit(surface, stage, x, 30, GREEN if kind == "go" else RED)
                draw_check(surface, stage, x, 20, 2, ok=kind == "go")
        draw_character(surface, stage, self.character, lerp(14, 74, min(1.0, share * 1.2)), 46, 10, 1, clock, punching=True)
        if share > 0.75:
            stage.text(surface, "Commission error!", 74, 10, 3.2, RED)


class HorseRaceAnimation(InsightAnimation):
    """The horse-race model of the stop-signal task (Logan & Cowan, 1984)."""

    title = "The race in your head"
    beats = (
        Beat("A car appears: the GO runner starts the race.", 4.0, "go_starts"),
        Beat("STOP sign: the STOP runner starts a bit later.", 4.0, "stop_starts"),
        Beat("STOP finishes first: the action is cancelled!", 4.5, "stop_wins"),
        Beat("Sign too late: GO wins and you act anyway.", 4.5, "go_wins"),
    )
    thumbnail_beat = 2
    background = (30, 26, 60)
    LANES = {"go": 18, "stop": 32}
    FINISH = 84
    GO_LOOK = None

    def track(self, surface, stage):
        for lane, y in self.LANES.items():
            pygame.draw.rect(surface, (60, 56, 100), pygame.Rect(stage.point(8, y - 5), (stage.size(80), stage.size(10))), border_radius=6)
            stage.text(surface, lane.upper(), 4, y, 3, BLUE if lane == "go" else RED)
        stage.line(surface, ui.WHITE, (self.FINISH, 10), (self.FINISH, 40), 0.6)
        stage.text(surface, "FINISH", self.FINISH, 44, 2.6, ui.WHITE)

    def runner(self, surface, stage, lane, progress, clock):
        look = CHARACTERS[0] if lane == "go" else CHARACTERS[1]
        x = lerp(12, self.FINISH, min(1.0, progress))
        draw_character(surface, stage, look, x, self.LANES[lane] + 5, 9, 1, clock, moving=progress < 1)

    def race(self, surface, stage, share, clock, stop_delay, stop_speed=1.6, show_stop=True):
        self.track(surface, stage)
        go = share * 1.0
        stop = max(0.0, share - stop_delay) * stop_speed
        self.runner(surface, stage, "go", go, clock)
        if show_stop:
            if share >= stop_delay:
                draw_stop_sign(surface, stage.point(lerp(12, 84, stop_delay), 6), int(stage.size(2.6)))
            self.runner(surface, stage, "stop", stop if share >= stop_delay else 0, clock)
        return go, stop

    def go_starts(self, surface, stage, share, clock):
        draw_race_car(surface, stage.point(50, 6), "right", int(stage.size(10)))
        self.race(surface, stage, share * 0.45, clock, 1.0, show_stop=False)

    def stop_starts(self, surface, stage, share, clock):
        self.race(surface, stage, 0.45 + share * 0.15, clock, 0.25)

    def stop_wins(self, surface, stage, share, clock):
        go, stop = self.race(surface, stage, 0.6 + share * 0.4, clock, 0.25)
        if stop >= 1:
            stage.text(surface, "Action cancelled!", 50, 46, 3.4, GREEN)

    def go_wins(self, surface, stage, share, clock):
        go, stop = self.race(surface, stage, share, clock, 0.55)
        if go >= 1:
            stage.text(surface, "Too late - you acted!", 50, 46, 3.4, RED)


STROOP_WORDS = (("RED", RED), ("BLUE", BLUE), ("GREEN", GREEN))


class StroopAnimation(InsightAnimation):
    """Naming the ink colour of colour words (Stroop, 1935)."""

    title = "The Stroop effect"
    beats = (
        Beat("Say the INK colour: easy when word and ink match.", 4.5, "match"),
        Beat("Now they clash: the word says RED, the ink is blue.", 5.0, "clash"),
        Beat("Reading is automatic - you have to hold it back.", 5.0, "compare"),
    )
    thumbnail_beat = 1
    background = (30, 30, 40)

    def words(self, surface, stage, pairs):
        for index, (word, color) in enumerate(pairs):
            stage.text(surface, word, 22 + index * 28, 18, 7, color)

    def match(self, surface, stage, share, clock):
        self.words(surface, stage, STROOP_WORDS)
        draw_character(surface, stage, self.character, 50, 46, 12, 1, clock)
        if share > 0.3:
            draw_bubble(surface, stage, 54, 32, 22, ui.WHITE, "red, blue, green!")

    def clash(self, surface, stage, share, clock):
        self.words(surface, stage, (("RED", BLUE), ("GREEN", RED), ("BLUE", GREEN)))
        draw_character(surface, stage, self.character, 50, 46, 12, 1, clock)
        text = "re... blue!" if share > 0.55 else "re..."
        draw_bubble(surface, stage, 54, 32, 20, ui.WHITE, text)
        if share < 0.55:
            stage.text(surface, "?", 44, 30, 4, YELLOW)

    def compare(self, surface, stage, share, clock):
        grow = ease(window(share, 0.0, 0.5))
        bars = [("word = ink", 0.45 * grow, GREEN, "fast"), ("word clashes", 0.85 * grow, RED, "slow")]
        draw_value_bars(surface, stage, bars, 20, 40, 60, 26)
        stage.text(surface, "Time to name the ink", 50, 6, 3.2, ui.WHITE)


class EgoDepletionAnimation(InsightAnimation):
    """A famous effect that did not replicate (Hagger et al., 2016)."""

    title = "Myth check: ego depletion"
    beats = (
        Beat("1998: resisting cookies seemed to drain a willpower battery.", 5.0, "battery"),
        Beat("2016: 23 labs tested it again, with 2,141 people.", 5.0, "labs"),
        Beat("Result: an effect close to zero. It did not replicate.", 5.5, "result"),
    )
    thumbnail_beat = 2
    background = (50, 40, 60)

    def battery(self, surface, stage, share, clock):
        for index in range(3):
            x = 16 + index * 7
            stage.circle(surface, (200, 150, 90), x, 30, 3)
            for dot in range(3):
                stage.circle(surface, (90, 60, 40), x - 1 + dot, 29 + (dot % 2), 0.5)
        draw_character(surface, stage, self.character, 40, 44, 13, 1, clock)
        stage.text(surface, "no!", 44, 22, 3, ui.WHITE)
        body = pygame.Rect(stage.point(62, 16), (stage.size(24), stage.size(14)))
        pygame.draw.rect(surface, ui.WHITE, body, max(1, int(stage.size(0.5))), border_radius=int(stage.size(1)))
        pygame.draw.rect(surface, ui.WHITE, pygame.Rect(stage.point(86, 20), (stage.size(2), stage.size(6))))
        level = 1 - ease(window(share, 0.2, 0.9)) * 0.8
        fill = pygame.Rect(stage.point(63, 17), (stage.size(22 * level), stage.size(12)))
        pygame.draw.rect(surface, GREEN if level > 0.4 else RED, fill)
        stage.text(surface, "willpower?", 74, 36, 3, ui.SOFT_BLUE)

    def labs(self, surface, stage, share, clock):
        shown = int(23 * ease(window(share, 0.0, 0.8))) + 1
        for index in range(min(23, shown)):
            x, y = 12 + (index % 8) * 11, 10 + (index // 8) * 12
            building = pygame.Rect(0, 0, stage.size(7), stage.size(6))
            building.midbottom = stage.point(x, y + 4)
            pygame.draw.rect(surface, (120, 130, 170), building)
            pygame.draw.polygon(surface, (90, 100, 140), [stage.point(x - 4.5, y - 2), stage.point(x, y - 5), stage.point(x + 4.5, y - 2)])
        stage.text(surface, "23 labs, 2,141 people, one shared plan", 50, 46, 3, ui.WHITE)

    def result(self, surface, stage, share, clock):
        stage.line(surface, ui.WHITE, (15, 30), (85, 30), 0.3)
        stage.text(surface, "no effect", 87, 30, 2.4, ui.WHITE, "midleft")
        for x in range(20, 81, 10):
            stage.line(surface, GREY, (x, 29), (x, 31), 0.3)
        drop = ease(window(share, 0.1, 0.5))
        center = lerp(70, 51.5, drop)
        stage.line(surface, YELLOW, (center - 6, 30), (center + 6, 30), 0.8)
        stage.circle(surface, YELLOW, center, 30, 1.6)
        stage.text(surface, "d = 0.04" if drop >= 1 else "?", center, 22, 3.4, YELLOW)
        if share > 0.6:
            draw_check(surface, stage, 50, 42, 2.4, ok=False)
            stage.text(surface, "MYTH", 58, 42, 3.4, RED, "midleft")


def draw_brain(surface, stage, x, y, size, glow=0.0, clock=0.0):
    """Draw a brain seen from the side (front to the left) with its frontal 'brake' area."""
    rect = pygame.Rect(0, 0, stage.size(size * 1.4), stage.size(size))
    rect.center = stage.point(x, y)
    pygame.draw.ellipse(surface, (240, 170, 180), rect)
    pygame.draw.ellipse(surface, (190, 110, 130), rect, max(1, int(stage.size(0.5))))
    for index in range(5):
        fold = pygame.Rect(0, 0, rect.width * 0.5, rect.height * 0.35)
        fold.center = (rect.left + rect.width * (0.25 + index * 0.13), rect.top + rect.height * (0.35 + (index % 2) * 0.25))
        pygame.draw.arc(surface, (190, 110, 130), fold, 0.3, 2.8, max(1, int(stage.size(0.4))))
    brake = (rect.left + rect.width * 0.18, rect.top + rect.height * 0.62)
    if glow:
        stage.translucent(surface, lambda layer: pygame.draw.circle(layer, YELLOW, brake, stage.size(size * 0.22)), int(200 * glow))
    pygame.draw.circle(surface, RED, brake, stage.size(size * 0.08))
    return brake


class BrainBrakeAnimation(InsightAnimation):
    """Where stopping happens in the brain, and why it matters in daily life."""

    title = "The brain's brake"
    beats = (
        Beat("A network in the right frontal lobe works like a brake.", 5.0, "brake"),
        Beat("Stop signal: the brake cancels the running movement.", 5.0, "stop"),
        Beat("In ADHD the brake is slower on average: a longer SSRT.", 5.5, "adhd"),
    )
    thumbnail_beat = 1
    background = (30, 30, 60)

    def brake(self, surface, stage, share, clock):
        brake = draw_brain(surface, stage, 50, 22, 30, glow=0.5 + 0.5 * math.sin(clock * 4), clock=clock)
        stage.text(surface, "right inferior frontal cortex", 50, 44, 3, YELLOW)
        pygame.draw.line(surface, YELLOW, brake, stage.point(36, 40), max(1, int(stage.size(0.3))))

    def stop(self, surface, stage, share, clock):
        brake = draw_brain(surface, stage, 26, 18, 22, glow=1.0 if share > 0.25 else 0.0, clock=clock)
        ground(surface, stage, (60, 60, 100), 44)
        slide = ease(window(share, 0.25, 0.7))
        x = lerp(50, 70, slide)
        draw_character(surface, stage, self.character, x, 44, 12, 1, clock, moving=slide < 1)
        if share > 0.2:
            draw_stop_sign(surface, stage.point(84, 18), int(stage.size(4)))
            travel = min(1.0, window(share, 0.2, 0.45))
            dot = lerp(stage.point(26, 22), stage.point(x, 34), travel)
            pygame.draw.circle(surface, YELLOW, dot, stage.size(1.2))

    def adhd(self, surface, stage, share, clock):
        grow = ease(window(share, 0.0, 0.5))
        bars = [("on average", 0.5 * grow, BLUE, "SSRT"), ("ADHD (average)", 0.72 * grow, ORANGE, "longer")]
        draw_value_bars(surface, stage, bars, 22, 40, 56, 30)
        stage.text(surface, "How long stopping takes", 50, 5, 3.2, ui.WHITE)


class InhibitionMapAnimation(MapAnimation):
    """How response inhibition fits together."""

    title = "The big picture"
    center = "STOPPING"
    nodes = (
        ("inhibition", "cancel an action", (20, 11)),
        ("go_nogo", "habit pulls you", (80, 11)),
        ("horse_race", "GO races STOP", (20, 39)),
        ("stroop", "hold back reading", (80, 39)),
    )
    beats = (
        Beat("Inhibition CANCELS actions that are already running ...", 3.5, "node_1"),
        Beat("... habits make holding back HARD ...", 3.5, "node_2"),
        Beat("... going and stopping RACE each other ...", 3.5, "node_3"),
        Beat("... and even automatic READING must be held back.", 4.5, "node_4"),
    )


class StopSkillAnimation(InsightAnimation):
    """The skill Level 2 rewards: a stop wave that freezes enemies."""

    title = "New skill: Stop Signal"
    beats = (
        Beat("You learned to stop. Now press R ...", 3.5, "press"),
        Beat("... and a STOP wave freezes everything nearby!", 4.5, "wave"),
    )
    background = (40, 30, 70)

    def press(self, surface, stage, share, clock):
        ground(surface, stage, (60, 52, 100))
        draw_character(surface, stage, self.character, 30, 42, 14, 1, clock)
        x = lerp(90, 60, share)
        draw_scaled(surface, stage, lambda image: graphics.draw_distractor(image, 5, 14, clock), (50, 50), x, 42, 9)
        stage.text(surface, "R", 30, 16, 6, YELLOW)

    def wave(self, surface, stage, share, clock):
        ground(surface, stage, (60, 52, 100))
        draw_character(surface, stage, self.character, 30, 42, 14, 1, clock)
        radius = 60 * ease(window(share, 0.0, 0.5))
        if share < 0.6:
            stage.circle(surface, (255, 120, 120), 30, 35, max(1, radius), 0.8)
        draw_scaled(surface, stage, lambda image: graphics.draw_distractor(image, 5, 14, 0.0), (50, 50), 60, 42, 9)
        if share > 0.3:
            draw_stop_sign(surface, stage.point(60, 22), int(stage.size(3.5)))
            stage.text(surface, "frozen!", 72, 26, 3, (170, 220, 255))


# ---------------------------------------------------------------------------
# Level 3: Executive control
# ---------------------------------------------------------------------------

FUNCTIONS = (("WORKING MEMORY", GREEN, 22), ("FLEXIBILITY", BLUE, 50), ("INHIBITION", RED, 78))


class ExecutiveAnimation(InsightAnimation):
    """The control room of the mind and its three core functions."""

    title = "The control room"
    beats = (
        Beat("Executive functions are the mind's control room.", 4.5, "room"),
        Beat("WORKING MEMORY holds and updates what you need now ...", 4.5, "updating"),
        Beat("... FLEXIBILITY switches rules, INHIBITION stops wrong moves.", 5.0, "others"),
        Beat("Related, yet separate - and planning builds on them.", 5.0, "venn"),
    )
    thumbnail_beat = 3
    background = (24, 30, 50)

    def panel(self, surface, stage, lit, clock):
        desk = pygame.Rect(stage.point(8, 30), (stage.size(84), stage.size(12)))
        pygame.draw.rect(surface, (70, 76, 100), desk, border_radius=int(stage.size(1)))
        for index, (name, color, x) in enumerate(FUNCTIONS):
            on = index in lit
            stage.circle(surface, color if on else GREY, x, 20, 6)
            angle = clock * 3 + index if on else 0.5
            stage.line(surface, ui.INK, (x, 20), (x + math.cos(angle) * 5, 20 + math.sin(angle) * 5), 0.6)
            stage.text(surface, name, x, 36, 2.8, color if on else GREY)

    def room(self, surface, stage, share, clock):
        self.panel(surface, stage, {int(clock * 2) % 3}, clock)
        draw_character(surface, stage, self.character, 50, 50, 10, 1, clock)

    def updating(self, surface, stage, share, clock):
        self.panel(surface, stage, {0}, clock)
        slots = ("K", "B") if share < 0.5 else ("B", "D")
        for index, letter in enumerate(slots):
            stage.text(surface, letter, 16 + index * 8, 8, 4, GREEN)
        if share >= 0.5:
            stage.text(surface, "K", 10 - 20 * window(share, 0.5, 1.0), 8, 4, GREY)

    def others(self, surface, stage, share, clock):
        lit = {1} if share < 0.5 else {1, 2}
        self.panel(surface, stage, lit, clock)
        if share >= 0.5:
            draw_stop_sign(surface, stage.point(78, 8), int(stage.size(3)))
        stage.text(surface, "colour -> shape", 50, 8, 3, BLUE)

    def venn(self, surface, stage, share, clock):
        spread = lerp(4, 9, ease(window(share, 0.0, 0.5)))
        for index, (name, color, _) in enumerate(FUNCTIONS):
            angle = -math.pi / 2 + index * 2 * math.pi / 3
            x, y = 50 + math.cos(angle) * spread * 1.4, 26 + math.sin(angle) * spread
            stage.translucent(surface, lambda layer, x=x, y=y, color=color: pygame.draw.circle(layer, color, stage.point(x, y), stage.size(13)), 110)
            stage.text(surface, name, 50 + math.cos(angle) * 22, 26 + math.sin(angle) * 17, 2.6, color)
        stage.text(surface, "common core", 50, 27, 2.4, ui.WHITE)


NBACK_LETTERS = ("K", "B", "K", "D", "B", "D", "F")


class UpdatingAnimation(InsightAnimation):
    """The n-back task and the updating of working memory."""

    title = "Working memory"
    beats = (
        Beat("Working memory: a small whiteboard with room for about four things.", 5.0, "workspace"),
        Beat("The n-back task: letters arrive one by one ...", 4.5, "arrive"),
        Beat("Same as two letters back? That is a match!", 4.5, "match"),
        Beat("Each new letter pushes the oldest out of memory.", 5.5, "update"),
    )
    thumbnail_beat = 1
    background = (20, 40, 34)

    def tile(self, surface, stage, x, y, letter, color=(120, 255, 160), border=None):
        rect = pygame.Rect(0, 0, stage.size(9), stage.size(9))
        rect.center = stage.point(x, y)
        pygame.draw.rect(surface, (20, 30, 26), rect, border_radius=int(stage.size(1)))
        if border:
            pygame.draw.rect(surface, border, rect, max(2, int(stage.size(0.6))), border_radius=int(stage.size(1)))
        stage.text(surface, letter, x, y, 6, color)

    def workspace(self, surface, stage, share, clock):
        board = pygame.Rect(stage.point(30, 8), (stage.size(56), stage.size(30)))
        pygame.draw.rect(surface, (235, 240, 245), board, border_radius=int(stage.size(1.5)))
        pygame.draw.rect(surface, GREY, board, max(1, int(stage.size(0.5))), border_radius=int(stage.size(1.5)))
        items = ("milk", "7 3 9", "Room B", "call Mia", "keys!")
        shown = min(len(items), int(share * 6) + 1)
        for index, item in enumerate(items[:shown]):
            x, y = 40 + (index % 2) * 24, 15 + (index // 2) * 8
            falls = index == 4
            stage.text(surface, item, x, y + (12 * ease(window(share, 0.85, 1.0)) if falls else 0), 3.2, RED if falls else ui.INK)
        if shown == len(items):
            stage.text(surface, "full - the fifth falls off!", 58, 44, 3, RED)
        draw_character(surface, stage, self.character, 16, 46, 14, 1, clock)

    def arrive(self, surface, stage, share, clock):
        shown = min(3, int(share * 3.5) + 1)
        for index in range(shown):
            self.tile(surface, stage, 30 + index * 20, 24, NBACK_LETTERS[index])

    def match(self, surface, stage, share, clock):
        for index in range(3):
            self.tile(surface, stage, 30 + index * 20, 24, NBACK_LETTERS[index], border=GREEN if index != 1 and share > 0.3 else None)
        if share > 0.3:
            pygame.draw.arc(surface, GREEN, pygame.Rect(stage.point(30, 10), (stage.size(40), stage.size(16))), 0.2, math.pi - 0.2, max(2, int(stage.size(0.6))))
            stage.text(surface, "MATCH - press SPACE!", 50, 42, 3.6, GREEN)

    def update(self, surface, stage, share, clock):
        step = min(len(NBACK_LETTERS) - 2, int(share * 4) + 1)
        stage.text(surface, "in memory:", 20, 10, 3, ui.SOFT_BLUE)
        for slot in range(2):
            self.tile(surface, stage, 18 + slot * 11, 24, NBACK_LETTERS[step - 1 + slot])
        self.tile(surface, stage, 70, 24, NBACK_LETTERS[step + 1], border=YELLOW)
        stage.text(surface, "new", 70, 36, 3, YELLOW)
        if step >= 2:
            stage.text(surface, NBACK_LETTERS[step - 2], 6, 24, 5, GREY)
            stage.text(surface, "out", 6, 32, 2.4, GREY)


PLAN_START = (("red", "green"), ("blue",), ())
PLAN_STEPS = (PLAN_START, (("red",), ("blue", "green"), ()), (("red", "green"), ("blue",), ()))


class PlanningAnimation(InsightAnimation):
    """Planning in the Tower of London (Shallice, 1982)."""

    title = "Planning ahead"
    beats = (
        Beat("Goal: rebuild the picture in as few moves as possible.", 5.0, "goal"),
        Beat("Good planners think through the moves first ...", 5.0, "think"),
        Beat("... then solve it without a wasted move.", 5.0, "solve"),
    )
    thumbnail_beat = 1
    background = (40, 30, 70)
    PATH = (
        (("red", "green"), ("blue",), ()),
        (("red",), ("blue",), ("green",)),
        (("red", "blue"), (), ("green",)),
        (("red", "blue", "green"), (), ()),
    )

    def tower(self, surface, stage, state, x, y, size):
        draw_tower(surface, state, stage.point(x, y), scale=stage.size(size) / 720)

    def goal(self, surface, stage, share, clock):
        self.tower(surface, stage, self.PATH[0], 27, 38, 50)
        stage.text(surface, "START", 27, 44, 3, ui.WHITE)
        self.tower(surface, stage, self.PATH[-1], 77, 38, 40)
        stage.text(surface, "GOAL", 77, 44, 3, YELLOW)

    def think(self, surface, stage, share, clock):
        self.tower(surface, stage, self.PATH[0], 26, 40, 48)
        draw_character(surface, stage, self.character, 62, 46, 13, -1, clock)
        bubble = pygame.Rect(stage.point(56, 3), (stage.size(40), stage.size(22)))
        pygame.draw.ellipse(surface, ui.WHITE, bubble)
        step = min(len(self.PATH) - 1, int(share * 4))
        self.tower(surface, stage, self.PATH[step], 76, 21, 22)
        stage.text(surface, f"move {step} ?", 76, 24, 2.4, ui.INK)

    def solve(self, surface, stage, share, clock):
        step = min(len(self.PATH) - 1, int(share * 4))
        self.tower(surface, stage, self.PATH[step], 40, 40, 60)
        stage.text(surface, f"moves: {step}", 80, 18, 4, ui.WHITE)
        if step == len(self.PATH) - 1:
            stage.text(surface, "best possible!", 80, 26, 3.4, GREEN)


class SwitchingAnimation(InsightAnimation):
    """Task switching and its cost (Rogers & Monsell, 1995)."""

    title = "Switch cost"
    beats = (
        Beat("Task A: is the number odd or even?", 4.0, "task_a"),
        Beat("Task B: is it smaller or bigger than 5?", 4.0, "task_b"),
        Beat("Switching between tasks costs time: the switch cost.", 5.5, "cost"),
    )
    thumbnail_beat = 2
    background = (30, 40, 70)

    def card(self, surface, stage, number, color, task):
        rect = pygame.Rect(0, 0, stage.size(18), stage.size(22))
        rect.center = stage.point(50, 22)
        pygame.draw.rect(surface, color, rect, border_radius=int(stage.size(2)))
        stage.text(surface, str(number), 50, 22, 10, ui.WHITE)
        stage.text(surface, task, 50, 40, 3.4, color)

    def task_a(self, surface, stage, share, clock):
        number = (3, 8, 7)[int(clock / 1.4) % 3]
        self.card(surface, stage, number, BLUE, "odd or even?")

    def task_b(self, surface, stage, share, clock):
        number = (2, 9, 6)[int(clock / 1.4) % 3]
        self.card(surface, stage, number, ORANGE, "smaller or bigger than 5?")

    def cost(self, surface, stage, share, clock):
        sequence = (("A", BLUE), ("A", BLUE), ("B", ORANGE), ("B", ORANGE), ("A", BLUE))
        for index, (task, color) in enumerate(sequence):
            switch = index > 0 and sequence[index - 1][0] != task
            x = 14 + index * 18
            rect = pygame.Rect(0, 0, stage.size(10), stage.size(8))
            rect.center = stage.point(x, 12)
            pygame.draw.rect(surface, color, rect, border_radius=int(stage.size(1)))
            stage.text(surface, task, x, 12, 4, ui.WHITE)
            grow = ease(window(share, index * 0.12, index * 0.12 + 0.3))
            height = (16 if switch else 9) * grow
            bar = pygame.Rect(0, 0, stage.size(6), max(1, stage.size(height)))
            bar.midbottom = stage.point(x, 42)
            pygame.draw.rect(surface, RED if switch else GREEN, bar, border_radius=int(stage.size(0.6)))
            if switch and grow >= 1:
                stage.text(surface, "switch!", x, 42 - height - 2.5, 2.4, RED)
        stage.text(surface, "reaction time", 50, 47, 2.6, ui.WHITE)


SORT_TARGET = (2, "red", "star")
SORT_PILES = ((1, "red", "circle"), (2, "blue", "triangle"), (3, "green", "star"))


class CardSortingAnimation(InsightAnimation):
    """Card sorting and perseveration (Grant & Berg, 1948; Milner, 1963)."""

    title = "Card sorting"
    beats = (
        Beat("Sort the card - but nobody tells you the rule.", 4.5, "unknown"),
        Beat("Found it: by COLOUR. Right, right, right ...", 4.5, "colour"),
        Beat("Suddenly the rule changes: 'Wrong!'", 4.0, "changed"),
        Beat("Many keep using the old rule: perseveration.", 5.0, "perseverate"),
    )
    thumbnail_beat = 3
    background = (34, 50, 44)

    def table(self, surface, stage, chosen=None, ok=None, target_y=8):
        for index, card in enumerate(SORT_PILES):
            rect = pygame.Rect(0, 0, stage.size(16), stage.size(11))
            rect.center = stage.point(22 + index * 28, 36)
            draw_card(surface, rect, card, stage.unit / 9)
            if chosen == index and ok is not None:
                draw_check(surface, stage, 22 + index * 28, 46, 2, ok)
        rect = pygame.Rect(0, 0, stage.size(16), stage.size(11))
        target_x = 50 if chosen is None else lerp(50, 22 + chosen * 28, 0.35)
        rect.center = stage.point(target_x, target_y + 6)
        draw_card(surface, rect, SORT_TARGET, stage.unit / 9)

    def unknown(self, surface, stage, share, clock):
        self.table(surface, stage)
        stage.text(surface, "?", 50 + math.sin(clock * 3) * 10, 26, 5, YELLOW)

    def colour(self, surface, stage, share, clock):
        self.table(surface, stage, 0, True)
        stage.text(surface, "rule: colour", 80, 6, 3, GREEN)

    def changed(self, surface, stage, share, clock):
        self.table(surface, stage, 0, False)
        stage.text(surface, "Wrong!", 80, 6, 4, RED)

    def perseverate(self, surface, stage, share, clock):
        chosen = 0 if share < 0.6 else 2
        self.table(surface, stage, chosen, chosen == 2)
        stage.text(surface, "colour again? Wrong!" if share < 0.6 else "shape! Right!", 76, 6, 3, RED if share < 0.6 else GREEN)


class ControlMapAnimation(MapAnimation):
    """How executive control fits together."""

    title = "The big picture"
    center = "EXECUTIVE\nCONTROL"
    nodes = (
        ("updating", "working memory", (20, 11)),
        ("planning", "planning ahead", (80, 11)),
        ("switching", "switching tasks", (20, 39)),
        ("card_sorting", "adapting to new rules", (80, 39)),
    )
    beats = (
        Beat("Control means UPDATING what you keep in mind ...", 3.5, "node_1"),
        Beat("... PLANNING before you act ...", 3.5, "node_2"),
        Beat("... SWITCHING between tasks ...", 3.5, "node_3"),
        Beat("... and noticing when the RULES change.", 4.5, "node_4"),
    )


# ---------------------------------------------------------------------------
# The villain (his animations are in guide_animations.py)
# ---------------------------------------------------------------------------


def draw_hackula(surface, stage, x, y, height, clock):
    """Draw Count Hackula, a vampire bat count, standing on (x, y)."""
    unit = height / 26
    cape = [stage.point(x - 9 * unit, y), stage.point(x - 6 * unit, y - 16 * unit), stage.point(x, y - 18 * unit), stage.point(x + 6 * unit, y - 16 * unit), stage.point(x + 9 * unit, y)]
    pygame.draw.polygon(surface, (40, 20, 50), cape)
    pygame.draw.polygon(surface, (160, 30, 50), [stage.point(x - 6 * unit, y - 16 * unit), stage.point(x, y - 10 * unit), stage.point(x + 6 * unit, y - 16 * unit)])
    stage.circle(surface, (200, 200, 220), x, y - 21 * unit, 5 * unit)
    for side in (-1, 1):
        pygame.draw.polygon(surface, (200, 200, 220), [stage.point(x + side * 3 * unit, y - 24 * unit), stage.point(x + side * 5 * unit, y - 30 * unit), stage.point(x + side * 5.5 * unit, y - 23 * unit)])
        stage.circle(surface, RED, x + side * 2 * unit, y - 22 * unit, 0.9 * unit)
    stage.text(surface, "p", x, y - 8 * unit, 6 * unit, YELLOW)
    stage.line(surface, ui.WHITE, (x - 1 * unit, y - 18.5 * unit), (x - 0.6 * unit, y - 17 * unit), 0.4 * unit)
    stage.line(surface, ui.WHITE, (x + 1 * unit, y - 18.5 * unit), (x + 0.6 * unit, y - 17 * unit), 0.4 * unit)


STORY_ANIMATIONS = {
    "open_science": OpenScienceIntroAnimation,
    "qrps": QrpsAnimation,
    "reproducibility": ReproducibilityAnimation,
    "file_drawer": FileDrawerAnimation,
    "open_practices": OpenPracticesAnimation,
    "prologue_map": PrologueMapAnimation,
    "inhibition": InhibitionAnimation,
    "go_nogo": GoNoGoAnimation,
    "horse_race": HorseRaceAnimation,
    "stroop": StroopAnimation,
    "ego_depletion": EgoDepletionAnimation,
    "brain_brake": BrainBrakeAnimation,
    "inhibition_map": InhibitionMapAnimation,
    "stop_skill": StopSkillAnimation,
    "executive_functions": ExecutiveAnimation,
    "updating": UpdatingAnimation,
    "planning": PlanningAnimation,
    "switching": SwitchingAnimation,
    "card_sorting": CardSortingAnimation,
    "control_map": ControlMapAnimation,
}


def register():
    """Add the animations to ``insight_animations.ANIMATIONS``."""
    insight_animations.ANIMATIONS.update(STORY_ANIMATIONS)
