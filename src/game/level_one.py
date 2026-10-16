"""Layout of Level 1, "Focus Fields" (topic: attention).

The level consists of six worlds that are connected by pipes. In the order
the player meets them:

1. Meadow: the basics, the insights "what is attention", "cocktail party"
   and "invisible gorilla", the Double Jump shrine, a secret pipe to the
   bonus room and Professor Fin's pond with the flanker task (which gives
   the flanker insight). A pipe behind the pond leads on.
2. Whispering Woods: springs, crumbling logs and spinning fire bars.
3. Crystal Cave: dark, lit only by the Spotlight. The spotlight insight,
   moving platforms, the Fear Conditioning shrine and a Brute in a tunnel.
4. Sky Bridge: cloud islands over the void, crumbling clouds, fire bars
   and a second Brute.
5. Sunset Heights: a chasm with crumbling platforms, the owl's quiz, where
   three golden pipes stand for three answers, and the QRP Blaster as the
   reward for the next levels.

A secret bonus room full of sparks can be reached from the meadow. On the
grid the worlds lie side by side; the woods and the sky bridge come last.

With the default player settings a jump is about 3.5 tiles high and 4.5 tiles
long; a double jump reaches about 7 tiles high and 8 tiles far. Everything
before the Double Jump shrine can be done with single jumps.
"""

from .config import LEVEL_ONE_NAME, TILE_SIZE
from .level import GROUND_ROW, Level

# First and last column of each world.
MEADOW = (0, 131)
CAVE = (132, 211)
SUNSET = (212, 293)
BONUS_ROOM = (294, 321)
FOREST = (322, 421)
SKY = (422, 521)
N_COLS = SKY[1] + 1
POND = (112, 127)
N_QUIZ_PIPES = 3

AIR = GROUND_ROW - 2  # row in which sparks float at jumping height
FLOOR = GROUND_ROW - 1  # row of things that lie on the ground, such as spikes
CEILING = 3  # lowest row of the ceiling in the cave and the bonus room


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
    _build_quiz(level)
    _build_bonus_room(level)
    _build_woods(level)
    _build_sky_bridge(level)
    level.world_order = [MEADOW[0], FOREST[0], CAVE[0], SKY[0], SUNSET[0]]
    return level


def _add_room(level, first_col, last_col):
    """Close a world in with a ceiling and a wall at each end."""
    level.add_rock(first_col, last_col, 0, CEILING)
    level.add_rock(first_col, first_col + 1, CEILING + 1, FLOOR)
    level.add_rock(last_col - 1, last_col, CEILING + 1, FLOOR)


def _build_meadow_start(level):
    level.add_ground(0, 28)
    level.add_sign(5, "Focus Fields", ("Find the five glowing eye orbs - some are hard to reach!",))
    level.add_spark_row(8, 11, AIR)
    level.add_demo("punch", 15)
    level.add_sign(16, "Punch!", ("F: punch crates and enemies.",))
    level.add_crates(19, top_row=8, spark_rows=(9,))
    level.add_block(21, 8, "spark")
    level.add_block(22, 8, "mushroom")  # the Zoom-shroom
    level.add_block(23, 8, "spark")
    level.add_enemy("distractor", 25)
    level.add_sparks([(29, 9), (30, 8), (31, 9)])  # arc over the first pit


def _build_spike_steps(level):
    level.add_ground(32, 52)
    level.add_platform(35, 37, 9)
    level.add_spark_row(35, 37, 8)
    level.add_platform(39, 42, 6)
    level.add_sparks([(39, 5), (40, 5), (42, 5)])
    level.add_orb("attention", 41, row=5)  # the first insight waits on the high step
    level.add_spikes(39, 41, FLOOR)
    level.add_block(46, 8, "shield")
    level.add_sign(44, "Spikebacks", ("Don't jump on them - punch (F) or shoot (G)!",))
    level.add_enemy("distractor", 46)
    level.add_enemy("spikeback", 49)
    level.add_checkpoint(51)


def _build_double_jump_wall(level):
    level.add_ground(56, 70)
    level.add_shrine("double_jump", 58)
    for col in (63, 64):
        level.add_column(col, top_row=8)  # four tiles: too high for a single jump
    level.add_orb("cocktail_party", 64, row=7)  # on top of the wall: needs the double jump
    # A secret: this pipe leads to the bonus room and back out behind the pit.
    level.add_pipe("to_bonus_room", 66, kind="bonus", target="bonus_room_entry", label="???")
    level.add_enemy("distractor", 69, patrol_cols=(68, 70))
    level.add_sparks([(72, 8), (73, 7), (74, 7), (75, 8)])  # arc over the wide pit


