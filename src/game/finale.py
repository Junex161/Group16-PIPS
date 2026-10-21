"""Layout of the Finale, "Count Hackula's Castle".

A short castle level in the spirit of the last castle in Super Mario. On
the way to the throne room every level returns once: lava and fire bars, a
red-light zone (response inhibition), a Brute that only fear conditioning
moves, and a switch puzzle (shifting). In the throne room waits the final
boss, Count Hackula (see ``hackula_boss.py``), whose three phases test
attention, response inhibition and executive control. Behind him is the
goal, and the story ends with the finale animation.

The hero starts with every skill of the game.
"""

from .config import TILE_SIZE
from .level import GROUND_ROW
from .story_level import FLOOR, StoryLevel

CASTLE = (0, 89)
THRONE_ROOM = (90, 139)
ARENA = (98, 121)
WINDOW_COLS = (102, 109, 116)
WINDOW_ROW = 9
N_COLS = THRONE_ROOM[1] + 1
CEILING = 3
START_SKILLS = ("punch", "double_jump", "fear", "blaster", "stop")


def build_finale():
    """
    Build a fresh copy of the Finale.

    Returns
    -------
    StoryLevel
        The level with all tiles, enemies and the final boss in place.
    """
    level = StoryLevel("finale", "Finale: Count Hackula's Castle", N_COLS, "castle", start_skills=START_SKILLS)
    _build_castle(level)
    _build_throne_room(level)
    level.world_order = [CASTLE[0], THRONE_ROOM[0]]
    return level


def _build_castle(level):
    level.add_ground(0, 14)
    level.add_sign(4, "Count Hackula's Castle", ("He is waiting at the top. Use everything you have learned!",))
    level.add_lava(15, 19)
    level.add_crumble(16, 10, n_tiles=2)
    level.add_ground(20, 34)
    level.add_firebar(26, 8, n_balls=5, speed=1.8)
    level.add_enemy("hackling", 30, surface_row=9, patrol_cols=(27, 34))
    level.add_enemy("spikeback", 32, patrol_cols=(29, 34))
    level.add_lava(35, 41)
    level.add_moving_platform(36, GROUND_ROW, n_tiles=3, travel_cols=3, period=3.5)

    level.add_ground(42, 60)
    level.add_checkpoint(43)
    level.add_red_light(45, 52, 49)
    level.add_block(48, 8, "heart")
    # A Brute under a low roof: only fear conditioning gets it out of the way.
    level.add_platform(54, 60, 8)
    level.add_enemy("brute", 57, patrol_cols=(55, 60))

    level.add_ground(64, CASTLE[1])
    level.add_switch(66, 8)
    level.add_color_blocks("red", [(70, row) for row in range(4, GROUND_ROW)])
    level.add_color_blocks("blue", [(72, 9), (73, 9), (74, 9)])
    level.add_block(73, 5, "star")
    level.add_checkpoint(77)
    level.add_enemy("hackling", 80, surface_row=9, patrol_cols=(78, 84))
    level.add_pipe("to_throne", 84, kind="travel", target="throne_entry", label="The throne room")
    level.add_rock(CASTLE[1] - 1, CASTLE[1], 0, FLOOR)


def _build_throne_room(level):
    first_col, last_col = THRONE_ROOM
    level.add_zone(first_col, "boss_hackula")
    level.add_room(first_col, last_col, 0)
    level.add_ground(first_col, last_col)
    level.add_pipe("throne_entry", 92)
    level.add_checkpoint(96)
    level.add_gate("throne_in", ARENA[0], 1)
    level.add_gate("throne_out", ARENA[1], 1)
    level.add_boss("count_hackula", ARENA[0], ARENA[1], "throne_in", "throne_out", card_cells=[(col, WINDOW_ROW) for col in WINDOW_COLS])
    level.goal_x = 130.5 * TILE_SIZE
