"""Layout of Level 2, "Hold Your Horses" (topic: response inhibition).

Every world asks the hero to stop in time:

1. Frost Peaks: slippery ice, where braking takes a while, sliding
   penguins and a first red-light zone; the insights "response inhibition"
   and "go/no-go".
2. Neon City: red-light zones (moving on red hurts), Signal Sam's
   stop-signal race in the middle (it opens the city gate and teaches the
   Stop Signal skill) and the insights "Stroop" and "ego depletion".
3. Volcano Fortress: lava pits with leaping embers and fire bars.
4. Captain Impulse's arena: the boss, the owl's quiz and the goal.

The hero starts with all skills of Level 1 (punch, double jump, fear
conditioning and the QRP Blaster).
"""

from .config import TILE_SIZE
from .level import GROUND_ROW
from .story_level import FLOOR, StoryLevel

ICE = (0, 129)
CITY = (130, 259)
VOLCANO = (260, 369)
ARENA_HALL = (370, 449)
ARENA = (378, 401)
N_COLS = ARENA_HALL[1] + 1
AIR = GROUND_ROW - 2
CEILING = 3
START_SKILLS = ("punch", "double_jump", "fear", "blaster")


def build_level_two():
    """
    Build a fresh copy of Level 2.

    Returns
    -------
    StoryLevel
        The level with all tiles, pickups, enemies and characters in place.
    """
    level = StoryLevel("level_2", "Level 2: Hold Your Horses", N_COLS, "ice", start_skills=START_SKILLS)
    _build_ice(level)
    _build_city(level)
    _build_volcano(level)
    _build_arena(level)
    level.world_order = [ICE[0], CITY[0], VOLCANO[0], ARENA_HALL[0]]
    return level


def _build_ice(level):
    level.add_ground(0, 24)
    level.add_sign(4, "Frost Peaks", ("Ice is slippery: start braking early!",))
    level.add_platform(18, 21, 9)
    level.add_orb("inhibition", 20, row=7)
    level.add_enemy("slider", 14, patrol_cols=(10, 24))
    level.add_sparks([(25, 9), (26, 8), (27, 9)])

    level.add_ground(29, 50)
    level.add_block(33, 8, "spark")
    level.add_block(34, 8, "shield")
    level.add_spikes(39, 41, FLOOR)  # slide into these and it hurts
    level.add_enemy("slider", 45, patrol_cols=(43, 50))
    level.add_crumble(52, 10)
    level.add_crumble(56, 9)
    level.add_spark_row(52, 57, 7)

    level.add_ground(60, 85)
    level.add_checkpoint(62)
    level.add_demo("red_light_how", 63)
    level.add_sign(64, "Red light!", ("When the light turns RED, stand still - on ice!",))
    level.add_red_light(67, 83, 75)
    level.add_block(73, 8, "star")
    level.add_spark_row(70, 80, AIR)

    level.add_ground(91, ICE[1])
    level.add_enemy("slider", 95, patrol_cols=(92, 101))
    level.add_enemy("slider", 99, patrol_cols=(92, 101))
    level.add_spring(104)
    level.add_platform(106, 110, 3)
    level.add_spark_row(106, 110, 2)
    level.add_orb("go_nogo", 109, row=1)
    level.add_checkpoint(113)
    level.add_spikes(116, 117, FLOOR)
    level.add_pipe("to_city", 124, kind="travel", target="city_entry", label="To Neon City")
    level.add_rock(ICE[1] - 1, ICE[1], 0, FLOOR)


