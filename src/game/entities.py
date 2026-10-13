"""Moving things in a level: the player, enemies, platforms and mushrooms.

Most of them are ``Body`` objects: rectangles with a velocity that collide
with the solid tiles of a level. Positions are in pixels, speeds in pixels per
second.
"""

import math

import pygame

from .config import SCREEN_HEIGHT, TILE_SIZE, PlayerSettings

GRAVITY = 2400.0


def approach(value, target, max_change):
    """Move ``value`` towards ``target`` by at most ``max_change``."""
    if value < target:
        return min(value + max_change, target)
    return max(value - max_change, target)


class Body:
    """A rectangle that moves through a level and is stopped by solid tiles."""

    def __init__(self, x, y, width, height):
        self.x, self.y = float(x), float(y)
        self.width, self.height = width, height
        self.vx = self.vy = 0.0
        self.on_ground = False
        self.hit_wall = False

    @property
    def rect(self):
        """Current hitbox as a pygame.Rect."""
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    @property
    def center_x(self):
        """Horizontal centre of the hitbox."""
        return self.x + self.width / 2

    def move(self, level, dt):
        """
        Move by the current velocity and resolve collisions with solid tiles.

        Sets ``on_ground`` and ``hit_wall``.

        Returns
        -------
        list of tuple
            The cells the body bumped into from below during this step.
        """
        self.x += self.vx * dt
        self.hit_wall = False
        for col, _ in level.solid_cells_in(self.x, self.y, self.width, self.height):
            if self.vx > 0:
                self.x = col * TILE_SIZE - self.width
            elif self.vx < 0:
                self.x = (col + 1) * TILE_SIZE
            self.hit_wall = True
        if self.hit_wall:
            self.vx = 0.0

        self.y += self.vy * dt
        self.on_ground = False
        bumped = []
        for col, row in level.solid_cells_in(self.x, self.y, self.width, self.height):
            if self.vy > 0:
                self.y = row * TILE_SIZE - self.height
                self.on_ground = True
            elif self.vy < 0:
                self.y = (row + 1) * TILE_SIZE
                bumped.append((col, row))
        if self.on_ground or bumped:
            self.vy = 0.0
        return bumped


