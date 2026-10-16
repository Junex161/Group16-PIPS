"""The boss fights of the Prologue and Levels 2 and 3.

Each boss turns the topic of its level into a game mechanic:

* ``FileDrawer`` (Prologue, publication bias): a filing cabinet that hides
  null results. Its drawers only open for a moment; punch an open drawer
  to free the hidden results.
* ``CaptainImpulse`` (Level 2, response inhibition): a charging robot bull
  with a traffic light. Hit it on GREEN; on RED, holding back is the right
  move - attacking then is a commission error that heals it. Sometimes the
  light jumps to red without warning, like a stop signal.
* ``RuleKeeper`` (Level 3, cognitive flexibility): it holds up a card, and
  the hero sorts it by jumping into one of three card blocks. Only the
  boss knows the rule (colour, shape or number), and it changes the rule
  without warning, as in the Wisconsin Card Sorting Test.

A boss does not know the level: ``StoryPlayScene`` tells it where the player
is and passes on hits. Positions are in pixels, durations in seconds.
"""

import math
import random

import pygame

from . import graphics, ui, worlds
from .config import SCREEN_HEIGHT, TILE_SIZE

CARD_DIMENSIONS = ("color", "shape", "number")
CARD_VALUES = {"color": ("red", "green", "blue"), "shape": ("circle", "triangle", "star"), "number": (1, 2, 3)}
CARDSORT_COLUMNS = ("participant_id", "attempt", "trial", "rule", "chosen_dimension", "correct", "perseverative")


