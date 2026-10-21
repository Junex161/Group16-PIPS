"""Level format of the Prologue and Levels 2 and 3.

``StoryLevel`` extends ``Level`` with the new building blocks of these
levels: gates that open after a challenge, answer blocks for the quiz,
red-light zones, conveyor belts, red and blue switch blocks, lava and a
boss hall. Level layouts (``prologue.py``, ``level_two.py`` and
``level_three.py``) build a ``StoryLevel`` step by step, just like
``level_one.py`` builds Level 1.
"""

from dataclasses import dataclass, field

from .config import TILE_SIZE
from .level import GROUND_ROW, THEMES, Level, Zone
from .worlds import STORY_THEMES, base_theme

FLOOR = GROUND_ROW - 1
SWITCH_COLORS = ("red", "blue")


@dataclass
class RedLight:
    """
    A zone of the red-light game: moving while the light is red hurts.

    ``first_x`` and ``last_x`` limit the watched area in pixels, ``light_x``
    is where the light stands and ``offset`` shifts its cycle in seconds.
    """

    first_x: float
    last_x: float
    light_x: float
    offset: float = 0.0
    state: str = "green"


@dataclass(frozen=True)
class BossSpec:
    """Where a boss fights: its kind, its hall (columns) and the gates of the hall."""

    kind: str
    first_col: int
    last_col: int
    gate_in: str
    gate_out: str
    card_cells: tuple = ()


@dataclass
class QuizSpec:
    """The final quiz: three answer blocks and the gate they open."""

    cells: tuple
    gate: str
    topics: tuple = field(default_factory=tuple)


class StoryLevel(Level):
    """
    A level of the Prologue, Level 2 or Level 3.

    Parameters
    ----------
    key : str
        Key of the level, e.g. "level_2".
    name : str
        Title shown to the player.
    n_cols : int
        Width of the level in tiles.
    first_theme : str
        Look of the first world (see ``worlds.STORY_THEMES``).
    start_skills : tuple of str, optional
        Skills the hero knows from the start.
    """

    def __init__(self, key, name, n_cols, first_theme, start_skills=("punch",)):
        super().__init__(name, n_cols)
        self.zones[0].theme = first_theme
        self.key = key
        self.start_skills = tuple(start_skills)
        self.gates = {}
        self.conveyors = {}
        self.color_blocks = {color: set() for color in SWITCH_COLORS}
        self.switches = set()
        self.red_lights = []
        self.lava_spans = []
        self.boss = None
        self.quiz = None

    # ----- building -------------------------------------------------------

    def add_zone(self, first_col, theme, dark=False):
        """Start a new world at ``first_col``; the new worlds are listed in ``worlds.py``."""
        if theme not in STORY_THEMES and theme not in THEMES:
            raise ValueError(f"unknown theme: {theme}")
        self.zones[-1].last_col = first_col - 1
        self.zones.append(Zone(first_col, theme, dark, self.n_cols - 1))

    def _platform_tile(self, col):
        """Name of the platform tile that fits the world at ``col``."""
        return f"plat_{base_theme(self.zone_at(col * TILE_SIZE).theme)}"

    def add_platform(self, first_col, last_col, row):
        """Add a floating row of platform tiles in the look of the world."""
        for col in range(first_col, last_col + 1):
            self.tiles[(col, row)] = self._platform_tile(col)

    def add_column(self, col, top_row, bottom_row=FLOOR):
        """Add a vertical stack of platform tiles, for stairs and walls."""
        for row in range(top_row, bottom_row + 1):
            self.tiles[(col, row)] = self._platform_tile(col)

    def add_room(self, first_col, last_col, ceiling=3):
        """Close a world in with a ceiling and a wall at each end."""
        self.add_rock(first_col, last_col, 0, ceiling)
        self.add_rock(first_col, first_col + 1, ceiling + 1, FLOOR)
        self.add_rock(last_col - 1, last_col, ceiling + 1, FLOOR)

    def add_gate(self, name, col, top_row, bottom_row=FLOOR, width=1):
        """Add a closed gate of bars that a challenge opens later."""
        cells = [(c, row) for c in range(col, col + width) for row in range(top_row, bottom_row + 1)]
        self.gates.setdefault(name, []).extend(cells)
        for cell in cells:
            self.tiles[cell] = "gate"

    def add_quiz(self, cols, row, gate, topics):
        """Add the three answer blocks of the final quiz and the gate they open."""
        cells = tuple((col, row) for col in cols)
        for cell in cells:
            self.tiles[cell] = "answer"
        self.quiz = QuizSpec(cells, gate, tuple(topics))

    def add_conveyor(self, first_col, last_col, row, direction):
        """Add a conveyor belt that carries the hero left (-1) or right (1)."""
        for col in range(first_col, last_col + 1):
            self.tiles[(col, row)] = "conveyor"
            self.conveyors[(col, row)] = direction

    def add_color_blocks(self, color, cells):
        """Add red or blue switch blocks; red ones are solid at the start."""
        if color not in SWITCH_COLORS:
            raise ValueError(f"color must be one of {SWITCH_COLORS}")
        for cell in cells:
            self.color_blocks[color].add(cell)
            if color == "red":
                self.tiles[cell] = "red_block"

    def add_switch(self, col, row):
        """Add a switch block; hitting it from below swaps red and blue blocks."""
        self.switches.add((col, row))
        self.tiles[(col, row)] = "switch_red"

    def add_red_light(self, first_col, last_col, light_col, offset=0.0):
        """Add a red-light zone between two columns, watched by a light at ``light_col``."""
        self.red_lights.append(RedLight(first_col * TILE_SIZE, (last_col + 1) * TILE_SIZE, (light_col + 0.5) * TILE_SIZE, offset))

    def add_lava(self, first_col, last_col):
        """Fill a pit with lava (only a look: falling in costs a heart as usual)."""
        self.lava_spans.append((first_col, last_col))

    def add_boss(self, kind, first_col, last_col, gate_in, gate_out, card_cells=()):
        """Add the boss hall: the gates close behind the hero and open after the fight."""
        self.boss = BossSpec(kind, first_col, last_col, gate_in, gate_out, tuple(card_cells))
        for cell in card_cells:
            self.tiles[cell] = "card"

    # ----- playing --------------------------------------------------------

    def open_gate(self, name):
        """Remove the bars of a gate."""
        for cell in self.gates.get(name, ()):
            if self.tiles.get(cell) == "gate":
                del self.tiles[cell]

    def close_gate(self, name):
        """Put the bars of a gate (back) in place."""
        for cell in self.gates.get(name, ()):
            self.tiles[cell] = "gate"

    def gate_is_open(self, name):
        """Return True if none of the gate's bars are in place."""
        return all(self.tiles.get(cell) != "gate" for cell in self.gates.get(name, ()))

    @property
    def active_color(self):
        """The colour of the switch blocks that are solid right now."""
        switch = next(iter(self.switches), None)
        return "red" if switch is None or self.tiles.get(switch) == "switch_red" else "blue"

    def toggle_switches(self):
        """Swap which colour of switch blocks is solid; return the new colour."""
        new = "blue" if self.active_color == "red" else "red"
        old = "red" if new == "blue" else "blue"
        for cell in self.color_blocks[old]:
            self.tiles.pop(cell, None)
        for cell in self.color_blocks[new]:
            self.tiles[cell] = f"{new}_block"
        for cell in self.switches:
            self.tiles[cell] = f"switch_{new}"
        return new