class Player(Body):
    """
    The player character.

    Parameters
    ----------
    x : float
        Left edge of the starting position.
    ground_y : float
        Height of the surface the player starts on.
    settings : PlayerSettings, optional
        Physics, health and skill settings.
    skills : iterable of str, optional
        Keys of the skills known from the start (see ``content.SKILLS``).
    """

    WIDTH, HEIGHT = 34, 50

    def __init__(self, x, ground_y, settings=PlayerSettings(), skills=("punch",)):
        super().__init__(x, ground_y - self.HEIGHT, self.WIDTH, self.HEIGHT)
        self.settings = settings
        self.skills = set(skills)
        self.hearts = settings.start_hearts
        self.sparks = 0
        self.facing = 1
        self.has_spotlight = False
        self.boost_timer = 0.0
        self.invulnerable_timer = 0.0
        self.punch_timer = 0.0
        self.fear_cooldown = 0.0
        # "jump" or "double_jump" in the frame a jump starts, otherwise None.
        self.jump_started = None
        self.previous_bottom = self.y + self.height
        self._punch_cooldown = 0.0
        self._air_jumps = 0
        self._coyote_timer = 0.0
        self._jump_buffer = 0.0
        self._jump_held = False

    @property
    def is_boosted(self):
        """True while a Zoom-shroom speeds the player up."""
        return self.boost_timer > 0

    @property
    def is_invulnerable(self):
        """True shortly after taking damage or respawning."""
        return self.invulnerable_timer > 0

    @property
    def is_punching(self):
        """True while the fist is out."""
        return self.punch_timer > 0

    @property
    def punch_rect(self):
        """The area in front of the player that a punch hits.

        It reaches a little above the head, so that one punch clears a gap
        in a stack of crates that is high enough to walk through.
        """
        reach = self.settings.punch_reach
        left = self.x + self.width if self.facing > 0 else self.x - reach
        return pygame.Rect(round(left), round(self.y) - 14, reach, self.height + 10)

    def press_jump(self):
        """Register that the jump key went down."""
        self._jump_buffer = self.settings.jump_buffer_time
        self._jump_held = True

    def release_jump(self):
        """Register that the jump key was released; cuts a rising jump short."""
        self._jump_held = False
        if self.vy < -self.settings.jump_cut_speed:
            self.vy = -self.settings.jump_cut_speed

    def start_punch(self):
        """Throw a punch; return False if the skill is missing or not ready."""
        if "punch" not in self.skills or self._punch_cooldown > 0:
            return False
        self.punch_timer = self.settings.punch_time
        self._punch_cooldown = self.settings.punch_cooldown
        return True

    def start_fear(self):
        """Use fear conditioning; return False if it is missing or recharging."""
        if "fear" not in self.skills or self.fear_cooldown > 0:
            return False
        self.fear_cooldown = self.settings.fear_cooldown
        return True

    def update(self, dt, move_direction, fast_fall, level):
        """
        Advance the player by one time step.

        Parameters
        ----------
        dt : float
            Time step in seconds.
        move_direction : int
            -1 (left), 0 or 1 (right).
        fast_fall : bool
            True while the player holds the fast-fall key.
        level : Level
            The level to collide with.

        Returns
        -------
        tuple or None
            The block cell hit with the head in this step, if any.
        """
        settings = self.settings
        for timer in ("boost_timer", "invulnerable_timer", "punch_timer", "fear_cooldown", "_punch_cooldown"):
            setattr(self, timer, max(0.0, getattr(self, timer) - dt))
        self._jump_buffer -= dt
        if self.on_ground:
            self._coyote_timer = settings.coyote_time
            self._air_jumps = 1
        else:
            self._coyote_timer -= dt

        speed = settings.walk_speed * (settings.boost_multiplier if self.is_boosted else 1)
        acceleration = settings.ground_acceleration if self.on_ground else settings.air_acceleration
        self.vx = approach(self.vx, move_direction * speed, acceleration * dt)
        if move_direction:
            self.facing = move_direction

        self.jump_started = None
        if self._jump_buffer > 0:
            if self._coyote_timer > 0:
                self._jump(settings.jump_speed, "jump")
            elif "double_jump" in self.skills and self._air_jumps > 0:
                self._air_jumps -= 1
                self._jump(settings.jump_speed * settings.double_jump_factor, "double_jump")
        gravity = settings.gravity * (settings.fast_fall_gravity_factor if fast_fall else 1)
        self.vy = min(self.vy + gravity * dt, settings.max_fall_speed)

        self.previous_bottom = self.y + self.height
        if self.vy < 0:
            self._reveal_hidden_blocks(level, self.y + self.vy * dt)
        bumped = self.move(level, dt)
        self.x = min(max(self.x, 0.0), level.pixel_width - self.width)
        if not bumped:
            return None
        return min(bumped, key=lambda cell: abs((cell[0] + 0.5) * TILE_SIZE - self.center_x))

    def _jump(self, speed, kind):
        self.vy = -speed
        self._jump_buffer = self._coyote_timer = 0.0
        self.jump_started = kind
        if not self._jump_held:
            self.release_jump()

    def _reveal_hidden_blocks(self, level, next_top):
        """Make hidden blocks solid if the head is about to pass into them."""
        for col, row in list(level.hidden_blocks):
            bottom = (row + 1) * TILE_SIZE
            overlaps = col * TILE_SIZE < self.x + self.width and (col + 1) * TILE_SIZE > self.x
            if overlaps and next_top < bottom <= self.y + 0.01:
                level.reveal_hidden_block((col, row))

    def bounce(self):
        """Bounce upwards after stomping an enemy (higher while jump is held)."""
        settings = self.settings
        self.vy = -(settings.jump_speed * 0.9 if self._jump_held else settings.stomp_bounce_speed)
        self._air_jumps = 1

    def take_hit(self, from_x):
        """
        Lose a heart and get knocked away from ``from_x``.

        Returns
        -------
        bool
            True if a heart was lost, False while invulnerable.
        """
        if self.is_invulnerable:
            return False
        self.hearts -= 1
        self.invulnerable_timer = self.settings.invulnerable_time
        self.vx = -360.0 if from_x > self.center_x else 360.0
        self.vy = -460.0
        return True

    def heal(self, amount=1):
        """Gain hearts up to the maximum; return True if any were gained."""
        before = self.hearts
        self.hearts = min(self.hearts + amount, self.settings.max_hearts)
        return self.hearts > before

    def add_sparks(self, amount=1):
        """Collect sparks; return True if this earned an extra heart."""
        per_heart = self.settings.sparks_per_heart
        earned = (self.sparks + amount) // per_heart > self.sparks // per_heart
        self.sparks += amount
        return earned and self.heal()

    def respawn(self, x, ground_y):
        """Place the player on a surface, standing still and briefly invulnerable."""
        self.x, self.y = float(x), float(ground_y - self.height)
        self.vx = self.vy = 0.0
        self.boost_timer = 0.0
        self.invulnerable_timer = self.settings.invulnerable_time


