"""Layout of Level 3, "Mission Control" (topic: executive control).

The three worlds each train one executive function (Miyake et al., 2000):

1. Clockwork Factory: conveyor belts and SWITCH blocks that swap red and
   blue blocks (shifting), and the Tower of London puzzle gate (planning);
   the insights "executive functions", "planning" and "switching".
2. Space Station: low gravity, hovering drones and the Memory Machine's
   2-back task (updating), which opens the door to the control room.
3. The Rule Keeper's control room: the card-sorting boss, the owl's quiz
   and the goal.

The hero starts with all skills of Levels 1 and 2.
"""

from .config import TILE_SIZE
from .level import GROUND_ROW
from .story_level import FLOOR, StoryLevel

FACTORY = (0, 159)
STATION = (160, 279)
CONTROL_ROOM = (280, 359)
ARENA = (288, 311)
CARD_COLS = (294, 299, 304)
CARD_ROW = 8
N_COLS = CONTROL_ROOM[1] + 1
AIR = GROUND_ROW - 2
CEILING = 3
ROOM_CEILING = 0
START_SKILLS = ("punch", "double_jump", "fear", "blaster", "stop")


def build_level_three():
    """
    Build a fresh copy of Level 3.

    Returns
    -------
    StoryLevel
        The level with all tiles, pickups, enemies and characters in place.
    """
    level = StoryLevel("level_3", "Level 3: Mission Control", N_COLS, "factory", start_skills=START_SKILLS)
    _build_factory(level)
    _build_station(level)
    _build_control_room(level)
    level.world_order = [FACTORY[0], STATION[0], CONTROL_ROOM[0]]
    return level


def _build_factory(level):
    level.add_ground(0, 31)
    level.add_sign(3, "Clockwork Factory", ("Belts carry you. SWITCH blocks swap red and blue blocks!",))
    level.add_platform(9, 12, 8)
    level.add_orb("executive_functions", 11, row=6)
    level.add_conveyor(14, 23, GROUND_ROW, -1)
    level.add_enemy("cogbot", 20, patrol_cols=(15, 23))
    # A switch puzzle: the red wall blocks the way, the blue bridge is missing.
    level.add_demo("switch_how", 22)
    level.add_switch(26, 8)
    level.add_color_blocks("red", [(30, row) for row in range(4, GROUND_ROW)])
    level.add_color_blocks("blue", [(col, 10) for col in range(32, 40)])

    level.add_ground(40, 70)
    level.add_checkpoint(42)
    level.add_enemy("cogbot", 47, patrol_cols=(44, 52))
    level.add_npc("tower_gate", 55)
    level.add_sign(52, "Tower gate", ("Locked. Solve the Tower of London (E)!",))
    level.add_gate("tower_gate", 60, 0)
    level.add_checkpoint(62)
    level.add_conveyor(64, 72, GROUND_ROW, 1)
    level.add_firebar(68, 8, n_balls=4, speed=1.8)

    level.add_ground(73, 100)
    # Now the rule is reversed: blue blocks the way, and a staircase of red
    # blocks leads to the switching insight.
    level.add_switch(76, 8)
    level.add_color_blocks("red", [(80, 9), (81, 9), (83, 7), (84, 7), (86, 5), (87, 5)])
    level.add_color_blocks("blue", [(90, row) for row in range(4, GROUND_ROW)])
    level.add_orb("switching", 87, row=3)
    level.add_enemy("cogbot", 95, patrol_cols=(92, 100))
    level.add_block(82, 4, "star")
    level.add_crumble(103, 10)
    level.add_crumble(107, 9)

    level.add_ground(110, FACTORY[1])
    level.add_checkpoint(112)
    level.add_enemy("cogbot", 118, patrol_cols=(115, 125))
    level.add_enemy("hackling", 122, surface_row=9, patrol_cols=(118, 128))
    level.add_conveyor(130, 140, GROUND_ROW, -1)
    level.add_spikes(143, 144, FLOOR)
    level.add_block(146, 8, "heart")
    level.add_pipe("to_station", 152, kind="travel", target="station_entry", label="To the Space Station")
    level.add_rock(FACTORY[1] - 1, FACTORY[1], 0, FLOOR)


def _build_station(level):
    first_col, last_col = STATION
    level.add_zone(first_col, "space")
    level.add_ground(first_col, 180)
    level.add_pipe("station_entry", 162)
    level.add_checkpoint(166)
    level.add_sign(168, "Space Station", ("Low gravity: you float higher and fall slower!",))
    level.add_enemy("drone", 175, surface_row=9, patrol_cols=(171, 180))
    level.add_platform(184, 186, 9)
    level.add_platform(189, 191, 7)
    level.add_spark_row(184, 191, 5)

    level.add_ground(194, 230)
    level.add_npc("memory_machine", 200)
    level.add_sign(197, "Control door", ("Locked. Feed the Memory Machine (E)!",))
    level.add_gate("station_gate", 206, 0)
    level.add_checkpoint(209)
    level.add_enemy("drone", 214, surface_row=8, patrol_cols=(211, 220))
    level.add_enemy("cogbot", 218, patrol_cols=(212, 226))
    level.add_switch(222, 7)
    level.add_color_blocks("blue", [(226, 9), (227, 9), (228, 9)])
    level.add_block(227, 5, "shield")

    level.add_ground(236, last_col)
    level.add_enemy("drone", 242, surface_row=7, patrol_cols=(238, 248))
    level.add_enemy("hackling", 260, surface_row=8, patrol_cols=(256, 266))
    level.add_firebar(250, 8, n_balls=5, speed=-1.6)
    level.add_checkpoint(256)
    level.add_enemy("cogbot", 262, patrol_cols=(258, 268))
    level.add_pipe("to_control", 272, kind="travel", target="control_entry", label="The Rule Keeper's control room")
    level.add_rock(last_col - 1, last_col, 0, FLOOR)


def _build_control_room(level):
    first_col, last_col = CONTROL_ROOM
    level.add_zone(first_col, "boss_rules")
    # A high ceiling leaves room for the floating boss.
    level.add_room(first_col, last_col, ROOM_CEILING)
    level.add_ground(first_col, last_col)
    level.add_pipe("control_entry", 282)
    level.add_checkpoint(286)
    level.add_gate("room_in", ARENA[0], ROOM_CEILING + 1)
    level.add_gate("room_out", ARENA[1], ROOM_CEILING + 1)
    level.add_boss("rule_keeper", ARENA[0], ARENA[1], "room_in", "room_out", card_cells=[(col, CARD_ROW) for col in CARD_COLS])
    level.add_npc("quiz_owl", 324)
    level.add_quiz((328, 332, 336), 8, gate="quiz_gate", topics=("executive_functions", "updating", "planning", "switching", "card_sorting"))
    level.add_gate("quiz_gate", 340, ROOM_CEILING + 1)
    level.goal_x = 346.5 * TILE_SIZE