def _build_hill_and_pond(level):
    level.add_ground(77, POND[0] - 1)
    level.add_ground(POND[1] + 1, MEADOW[1])
    level.add_pipe("from_bonus_room", 78)
    level.add_ground(83, 91, top_row=10)  # hill
    level.add_block(86, 6, "spark")
    level.add_block(87, 6, "heart")
    level.add_block(88, 6, "mushroom")
    level.add_orb("gorilla", 87, row=3)  # high above the blocks: double jump from the hill
    level.add_enemy("spikeback", 89, surface_row=10)
    level.add_firebar(92, 8, n_balls=4, speed=1.8)
    level.add_crates(94, top_row=8, spark_rows=(8, 9))
    level.add_enemy("distractor", 97)
    level.add_enemy("buzzer", 99, surface_row=10, patrol_cols=(96, 100))
    level.add_checkpoint(101)
    level.add_sign(
        104,
        "Professor Fin's Pond",
        ("Too wide to jump. Talk to Professor Fin (E).",),
    )
    level.add_npc("professor_fin", 108)
    level.add_pond(*POND)
    level.add_pipe("to_woods", 129, kind="travel", target="woods_entry", label="To the Whispering Woods")


def _build_cave_entrance(level):
    first_col, last_col = CAVE
    level.add_zone(first_col, "cave", dark=True)
    level.add_ground(first_col, 140)
    _add_room(level, first_col, last_col)
    level.add_pipe("cave_entry", 134)
    level.add_checkpoint(137)
    level.add_orb("spotlight", 139)

    level.add_ground(144, 158)
    level.add_spikes(147, 148, FLOOR)
    level.add_rock(147, 148, CEILING + 1, 5)  # stalactite: do not double jump here
    level.add_spikes(147, 148, 6, pointing="down")
    level.add_block(151, 8, "star", hidden=True)
    level.add_enemy("distractor", 152)
    level.add_enemy("spikeback", 155)
    level.add_firebar(157, 8, n_balls=4, speed=-2.0)
    level.add_moving_platform(159, GROUND_ROW, n_tiles=3, travel_cols=5, period=5.0)
    level.add_spark_row(161, 164, AIR)


def _build_cave_tunnel(level):
    level.add_ground(167, 188)
    level.add_shrine("fear", 169)
    level.add_checkpoint(171)
    level.add_sign(173, "A Brute!", ("Too tough to fight. Scare it away with Q!",))
    level.add_rock(176, 185, CEILING + 1, 8)  # low tunnel
    level.add_enemy("brute", 181, patrol_cols=(177, 185))
    level.add_spark_row(178, 184, FLOOR)


def _build_cave_exit(level):
    level.add_ground(192, CAVE[1])
    level.add_moving_platform(194, FLOOR, n_tiles=2, travel_rows=-5, period=4.0)
    level.add_platform(197, 200, 6)
    level.add_spark_row(197, 200, 5)
    level.add_enemy("spikeback", 199, patrol_cols=(196, 203))
    level.add_block(203, 8, "heart", hidden=True)
    level.add_enemy("buzzer", 201, surface_row=10, patrol_cols=(198, 204))
    level.add_pipe("to_sky", 206, kind="travel", target="sky_entry", label="To the Sky Bridge")


def _build_sunset_chasm(level):
    first_col = SUNSET[0]
    level.add_zone(first_col, "sunset")
    level.add_ground(first_col, 226)
    level.add_pipe("sunset_entry", 213)
    level.add_checkpoint(216)
    level.add_spark_row(220, 223, AIR)
    level.add_crumble(229, 10)
    level.add_moving_platform(232, 10, n_tiles=3, travel_cols=4, period=4.5)
    level.add_enemy("buzzer", 235, surface_row=7)
    level.add_spark_row(233, 237, 8)
    level.add_crumble(240, 9)
    level.add_sparks([(240, 7), (241, 7)])


def _build_quiz(level):
    level.add_ground(243, SUNSET[1])
    level.add_checkpoint(244)
    for step, col in enumerate(range(246, 250)):
        level.add_column(col, top_row=FLOOR - step)
    level.add_platform(252, 255, 6)
    level.add_spark_row(252, 255, 5)
    level.add_enemy("buzzer", 253, surface_row=4, patrol_cols=(251, 256))
    level.add_enemy("spikeback", 253, patrol_cols=(250, 256))
    level.add_enemy("distractor", 255, patrol_cols=(250, 256))
    level.add_column(257, top_row=FLOOR)  # keeps enemies away from the owl
    level.add_npc("owl", 259)
    # Three golden pipes are the answers of the quiz; only the right one
    # leads to the pipe behind the wall.
    for answer_index in range(N_QUIZ_PIPES):
        level.add_pipe(f"answer_{answer_index}", 262 + answer_index * 5, kind="quiz", target="goal_entry", answer_index=answer_index)
    level.add_rock(276, 277, 0, FLOOR)
    level.add_pipe("goal_entry", 279)
    # The reward for finishing the level: the QRP Blaster for the next levels.
    level.add_shrine("blaster", 283)
    level.goal_x = 286.5 * TILE_SIZE


