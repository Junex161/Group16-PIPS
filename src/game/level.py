"""Level data: the tile grid and everything that is placed in a level.

A level is a grid of square tiles. Positions are given as ``(col, row)`` cells
with row 0 at the top of the screen. The ``add_*`` methods are used by the
level definitions (see ``level_one.py``) to build a level step by step.

A level is split into zones ("worlds") that lie next to each other on the
grid. The camera never leaves the zone the player is in, and pipes are the
only way from one zone to another.
"""

from dataclasses import dataclass, field

import pygame

from .config import SCREEN_HEIGHT, TILE_SIZE

LEVEL_ROWS = SCREEN_HEIGHT // TILE_SIZE
# Row of the top ground tile; characters on the ground stand in the row above.
GROUND_ROW = 12
# What a question block can hold; the items are explained in entities.PowerUp.
BLOCK_CONTENTS = ("spark", "heart", "mushroom", "star", "shield")
THEMES = ("meadow", "forest", "cave", "sky", "sunset")
PIPE_KINDS = ("travel", "bonus", "quiz", "exit")
PIPE_WIDTH_TILES = 2
PIPE_HEIGHT_TILES = 2


@dataclass
class Spark:
    """A collectible spark at a pixel position."""

    x: float
    y: float
    collected: bool = False


@dataclass
class Checkpoint:
    """A flag at pixel column ``x`` on a surface at pixel height ``ground_y``."""

    x: float
    ground_y: float
    active: bool = False


@dataclass
class Shrine:
    """A glowing stone that teaches the skill ``skill`` (see content.SKILLS)."""

    skill: str
    x: float
    ground_y: float
    used: bool = False


@dataclass
class InsightOrb:
    """A floating orb; touching it plays the animation of the insight ``key``."""

    key: str
    x: float
    y: float
    collected: bool = False


@dataclass
class Demo:
    """A short animation that plays once when the player walks past ``x``."""

    key: str
    x: float
    shown: bool = False


@dataclass(frozen=True)
class Pipe:
    """
    A pipe the player can stand on and enter.

    ``kind`` is "travel" (leads to ``target``, the name of another pipe),
    "bonus" (the same, but to a secret room), "quiz" (an answer of the
    final quiz, numbered by ``answer_index``) or "exit" (arrival only).
    """

    name: str
    col: int
    top_row: int
    kind: str = "exit"
    target: str = None
    label: str = ""
    answer_index: int = None

    @property
    def x(self):
        """Pixel column of the middle of the pipe."""
        return (self.col + PIPE_WIDTH_TILES / 2) * TILE_SIZE

    @property
    def ground_y(self):
        """Pixel height of the top of the pipe, where the player stands."""
        return self.top_row * TILE_SIZE

    @property
    def rect(self):
        """Pixel rectangle of the pipe."""
        return pygame.Rect(self.col * TILE_SIZE, self.ground_y, PIPE_WIDTH_TILES * TILE_SIZE, PIPE_HEIGHT_TILES * TILE_SIZE)


@dataclass(frozen=True)
class Sign:
    """A readable sign post."""

    x: float
    ground_y: float
    title: str
    pages: tuple


@dataclass(frozen=True)
class Npc:
    """A character to talk to; ``kind`` is "professor_fin" or "owl"."""

    kind: str
    x: float
    ground_y: float


@dataclass(frozen=True)
class EnemyStart:
    """Where an enemy of a ``kind`` (see entities.ENEMY_KINDS) starts."""

    kind: str
    x: float
    ground_y: float
    patrol: tuple = None


@dataclass(frozen=True)
class PlatformStart:
    """Path of a moving platform; all values in pixels, ``period`` in seconds."""

    x: float
    y: float
    width: int
    travel_x: float = 0.0
    travel_y: float = 0.0
    period: float = 4.0


@dataclass(frozen=True)
class FireBarStart:
    """A spinning bar of fireballs around the centre of a block (pixels, radians per second)."""

    x: float
    y: float
    n_balls: int
    speed: float
    angle: float = 0.0


@dataclass
class Zone:
    """A world of the level with its own look and music."""

    first_col: int
    theme: str
    dark: bool = False
    last_col: int = field(default=0)


def cell_rect(cell):
    """Return the pixel rectangle of a ``(col, row)`` cell."""
    col, row = cell
    return pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)


