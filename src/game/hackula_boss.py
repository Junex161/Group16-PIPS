"""The final boss: Count Hackula himself.

The fight has three phases, one for each topic of the game:

1. **Shadows (attention):** the Count turns almost invisible and flits
   through the dark hall together with two dark copies of himself. Only the
   real Count casts a shadow on the floor and has glowing eyes - pay
   attention to them and hit him. Touching a copy (a distractor) bursts it
   into a swarm of bats.
2. **Swoops (response inhibition):** he swoops across the hall, just above
   the hero's head. With green eyes, jump into him or punch him; with red
   eyes, stay on the ground - attacking heals him (a commission error) and
   touching him hurts. Sometimes the eyes turn red without warning - stop!
   The Stop Signal (R) freezes him in the air.
3. **Sunlight (executive control and Open Science):** he hides in the dark
   and closes the curtains. Three windows stand for Preregister, Open data
   and Replicate. He shows them in an order; hit the window blocks from below
   in the same order (keep it in working memory!) to let the light in.
   Sunlight - like open, transparent science - finishes the vampire.

The QRP Blaster is no use against him: p-hacking only feeds him and heals
him. He has to be beaten with the skills of the game.
"""

import math

import pygame

from . import graphics, ui
from .bosses import BOSS_KINDS, Boss, Hazard
from .config import TILE_SIZE

PHASES = ("shadow", "swoop", "sunlight")
# How visible the Count and his copies are in the dark during the first phase (0 to 255).
SHADOW_ALPHA = 55
# Bats that fly out of a copy the hero touches, per difficulty.
BATS_PER_COPY = {"easy": 2, "medium": 3, "hard": 4}
# The three windows of the last phase and how they are drawn.
WINDOWS = ("preregister", "open_data", "replicate")
WINDOW_LABELS = {"preregister": "PREREGISTER", "open_data": "OPEN DATA", "replicate": "REPLICATE"}
EYES = {"green": (90, 230, 110), "red": (240, 60, 60), "gold": (255, 214, 92)}


def draw_count(surface, center, time, eyes="gold", alpha=255, flying=True, shadow_y=None, scale=1.0):
    """
    Draw Count Hackula, a vampire bat in a cape, centred on ``center``.

    Parameters
    ----------
    eyes : str
        Colour of the eyes: "gold", "green" or "red".
    alpha : int
        Opacity, for the see-through copies and when he burns away.
    flying : bool
        Flapping wings instead of a hanging cape.
    shadow_y : float or None
        Height of the floor; the real Count casts a shadow there.
    """
    x, y = center
    if shadow_y is not None:
        width = 100 * scale * (1 - min(0.5, (shadow_y - y) / 700))
        pygame.draw.ellipse(surface, (8, 4, 12), (x - width / 2, shadow_y - 10, width, 18))
        pygame.draw.ellipse(surface, (255, 214, 92), (x - width / 2 - 4, shadow_y - 12, width + 8, 22), 2)
    size = int(150 * scale)
    image = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size / 2
    s = scale
    flap = math.sin(time * 9) * 18 * s if flying else 0
    for side in (-1, 1):
        wing = [(c + side * 16 * s, c - 6 * s), (c + side * 66 * s, c - 30 * s + flap), (c + side * 58 * s, c + 4 * s), (c + side * 44 * s, c - 4 * s), (c + side * 34 * s, c + 14 * s)]
        pygame.draw.polygon(image, (60, 20, 70), wing)
        pygame.draw.polygon(image, (30, 10, 40), wing, max(1, int(2 * s)))
    cape = [(c - 26 * s, c + 40 * s), (c - 18 * s, c - 4 * s), (c, c - 10 * s), (c + 18 * s, c - 4 * s), (c + 26 * s, c + 40 * s)]
    pygame.draw.polygon(image, (40, 16, 50), cape)
    pygame.draw.polygon(image, (170, 30, 50), [(c - 18 * s, c - 4 * s), (c, c + 12 * s), (c + 18 * s, c - 4 * s)])
    pygame.draw.circle(image, (205, 205, 225), (c, c - 22 * s), 17 * s)
    for side in (-1, 1):
        pygame.draw.polygon(image, (205, 205, 225), [(c + side * 8 * s, c - 34 * s), (c + side * 16 * s, c - 54 * s), (c + side * 18 * s, c - 30 * s)])
        pygame.draw.circle(image, EYES[eyes], (c + side * 7 * s, c - 25 * s), 4 * s)
    pygame.draw.polygon(image, (255, 255, 255), [(c - 6 * s, c - 13 * s), (c - 3 * s, c - 6 * s), (c - 1 * s, c - 13 * s)])
    pygame.draw.polygon(image, (255, 255, 255), [(c + 6 * s, c - 13 * s), (c + 3 * s, c - 6 * s), (c + 1 * s, c - 13 * s)])
    label = ui.get_font(max(10, int(26 * s)), bold=True).render("p", True, (255, 214, 92))
    image.blit(label, label.get_rect(center=(c, c + 22 * s)))
    if alpha < 255:
        image.set_alpha(alpha)
    surface.blit(image, image.get_rect(center=(x, y)))