def _build_bonus_room(level):
    first_col, last_col = BONUS_ROOM
    level.add_zone(first_col, "cave")
    level.add_ground(first_col, last_col)
    _add_room(level, first_col, last_col)
    level.add_pipe("bonus_room_entry", 297)
    for row in (8, 9, 10):
        level.add_spark_row(301, 312, row)
    level.add_block(314, 8, "star")
    level.add_pipe("bonus_room_exit", 316, kind="travel", target="from_bonus_room", label="Back to the meadow")


def _build_woods(level):
    first_col, last_col = FOREST
    level.add_zone(first_col, "forest")
    level.add_ground(first_col, 335)
    level.add_pipe("woods_entry", 324)
    level.add_checkpoint(328)
    level.add_sign(330, "Whispering Woods", ("Jump on springs. Mossy logs crumble - don't stand still!",))
    # A pit with crumbling logs below and a high ledge that only a spring reaches.
    level.add_spring(334)
    level.add_platform(336, 340, 4)
    level.add_spark_row(336, 340, 3)
    level.add_crumble(337, 9)
    level.add_crumble(341, 9)

    level.add_ground(344, 360)
    level.add_enemy("spikeback", 348)
    level.add_enemy("distractor", 352)
    level.add_block(353, 8, "star")
    level.add_firebar(355, 8, n_balls=5, speed=1.7)
    level.add_crumble(361, 10)
    level.add_crumble(365, 9)

    level.add_ground(367, 390)
    level.add_checkpoint(369)
    level.add_ground(372, 376, top_row=9)  # hill
    level.add_enemy("buzzer", 374, surface_row=7, patrol_cols=(371, 377))
    level.add_spring(378)
    level.add_platform(381, 384, 3)
    level.add_spark_row(381, 384, 2)
    level.add_block(383, 0, "heart", hidden=True)
    level.add_spikes(380, 383, GROUND_ROW - 1)
    level.add_firebar(389, 8, n_balls=5, speed=-1.6)
    level.add_moving_platform(391, GROUND_ROW, n_tiles=3, travel_cols=5, period=4.0)
    level.add_enemy("buzzer", 395, surface_row=8)

    level.add_ground(399, last_col)
    level.add_crates(403, top_row=7, spark_rows=(7,))
    level.add_enemy("distractor", 406, patrol_cols=(404, 413))
    level.add_enemy("distractor", 409, patrol_cols=(404, 413))
    level.add_enemy("spikeback", 412, patrol_cols=(404, 413))
    level.add_firebar(410, 7, n_balls=4, speed=2.0)
    level.add_pipe("woods_exit", 416, kind="travel", target="cave_entry", label="To the Crystal Cave")
    level.add_rock(last_col - 1, last_col, 0, FLOOR)


def _build_sky_bridge(level):
    first_col, last_col = SKY
    level.add_zone(first_col, "sky")
    level.add_ground(first_col, 430)
    level.add_pipe("sky_entry", 424)
    level.add_checkpoint(428)
    # Crumbling clouds over the void.
    level.add_crumble(432, 11, n_tiles=3)
    level.add_crumble(436, 10, n_tiles=3)
    level.add_crumble(440, 9, n_tiles=3)
    level.add_crumble(444, 10, n_tiles=3)
    level.add_spark_row(436, 445, 7)

    level.add_ground(448, 455)
    level.add_enemy("buzzer", 451, surface_row=10)
    level.add_firebar(452, 9, n_balls=4, speed=1.9)
    level.add_moving_platform(457, GROUND_ROW, n_tiles=3, travel_cols=6, period=5.0)

    level.add_ground(467, 472)
    level.add_spring(471)  # the only way across the next gap
    level.add_platform(474, 479, 4)
    level.add_spark_row(474, 479, 3)
    level.add_block(477, 0, "shield")

    level.add_ground(481, 495)
    level.add_checkpoint(483)
    level.add_platform(485, 494, 8)  # a low roof: no jumping over the Brute
    level.add_enemy("brute", 489, patrol_cols=(486, 494))
    level.add_crumble(500, 11)
    level.add_crumble(503, 10)
    level.add_crumble(506, 9)
    level.add_firebar(504, 6, n_balls=4, speed=-1.6)

    level.add_ground(509, last_col)
    level.add_checkpoint(510)
    level.add_enemy("spikeback", 512, patrol_cols=(511, 514))
    level.add_enemy("distractor", 513, patrol_cols=(511, 514))
    level.add_pipe("sky_exit", 516, kind="travel", target="sunset_entry", label="To the Sunset Heights")
    level.add_rock(last_col - 1, last_col, 0, FLOOR)
