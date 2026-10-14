"""Layout of the Prologue, "The Replication Crisis" (topic: Open Science).

The Prologue is also the tutorial of the game: every new move is introduced
on its own, with a short sign, before it is needed. Three worlds are
connected by pipes:

1. Old Campus: Professor Shell tells the story, the hero learns to walk,
   jump, hit blocks, stomp and punch; the insight "replication".
2. The Archive: stacks of shaky findings crumble under the hero's feet;
   the insight "the Reproducibility Project".
3. The File Drawer's hall: the boss fight (publication bias), the insight
   "Open Science", the owl's quiz and the goal.

The hero starts with Punch only; everything here can be done with single
jumps (about 3.5 tiles high and 4.5 tiles far).
"""

from .config import TILE_SIZE
from .level import GROUND_ROW
from .story_level import FLOOR, StoryLevel

CAMPUS = (0, 119)
ARCHIVE = (120, 229)
HALL = (230, 299)
N_COLS = HALL[1] + 1
ARENA = (238, 261)
AIR = GROUND_ROW - 2
CEILING = 3


def build_prologue():
    """
    Build a fresh copy of the Prologue.

    Returns
    -------
    StoryLevel
        The level with all tiles, pickups, enemies and characters in place.
    """
    level = StoryLevel("prologue", "Prologue: The Replication Crisis", N_COLS, "campus", start_skills=("punch",))
    _build_campus(level)
    _build_archive(level)
    _build_hall(level)
    level.world_order = [CAMPUS[0], ARCHIVE[0], HALL[0]]
    return level


def _build_campus(level):
    level.add_ground(0, 30)
    level.add_npc("professor_shell", 7)
    level.add_sign(11, "Moving", ("A/D: walk.  SPACE or W: jump - hold it to jump higher.",))
    level.add_spark_row(13, 16, AIR)
    level.add_sign(18, "Blocks", ("Jump into a ?-block from below.",))
    level.add_block(20, 8, "spark")
    level.add_block(21, 8, "mushroom")
    level.add_block(22, 8, "spark")
    level.add_sign(24, "Hacklings", ("Count Hackula's bats! Jump on them.",))
    level.add_enemy("hackling", 28, surface_row=10, patrol_cols=(25, 30))
    level.add_sparks([(31, 9), (32, 8), (33, 9)])

    level.add_ground(34, 60)
    level.add_demo("punch", 36)
    level.add_crates(40, top_row=8, spark_rows=(9,))
    level.add_enemy("hackling", 45, surface_row=9, patrol_cols=(42, 48))
    level.add_checkpoint(49)
    for step, col in enumerate(range(51, 54)):
        level.add_column(col, top_row=FLOOR - step)
    level.add_platform(55, 58, 7)
    level.add_spark_row(55, 58, 6)
    level.add_orb("replication", 57, row=5)  # the first insight waits on the high step

    level.add_ground(64, 90)
    level.add_enemy("distractor", 68, patrol_cols=(66, 74))
    level.add_block(71, 8, "heart")
    level.add_block(80, 8, "star", hidden=True)
    level.add_enemy("hackling", 79, surface_row=8, patrol_cols=(76, 84))
    level.add_crates(86, top_row=9)
    level.add_moving_platform(92, GROUND_ROW, n_tiles=3, travel_cols=3, period=4.0)

    level.add_ground(99, CAMPUS[1])
    level.add_checkpoint(101)
    level.add_sign(106, "Pipes", ("Stand on a pipe and press S to go down.",))
    level.add_pipe("to_archive", 112, kind="travel", target="archive_entry", label="Into the Archive")
    level.add_rock(CAMPUS[1] - 1, CAMPUS[1], 0, FLOOR)


def _build_archive(level):
    first_col, last_col = ARCHIVE
    level.add_zone(first_col, "archive")
    level.add_room(first_col, last_col, CEILING)
    level.add_ground(first_col, 140)
    level.add_pipe("archive_entry", 122)
    level.add_checkpoint(126)
    level.add_sign(129, "Shaky findings", ("Unreplicated findings crumble - keep moving!",))
    # Crumbling stacks of 'findings' over a gap.
    level.add_crumble(142, 10)
    level.add_crumble(146, 9)
    level.add_crumble(150, 10)
    level.add_spark_row(145, 149, 7)

    level.add_ground(153, 176)
    level.add_platform(156, 159, 9)
    level.add_platform(162, 165, 7)
    level.add_orb("reproducibility", 164, row=5)
    level.add_enemy("hackling", 160, surface_row=8, patrol_cols=(157, 166))
    level.add_block(157, 5, "shield")
    level.add_enemy("distractor", 170, patrol_cols=(167, 173))
    level.add_crates(175, top_row=8, spark_rows=(10,))

    level.add_ground(177, 199)
    level.add_platform(180, 184, 8)
    level.add_spikes(181, 183, FLOOR)
    level.add_spark_row(180, 184, 7)
    level.add_checkpoint(187)
    level.add_enemy("hackling", 192, surface_row=9, patrol_cols=(189, 197))
    level.add_enemy("distractor", 195, patrol_cols=(190, 199))
    level.add_crumble(202, 10)
    level.add_crumble(205, 9)
    level.add_crumble(208, 10)

    level.add_ground(211, last_col)
    level.add_checkpoint(213)
    level.add_sign(216, "Shhh ...", ("Something is rattling behind that pipe ...",))
    level.add_pipe("to_hall", 222, kind="travel", target="hall_entry", label="The File Drawer's hall")


def _build_hall(level):
    first_col, last_col = HALL
    level.add_zone(first_col, "boss_drawer")
    level.add_room(first_col, last_col, CEILING)
    level.add_ground(first_col, last_col)
    level.add_pipe("hall_entry", 232)
    level.add_checkpoint(236)
    level.add_gate("hall_in", ARENA[0], CEILING + 1)
    level.add_gate("hall_out", ARENA[1], CEILING + 1)
    level.add_boss("file_drawer", ARENA[0], ARENA[1], "hall_in", "hall_out")
    level.add_orb("open_science", 271, row=9)
    level.add_npc("quiz_owl", 275)
    level.add_quiz((279, 283, 287), 8, gate="quiz_gate", topics=("replication", "reproducibility", "file_drawer", "open_science"))
    level.add_gate("quiz_gate", 291, CEILING + 1)
    level.goal_x = 295.5 * TILE_SIZE
