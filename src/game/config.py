"""Central settings for the game.

Everything a user may reasonably want to tune (window size, player physics,
flanker task timing, pass threshold) lives here, so no other module needs to
be edited to change it.
"""

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

GAME_TITLE = "Mind Quest"
LEVEL_ONE_NAME = "Level 1: Focus Fields"
MUSIC_VOLUME = 0.22
SOUND_VOLUME = 0.35

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TILE_SIZE = 48
# Longest simulated time step; keeps physics stable if a frame takes too long.
MAX_FRAME_TIME = 1 / 30


@dataclass(frozen=True)
class PlayerSettings:
    """Movement and health settings of the player character.

    Speeds are in pixels per second, accelerations in pixels per second
    squared and durations in seconds.
    """

    walk_speed: float = 300.0
    ground_acceleration: float = 2600.0
    air_acceleration: float = 1800.0
    gravity: float = 2400.0
    jump_speed: float = 900.0
    # Upward speed left after releasing the jump key early (short hop).
    jump_cut_speed: float = 350.0
    fast_fall_gravity_factor: float = 1.8
    max_fall_speed: float = 1100.0
    # Grace period in which a jump still works just after walking off a ledge.
    coyote_time: float = 0.10
    # A jump pressed this long before landing is still carried out.
    jump_buffer_time: float = 0.12
    stomp_bounce_speed: float = 560.0
    start_hearts: int = 3
    max_hearts: int = 5
    invulnerable_time: float = 1.5
    boost_multiplier: float = 1.5
    boost_duration: float = 8.0
    sparks_per_heart: int = 25
    # Strength of the second jump relative to the first one.
    double_jump_factor: float = 1.0
    # Flying speed in admin mode.
    fly_speed: float = 700.0
    punch_time: float = 0.18
    punch_cooldown: float = 0.35
    punch_reach: int = 46
    fear_radius: float = 400.0
    fear_duration: float = 4.0
    fear_cooldown: float = 6.0


@dataclass(frozen=True)
class FlankerSettings:
    """Design and timing of the child flanker task (durations in seconds).

    The defaults follow the child Attention Network Test (Rueda et al., 2004):
    a variable fixation period and a response window of 1.7 seconds.
    """

    n_practice_trials: int = 6
    # Each of the 6 cells (3 conditions x 2 directions) is shown this often.
    n_test_repetitions: int = 4
    pass_accuracy: float = 0.90
    fixation_min: float = 0.4
    fixation_max: float = 1.6
    response_deadline: float = 1.7
    practice_feedback_time: float = 1.6
    test_feedback_time: float = 0.6

    def __post_init__(self):
        if not 0 < self.pass_accuracy <= 1:
            raise ValueError("pass_accuracy must be between 0 and 1")
        if self.fixation_min > self.fixation_max:
            raise ValueError("fixation_min must not exceed fixation_max")
        if self.n_test_repetitions < 1:
            raise ValueError("n_test_repetitions must be at least 1")