def _build_city(level):
    first_col, last_col = CITY
    level.add_zone(first_col, "city")
    level.add_ground(first_col, 160)
    level.add_pipe("city_entry", 132)
    level.add_checkpoint(136)
    level.add_sign(138, "Neon City", ("RED light: freeze!  GREEN light: go!",))
    level.add_red_light(141, 160, 150)
    level.add_platform(150, 154, 9)
    level.add_orb("stroop", 152, row=7)
    level.add_enemy("distractor", 146, patrol_cols=(142, 149))

    level.add_ground(165, 205)
    level.add_npc("signal_sam", 170)
    level.add_sign(167, "City gate", ("Locked. Win Signal Sam's race (E)!",))
    level.add_gate("city_gate", 176, 0)
    level.add_checkpoint(178)
    level.add_red_light(181, 199, 190, offset=1.5)
    level.add_enemy("distractor", 185, patrol_cols=(182, 198))
    level.add_enemy("spikeback", 193, patrol_cols=(182, 198))
    level.add_block(188, 8, "heart")
    level.add_moving_platform(207, GROUND_ROW, n_tiles=3, travel_cols=4, period=4.0)

    level.add_ground(215, last_col)
    level.add_platform(218, 221, 9)
    level.add_platform(223, 226, 6)
    level.add_orb("ego_depletion", 225, row=3)
    level.add_enemy("buzzer", 230, surface_row=8, patrol_cols=(227, 236))
    level.add_enemy("hackling", 233, surface_row=6, patrol_cols=(228, 240))
    level.add_checkpoint(238)
    level.add_crates(242, top_row=8, spark_rows=(9, 10))
    level.add_enemy("spikeback", 246, patrol_cols=(244, 250))
    level.add_pipe("to_volcano", 252, kind="travel", target="volcano_entry", label="To the Volcano Fortress")
    level.add_rock(last_col - 1, last_col, 0, FLOOR)


def _build_volcano(level):
    first_col, last_col = VOLCANO
    level.add_zone(first_col, "volcano")
    level.add_ground(first_col, 275)
    level.add_pipe("volcano_entry", 262)
    level.add_checkpoint(266)
    level.add_sign(268, "Embers", ("They leap out of the lava. Punch or shoot them!",))
    level.add_lava(276, 281)
    level.add_enemy("ember", 278)

    level.add_ground(282, 295)
    level.add_firebar(288, 8, n_balls=5, speed=1.7)
    level.add_enemy("spikeback", 292, patrol_cols=(289, 295))
    level.add_lava(296, 303)
    level.add_crumble(298, 10)
    level.add_enemy("ember", 301)

    level.add_ground(304, 325)
    level.add_checkpoint(306)
    level.add_platform(310, 314, 8)
    level.add_firebar(312, 5, n_balls=4, speed=-2.0)
    level.add_block(314, 4, "mushroom")
    level.add_enemy("distractor", 318, patrol_cols=(315, 324))
    level.add_enemy("hackling", 322, surface_row=9, patrol_cols=(318, 325))
    level.add_lava(326, 333)
    level.add_moving_platform(327, GROUND_ROW, n_tiles=3, travel_cols=3, period=3.5)
    level.add_enemy("ember", 332)

    level.add_ground(334, last_col)
    level.add_checkpoint(336)
    level.add_block(340, 8, "heart")
    level.add_firebar(346, 9, n_balls=4, speed=2.2)
    level.add_enemy("spikeback", 351, patrol_cols=(348, 356))
    level.add_pipe("to_arena", 362, kind="travel", target="arena_entry", label="Captain Impulse's arena")
    level.add_rock(last_col - 1, last_col, 0, FLOOR)


def _build_arena(level):
    first_col, last_col = ARENA_HALL
    level.add_zone(first_col, "boss_impulse")
    level.add_room(first_col, last_col, CEILING)
    level.add_ground(first_col, last_col)
    level.add_pipe("arena_entry", 372)
    level.add_checkpoint(376)
    level.add_gate("arena_in", ARENA[0], CEILING + 1)
    level.add_gate("arena_out", ARENA[1], CEILING + 1)
    level.add_boss("captain_impulse", ARENA[0], ARENA[1], "arena_in", "arena_out")
    level.add_npc("quiz_owl", 422)
    level.add_quiz((426, 430, 434), 8, gate="quiz_gate", topics=("inhibition", "go_nogo", "horse_race", "stroop", "ego_depletion"))
    level.add_gate("quiz_gate", 438, CEILING + 1)
    level.goal_x = 444.5 * TILE_SIZE