class Hazard:
    """
    Something the boss throws or drops; touching it hurts the hero.

    Parameters
    ----------
    x, y : float
        Centre in pixels.
    width, height : int
        Size of the hitbox.
    vx, vy : float
        Velocity in pixels per second.
    kind : str
        How it looks: "paper", "wave", "bolt", "cog" or "warning".
    gravity : float, optional
        Downward acceleration.
    lifetime : float, optional
        Seconds until it disappears.
    label : str, optional
        Text written on it.
    """

    def __init__(self, x, y, width, height, vx, vy, kind, gravity=0.0, lifetime=4.0, label=""):
        self.x, self.y, self.width, self.height = x, y, width, height
        self.vx, self.vy, self.kind, self.gravity = vx, vy, kind, gravity
        self.lifetime, self.label = lifetime, label
        self.age = 0.0

    @property
    def rect(self):
        """Current hitbox."""
        rect = pygame.Rect(0, 0, self.width, self.height)
        rect.center = (round(self.x), round(self.y))
        return rect

    @property
    def harmful(self):
        """Warnings only show where something will fall; they do not hurt."""
        return self.kind != "warning"

    @property
    def is_gone(self):
        """True when the hazard is over."""
        return self.age >= self.lifetime or self.y > SCREEN_HEIGHT + 100

    def update(self, dt, ground_y):
        """Move; papers and cards vanish when they land."""
        self.age += dt
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.kind in ("paper", "cog") and self.y + self.height / 2 >= ground_y:
            self.lifetime = 0.0

    def draw(self, surface, camera, time):
        rect = self.rect.move(-camera, 0)
        if self.kind == "paper":
            angle = (self.age * 400) % 360
            image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            image.fill((255, 230, 120))
            pygame.draw.rect(image, graphics.OUTLINE, image.get_rect(), 2)
            label = ui.get_font(16, bold=True).render(self.label, True, (150, 30, 30))
            image.blit(label, label.get_rect(center=image.get_rect().center))
            image = pygame.transform.rotate(image, angle)
            surface.blit(image, image.get_rect(center=rect.center))
        elif self.kind == "wave":
            for index in range(3):
                pygame.draw.arc(surface, (255, 200, 120), rect.inflate(-index * 8, 0).move(0, index * 4), 0, math.pi, 4)
        elif self.kind == "bolt":
            points = [(rect.centerx, rect.top), (rect.centerx - 10, rect.centery), (rect.centerx + 6, rect.centery), (rect.centerx - 4, rect.bottom)]
            pygame.draw.lines(surface, (255, 250, 150), False, points, 7)
            pygame.draw.lines(surface, (255, 255, 255), False, points, 3)
        elif self.kind == "cog":
            worlds.draw_gear(surface, rect.center, self.width // 2 - 4, self.age * 6, (200, 80, 90))
        elif self.kind == "warning":
            if int(time * 10) % 2 == 0:
                pygame.draw.ellipse(surface, (255, 80, 80), (rect.centerx - 26, rect.bottom - 10, 52, 12), 3)


class Boss:
    """
    Base class of the bosses.

    Parameters
    ----------
    arena : tuple of float
        Left and right pixel edge of the boss hall.
    ground_y : float
        Height of the floor of the hall.
    difficulty_key : str
        "easy", "medium" or "hard".
    rng : random.Random or None, optional
        Random number generator.
    """

    name = "Boss"
    title = ""
    HIT_POINTS = {"easy": 4, "medium": 6, "hard": 8}

    def __init__(self, arena, ground_y, difficulty_key="medium", rng=None):
        self.arena = arena
        self.ground_y = ground_y
        self.difficulty_key = difficulty_key
        self.rng = rng or random.Random()
        self.max_hp = self.HIT_POINTS.get(difficulty_key, self.HIT_POINTS["medium"])
        self.hp = self.max_hp
        self.active = False
        self.hazards = []
        self.events = []
        self.flash = 0.0
        self.frozen = 0.0
        self.time = 0.0

    @property
    def defeated(self):
        """True once all hit points are gone."""
        return self.hp <= 0

    @property
    def phase(self):
        """1, 2 or 3: the boss gets faster as it loses hit points."""
        share = self.hp / self.max_hp
        return 1 if share > 2 / 3 else 2 if share > 1 / 3 else 3

    @property
    def body_rect(self):
        """Touching this area hurts the hero (None if nothing does)."""
        return None

    def freeze(self, seconds):
        """Stop moving and attacking for a while (the Stop Signal skill)."""
        self.frozen = max(self.frozen, seconds)

    def damage(self, amount=1):
        """Lose hit points and blink."""
        self.hp = max(0, self.hp - amount)
        self.flash = 0.4
        self.events.append(("hit", self.hp))
        if self.defeated:
            self.hazards = []
            self.events.append(("defeated", 0))

    def update(self, dt, player):
        """Advance the boss; ``player`` is the hero."""
        self.time += dt
        self.flash = max(0.0, self.flash - dt)
        for hazard in self.hazards:
            hazard.update(dt, self.ground_y)
        self.hazards = [hazard for hazard in self.hazards if not hazard.is_gone]
        if self.frozen > 0:
            self.frozen -= dt
            return False
        return self.active and not self.defeated

    def strike(self, rect, kind):
        """
        The hero attacks the area ``rect`` with a "punch", "shot" or "stomp".

        Returns
        -------
        str or None
            "hit" (damage dealt), "heal" (a commission error), "blocked" or
            None if the attack missed the boss.
        """
        return None

    def draw(self, surface, camera, time):
        """Draw the boss behind the tiles (its hazards are drawn by the scene)."""

    def draw_front(self, surface, camera, time):
        """Draw parts that belong in front of the tiles (nothing by default)."""

    def draw_health(self, surface):
        """Draw the name and a health bar at the top of the screen."""
        bar = pygame.Rect(0, 0, 420, 22)
        bar.midtop = (surface.get_width() // 2, 72)
        ui.draw_text(surface, self.name, (bar.centerx, bar.top - 4), 30, ui.GOLD, "midbottom", bold=True, shadow=True)
        pygame.draw.rect(surface, ui.INK, bar, border_radius=11)
        share = self.hp / self.max_hp
        pygame.draw.rect(surface, (236, 64, 86), (bar.x, bar.y, int(bar.width * share), bar.height), border_radius=11)
        pygame.draw.rect(surface, ui.WHITE, bar, 2, border_radius=11)
        if self.frozen > 0:
            ui.draw_text(surface, "FROZEN", (bar.right + 12, bar.centery), 26, (170, 220, 255), "midleft", bold=True)


# ---------------------------------------------------------------------------
# Prologue: the File Drawer
# ---------------------------------------------------------------------------


class FileDrawer(Boss):
    """A filing cabinet full of hidden null results (publication bias)."""

    name = "The File Drawer"
    WIDTH, HEIGHT = 3 * TILE_SIZE, 216
    DRAWER_HEIGHT = 60
    DRAWER_REACH = 56
    HIT_POINTS = {"easy": 4, "medium": 6, "hard": 8}

    def __init__(self, arena, ground_y, difficulty_key="medium", rng=None):
        super().__init__(arena, ground_y, difficulty_key, rng)
        self.x = arena[1] - 6 * TILE_SIZE
        self.y = ground_y - self.HEIGHT
        self.hop = 0.0
        self.open_drawer = None
        self.state_timer = 1.5
        self.throw_timer = 2.0
        self.hop_timer = 5.0

    @property
    def body_rect(self):
        return pygame.Rect(self.x, self.y - self.hop, self.WIDTH, self.HEIGHT)

    def drawer_rect(self, index, open_share=1.0):
        """Area of drawer ``index`` (0 = top); an open drawer sticks out to the left."""
        body = self.body_rect
        top = body.top + 12 + index * (self.DRAWER_HEIGHT + 10)
        reach = self.DRAWER_REACH * open_share
        return pygame.Rect(body.left + 12 - reach, top, body.width - 24 + reach, self.DRAWER_HEIGHT)

    def update(self, dt, player):
        if not super().update(dt, player):
            return
        speed = 1 + 0.35 * (self.phase - 1)
        self.state_timer -= dt * speed
        if self.state_timer <= 0:
            if self.open_drawer is None:
                # The bottom drawer opens most often, so it can always be reached.
                self.open_drawer = self.rng.choice((0, 1, 2, 2))
                self.state_timer = 2.4 if self.difficulty_key != "hard" else 1.8
            else:
                self.open_drawer = None
                self.state_timer = 1.4
        self.throw_timer -= dt * speed
        if self.throw_timer <= 0:
            self.throw_timer = 2.2
            for _ in range(1 if self.phase == 1 else 2):
                self._throw(player.center_x + self.rng.uniform(-80, 80))
        if self.phase >= 2:
            self.hop_timer -= dt
            if self.hop_timer <= 0:
                self.hop_timer = 4.5
                self.events.append(("hop", 0))
                for direction in (-1, 1):
                    self.hazards.append(Hazard(self.x + self.WIDTH / 2, self.ground_y - 12, 60, 24, direction * 330, 0, "wave", lifetime=2.6))

    def _throw(self, target_x):
        """Throw a 'significant' paper on an arc towards ``target_x``."""
        start_x, start_y = self.x + 20, self.y - 10
        flight, gravity = 1.1, 1400.0
        vx = (target_x - start_x) / flight
        vy = (self.ground_y - start_y - 0.5 * gravity * flight**2) / flight
        self.hazards.append(Hazard(start_x, start_y, 52, 30, vx, vy, "paper", gravity, 3.0, "p<.05"))

    def strike(self, rect, kind):
        if not self.active or self.defeated:
            return None
        if self.open_drawer is not None and rect.colliderect(self.drawer_rect(self.open_drawer)):
            self.open_drawer = None
            self.state_timer = 1.2
            self.damage()
            return "hit"
        if rect.colliderect(self.body_rect):
            return "blocked"
        return None

    def draw(self, surface, camera, time):
        body = self.body_rect.move(-camera, 0)
        color = (255, 255, 255) if self.flash > 0 and int(time * 20) % 2 == 0 else (110, 120, 140)
        pygame.draw.rect(surface, color, body, border_radius=12)
        pygame.draw.rect(surface, graphics.OUTLINE, body, 4, border_radius=12)
        for index in range(3):
            is_open = index == self.open_drawer
            drawer = self.drawer_rect(index, 1.0 if is_open else 0.0).move(-camera, 0)
            pygame.draw.rect(surface, (150, 160, 180) if not is_open else (190, 200, 220), drawer, border_radius=8)
            pygame.draw.rect(surface, graphics.OUTLINE, drawer, 3, border_radius=8)
            handle = pygame.Rect(0, 0, 40, 10)
            handle.center = (drawer.left + 40, drawer.centery)
            pygame.draw.rect(surface, (220, 200, 120), handle, border_radius=4)
            if is_open:
                # Hidden null results peek out of the open drawer.
                for paper in range(3):
                    sheet = pygame.Rect(drawer.left + 6 + paper * 14, drawer.top - 14 + (paper % 2) * 4, 22, 26)
                    pygame.draw.rect(surface, (250, 246, 230), sheet)
                    pygame.draw.rect(surface, graphics.OUTLINE, sheet, 1)
                ui.draw_text(surface, "n.s.", (drawer.left + 30, drawer.top - 8), 20, (90, 90, 120), "midbottom", bold=True)
                if int(time * 4) % 2 == 0:
                    ui.draw_text(surface, "PUNCH!", (drawer.centerx - 30, drawer.bottom + 4), 22, ui.GOLD, "midtop", bold=True, shadow=True)
        # Angry eyes on top of the cabinet.
        for side in (-1, 1):
            eye = (body.centerx + side * 26, body.top - 18)
            pygame.draw.circle(surface, (255, 255, 255), eye, 13)
            pygame.draw.circle(surface, graphics.OUTLINE, (eye[0] - 3, eye[1] + 2), 6)
            pygame.draw.line(surface, graphics.OUTLINE, (eye[0] - side * 14, eye[1] - 16), (eye[0] + side * 8, eye[1] - 8), 4)
        ui.draw_text(surface, "PUBLISHED", (body.centerx, body.bottom - 22), 20, ui.INK, "center", bold=True)
        super().draw(surface, camera, time)


# ---------------------------------------------------------------------------
# Level 2: Captain Impulse
# ---------------------------------------------------------------------------


class CaptainImpulse(Boss):
    """A charging robot bull with a traffic light on its head."""

    name = "Captain Impulse"
    WIDTH, HEIGHT = 96, 116
    WALK_SPEED = 70.0
    CHARGE_SPEED = 430.0
    HIT_POINTS = {"easy": 5, "medium": 8, "hard": 10}

    def __init__(self, arena, ground_y, difficulty_key="medium", rng=None):
        super().__init__(arena, ground_y, difficulty_key, rng)
        self.x = arena[1] - 7 * TILE_SIZE
        self.y = ground_y - self.HEIGHT
        self.facing = -1
        self.light = "green"
        self.light_timer = 2.4
        self.stop_signal_at = None
        self.charge_direction = 0
        self._plan_green()

    @property
    def body_rect(self):
        return pygame.Rect(round(self.x), round(self.y), self.WIDTH, self.HEIGHT)

    @property
    def stop_chance(self):
        """How often a green phase ends in a sudden stop signal."""
        return {1: 0.3, 2: 0.45, 3: 0.6}[self.phase]

    def _plan_green(self):
        self.light = "green"
        self.light_timer = self.green_time = max(1.4, 2.6 - 0.4 * (self.phase - 1))
        self.stop_signal_at = None
        if self.rng.random() < self.stop_chance:
            # Seconds into the green phase at which the light jumps to red.
            self.stop_signal_at = self.rng.uniform(0.35, self.green_time - 0.3)

    def _turn_red(self, sudden, player):
        self.light = "red"
        self.light_timer = 2.4
        self.charge_direction = 1 if player.center_x > self.x + self.WIDTH / 2 else -1
        self.facing = self.charge_direction
        self.events.append(("stop_signal" if sudden else "red", 0))

    def update(self, dt, player):
        if not super().update(dt, player):
            return
        left, right = self.arena[0] + TILE_SIZE * 2, self.arena[1] - TILE_SIZE * 2 - self.WIDTH
        self.light_timer -= dt
        if self.light == "green":
            if self.stop_signal_at is not None and self.green_time - self.light_timer >= self.stop_signal_at:
                self._turn_red(True, player)
                return
            self.facing = 1 if player.center_x > self.x + self.WIDTH / 2 else -1
            self.x += self.facing * self.WALK_SPEED * dt
            if self.light_timer <= 0:
                self.light, self.light_timer = "yellow", 0.7
        elif self.light == "yellow":
            if self.light_timer <= 0:
                self._turn_red(False, player)
        else:
            if self.light_timer < 1.9:  # a short wind-up, then the charge
                speed = self.CHARGE_SPEED * (1 + 0.15 * (self.phase - 1))
                self.x += self.charge_direction * speed * dt
                if self.x <= left or self.x >= right:
                    self.charge_direction *= -1
                    self.facing = self.charge_direction
                    self.events.append(("bump", 0))
            if self.light_timer <= 0:
                self._plan_green()
        self.x = min(max(self.x, left), right)

    def strike(self, rect, kind):
        if not self.active or self.defeated or not rect.colliderect(self.body_rect.inflate(16, 16)):
            return None
        if self.light == "green":
            self.damage()
            return "hit"
        if self.light == "red" and self.difficulty_key != "easy":
            self.hp = min(self.max_hp, self.hp + 1)
            self.events.append(("heal", self.hp))
            return "heal"
        return "blocked"

    def draw(self, surface, camera, time):
        body = self.body_rect.move(-camera, 0)
        blink = self.flash > 0 and int(time * 20) % 2 == 0
        metal = (255, 255, 255) if blink else (150, 70, 70)
        dark = (100, 40, 40)
        step = math.sin(time * (16 if self.light == "red" and self.light_timer < 1.9 else 6)) * 4 * (self.frozen <= 0)
        for leg_x in (body.left + 14, body.left + 40, body.left + 62):
            pygame.draw.rect(surface, dark, (leg_x, body.bottom - 22 + (step if leg_x % 2 else -step) * 0.5, 16, 22), border_radius=4)
        torso = pygame.Rect(body.left, body.top + 34, body.width, 64)
        pygame.draw.rect(surface, metal, torso, border_radius=18)
        pygame.draw.rect(surface, graphics.OUTLINE, torso, 3, border_radius=18)
        head_x = torso.right - 14 if self.facing > 0 else torso.left + 14
        head = pygame.Rect(0, 0, 50, 42)
        head.center = (head_x, torso.top + 24)
        pygame.draw.rect(surface, metal, head, border_radius=12)
        pygame.draw.rect(surface, graphics.OUTLINE, head, 3, border_radius=12)
        for side in (-1, 1):
            horn_base = (head.centerx + side * 16, head.top + 4)
            pygame.draw.polygon(surface, (240, 236, 220), [horn_base, (horn_base[0] + side * 18, horn_base[1] - 22), (horn_base[0] + side * 4, horn_base[1] + 6)])
        eye = (head.centerx + self.facing * 10, head.centery - 2)
        pygame.draw.circle(surface, (255, 240, 120), eye, 7)
        pygame.draw.circle(surface, (255, 200, 200), (head.centerx + self.facing * 20, head.bottom - 8), 5)
        # The traffic light on its back.
        light_box = pygame.Rect(0, 0, 34, 70)
        light_box.midbottom = (torso.centerx - self.facing * 8, torso.top + 6)
        pygame.draw.rect(surface, (30, 30, 40), light_box, border_radius=10)
        pygame.draw.rect(surface, ui.GOLD, light_box, 2, border_radius=10)
        colors = {"red": (240, 60, 60), "yellow": (255, 200, 60), "green": (70, 220, 100)}
        for index, name in enumerate(("red", "yellow", "green")):
            center = (light_box.centerx, light_box.top + 13 + index * 22)
            on = self.light == name
            pygame.draw.circle(surface, colors[name] if on else tuple(c // 4 for c in colors[name]), center, 9)
            if on:
                glow = pygame.Surface((80, 80), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*colors[name], 70), (40, 40), 34)
                surface.blit(glow, (center[0] - 40, center[1] - 40))
        label = {"green": "HIT IT!", "yellow": "WAIT...", "red": "HOLD BACK!"}[self.light]
        ui.draw_text(surface, label, (body.centerx, light_box.top - 6), 26, colors[self.light], "midbottom", bold=True, shadow=True)
        if self.frozen > 0:
            ice = pygame.Surface(body.inflate(20, 20).size, pygame.SRCALPHA)
            ice.fill((170, 220, 255, 90))
            surface.blit(ice, body.inflate(20, 20))
        super().draw(surface, camera, time)


# ---------------------------------------------------------------------------
# Level 3: the Rule Keeper
# ---------------------------------------------------------------------------


def make_choices(target, rng):
    """
    Make three cards that each match ``target`` on exactly one dimension.

    Returns
    -------
    tuple
        ``(cards, dimensions)``: the three cards ``(number, colour, shape)``
        and the dimension on which each one matches the target.
    """
    dimensions = list(CARD_DIMENSIONS)
    rng.shuffle(dimensions)
    target_values = dict(zip(("number", "color", "shape"), target))
    cards = []
    for matching in dimensions:
        values = {}
        for dimension in CARD_DIMENSIONS:
            if dimension == matching:
                values[dimension] = target_values[dimension]
            else:
                values[dimension] = rng.choice([v for v in CARD_VALUES[dimension] if v != target_values[dimension]])
        cards.append((values["number"], values["color"], values["shape"]))
    return cards, dimensions


class RuleKeeper(Boss):
    """
    A floating robot that changes its sorting rule without warning.

    Parameters
    ----------
    arena : tuple of float
        Left and right pixel edge of the hall.
    ground_y : float
        Height of the floor.
    card_cells : list of tuple
        The three ``(col, row)`` cells of the card blocks.
    difficulty_key : str, optional
        "easy", "medium" or "hard".
    rng : random.Random or None, optional
        Random number generator.
    """

    name = "The Rule Keeper"
    RULES = ("color", "shape", "number")
    HOVER_Y = 210.0
    SWITCH_AFTER = {"easy": 2, "medium": 3, "hard": 4}

    def __init__(self, arena, ground_y, card_cells, difficulty_key="medium", rng=None):
        self.switch_after = self.SWITCH_AFTER.get(difficulty_key, 3)
        self.HIT_POINTS = {difficulty_key: self.switch_after * len(self.RULES)}
        super().__init__(arena, ground_y, difficulty_key, rng)
        self.card_cells = list(card_cells)
        self.rule_index = 0
        self.streak = 0
        self.previous_rule = None
        self.trials = []
        self.feedback = None
        self.feedback_timer = 0.0
        self.drop_timer = 3.0
        self.x = (arena[0] + arena[1]) / 2
        self.y = self.HOVER_Y
        self._new_round()

    @property
    def rule(self):
        """The current sorting rule: "color", "shape" or "number"."""
        return self.RULES[self.rule_index % len(self.RULES)]

    @property
    def body_rect(self):
        return None  # it floats out of reach

    def _new_round(self):
        self.target = (self.rng.choice((1, 2, 3)), self.rng.choice(CARD_VALUES["color"]), self.rng.choice(CARD_VALUES["shape"]))
        self.choices, self.choice_dimensions = make_choices(self.target, self.rng)

    def choose(self, index):
        """
        The hero sorted the target card onto card block ``index``.

        Returns
        -------
        bool or None
            True if it was right, False if wrong, None while the boss is
            still showing feedback.
        """
        if not self.active or self.defeated or self.feedback is not None:
            return None
        chosen = self.choice_dimensions[index]
        correct = chosen == self.rule
        self.trials.append({
            "trial": len(self.trials) + 1,
            "rule": self.rule,
            "chosen_dimension": chosen,
            "correct": correct,
            "perseverative": (not correct) and chosen == self.previous_rule,
        })
        self.feedback, self.feedback_timer = ("right" if correct else "wrong"), 1.1
        if correct:
            self.streak += 1
            self.damage()
            if self.streak >= self.switch_after and not self.defeated:
                self.previous_rule = self.rule
                self.rule_index += 1
                self.streak = 0
        else:
            self.streak = 0
            x, _ = self.card_center(index)
            self._drop_bolt(x)
        return correct

    def card_center(self, index):
        """Pixel centre of card block ``index``."""
        col, row = self.card_cells[index]
        return ((col + 0.5) * TILE_SIZE, (row + 0.5) * TILE_SIZE)

    def _drop_bolt(self, x):
        self.hazards.append(Hazard(x, self.ground_y - 6, 52, 12, 0, 0, "warning", lifetime=0.7))
        self.hazards.append(Hazard(x, self.y + 60, 30, 70, 0, 260, "bolt", gravity=2400, lifetime=2.0))

    def update(self, dt, player):
        if self.feedback is not None:
            self.feedback_timer -= dt
            if self.feedback_timer <= 0:
                self.feedback = None
                self._new_round()
        if not super().update(dt, player):
            return
        self.x = (self.arena[0] + self.arena[1]) / 2 + math.sin(self.time * 0.7) * 160
        self.y = self.HOVER_Y + math.sin(self.time * 1.9) * 14
        self.drop_timer -= dt
        if self.drop_timer <= 0:
            self.drop_timer = {"easy": 3.6, "medium": 2.8, "hard": 2.1}.get(self.difficulty_key, 2.8)
            x = min(max(player.center_x + self.rng.uniform(-120, 120), self.arena[0] + 2 * TILE_SIZE), self.arena[1] - 2 * TILE_SIZE)
            self.hazards.append(Hazard(x, self.ground_y - 6, 52, 12, 0, 0, "warning", lifetime=0.8))
            self.hazards.append(Hazard(x, -40, 40, 40, 0, 0, "cog", gravity=900, lifetime=4.0))

    def draw(self, surface, camera, time):
        x, y = self.x - camera, self.y
        blink = self.flash > 0 and int(time * 20) % 2 == 0
        body = pygame.Rect(0, 0, 150, 110)
        body.center = (x, y)
        pygame.draw.ellipse(surface, (255, 255, 255) if blink else (90, 96, 140), body)
        pygame.draw.ellipse(surface, graphics.OUTLINE, body, 4)
        for side in (-1, 1):
            arm_end = (x + side * 110, y + 10 + math.sin(time * 3 + side) * 10)
            pygame.draw.line(surface, (90, 96, 140), (x + side * 70, y), arm_end, 10)
            worlds.draw_gear(surface, arm_end, 14, time * 3 * side, (150, 156, 170))
        for side in (-1, 1):
            pygame.draw.circle(surface, (255, 255, 255), (x + side * 30, y - 22), 13)
            look = 4 if self.feedback != "wrong" else 0
            pygame.draw.circle(surface, (200, 40, 80), (x + side * 30, y - 22 + look), 6)
        # The card to sort, held in front of its body.
        card = pygame.Rect(0, 0, 90, 64)
        card.center = (x, y + 26)
        worlds.draw_card(surface, card, self.target)
        pygame.draw.rect(surface, ui.GOLD, card, 3, border_radius=8)
        ui.draw_text(surface, "SORT ME!", (x, card.bottom + 6), 22, ui.GOLD, "midtop", bold=True, shadow=True)
        if self.feedback == "right":
            ui.draw_text(surface, "Right!", (x, y - 80), 44, ui.GREEN, "center", bold=True, shadow=True)
        elif self.feedback == "wrong":
            ui.draw_text(surface, "Wrong!", (x, y - 80), 44, ui.RED, "center", bold=True, shadow=True)
        super().draw(surface, camera, time)

    def draw_front(self, surface, camera, time):
        # The three card blocks show the cards to choose from, a bit larger
        # than the blocks themselves so that they are easy to read.
        for index, card_value in enumerate(self.choices):
            cx, cy = self.card_center(index)
            rect = pygame.Rect(0, 0, 84, 60)
            rect.center = (cx - camera, cy)
            worlds.draw_card(surface, rect, card_value, 0.9)


BOSS_KINDS = {"file_drawer": FileDrawer, "captain_impulse": CaptainImpulse, "rule_keeper": RuleKeeper}