class MovingPlatform:
    """
    A platform that glides back and forth and carries the player.

    It is solid only from above: the player can jump up through it.

    Parameters
    ----------
    x, y : float
        Top-left corner at one end of the path.
    width : int
        Width in pixels.
    travel_x, travel_y : float
        Offset of the other end of the path in pixels.
    period : float
        Seconds for one full trip there and back.
    """

    HEIGHT = 20
    # How far above the platform a falling body is already pulled onto it.
    SNAP_DISTANCE = 8

    def __init__(self, x, y, width, travel_x=0.0, travel_y=0.0, period=4.0):
        self.start_x, self.start_y = float(x), float(y)
        self.x, self.y = self.start_x, self.start_y
        self.width = width
        self.travel_x, self.travel_y, self.period = travel_x, travel_y, period
        self.delta_x = self.delta_y = 0.0
        self.previous_y = self.y
        self.time = 0.0

    @property
    def rect(self):
        """Current area of the platform."""
        return pygame.Rect(round(self.x), round(self.y), self.width, self.HEIGHT)

    def update(self, dt):
        """Glide along the path; remembers how far the platform moved."""
        self.time += dt
        share = 0.5 * (1 - math.cos(2 * math.pi * self.time / self.period))
        new_x = self.start_x + self.travel_x * share
        new_y = self.start_y + self.travel_y * share
        self.delta_x, self.delta_y = new_x - self.x, new_y - self.y
        self.previous_y = self.y
        self.x, self.y = new_x, new_y

    def carry(self, body):
        """
        Put ``body`` on the platform if it is landing or standing on it.

        Call this after the body has moved. Returns True if it is carried.
        """
        over = body.x + body.width > self.x and body.x < self.x + self.width
        was_above = body.previous_bottom <= self.previous_y + self.SNAP_DISTANCE
        reaches = body.y + body.height >= self.y - self.SNAP_DISTANCE - abs(self.delta_y)
        if body.vy < 0 or not (over and was_above and reaches):
            return False
        body.y = self.y - body.height
        body.x += self.delta_x
        body.vy = 0.0
        body.on_ground = True
        return True


