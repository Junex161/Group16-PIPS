"""Central settings for the game.

Everything a user may reasonably want to tune (window size, player physics,
flanker task timing, pass threshold) lives here, so no other module needs to
be edited to change it.
"""

from dataclasses import dataclass, replace
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
    star_duration: float = 8.0
    # Upward speed after landing on a spring (about ten tiles high).
    spring_speed: float = 1500.0
    sparks_per_heart: int = 25
    # Strength of the second jump relative to the first one.
    double_jump_factor: float = 1.0
    # Flying speed in admin mode.
    fly_speed: float = 700.0
    punch_time: float = 0.18
    punch_cooldown: float = 0.35
    punch_reach: int = 46
    shot_cooldown: float = 0.4
    shot_speed: float = 720.0
    shot_lifetime: float = 0.9
    fear_radius: float = 400.0
    fear_duration: float = 4.0
    fear_cooldown: float = 6.0


@dataclass(frozen=True)
class Difficulty:
    """
    How hard the game is. The map looks the same in every mode.

    ``jump_factor`` and ``enemy_speed_factor`` scale the normal values,
    ``enemy_share`` is the share of the ordinary enemies that appear,
    ``pit_narrowing`` is the number of tiles added to each edge of a pit and
    ``flanker_pass_accuracy`` replaces the pass threshold of the flanker task
    (None keeps the one from ``FlankerSettings``).
    """

    key: str
    name: str
    description: str
    start_hearts: int = 3
    max_hearts: int = 5
    jump_factor: float = 1.0
    coyote_time: float = 0.10
    invulnerable_time: float = 1.5
    enemy_speed_factor: float = 1.0
    enemy_share: float = 1.0
    pit_narrowing: int = 0
    falling_costs_heart: bool = True
    wrong_answer_costs_heart: bool = True
    flanker_pass_accuracy: float | None = None

    def apply_to(self, settings):
        """Return a copy of ``PlayerSettings`` adjusted to this difficulty."""
        return replace(
            settings,
            start_hearts=self.start_hearts,
            max_hearts=self.max_hearts,
            jump_speed=settings.jump_speed * self.jump_factor,
            coyote_time=self.coyote_time,
            invulnerable_time=self.invulnerable_time,
        )


DIFFICULTIES = (
    Difficulty(
        key="easy",
        name="Easy",
        description="Five hearts, higher jumps, narrower pits, fewer and slower enemies. "
        "Falling and wrong quiz answers cost no heart, and 75% is enough in the Pond Challenge.",
        start_hearts=5,
        max_hearts=6,
        jump_factor=1.1,
        coyote_time=0.2,
        invulnerable_time=2.5,
        enemy_speed_factor=0.6,
        enemy_share=0.5,
        pit_narrowing=1,
        falling_costs_heart=False,
        wrong_answer_costs_heart=False,
        flanker_pass_accuracy=0.75,
    ),
    Difficulty(
        key="medium",
        name="Medium",
        description="The standard game: three hearts, all enemies, 90% needed in the Pond Challenge.",
    ),
    Difficulty(
        key="hard",
        name="Hard",
        description="Three hearts and no more than four, faster enemies and less time to recover after a hit.",
        max_hearts=4,
        coyote_time=0.06,
        invulnerable_time=1.0,
        enemy_speed_factor=1.4,
    ),
)
DEFAULT_DIFFICULTY = DIFFICULTIES[1]


@dataclass(frozen=True)
class FlankerSettings:
    """Design and timing of the child flanker task (durations in seconds).

    The defaults follow the child Attention Network Test (Rueda et al., 2004):
    a variable fixation period and a response window of 1.7 seconds.
    """

    n_practice_trials: int = 6
    # How often the balanced set of 36 trials is shown: 3 conditions x 2
    # directions x 2 spacings x 3 numbers of flankers (neutral trials, which
    # have no flankers, are repeated to match).
    n_test_repetitions: int = 1
    # Gaps between neighbouring fish in pixels and numbers of flanking fish.
    spacings: tuple = (35, 85)
    flanker_counts: tuple = (4, 6, 8)
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
        if not self.spacings or any(spacing < 0 for spacing in self.spacings):
            raise ValueError("spacings must be zero or more pixels")
        if not self.flanker_counts or any(count < 2 or count % 2 for count in self.flanker_counts):
            raise ValueError("flanker_counts must be even numbers of at least 2")


@dataclass(frozen=True)
class StopSignalSettings:
    """Design and timing of the stop-signal task in Level 2 (durations in seconds).

    The design follows the consensus guide of Verbruggen et al. (2019): a
    quarter of the trials are stop trials, and the stop-signal delay (SSD)
    is adjusted in steps of 50 ms so that stopping succeeds about half of
    the time. The task is passed with enough correct go responses and at
    least some successful stops. The guide recommends at least 50 stop
    trials for a reliable SSRT; the game uses fewer by default to keep the
    task short, so raise ``n_test_trials`` for real data collection.
    """

    n_practice_trials: int = 12
    n_test_trials: int = 64
    stop_share: float = 0.25
    ssd_start: float = 0.25
    ssd_step: float = 0.05
    ssd_min: float = 0.05
    ssd_max: float = 0.9
    fixation_time: float = 0.5
    response_deadline: float = 1.25
    practice_feedback_time: float = 1.4
    test_feedback_time: float = 0.5
    pass_go_accuracy: float = 0.85
    pass_stop_success: float = 0.25

    def __post_init__(self):
        if not 0 < self.stop_share < 1:
            raise ValueError("stop_share must be between 0 and 1")
        if not self.ssd_min <= self.ssd_start <= self.ssd_max:
            raise ValueError("ssd_start must lie between ssd_min and ssd_max")
        if self.ssd_max >= self.response_deadline:
            raise ValueError("ssd_max must be shorter than the response deadline")


@dataclass(frozen=True)
class NBackSettings:
    """Design and timing of the n-back task in Level 3 (durations in seconds).

    A letter is shown for ``stimulus_time``, followed by a blank screen; the
    player can answer until the next letter appears. A third of the letters
    are targets, as in many working-memory studies (Owen et al., 2005).
    """

    n: int = 2
    n_practice_trials: int = 14
    n_practice_targets: int = 5
    n_test_trials: int = 36
    n_test_targets: int = 12
    stimulus_time: float = 0.5
    blank_time: float = 2.0
    practice_feedback_time: float = 1.2
    letters: str = "BCDFGHKL"
    pass_accuracy: float = 0.80
    # Share of the matches that must be caught, so that doing nothing never passes.
    pass_hit_rate: float = 0.5

    def __post_init__(self):
        if self.n < 1:
            raise ValueError("n must be at least 1")
        for trials, targets in ((self.n_practice_trials, self.n_practice_targets), (self.n_test_trials, self.n_test_targets)):
            if not 0 <= targets <= trials - self.n:
                raise ValueError("there must be room for every target after the first n letters")
        if len(set(self.letters)) < self.n + 2:
            raise ValueError("letters needs more different letters than n + 1")


@dataclass(frozen=True)
class TowerSettings:
    """The Tower of London puzzles in Level 3 (Shallice, 1982).

    ``problem_moves`` lists the minimal number of moves of each puzzle, in
    the order they are played. ``max_extra_moves`` is how many moves more than
    the minimum are allowed before a puzzle starts over.
    """

    problem_moves: tuple = (3, 4, 5)
    max_extra_moves: int = 6

    def __post_init__(self):
        if not all(1 <= moves <= 8 for moves in self.problem_moves):
            raise ValueError("Tower of London problems need between 1 and 8 moves")