def draw_window_icon(surface, rect, kind, open_share=0.0):
    """Draw one of the three windows: a curtain over an Open Science symbol."""
    pygame.draw.rect(surface, (40, 36, 70), rect, border_radius=6)
    inner = rect.inflate(-10, -10)
    if open_share > 0:
        pygame.draw.rect(surface, (255, 236, 150), inner, border_radius=4)
    x, y = inner.center
    color = (60, 60, 90) if open_share > 0 else (230, 230, 245)
    if kind == "preregister":
        pygame.draw.rect(surface, color, (x - 9, y - 2, 18, 13), border_radius=3)
        pygame.draw.arc(surface, color, (x - 7, y - 13, 14, 18), 0, math.pi, 3)
    elif kind == "open_data":
        pygame.draw.rect(surface, color, (x - 12, y - 4, 24, 14), 3, border_radius=2)
        pygame.draw.line(surface, color, (x - 12, y - 4), (x - 4, y - 13), 3)
        pygame.draw.line(surface, color, (x + 12, y - 4), (x + 4, y - 13), 3)
    else:
        for dx in (-7, 7):
            pygame.draw.circle(surface, color, (x + dx, y - 6), 5)
            pygame.draw.rect(surface, color, (x + dx - 5, y, 10, 10), border_radius=3)
    if open_share < 1:
        # The red curtains slide apart as the window opens.
        width = inner.width / 2 * (1 - open_share)
        for left in (inner.left, inner.right - width):
            pygame.draw.rect(surface, (150, 30, 50), (left, inner.top, width, inner.height))
    pygame.draw.rect(surface, graphics.OUTLINE, rect, 3, border_radius=6)