class Enemy(Body):
    """
    Base class of all enemies.

    Class attributes describe a kind of enemy: its size, its walking and
    fleeing speed and whether it can be stomped or punched.

    Parameters
    ----------
    x : float
        Left edge of the starting position.
    ground_y : float
        Height of the surface the enemy starts on.
    patrol : tuple of float or None, optional
        Left and right pixel limits of the area the enemy walks in.
    """

    kind = "enemy"
    WIDTH, HEIGHT = 40, 34
    SPEED = 70.0
    FLEE_SPEED = 210.0
    SQUISH_TIME = 0.4
    stompable = True
    punchable = True

    def __init__(self, x, ground_y, patrol=None):
        super().__init__(x, ground_y - self.HEIGHT, self.WIDTH, self.HEIGHT)
        self.patrol = patrol
        self.direction = -1
        self.fear_timer = 0.0
        self.squish_timer = None
        self.knocked_out = False

    @property
    def is_afraid(self):
        """True while the enemy runs away after fear conditioning."""
        return self.fear_timer > 0

    @property
    def is_active(self):
        """True while the enemy can still touch the player."""
        return self.squish_timer is None and not self.knocked_out

    @property
    def is_gone(self):
        """True when the enemy can be removed from the level."""
        return (self.squish_timer is not None and self.squish_timer <= 0) or self.y > SCREEN_HEIGHT + 200

    def squish(self):
        """Defeat the enemy by a stomp."""
        self.squish_timer = self.SQUISH_TIME

    def knock_out(self, direction):
        """Defeat the enemy by a punch: it flies off the screen."""
        self.knocked_out = True
        self.vx, self.vy = direction * 260.0, -520.0

    def frighten(self, duration, from_x):
        """Make the enemy run away from pixel column ``from_x``."""
        self.fear_timer = duration
        self.direction = 1 if self.center_x >= from_x else -1

    def update(self, dt, level):
        """Walk, fall and turn around where needed."""
        if self.squish_timer is not None:
            self.squish_timer -= dt
            return
        self.vy = min(self.vy + GRAVITY * dt, 1000.0)
        if self.knocked_out:
            self.x += self.vx * dt
            self.y += self.vy * dt
            return
        self.fear_timer = max(0.0, self.fear_timer - dt)
        self.vx = self.direction * (self.FLEE_SPEED if self.is_afraid else self.SPEED)
        self.move(level, dt)
        if self.is_afraid:
            return  # a frightened enemy does not watch its step
        if self.hit_wall or self._leaves_patrol():
            self.direction *= -1
        elif self.on_ground:
            front_x = self.x + self.width + 2 if self.direction > 0 else self.x - 2
            below = (int(front_x // TILE_SIZE), int((self.y + self.height + 2) // TILE_SIZE))
            if not level.is_solid(*below):
                self.direction *= -1

    def _leaves_patrol(self):
        if self.patrol is None:
            return False
        left, right = self.patrol
        return (self.direction < 0 and self.x <= left) or (self.direction > 0 and self.x + self.width >= right)


class Distractor(Enemy):
    """The basic enemy: walks back and forth, can be stomped and punched."""

    kind = "distractor"


class Spikeback(Enemy):
    """A spiky enemy: jumping on it hurts, so it has to be punched."""

    kind = "spikeback"
    WIDTH, HEIGHT = 42, 34
    SPEED = 55.0
    stompable = False


class Brute(Enemy):
    """A big, tough enemy: only fear conditioning gets it out of the way."""

    kind = "brute"
    WIDTH, HEIGHT = 64, 100
    SPEED = 40.0
    FLEE_SPEED = 230.0
    stompable = False
    punchable = False


class Buzzer(Enemy):
    """
    A flying enemy that hovers back and forth.

    Parameters
    ----------
    x : float
        Left edge of the starting position.
    ground_y : float
        Height it hovers at (bottom of the hitbox).
    patrol : tuple of float or None, optional
        Left and right pixel limits; defaults to three tiles to each side.
    """

    kind = "buzzer"
    WIDTH, HEIGHT = 40, 30
    SPEED = 90.0
    BOB_HEIGHT = 18

    def __init__(self, x, ground_y, patrol=None):
        super().__init__(x, ground_y, patrol or (x - 3 * TILE_SIZE, x + 3 * TILE_SIZE + self.WIDTH))
        self.hover_y = self.y
        self.time = 0.0

    def update(self, dt, level):
        """Hover along the patrol path; falls only when defeated."""
        if not self.is_active:
            super().update(dt, level)
            return
        self.time += dt
        self.fear_timer = max(0.0, self.fear_timer - dt)
        self.vx = self.direction * (self.FLEE_SPEED if self.is_afraid else self.SPEED)
        self.vy = 0.0
        self.y = self.hover_y
        self.move(level, dt)
        self.y = self.hover_y + math.sin(self.time * 3) * self.BOB_HEIGHT
        if not self.is_afraid and (self.hit_wall or self._leaves_patrol()):
            self.direction *= -1


ENEMY_KINDS = {cls.kind: cls for cls in (Distractor, Spikeback, Brute, Buzzer)}


class Mushroom(Body):
    """A Zoom-shroom that slides along the ground after leaving its block."""

    SIZE = 36
    SPEED = 110.0

    def __init__(self, cell):
        col, row = cell
        super().__init__(col * TILE_SIZE + (TILE_SIZE - self.SIZE) / 2, row * TILE_SIZE - self.SIZE, self.SIZE, self.SIZE)
        self.direction = 1

    def update(self, dt, level):
        """Slide, fall and bounce off walls."""
        self.vx = self.direction * self.SPEED
        self.vy = min(self.vy + GRAVITY * dt, 1000.0)
        self.move(level, dt)
        if self.hit_wall:
            self.direction *= -1


class Effect:
    """
    A short visual effect at a pixel position.

    Parameters
    ----------
    kind : str
        "text" (rising text), "ring" (growing circle) or "burst" (debris).
    x, y : float
        Position in the level.
    text : str, optional
        The text of a "text" effect.
    color : tuple of int, optional
        RGB colour.
    lifetime : float, optional
        Seconds until the effect disappears.
    """

    def __init__(self, kind, x, y, text="", color=(255, 255, 255), lifetime=1.1):
        self.kind, self.x, self.y, self.text, self.color = kind, x, y, text, color
        self.lifetime = lifetime
        self.age = 0.0

    @property
    def progress(self):
        """Share of the lifetime that has passed, from 0 to 1."""
        return min(1.0, self.age / self.lifetime)

    @property
    def is_gone(self):
        """True when the effect is over."""
        return self.age >= self.lifetime

    def update(self, dt):
        """Age the effect; texts rise."""
        self.age += dt
        if self.kind == "text":
            self.y -= 50 * dt
