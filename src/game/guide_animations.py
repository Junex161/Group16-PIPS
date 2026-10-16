"""Animations that tell the story and show how bosses and new mechanics work.

These are not insights: they carry no card at the end. They replace text
boxes wherever a picture explains faster than words:

* ``hackula`` and ``finale``: the beginning and the end of the story,
* ``drawer_how``, ``impulse_how`` and ``rules_how``: how to beat each boss,
* ``red_light_how`` and ``switch_how``: the red-light zones of Level 2 and
  the switch blocks of Level 3.

``register()`` adds them to ``insight_animations.ANIMATIONS``.
"""

import math

import pygame

from . import graphics, insight_animations, ui, worlds
from .bosses import CaptainImpulse, FileDrawer
from .characters import CHARACTERS
from .config import TILE_SIZE
from .experiment_scenes import draw_stop_sign
from .insight_animations import GREEN, GREY, RED, YELLOW, Beat, InsightAnimation, draw_character, draw_scaled, ease, lerp, window
from .story_animations import draw_cabinet, draw_check, draw_hackula, draw_paper, ground
from .worlds import draw_card, draw_hackling

LIGHT_COLORS = {"green": (70, 220, 100), "yellow": (255, 200, 60), "red": (240, 60, 60)}


def draw_traffic_light(surface, stage, x, y, state, size=1.0):
    """Draw a traffic light whose bottom stands on (x, y)."""
    box = pygame.Rect(0, 0, stage.size(5 * size), stage.size(13 * size))
    box.midbottom = stage.point(x, y)
    pygame.draw.rect(surface, (30, 30, 40), box, border_radius=int(stage.size(1)))
    pygame.draw.rect(surface, ui.GOLD, box, max(1, int(stage.size(0.3))), border_radius=int(stage.size(1)))
    for index, name in enumerate(("red", "yellow", "green")):
        color = LIGHT_COLORS[name]
        center = (box.centerx, box.top + box.height * (0.18 + index * 0.32))
        pygame.draw.circle(surface, color if name == state else tuple(c // 4 for c in color), center, stage.size(1.6 * size))


def _drawer_image(open_drawer, time):
    """The File Drawer boss drawn onto its own image (300 x 260 pixels)."""
    boss = FileDrawer((0, 10 * TILE_SIZE), 250)
    boss.open_drawer = open_drawer
    image = pygame.Surface((300, 260), pygame.SRCALPHA)
    boss.draw(image, boss.x - 100, time)
    return image


def _impulse_image(light, time, frozen=False):
    """Captain Impulse drawn onto its own image (200 x 200 pixels)."""
    boss = CaptainImpulse((0, 10 * TILE_SIZE), 190)
    boss.light, boss.facing = light, -1
    boss.frozen = 1.0 if frozen else 0.0
    image = pygame.Surface((200, 200), pygame.SRCALPHA)
    boss.draw(image, boss.x - 50, time)
    return image


def blit_scaled(surface, stage, image, x, y, height):
    """Scale an image to ``height`` stage units and put its bottom centre on (x, y)."""
    pixels = max(4, int(stage.size(height)))
    scaled = pygame.transform.smoothscale(image, (int(pixels * image.get_width() / image.get_height()), pixels))
    surface.blit(scaled, scaled.get_rect(midbottom=stage.point(x, y)))


# ---------------------------------------------------------------------------
# The story
# ---------------------------------------------------------------------------

HACK_P_VALUES = (0.41, 0.27, 0.62, 0.18, 0.33, 0.04)


class HackulaAnimation(InsightAnimation):
    """The beginning of the story: how Count Hackula p-hacks."""

    title = "Count Hackula"
    beats = (
        Beat("Count Hackula runs test after test until one hits p<.05 ...", 6.0, "tests"),
        Beat("... publishes only that lucky result and hides the rest ...", 5.0, "hide"),
        Beat("... and now fake findings fill the archive. Stop him!", 5.0, "pile"),
    )
    background = (30, 16, 40)

    def tests(self, surface, stage, share, clock):
        draw_hackula(surface, stage, 14, 46, 24, clock)
        baseline, top = 40, 8
        line_y = baseline - (baseline - top) * 0.05 / 0.7
        stage.line(surface, RED, (26, line_y), (92, line_y), 0.35)
        stage.text(surface, "p = .05", 94, line_y - 3, 2.4, RED)
        shown = min(len(HACK_P_VALUES), int(share * 1.15 * len(HACK_P_VALUES)) + 1)
        for index, p_value in enumerate(HACK_P_VALUES[:shown]):
            height = (baseline - top) * p_value / 0.7
            bar = pygame.Rect(stage.point(30 + index * 10, baseline - height), (stage.size(6), stage.size(height)))
            pygame.draw.rect(surface, GREEN if p_value < 0.05 else GREY, bar, border_radius=3)
            stage.text(surface, f"test {index + 1}", 33 + index * 10, baseline + 2.5, 2.2, ui.WHITE)
        if shown == len(HACK_P_VALUES):
            stage.text(surface, "'Significant!'", 83, 10, 3.4, GREEN)

    def hide(self, surface, stage, share, clock):
        draw_hackula(surface, stage, 14, 46, 24, clock)
        draw_cabinet(surface, stage, 40, 46, ease(window(share, 0.0, 0.3)) * (1 - ease(window(share, 0.75, 1.0))))
        for index in range(5):
            travel = ease(window(share, 0.1 + index * 0.1, 0.45 + index * 0.1))
            if travel < 1:
                draw_paper(surface, stage, *lerp((30 + index * 10, 12), (38, 26), travel), label="n.s.", label_color=GREY, size=1 - 0.4 * travel)
        journal = pygame.Rect(0, 0, stage.size(16), stage.size(22))
        journal.midbottom = stage.point(80, 44)
        pygame.draw.rect(surface, (180, 60, 60), journal, border_radius=int(stage.size(1)))
        stage.text(surface, "JOURNAL", 80, 26, 2.6, ui.WHITE)
        draw_paper(surface, stage, *lerp((60, 12), (80, 35), ease(window(share, 0.2, 0.6))), color=YELLOW, label="p<.05")

    def pile(self, surface, stage, share, clock):
        n_shown = int(12 * ease(window(share, 0.0, 0.7)))
        for index in range(n_shown):
            draw_paper(surface, stage, 52 + (index % 4) * 8, 40 - (index // 4) * 9, color=YELLOW, label="p<.05")
        draw_hackula(surface, stage, 24, 44, 24, clock)
        for index in range(3):
            draw_scaled(surface, stage, lambda image, offset=index: draw_hackling(image, 5, 10, clock + offset), (50, 40), 40 + index * 9, 12 + math.sin(clock * 3 + index) * 2, 5)
        if share > 0.6:
            draw_character(surface, stage, self.character, 90, 46, 12, -1, clock)
            stage.text(surface, "!", 90, 30, 5, YELLOW)


class FinaleAnimation(InsightAnimation):
    """The end of the story, after the last boss."""

    title = "The land of the Mind is safe!"
    beats = (
        Beat("Your replications checked Count Hackula's 'findings' one by one ...", 5.0, "check"),
        Beat("... and his p-hacked results crumbled to dust.", 4.5, "crumble"),
        Beat("Count Hackula flees - and takes his bats with him!", 4.5, "flee"),
        Beat("Careful, open science: the best weapon against fake findings.", 5.5, "hero"),
    )
    background = (24, 40, 70)

    def papers(self, surface, stage, share, checked, falling=0.0):
        for index in range(8):
            x, y = 40 + (index % 4) * 12, 18 + (index // 4) * 14
            ok = index in (2, 5)
            if index < checked:
                if ok:
                    draw_paper(surface, stage, x, y, color=(150, 230, 160), label="real")
                    draw_check(surface, stage, x + 4, y - 4, 1.5)
                else:
                    drop = falling * (1 + index * 0.1)
                    if drop < 1:
                        draw_paper(surface, stage, x, y + drop * 30, color=YELLOW, label="p<.05", size=1 - drop * 0.5)
            else:
                draw_paper(surface, stage, x, y, color=YELLOW, label="p<.05")

    def check(self, surface, stage, share, clock):
        draw_character(surface, stage, self.character, 16, 46, 14, 1, clock)
        self.papers(surface, stage, share, int(share * 9))

    def crumble(self, surface, stage, share, clock):
        draw_character(surface, stage, self.character, 16, 46, 14, 1, clock)
        self.papers(surface, stage, share, 8, ease(share))

    def flee(self, surface, stage, share, clock):
        fly = ease(window(share, 0.2, 1.0))
        draw_hackula(surface, stage, lerp(60, 120, fly), lerp(44, -10, fly), 22, clock)
        for index in range(4):
            draw_scaled(surface, stage, lambda image, offset=index: draw_hackling(image, 5, 10, clock + offset), (50, 40), lerp(50 + index * 8, 130, fly), lerp(20, -20, fly) + index * 2, 5)
        draw_character(surface, stage, self.character, 20, 46, 14, 1, clock)
        if share > 0.5:
            stage.text(surface, "Hooray!", 20, 26, 3.6, YELLOW)

    def hero(self, surface, stage, share, clock):
        ground(surface, stage, (80, 150, 90), 42)
        for index, label in enumerate(("PREREGISTER", "OPEN DATA", "REPLICATE")):
            x = 22 + index * 28
            sign = pygame.Rect(0, 0, stage.size(22), stage.size(7))
            sign.center = stage.point(x, 12 + math.sin(clock * 2 + index) * 0.8)
            pygame.draw.rect(surface, (40, 120, 90), sign, border_radius=int(stage.size(1)))
            stage.text(surface, label, x, 12 + math.sin(clock * 2 + index) * 0.8, 2.4, ui.WHITE)
        for index, character in enumerate((self.character, *[c for c in CHARACTERS if c != self.character][:2])):
            hop = abs(math.sin(clock * 4 + index)) * 2
            draw_character(surface, stage, character, 38 + index * 12, 42 - hop, 12, 1, clock + index)


# ---------------------------------------------------------------------------
# How to beat the bosses
# ---------------------------------------------------------------------------


class DrawerHowAnimation(InsightAnimation):
    """How to beat the File Drawer."""

    title = "The File Drawer"
    beats = (
        Beat("Count Hackula's File Drawer hides the null results.", 4.0, "closed"),
        Beat("A drawer opens for a moment - punch the OPEN drawer!", 5.0, "punch"),
        Beat("Jump over its 'p < .05' papers and shock waves.", 4.5, "dodge"),
    )
    background = (60, 40, 30)

    def closed(self, surface, stage, share, clock):
        ground(surface, stage, (110, 74, 50))
        blit_scaled(surface, stage, _drawer_image(None, clock), 72, 42, 34)
        draw_character(surface, stage, self.character, 24, 42, 13, 1, clock)
        for index in range(3):
            stage.text(surface, "n.s.", 66 + index * 6, 12 + math.sin(clock * 3 + index) * 1.5, 2.4, GREY)

    def punch(self, surface, stage, share, clock):
        ground(surface, stage, (110, 74, 50))
        hit = share > 0.6
        blit_scaled(surface, stage, _drawer_image(None if hit else 2, clock), 72, 42, 34)
        walk = ease(window(share, 0.1, 0.5))
        draw_character(surface, stage, self.character, lerp(24, 50, walk), 42, 13, 1, clock, moving=walk < 1, punching=0.5 < share < 0.7)
        if hit:
            for index in range(4):
                fly = window(share, 0.6, 1.0)
                draw_paper(surface, stage, 60 + index * 4, 34 - fly * (20 + index * 4), label="n.s.", label_color=GREY, size=0.8)
            stage.text(surface, "Freed!", 50, 12, 3.6, GREEN)

    def dodge(self, surface, stage, share, clock):
        ground(surface, stage, (110, 74, 50))
        blit_scaled(surface, stage, _drawer_image(None, clock), 72, 42, 34)
        jump = math.sin(min(1.0, window(share, 0.35, 0.75)) * math.pi) * 12
        draw_character(surface, stage, self.character, 30, 42 - jump, 13, 1, clock)
        x = lerp(64, 4, share)
        stage.line(surface, (255, 200, 120), (x - 4, 41), (x + 4, 41), 1.2)
        draw_paper(surface, stage, lerp(62, 26, share), 10 + 30 * share**2, color=YELLOW, label="p<.05", size=0.8)


class ImpulseHowAnimation(InsightAnimation):
    """How to beat Captain Impulse."""

    title = "Captain Impulse"
    beats = (
        Beat("GREEN light: Captain Impulse is open - hit him!", 4.5, "green"),
        Beat("RED light: hold back! Hitting him now heals him.", 5.0, "red"),
        Beat("Red can come suddenly - stop! R freezes his charge.", 5.0, "sudden"),
    )
    background = (70, 20, 20)

    def green(self, surface, stage, share, clock):
        ground(surface, stage, (70, 40, 40))
        blit_scaled(surface, stage, _impulse_image("green", clock), 62, 42, 26)
        draw_character(surface, stage, self.character, 40, 42, 13, 1, clock, punching=(clock % 1.2) < 0.3)
        if (clock % 1.2) < 0.4:
            stage.text(surface, "HIT!", 54, 12, 4, GREEN)

    def red(self, surface, stage, share, clock):
        ground(surface, stage, (70, 40, 40))
        blit_scaled(surface, stage, _impulse_image("red", clock), 62, 42, 26)
        mistake = 0.45 < share < 0.75
        draw_character(surface, stage, self.character, 40, 42, 13, 1, clock, punching=mistake)
        if mistake:
            stage.text(surface, "Commission error: +1 for him!", 50, 10, 3, RED)
        else:
            stage.text(surface, "hold ...", 40, 22, 3, ui.WHITE)

    def sudden(self, surface, stage, share, clock):
        ground(surface, stage, (70, 40, 40))
        frozen = share > 0.45
        x = 70 if share < 0.25 else lerp(70, 52, ease(window(share, 0.25, 0.45)))
        blit_scaled(surface, stage, _impulse_image("green" if share < 0.2 else "red", clock, frozen), x, 42, 26)
        draw_character(surface, stage, self.character, 26, 42, 13, 1, clock)
        if share > 0.35:
            stage.text(surface, "R", 26, 18, 5, YELLOW)
        if frozen:
            draw_stop_sign(surface, stage.point(x, 8), int(stage.size(3)))
            stage.text(surface, "frozen!", x + 10, 12, 3, (170, 220, 255))


RULE_TARGET = (2, "blue", "star")
RULE_CHOICES = ((1, "blue", "circle"), (3, "red", "star"), (2, "green", "triangle"))


class RulesHowAnimation(InsightAnimation):
    """How to beat the Rule Keeper."""

    title = "The Rule Keeper"
    beats = (
        Beat("Jump into the card block that matches his card.", 5.0, "jump"),
        Beat("Only he knows the rule: colour, shape or number.", 4.5, "rules"),
        Beat("'Wrong!' after a run of 'Right!'? The rule changed - switch!", 5.5, "switch"),
    )
    background = (14, 14, 40)

    def table(self, surface, stage, mark=None, ok=None):
        rect = pygame.Rect(0, 0, stage.size(14), stage.size(10))
        rect.center = stage.point(50, 9)
        draw_card(surface, rect, RULE_TARGET, stage.unit / 9)
        pygame.draw.rect(surface, ui.GOLD, rect, max(1, int(stage.size(0.4))), border_radius=6)
        for index, card in enumerate(RULE_CHOICES):
            block = pygame.Rect(0, 0, stage.size(12), stage.size(9))
            block.center = stage.point(25 + index * 25, 27)
            draw_card(surface, block, card, stage.unit / 9)
            if mark == index and ok is not None:
                draw_check(surface, stage, 25 + index * 25, 20, 2, ok)

    def jump(self, surface, stage, share, clock):
        ground(surface, stage, (70, 76, 110))
        self.table(surface, stage, 0, True if share > 0.6 else None)
        hop = math.sin(min(1.0, window(share, 0.3, 0.7)) * math.pi) * 10
        draw_character(surface, stage, self.character, 25, 46 - hop, 11, 1, clock)
        if share > 0.6:
            stage.text(surface, "Right! (same colour)", 70, 44, 3, GREEN)

    def rules(self, surface, stage, share, clock):
        ground(surface, stage, (70, 76, 110))
        self.table(surface, stage)
        lit = int(clock / 1.2) % 3
        for index, name in enumerate(("COLOUR", "SHAPE", "NUMBER")):
            stage.text(surface, name, 25 + index * 25, 40, 3.4, YELLOW if index == lit else GREY)

    def switch(self, surface, stage, share, clock):
        ground(surface, stage, (70, 76, 110))
        if share < 0.5:
            self.table(surface, stage, 0, False)
            stage.text(surface, "Colour again? Wrong!", 50, 42, 3.2, RED)
        else:
            self.table(surface, stage, 1, True)
            stage.text(surface, "Try SHAPE - Right!", 50, 42, 3.2, GREEN)


# ---------------------------------------------------------------------------
# New mechanics
# ---------------------------------------------------------------------------


class RedLightHowAnimation(InsightAnimation):
    """The red-light zones of Level 2."""

    title = "Red light, green light"
    beats = (
        Beat("GREEN light: run!", 3.5, "green"),
        Beat("RED light: freeze - moving now costs a heart!", 4.5, "red"),
        Beat("On ice you slide: start braking at YELLOW!", 5.0, "yellow"),
    )
    background = (40, 26, 80)

    def scene(self, surface, stage, state):
        ground(surface, stage, (90, 90, 110), 42)
        draw_traffic_light(surface, stage, 84, 30, state, 1.2)
        if state == "red":
            stage.translucent(surface, lambda layer: pygame.draw.polygon(layer, (255, 60, 60), [stage.point(84, 16), stage.point(0, 42), stage.point(80, 42)]), 50)

    def green(self, surface, stage, share, clock):
        self.scene(surface, stage, "green")
        draw_character(surface, stage, self.character, lerp(10, 60, share), 42, 13, 1, clock, moving=True)

    def red(self, surface, stage, share, clock):
        self.scene(surface, stage, "red")
        moving = share > 0.55
        x = 40 + (8 * window(share, 0.55, 0.8) if moving else 0)
        draw_character(surface, stage, self.character, x, 42, 13, 1, clock, moving=moving)
        if moving:
            stage.text(surface, "Ouch! -1 heart", x, 20, 3.2, RED)
        else:
            stage.text(surface, "freeze ...", x, 22, 3, ui.WHITE)

    def yellow(self, surface, stage, share, clock):
        state = "yellow" if share < 0.5 else "red"
        self.scene(surface, stage, state)
        pygame.draw.rect(surface, (220, 236, 250), pygame.Rect(stage.point(0, 42), (stage.size(100), stage.size(2))))
        slide = ease(window(share, 0.0, 0.6))
        x = lerp(20, 46, slide)
        draw_character(surface, stage, self.character, x, 42, 13, 1, clock, moving=slide < 1)
        if slide < 1:
            for index in range(3):
                stage.circle(surface, ui.WHITE, x - 4 - index * 3, 41, 0.8)
        else:
            draw_check(surface, stage, x, 22, 2)


class SwitchHowAnimation(InsightAnimation):
    """The red and blue switch blocks of Level 3."""

    title = "Switch blocks"
    beats = (
        Beat("Hit a SWITCH block from below ...", 3.5, "hit"),
        Beat("... red and blue blocks swap - the way is free!", 4.5, "swap"),
    )
    background = (40, 44, 52)

    def blocks(self, surface, stage, active):
        size = stage.size(6)
        for color, cells in (("red", [(60, 18 + row * 6) for row in range(4)]), ("blue", [(70 + col * 6, 30) for col in range(3)])):
            for x, y in cells:
                rect = pygame.Rect(stage.point(x, y), (size, size))
                if color == active:
                    pygame.draw.rect(surface, worlds.BLOCK_COLORS[color], rect, border_radius=4)
                    pygame.draw.rect(surface, graphics.OUTLINE, rect, 2, border_radius=4)
                else:
                    worlds.draw_block_outline(surface, rect, color)

    def switch_block(self, surface, stage, color):
        rect = pygame.Rect(stage.point(26, 18), (stage.size(6), stage.size(6)))
        pygame.draw.rect(surface, (240, 240, 250), rect, border_radius=4)
        pygame.draw.rect(surface, worlds.BLOCK_COLORS[color], rect.inflate(-stage.size(1.4), -stage.size(1.4)), border_radius=3)

    def hit(self, surface, stage, share, clock):
        ground(surface, stage, (110, 116, 128), 42)
        hop = math.sin(min(1.0, window(share, 0.3, 0.7)) * math.pi) * 12
        self.switch_block(surface, stage, "red")
        self.blocks(surface, stage, "red")
        draw_character(surface, stage, self.character, 29, 42 - hop, 12, 1, clock)

    def swap(self, surface, stage, share, clock):
        ground(surface, stage, (110, 116, 128), 42)
        self.switch_block(surface, stage, "blue")
        self.blocks(surface, stage, "blue")
        walk = ease(window(share, 0.2, 1.0))
        draw_character(surface, stage, self.character, lerp(29, 92, walk), 42, 12, 1, clock, moving=walk < 1)


class HackulaHowAnimation(InsightAnimation):
    """How to beat Count Hackula, one beat per phase."""

    title = "Count Hackula"
    beats = (
        Beat("Three Counts - only the real one casts a shadow. Hit him!", 5.5, "decoys"),
        Beat("Swoop: GREEN eyes - jump into him. RED eyes - stay down!", 5.5, "swoop"),
        Beat("Open the windows in HIS order - sunlight ends him!", 6.0, "sunlight"),
    )
    background = (20, 14, 34)

    def count(self, surface, stage, x, y, clock, eyes="gold", shadow=False, alpha=255):
        from .hackula_boss import draw_count

        draw_count(surface, stage.point(x, y), clock, eyes, alpha, shadow_y=stage.point(0, 42)[1] if shadow else None, scale=stage.unit / 9)

    def decoys(self, surface, stage, share, clock):
        ground(surface, stage, (70, 60, 80))
        for index, x in enumerate((25, 50, 75)):
            if index == 2 and share > 0.7:
                continue
            self.count(surface, stage, x, 28 + math.sin(clock * 3 + index) * 1.5, clock + index, shadow=index == 2)
        if share > 0.35:
            pygame.draw.circle(surface, YELLOW, stage.point(75, 41), stage.size(6), max(1, int(stage.size(0.5))))
            stage.text(surface, "shadow = real!", 75, 47, 2.6, YELLOW)
        draw_character(surface, stage, self.character, lerp(10, 66, ease(window(share, 0.4, 0.7))), 42, 11, 1, clock, punching=share > 0.65)

    def swoop(self, surface, stage, share, clock):
        ground(surface, stage, (70, 60, 80))
        eyes = "green" if share < 0.5 else "red"
        x = lerp(90, 10, share)
        self.count(surface, stage, x, 12 + math.sin(share * math.pi) * 18, clock, eyes)
        hop = 10 * max(0.0, 1 - abs(x - 50) / 14) if eyes == "green" else 0
        draw_character(surface, stage, self.character, 50, 42 - hop, 11, 1, clock)
        stage.text(surface, "jump into him!" if eyes == "green" else "stay down ...", 50, 47, 3, GREEN if eyes == "green" else RED)

    def sunlight(self, surface, stage, share, clock):
        from .hackula_boss import WINDOWS, draw_window_icon

        ground(surface, stage, (70, 60, 80))
        order = (1, 0, 2)
        opened = int(share * 4)
        for index, kind in enumerate(WINDOWS):
            rect = pygame.Rect(0, 0, stage.size(10), stage.size(10))
            rect.center = stage.point(25 + index * 25, 30)
            is_open = index in order[:opened]
            draw_window_icon(surface, rect, kind, 1.0 if is_open else 0.0)
            if is_open:
                stage.text(surface, str(order.index(index) + 1), 25 + index * 25, 22, 3.4, YELLOW)
        self.count(surface, stage, 50, 10, clock, "gold", alpha=int(255 * (1 - 0.8 * window(share, 0.75, 1.0))))
        if share > 0.75:
            stage.translucent(surface, lambda layer: layer.fill((255, 240, 160)), 70)


GUIDE_ANIMATIONS = {
    "hackula": HackulaAnimation,
    "finale": FinaleAnimation,
    "drawer_how": DrawerHowAnimation,
    "impulse_how": ImpulseHowAnimation,
    "rules_how": RulesHowAnimation,
    "red_light_how": RedLightHowAnimation,
    "switch_how": SwitchHowAnimation,
    "hackula_how": HackulaHowAnimation,
}


def register():
    """Add the animations to ``insight_animations.ANIMATIONS``."""
    insight_animations.ANIMATIONS.update(GUIDE_ANIMATIONS)
