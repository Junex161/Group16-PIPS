"""Layout of Level 1, "Focus Fields" (topic: attention).

The level has three zones and reads from left to right:

1. Meadow: the basics, crates to punch, spikes, the first Spikeback, the
   Double Jump shrine and Professor Fin's pond with the flanker task.
2. Cave: dark, lit only by the Spotlight. Moving platforms, stalactites, the
   Fear Conditioning shrine and a Brute that blocks a tunnel.
3. Sunset Heights: a chasm with moving platforms, the owl's quiz gate and
   the goal.

With the default player settings a jump is about 3.5 tiles high and 4.5 tiles
long; a double jump reaches about 7 tiles high and 8 tiles far. Everything
before the Double Jump shrine can be done with single jumps.
"""

from .config import LEVEL_ONE_NAME, TILE_SIZE
from .content import QRP_SIGN
from .level import GROUND_ROW, Level

N_COLS = 292
POND = (112, 127)
CAVE = (131, 209)
AIR = GROUND_ROW - 2  # row in which sparks float at jumping height
FLOOR = GROUND_ROW - 1  # row of things that lie on the ground, such as spikes
CAVE_CEILING = 3  # lowest row of the cave ceiling


def build_level_one():
    """
    Build a fresh copy of Level 1.

    Returns
    -------
    Level
        The level with all tiles, pickups, enemies and characters in place.
    """
    level = Level(LEVEL_ONE_NAME, N_COLS)
    _build_meadow_start(level)
    _build_spike_steps(level)
    _build_double_jump_wall(level)
    _build_hill_and_pond(level)
    _build_cave_entrance(level)
    _build_cave_tunnel(level)
    _build_cave_exit(level)
    _build_sunset_chasm(level)
    _build_final_stretch(level)
    return level


def _build_meadow_start(level):
    level.add_ground(0, 28)
    level.add_sign(
        5,
        "Welcome to the Focus Fields",
        (
            "Attention notes are hidden all over this level. Collect them and read them "
            "carefully: the owl at the gate will ask you about attention!",
            "Press TAB at any time to re-read your notes. Jump into '?' blocks from "
            "below, and jump on Distractors to get rid of them.",
        ),
    )
    level.add_sign(9, "The QRP Blaster", QRP_SIGN)
    level.add_spark_row(8, 11, AIR)
    level.add_note("cocktail_party", 13, FLOOR)
    level.add_sign(16, "Punch!", ("Cracked crates block the way. Press F to punch them to pieces. "
                                  "A punch also knocks out enemies in front of you.",))
    level.add_crates(19, top_row=8, spark_rows=(9,))
    level.add_block(21, 8, "spark")
    level.add_block(22, 8, "mushroom")
    level.add_block(23, 8, "spark")
    level.add_enemy("distractor", 25)
    level.add_sparks([(29, 9), (30, 8), (31, 9)])  # arc over the first pit


def _build_spike_steps(level):
    level.add_ground(32, 52)
    level.add_platform(35, 37, 9)
    level.add_spark_row(35, 37, 8)
    level.add_platform(39, 42, 6)
    level.add_sparks([(39, 5), (40, 5), (42, 5)])
    level.add_note("filter", 41, 5)
    level.add_spikes(39, 41, FLOOR)
    level.add_sign(44, "Careful: Spikebacks", ("Never jump on a Spikeback! Punch it with F instead.",))
    level.add_enemy("distractor", 46)
    level.add_enemy("spikeback", 49)
    level.add_checkpoint(51)


def _build_double_jump_wall(level):
    level.add_ground(56, 70)
    level.add_shrine("double_jump", 58)
    for col in (63, 64):
        level.add_column(col, top_row=8)  # four tiles: too high for a single jump
    level.add_sparks([(63, 6), (64, 6)])
    level.add_enemy("distractor", 67)
    level.add_sparks([(72, 8), (73, 7), (74, 7), (75, 8)])  # arc over the wide pit


def _build_hill_and_pond(level):
    level.add_ground(77, 111)
    level.add_enemy("buzzer", 80, surface_row=FLOOR)
    level.add_ground(83, 91, top_row=10)  # hill
    level.add_block(86, 6, "spark")
    level.add_block(87, 6, "note:gorilla")
    level.add_block(88, 6, "spark")
    level.add_enemy("spikeback", 89, surface_row=10)
    level.add_crates(94, top_row=8, spark_rows=(8, 9))
    level.add_enemy("distractor", 97)
    level.add_enemy("buzzer", 99, surface_row=10, patrol_cols=(96, 100))
    level.add_checkpoint(101)
    level.add_sign(
        104,
        "Professor Fin's Pond",
        ("The pond is too wide to jump. Talk to Professor Fin (press E) and win his "
         "challenge to cross it.",),
    )
    level.add_npc("professor_fin", 108)
    level.add_pond(*POND)