class CountHackula(Boss):
    """
    Count Hackula, the final boss (see the module docstring for the phases).

    Parameters
    ----------
    arena : tuple of float
        Left and right pixel edge of the throne room.
    ground_y : float
        Height of the floor.
    window_cells : list of tuple
        The three ``(col, row)`` cells of the window blocks.
    difficulty_key : str, optional
        "easy", "medium" or "hard".
    rng : random.Random or None, optional
        Random number generator.
    """

    name = "Count Hackula"
    GHOST_FIELDS = ("x", "y", "hp", "flash", "frozen", "eyes", "spots", "real_spot", "time")
    HITS_PER_PHASE = {"easy": 2, "medium": 3, "hard": 4}
    RADIUS = 34
    SWOOP_DEPTH = 150
    # Touching him (jumping into him) counts as an attack, not only as a hit on the hero.
    touch_hits = True

    def __init__(self, arena, ground_y, window_cells, difficulty_key="medium", rng=None):
        self.hits_per_phase = self.HITS_PER_PHASE.get(difficulty_key, 3)
        # Two phases of hits, and the sunlight as the final blow.
        self.HIT_POINTS = {difficulty_key: 2 * self.hits_per_phase + 1}
        super().__init__(arena, ground_y, difficulty_key, rng)
        self.window_cells = list(window_cells)
        self.left, self.right = arena[0] + 3 * TILE_SIZE, arena[1] - 3 * TILE_SIZE
        self.x, self.y = (self.left + self.right) / 2, ground_y - 220
        self.eyes = "gold"
        self.spots = []
        self.real_spot = 0
        self.move_from = None
        self.move_timer = 0.0
        self.shuffle_timer = 0.0
        self.throw_timer = 3.0
        self.swoop = None
        self.swoop_timer = 1.5
        self.sequence = []
        self.shown_until = 0.0
        self.progress = 0
        self.opened = set()
        self.reset_timer = 0.0
        self.burn = 0.0
        self.copy_cooldown = 0.0
        self.hero_x = self.x
        self._start_shadow()

    # ----- phases ---------------------------------------------------------

    @property
    def phase(self):
        """The current phase: "shadow", "swoop" or "sunlight"."""
        done = self.max_hp - self.hp
        if done < self.hits_per_phase:
            return "shadow"
        if done < 2 * self.hits_per_phase:
            return "swoop"
        return "sunlight"

    def _hover_spots(self):
        width = self.right - self.left
        return [(self.left + width * share, self.ground_y - 62) for share in (0.1, 0.5, 0.9)]

    def apply_ghost_state(self, state):
        super().apply_ghost_state(state)
        # The recorded Count stays where it was recorded.
        self.spots = [tuple(spot) for spot in self.spots]
        self.move_from, self.move_timer = list(self.spots), 0.0

    def _start_shadow(self):
        self.spots = self._hover_spots()
        self._shuffle()

    def _shuffle(self):
        """The Count flits to another place in the dark."""
        self.move_from = [(self.x, self.y)] * 3 if not self.spots else list(self.spots)
        self.rng.shuffle(self.spots)
        self.real_spot = self.rng.randrange(3)
        self.move_timer = 0.6
        self.shuffle_timer = {"easy": 4.0, "medium": 3.2, "hard": 2.6}.get(self.difficulty_key, 3.2)
        self.events.append(("shuffle", 0))

    def _positions(self):
        """Current centres of the three places he flits between (he is at ``real_spot``)."""
        share = 1 - max(0.0, self.move_timer) / 0.6
        return [(a[0] + (b[0] - a[0]) * share, a[1] + (b[1] - a[1]) * share - math.sin(share * math.pi) * 80) for a, b in zip(self.move_from, self.spots)]

    def copy_rects(self):
        """Hitboxes of the two dark copies (only in the first phase, once they have landed)."""
        if self.defeated or self.phase != "shadow" or self.move_timer > 0:
            return []
        rects = []
        for index, (x, y) in enumerate(self._positions()):
            if index != self.real_spot:
                rects.append(pygame.Rect(x - self.RADIUS, y - self.RADIUS, 2 * self.RADIUS, 2 * self.RADIUS))
        return rects

    def _burst_copy(self, rect):
        """A copy was only a distraction: it bursts into bats and the Count flits away."""
        self.copy_cooldown = 1.2
        self.events.append(("decoy", 0))
        count = BATS_PER_COPY.get(self.difficulty_key, 3)
        for index in range(count):
            # They flutter up first and dive at where the hero was about 1.5 s later: keep moving!
            spread = (index - (count - 1) / 2) * 90
            vx = (self.hero_x + spread - rect.centerx) / 1.5
            self.hazards.append(Hazard(rect.centerx, rect.top, 30, 18, vx, -260, "bat", gravity=420, lifetime=3.0))
        self._shuffle()

    def _feed(self):
        """A QRP shot: p-hacking only feeds the Count and heals him a little."""
        start = 0 if self.phase == "shadow" else self.hits_per_phase
        if self.max_hp - self.hp > start:
            self.hp += 1
        self.events.append(("fed", self.hp))
        return "fed"

    def _start_sunlight(self):
        self.sequence = list(WINDOWS)
        self.rng.shuffle(self.sequence)
        self.progress = 0
        self.opened = set()
        repeats = 2 if self.difficulty_key == "easy" else 1
        self.shown_until = self.time + 1.0 * len(self.sequence) * repeats + 0.6
        self.events.append(("sequence", 0))

    @property
    def showing_sequence(self):
        """True while the Count shows the order of the windows."""
        return self.phase == "sunlight" and self.time < self.shown_until

    def shown_window(self):
        """The window the Count points at right now, or None."""
        if not self.showing_sequence:
            return None
        repeats = 2 if self.difficulty_key == "easy" else 1
        start = self.shown_until - 1.0 * len(self.sequence) * repeats - 0.6
        index = int((self.time - start) / 1.0)
        return self.sequence[index % len(self.sequence)] if 0 <= index < len(self.sequence) * repeats else None

    # ----- the fight ------------------------------------------------------

    @property
    def body_rect(self):
        if self.defeated or self.phase == "sunlight":
            return None
        if self.phase == "shadow":
            x, y = self._positions()[self.real_spot]
        else:
            x, y = self.x, self.y
        return pygame.Rect(x - self.RADIUS, y - self.RADIUS, 2 * self.RADIUS, 2 * self.RADIUS)

    def damage(self, amount=1):
        before = self.phase
        super().damage(amount)
        if self.defeated:
            return
        if self.phase != before:
            self.events.append(("phase", 0))
            if self.phase == "swoop":
                self.x, self.y = self.right, self.ground_y - 260
                self.swoop, self.swoop_timer = None, 1.2
            elif self.phase == "sunlight":
                self.x, self.y = (self.left + self.right) / 2, self.ground_y - 300
                self._start_sunlight()
        elif self.phase == "shadow":
            self._shuffle()

    def update(self, dt, player):
        if self.defeated:
            self.burn = min(1.0, self.burn + dt)
        if not super().update(dt, player):
            return
        phase = self.phase
        self.hero_x = player.center_x
        self.copy_cooldown -= dt
        if phase == "shadow" and self.copy_cooldown <= 0:
            for rect in self.copy_rects():
                if rect.colliderect(player.rect):
                    self._burst_copy(rect)
                    break
        self.throw_timer -= dt
        if self.throw_timer <= 0 and phase != "swoop":
            self.throw_timer = {"easy": 4.0, "medium": 3.0, "hard": 2.2}.get(self.difficulty_key, 3.0)
            self._throw(player.center_x)
        if phase == "shadow":
            self.move_timer -= dt
            self.shuffle_timer -= dt
            if self.shuffle_timer <= 0:
                self._shuffle()
            self.x, self.y = self._positions()[self.real_spot]
        elif phase == "swoop":
            self._update_swoop(dt, player)
        else:
            self.y = self.ground_y - 300 + math.sin(self.time * 2) * 10
            if self.reset_timer > 0:
                self.reset_timer -= dt
                if self.reset_timer <= 0:
                    self._start_sunlight()

    def _update_swoop(self, dt, player):
        if self.swoop is None:
            self.swoop_timer -= dt
            self.eyes = "gold"
            if self.swoop_timer <= 0:
                start = self.x
                end = self.left if start > (self.left + self.right) / 2 else self.right
                red_chance = {"easy": 0.25, "medium": 0.35, "hard": 0.45}.get(self.difficulty_key, 0.35)
                eyes = "red" if self.rng.random() < red_chance else "green"
                # Sometimes green turns red half-way through: a stop signal.
                sudden = eyes == "green" and self.rng.random() < 0.35
                self.swoop = {"start": start, "end": end, "time": 0.0, "length": 2.2, "eyes": eyes, "sudden_at": self.rng.uniform(0.3, 0.6) if sudden else None}
            return
        swoop = self.swoop
        swoop["time"] += dt
        share = min(1.0, swoop["time"] / swoop["length"])
        if swoop["sudden_at"] is not None and share >= swoop["sudden_at"] and swoop["eyes"] == "green":
            swoop["eyes"] = "red"
            self.events.append(("stop_signal", 0))
        self.eyes = swoop["eyes"]
        self.x = swoop["start"] + (swoop["end"] - swoop["start"]) * share
        # Down to just above the hero's head, then up again: standing still is
        # safe, jumping into him hits him on green and hurts on red.
        self.y = self.ground_y - 260 + math.sin(share * math.pi) * self.SWOOP_DEPTH
        if share >= 1:
            self.swoop = None
            self.swoop_timer = {"easy": 1.8, "medium": 1.3, "hard": 0.9}.get(self.difficulty_key, 1.3)

    def _throw(self, target_x):
        flight, gravity = 1.1, 1400.0
        vx = (target_x - self.x) / flight
        vy = (self.ground_y - self.y - 0.5 * gravity * flight**2) / flight
        self.hazards.append(Hazard(self.x, self.y, 52, 30, vx, vy, "paper", gravity, 3.0, "p<.05"))

    def strike(self, rect, kind):
        if not self.active or self.defeated:
            return None
        if self.flash > 0:
            return "blocked"  # a short break after each hit, so one jump counts once
        phase = self.phase
        if kind == "shot":
            body = self.body_rect
            targets = ([body] if body is not None else []) + self.copy_rects()
            return self._feed() if any(rect.colliderect(target) for target in targets) else None
        if phase == "shadow":
            body = self.body_rect
            if body is not None and rect.colliderect(body):
                self.damage()
                return "hit"
            copy = next((copy for copy in self.copy_rects() if rect.colliderect(copy)), None)
            if copy is not None and self.copy_cooldown <= 0:
                self._burst_copy(copy)
                return "decoy"
            return None
        if phase == "swoop":
            body = self.body_rect
            if body is None or not rect.colliderect(body.inflate(16, 16)):
                return None
            if self.eyes == "green":
                self.damage()
                return "hit"
            if self.eyes == "red" and self.difficulty_key != "easy":
                if self.max_hp - self.hp > self.hits_per_phase:
                    self.hp += 1
                self.events.append(("heal", self.hp))
                return "heal"
            return "blocked"
        return None

    def choose(self, index):
        """
        The hero hit window block ``index`` from below (sunlight phase).

        Returns True if it was the next window in the order, False if not,
        and None if windows cannot be chosen right now.
        """
        if not self.active or self.defeated or self.phase != "sunlight" or self.showing_sequence or self.reset_timer > 0:
            return None
        window = WINDOWS[index]
        if window in self.opened:
            return None
        if window == self.sequence[self.progress]:
            self.opened.add(window)
            self.progress += 1
            self.events.append(("window", index))
            if self.progress == len(self.sequence):
                self.damage(self.hp)
            return True
        # Wrong order: the curtains close and he shows a new order.
        self.opened = set()
        self.progress = 0
        self.reset_timer = 1.4
        x = (self.window_cells[index][0] + 0.5) * TILE_SIZE
        self.hazards.append(Hazard(x, self.ground_y - 6, 52, 12, 0, 0, "warning", lifetime=0.7))
        self.hazards.append(Hazard(x, self.y + 60, 30, 70, 0, 260, "bolt", gravity=2400, lifetime=2.0))
        return False

    # ----- drawing --------------------------------------------------------

    def draw(self, surface, camera, time):
        if self.defeated and self.burn >= 1:
            return
        phase = self.phase
        if self.defeated:
            draw_count(surface, (self.x - camera, self.y - self.burn * 80), time, "gold", int(255 * (1 - self.burn)))
            return
        if phase == "shadow":
            # The copies look just like him in the dark, but cast no shadow.
            for index, (x, y) in enumerate(self._positions()):
                if index != self.real_spot:
                    draw_count(surface, (x - camera, y), time + index, "gold", SHADOW_ALPHA)
            # Almost invisible in the dark: only the shadow and the eyes show where he is.
            x, y = self._positions()[self.real_spot]
            alpha = 255 if self.flash > 0 else SHADOW_ALPHA
            draw_count(surface, (x - camera, y), time, "gold", alpha, shadow_y=self.ground_y)
            for side in (-1, 1):
                glint = 4 + int(2 * math.sin(time * 8))
                pygame.draw.circle(surface, EYES["gold"], (x - camera + side * 7, y - 25), glint)
        else:
            blink = self.flash > 0 and int(time * 20) % 2 == 0
            draw_count(surface, (self.x - camera, self.y), time, self.eyes, 120 if blink else 255, shadow_y=self.ground_y if phase == "swoop" else None)
            label = {"green": "JUMP INTO HIM!", "red": "STAY DOWN!"}.get(self.eyes)
            if phase == "swoop" and label:
                ui.draw_text(surface, label, (self.x - camera, self.y - 70), 26, EYES[self.eyes], "midbottom", bold=True, shadow=True)
        if self.frozen > 0:
            pygame.draw.circle(surface, (170, 220, 255), (self.x - camera, self.y), 50, 3)

    def draw_front(self, surface, camera, time):
        """The windows, the sunbeams and the order the Count shows."""
        shown = self.shown_window()
        for index, (col, row) in enumerate(self.window_cells):
            window = WINDOWS[index]
            rect = pygame.Rect(col * TILE_SIZE - camera - 12, row * TILE_SIZE - 12, TILE_SIZE + 24, TILE_SIZE + 24)
            is_open = window in self.opened or self.defeated
            if is_open:
                beam = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
                pygame.draw.polygon(beam, (255, 240, 160, 70), [(rect.left, rect.top), (rect.right, rect.top), (self.x - camera + 30, self.y), (self.x - camera - 30, self.y)])
                surface.blit(beam, (0, 0))
            draw_window_icon(surface, rect, window, 1.0 if is_open else 0.0)
            ui.draw_text(surface, WINDOW_LABELS[window], (rect.centerx, rect.bottom + 4), 20, ui.WHITE, "midtop", bold=True, shadow=True)
            if shown == window:
                pygame.draw.rect(surface, ui.GOLD, rect.inflate(14, 14), 5, border_radius=10)
        if self.phase == "sunlight" and not self.defeated:
            if self.showing_sequence:
                text = "Remember the order!"
            elif self.reset_timer > 0:
                text = "Wrong order! Watch again ..."
            else:
                text = f"Open the windows in his order: {self.progress}/{len(self.sequence)}"
            ui.draw_text(surface, text, (surface.get_width() // 2, 112), 30, ui.GOLD, "midtop", bold=True, shadow=True)
            if shown:
                bubble = pygame.Rect(0, 0, 150, 34)
                bubble.midbottom = (self.x - camera, self.y - 60)
                ui.draw_panel(surface, bubble, radius=10)
                ui.draw_text(surface, WINDOW_LABELS[shown], bubble.center, 22, ui.GOLD, "center", bold=True)


def register():
    """Add Count Hackula to ``bosses.BOSS_KINDS``."""
    BOSS_KINDS["count_hackula"] = CountHackula