class Level:
    """
    A tile grid plus the objects placed in it.

    Parameters
    ----------
    name : str
        Title shown to the player.
    n_cols : int
        Width of the level in tiles.
    """

    def __init__(self, name, n_cols):
        self.name = name
        self.n_cols = n_cols
        self.tiles = {}
        self.block_contents = {}
        self.hidden_blocks = {}
        self.crate_contents = {}
        self.spikes = {}
        self.sparks = []
        self.checkpoints = []
        self.shrines = []
        self.orbs = []
        self.demos = []
        self.pipes = {}
        self.signs = []
        self.npcs = []
        self.enemy_starts = []
        self.platform_starts = []
        self.crumble_starts = []
        self.firebar_starts = []
        self.springs = []
        self.water_spans = []
        self.bridge_cells = []
        self.zones = [Zone(0, "meadow", last_col=n_cols - 1)]
        # First columns of the worlds in the order the player travels them.
        self.world_order = [0]
        self.player_start = (TILE_SIZE * 2.0, GROUND_ROW * TILE_SIZE)
        self.goal_x = (n_cols - 3) * TILE_SIZE

    @property
    def pixel_width(self):
        """Width of the level in pixels."""
        return self.n_cols * TILE_SIZE

    # ----- building -------------------------------------------------------

    def add_zone(self, first_col, theme, dark=False):
        """Start a new zone at ``first_col``; it lasts until the next zone."""
        if theme not in THEMES:
            raise ValueError(f"theme must be one of {THEMES}")
        self.zones[-1].last_col = first_col - 1
        self.zones.append(Zone(first_col, theme, dark, self.n_cols - 1))

    def add_ground(self, first_col, last_col, top_row=GROUND_ROW):
        """Fill the columns with ground from ``top_row`` down to the bottom."""
        self.add_rock(first_col, last_col, top_row, LEVEL_ROWS - 1)

    def add_rock(self, first_col, last_col, top_row, bottom_row):
        """Fill a rectangle of cells with ground, for ceilings and walls."""
        for col in range(first_col, last_col + 1):
            for row in range(top_row, bottom_row + 1):
                self.tiles[(col, row)] = "ground"

    def add_platform(self, first_col, last_col, row):
        """Add a floating row of bricks."""
        for col in range(first_col, last_col + 1):
            self.tiles[(col, row)] = "brick"

    def add_column(self, col, top_row, bottom_row=GROUND_ROW - 1):
        """Add a vertical stack of bricks, for stairs and walls."""
        for row in range(top_row, bottom_row + 1):
            self.tiles[(col, row)] = "brick"

    def add_crates(self, col, top_row, bottom_row=GROUND_ROW - 1, spark_rows=()):
        """Add a stack of crates that a punch breaks; some may hold a spark."""
        for row in range(top_row, bottom_row + 1):
            self.tiles[(col, row)] = "crate"
            if row in spark_rows:
                self.crate_contents[(col, row)] = "spark"

    def add_spikes(self, first_col, last_col, row, pointing="up"):
        """Add spikes that hurt on touch; they point "up" or "down"."""
        if pointing not in ("up", "down"):
            raise ValueError('pointing must be "up" or "down"')
        for col in range(first_col, last_col + 1):
            self.spikes[(col, row)] = pointing

    def add_block(self, col, row, content, hidden=False):
        """
        Add a question block that releases ``content`` when hit from below.

        Parameters
        ----------
        col, row : int
            Cell of the block.
        content : str
            One of ``BLOCK_CONTENTS``.
        hidden : bool, optional
            Hidden blocks are invisible and not solid until they are hit.
        """
        if content not in BLOCK_CONTENTS:
            raise ValueError(f"unknown block content: {content}")
        if hidden:
            self.hidden_blocks[(col, row)] = content
        else:
            self.tiles[(col, row)] = "question"
            self.block_contents[(col, row)] = content

    def add_sparks(self, cells):
        """Add one spark in the middle of each ``(col, row)`` cell."""
        for cell in cells:
            self.sparks.append(Spark(*cell_rect(cell).center))

    def add_spark_row(self, first_col, last_col, row):
        """Add a horizontal row of sparks."""
        self.add_sparks((col, row) for col in range(first_col, last_col + 1))

    def add_checkpoint(self, col, surface_row=GROUND_ROW):
        """Add a checkpoint flag standing on the surface at ``surface_row``."""
        self.checkpoints.append(Checkpoint((col + 0.5) * TILE_SIZE, surface_row * TILE_SIZE))

    def add_shrine(self, skill, col, surface_row=GROUND_ROW):
        """Add a shrine that teaches a skill when the player touches it."""
        self.shrines.append(Shrine(skill, (col + 0.5) * TILE_SIZE, surface_row * TILE_SIZE))

    def add_orb(self, key, col, row=GROUND_ROW - 1):
        """Add an insight orb in the middle of a cell (see insight_animations.py)."""
        self.orbs.append(InsightOrb(key, *cell_rect((col, row)).center))

    def add_demo(self, key, col):
        """Play the animation ``key`` (see insight_animations.py) when the player passes ``col``."""
        self.demos.append(Demo(key, col * TILE_SIZE))

    def add_pipe(self, name, col, kind="exit", target=None, label="", answer_index=None, surface_row=GROUND_ROW):
        """
        Add a pipe that stands on the surface at ``surface_row``.

        Parameters
        ----------
        name : str
            Unique name, used as ``target`` by other pipes.
        col : int
            Left column of the pipe, which is two tiles wide and two high.
        kind : str, optional
            "travel", "bonus", "quiz" or "exit" (see ``Pipe``).
        target : str or None, optional
            Name of the pipe the player comes out of.
        label : str, optional
            Text shown above the pipe.
        answer_index : int or None, optional
            For quiz pipes: which answer of the question the pipe stands for.
        """
        if kind not in PIPE_KINDS:
            raise ValueError(f"kind must be one of {PIPE_KINDS}")
        top_row = surface_row - PIPE_HEIGHT_TILES
        self.pipes[name] = Pipe(name, col, top_row, kind, target, label, answer_index)
        for pipe_col in range(col, col + PIPE_WIDTH_TILES):
            for row in range(top_row, surface_row):
                self.tiles[(pipe_col, row)] = "pipe"

    def add_sign(self, col, title, pages, surface_row=GROUND_ROW):
        """Add a sign with a title and one or more pages of text."""
        self.signs.append(Sign((col + 0.5) * TILE_SIZE, surface_row * TILE_SIZE, title, tuple(pages)))

    def add_npc(self, kind, col, surface_row=GROUND_ROW):
        """Add a character the player can talk to."""
        self.npcs.append(Npc(kind, (col + 0.5) * TILE_SIZE, surface_row * TILE_SIZE))

    def add_enemy(self, kind, col, surface_row=GROUND_ROW, patrol_cols=None):
        """
        Add an enemy.

        Parameters
        ----------
        kind : str
            "distractor", "spikeback", "brute" or "buzzer".
        col : int
            Starting column.
        surface_row : int, optional
            Row of the surface it stands on (for a buzzer: hovers above).
        patrol_cols : tuple of int or None, optional
            First and last column of the area it stays in.
        """
        patrol = None
        if patrol_cols is not None:
            patrol = (patrol_cols[0] * TILE_SIZE, (patrol_cols[1] + 1) * TILE_SIZE)
        self.enemy_starts.append(EnemyStart(kind, col * TILE_SIZE, surface_row * TILE_SIZE, patrol))

    def add_moving_platform(self, col, row, n_tiles=3, travel_cols=0, travel_rows=0, period=4.0):
        """Add a platform whose top is at the top of ``row`` and that travels by the given tiles."""
        self.platform_starts.append(
            PlatformStart(col * TILE_SIZE, row * TILE_SIZE, n_tiles * TILE_SIZE, travel_cols * TILE_SIZE, travel_rows * TILE_SIZE, period)
        )

    def add_crumble(self, col, row, n_tiles=2):
        """Add a platform that falls down shortly after the player lands on it, and comes back later."""
        self.crumble_starts.append(PlatformStart(col * TILE_SIZE, row * TILE_SIZE, n_tiles * TILE_SIZE))

    def add_spring(self, col, surface_row=GROUND_ROW):
        """Add a spring on the surface at ``surface_row``; landing on it launches the player."""
        self.springs.append(pygame.Rect(col * TILE_SIZE + 6, surface_row * TILE_SIZE - 24, TILE_SIZE - 12, 24))

    def add_firebar(self, col, row, n_balls=5, speed=1.6, angle=0.0):
        """
        Add a spinning bar of fireballs around a fixed block.

        Parameters
        ----------
        col, row : int
            Cell of the block in the middle.
        n_balls : int, optional
            Length of the bar in fireballs.
        speed : float, optional
            Turns in radians per second; negative values turn the other way.
        angle : float, optional
            Starting angle in radians.
        """
        self.tiles[(col, row)] = "used"
        center = cell_rect((col, row)).center
        self.firebar_starts.append(FireBarStart(*center, n_balls, speed, angle))

    def add_pond(self, first_col, last_col, row=GROUND_ROW):
        """Add water that can only be crossed once the bridge is built."""
        self.water_spans.append((first_col, last_col))
        self.bridge_cells = [(col, row) for col in range(first_col, last_col + 1)]

    def pits(self):
        """Return the ``(first_col, last_col)`` spans without ground, ponds excluded."""
        bottom = LEVEL_ROWS - 1
        water = {col for first, last in self.water_spans for col in range(first, last + 1)}
        spans, first = [], None
        for col in range(self.n_cols + 1):
            is_open = col < self.n_cols and (col, bottom) not in self.tiles and col not in water
            if is_open and first is None:
                first = col
            elif not is_open and first is not None:
                spans.append((first, col - 1))
                first = None
        return spans

    def narrow_pits(self, n_tiles, min_width=2):
        """
        Make every pit narrower by adding ground at its edges.

        Parameters
        ----------
        n_tiles : int
            Number of ground columns added to each edge of a pit.
        min_width : int, optional
            Pits are never made narrower than this many tiles, so that they
            stay visible and big enemies still fall into them.
        """
        for first, last in self.pits():
            for step in range(2 * n_tiles):
                if last - first + 1 <= min_width:
                    break
                if step % 2 == 0:
                    self.add_ground(first, first)
                    first += 1
                else:
                    self.add_ground(last, last)
                    last -= 1

    # ----- playing --------------------------------------------------------

    def is_solid(self, col, row):
        """Return True if the cell blocks movement."""
        return (col, row) in self.tiles

    def solid_cells_in(self, x, y, width, height):
        """Return the solid cells that overlap a pixel rectangle."""
        first_col, last_col = int(x // TILE_SIZE), int((x + width - 0.001) // TILE_SIZE)
        first_row, last_row = int(y // TILE_SIZE), int((y + height - 0.001) // TILE_SIZE)
        return [
            (col, row)
            for col in range(first_col, last_col + 1)
            for row in range(first_row, last_row + 1)
            if (col, row) in self.tiles
        ]

    def zone_at(self, x):
        """Return the zone that contains pixel column ``x``."""
        col = x // TILE_SIZE
        for zone in reversed(self.zones):
            if col >= zone.first_col:
                return zone
        return self.zones[0]

    def progress_of(self, x):
        """Sort key for a pixel column: how far along the player's journey it is."""
        zone = self.zone_at(x)
        order = self.world_order.index(zone.first_col) if zone.first_col in self.world_order else len(self.world_order)
        return (order, x)

    def darkness_at(self, x):
        """Return how dark it is at pixel column ``x``: 0 (daylight) or 1."""
        return 1.0 if self.zone_at(x).dark else 0.0

    def pipe_under(self, x, bottom_y):
        """Return the pipe whose top a body at (x, bottom_y) stands on, or None."""
        for pipe in self.pipes.values():
            if abs(pipe.x - x) < TILE_SIZE * 0.8 and abs(pipe.ground_y - bottom_y) < 2:
                return pipe
        return None

    def spike_hits(self, rect):
        """Return True if a pixel rectangle touches the sharp half of a spike."""
        for (col, row), pointing in self.spikes.items():
            left, top = col * TILE_SIZE + 8, row * TILE_SIZE + (22 if pointing == "up" else 0)
            if rect.colliderect((left, top, TILE_SIZE - 16, TILE_SIZE - 22)):
                return True
        return False

    def break_crates(self, rect):
        """
        Break all crates that a pixel rectangle touches.

        Returns
        -------
        list of tuple
            ``(cell, content)`` for every broken crate; content is "spark" or None.
        """
        broken = []
        for cell in self.solid_cells_in(rect.x, rect.y, rect.width, rect.height):
            if self.tiles[cell] == "crate":
                del self.tiles[cell]
                broken.append((cell, self.crate_contents.pop(cell, None)))
        return broken

    def hit_block(self, cell):
        """Use up a question block and return its content (None if empty)."""
        if self.tiles.get(cell) != "question":
            return None
        self.tiles[cell] = "used"
        return self.block_contents.pop(cell, None)

    def reveal_hidden_block(self, cell):
        """Turn a hidden block into a normal, solid question block."""
        self.add_block(*cell, self.hidden_blocks.pop(cell))

    def build_bridge(self):
        """Make the pond crossable."""
        for cell in self.bridge_cells:
            self.tiles[cell] = "bridge"