def _build_cave_entrance(level):
    first_col, last_col = CAVE
    level.add_zone(first_col, "cave", dark=True)
    level.add_ground(128, 140)
    level.add_checkpoint(129)
    level.add_rock(first_col + 1, last_col, 0, CAVE_CEILING)
    level.add_rock(first_col + 1, first_col + 2, CAVE_CEILING + 1, 7)  # rock face above the mouth
    level.add_sign(
        135,
        "The Dark Cave",
        ("It is dark in here, but your Spotlight lights the way. It also makes hidden "
         "blocks shimmer: jump into a shimmering outline from below!",),
    )
    level.add_block(138, 8, "note:spotlight", hidden=True)
    level.add_spark_row(139, 140, AIR)

    level.add_ground(144, 158)
    level.add_spikes(147, 148, FLOOR)
    level.add_rock(147, 148, CAVE_CEILING + 1, 5)  # stalactite: do not double jump here
    level.add_spikes(147, 148, 6, pointing="down")
    level.add_enemy("distractor", 152)
    level.add_enemy("spikeback", 155)
    level.add_moving_platform(159, GROUND_ROW, n_tiles=3, travel_cols=5, period=5.0)
    level.add_spark_row(161, 164, AIR)


def _build_cave_tunnel(level):
    level.add_ground(167, 188)
    level.add_shrine("fear", 169)
    level.add_checkpoint(171)
    level.add_sign(173, "A Brute!", ("Brutes are too tough to punch and too big to jump over. "
                                     "Scare it away with Q!",))
    level.add_rock(176, 185, CAVE_CEILING + 1, 8)  # low tunnel
    level.add_enemy("brute", 181, patrol_cols=(177, 185))
    level.add_spark_row(178, 184, AIR + 1)


def _build_cave_exit(level):
    last_col = CAVE[1]
    level.add_ground(192, 214)
    level.add_moving_platform(194, FLOOR, n_tiles=2, travel_rows=-5, period=4.0)
    level.add_platform(197, 200, 6)
    level.add_sparks([(197, 5), (198, 5), (200, 5)])
    level.add_note("networks", 199, 5)
    level.add_enemy("spikeback", 199, patrol_cols=(196, 204))
    level.add_block(203, 8, "heart", hidden=True)
    level.add_enemy("buzzer", 205, surface_row=10)
    level.add_rock(last_col - 1, last_col, CAVE_CEILING + 1, 7)  # rock face above the exit
    level.add_zone(last_col + 1, "sunset")
    level.add_checkpoint(212)


def _build_sunset_chasm(level):
    level.add_ground(218, 226)
    level.add_spark_row(220, 223, AIR)
    level.add_platform(229, 230, 10)
    level.add_moving_platform(232, 10, n_tiles=3, travel_cols=4, period=4.5)
    level.add_enemy("buzzer", 235, surface_row=7)
    level.add_spark_row(233, 237, 8)
    level.add_platform(240, 241, 9)
    level.add_sparks([(240, 7), (241, 7)])


def _build_final_stretch(level):
    level.add_ground(243, N_COLS - 1)
    level.add_checkpoint(244)
    for step, col in enumerate(range(246, 250)):
        level.add_column(col, top_row=FLOOR - step)
    level.add_platform(252, 255, 6)
    level.add_enemy("buzzer", 253, surface_row=4, patrol_cols=(251, 256))
    level.add_spark_row(252, 255, 5)
    level.add_block(258, 8, "mushroom")
    level.add_enemy("spikeback", 253, patrol_cols=(250, 262))
    level.add_enemy("distractor", 257)
    level.add_crates(263, top_row=8, spark_rows=(10,))
    level.add_spikes(266, 268, FLOOR)
    level.add_column(273, top_row=FLOOR)  # keeps enemies away from the owl
    level.add_npc("owl", 276)
    level.add_gate(280)
    level.add_spark_row(282, 284, AIR)
    level.goal_x = 285.5 * TILE_SIZE
