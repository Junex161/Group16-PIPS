"""Logic of the stop-signal task: trial lists, the SSD staircase and scoring.

On every trial a race car points left or right and the player presses the
matching key as fast as possible (a go trial). On a quarter of the trials a
STOP sign appears shortly after the car, and the player has to withhold the
response (a stop trial). The delay between car and STOP sign, the
stop-signal delay (SSD), follows a staircase: it grows after a successful
stop and shrinks after a failed one, so that stopping succeeds about half
of the time. From the go reaction times and the mean SSD the stop-signal
reaction time (SSRT), the duration of the stopping process, is estimated
with the integration method (Logan & Cowan, 1984; Verbruggen et al., 2019).

This module contains no pygame code.
"""

import math
import random
from dataclasses import dataclass
from statistics import mean

DIRECTIONS = ("left", "right")
TRIAL_TYPES = ("go", "stop")
COLUMNS = (
    "participant_id",
    "attempt",
    "block",
    "trial",
    "trial_type",
    "direction",
    "ssd_ms",
    "response",
    "correct",
    "rt_ms",
)


@dataclass(frozen=True)
class StopTrial:
    """One trial: "go" or "stop", and the direction the car points to."""

    trial_type: str
    direction: str

    def __post_init__(self):
        if self.trial_type not in TRIAL_TYPES:
            raise ValueError(f"trial_type must be one of {TRIAL_TYPES}")
        if self.direction not in DIRECTIONS:
            raise ValueError(f"direction must be one of {DIRECTIONS}")


@dataclass(frozen=True)
class StopResult:
    """
    The outcome of one trial.

    ``ssd_ms`` is the stop-signal delay (None on go trials). ``response`` and
    ``rt_ms`` are None if no key was pressed. A go trial is correct when the
    right key was pressed in time, a stop trial when no key was pressed.
    """

    block: str
    trial: int
    trial_type: str
    direction: str
    ssd_ms: int | None
    response: str | None
    correct: bool
    rt_ms: int | None


@dataclass(frozen=True)
class StopSummary:
    """
    Performance in one block.

    ``go_accuracy`` is the share of go trials with the correct key in time,
    ``stop_success`` the share of stop trials without a response, and
    ``ssrt_ms`` the stop-signal reaction time (None if it cannot be
    estimated, for example without any stop trials).
    """

    n_go: int
    n_stop: int
    go_accuracy: float
    go_omissions: int
    mean_go_rt_ms: float | None
    stop_success: float
    mean_ssd_ms: float | None
    ssrt_ms: float | None


class Staircase:
    """
    The one-up/one-down tracking of the stop-signal delay.

    Parameters
    ----------
    start, step, minimum, maximum : float
        Starting delay, step size and limits in seconds.
    """

    def __init__(self, start, step, minimum, maximum):
        self.value, self.step, self.minimum, self.maximum = start, step, minimum, maximum

    def update(self, stopped):
        """Make stopping harder after a success and easier after a failure."""
        change = self.step if stopped else -self.step
        self.value = round(min(self.maximum, max(self.minimum, self.value + change)), 6)
        return self.value


def make_trials(n_trials, stop_share, rng=None):
    """
    Create a shuffled list of go and stop trials.

    Parameters
    ----------
    n_trials : int
        Total number of trials.
    stop_share : float
        Share of stop trials (rounded to whole trials).
    rng : random.Random or None, optional
        Random number generator; pass a seeded one for reproducible orders.

    Returns
    -------
    list of StopTrial
        The first trial is always a go trial, and the directions are
        balanced within go and within stop trials.
    """
    if n_trials < 1:
        raise ValueError("n_trials must be at least 1")
    rng = rng or random.Random()
    n_stop = min(n_trials - 1, round(n_trials * stop_share))
    trials = []
    for trial_type, count in (("go", n_trials - n_stop), ("stop", n_stop)):
        directions = [DIRECTIONS[index % 2] for index in range(count)]
        rng.shuffle(directions)
        trials += [StopTrial(trial_type, direction) for direction in directions]
    rng.shuffle(trials)
    first_go = next(index for index, trial in enumerate(trials) if trial.trial_type == "go")
    trials[0], trials[first_go] = trials[first_go], trials[0]
    return trials


def ssrt_integration(go_rts_ms, p_respond, mean_ssd_ms):
    """
    Estimate the stop-signal reaction time with the integration method.

    The go reaction times are sorted, and the one at the rank that
    corresponds to the probability of responding on stop trials is taken
    as the moment the stop process finishes; the mean SSD is subtracted.

    Parameters
    ----------
    go_rts_ms : list of float
        Reaction times of all go trials; missed go trials should already be
        replaced by the longest reaction time (Verbruggen et al., 2019).
    p_respond : float
        Share of stop trials with a response.
    mean_ssd_ms : float
        Mean stop-signal delay.

    Returns
    -------
    float or None
        The SSRT in milliseconds, or None without go reaction times.
    """
    if not go_rts_ms:
        return None
    ordered = sorted(go_rts_ms)
    rank = min(len(ordered), max(1, math.ceil(p_respond * len(ordered))))
    return ordered[rank - 1] - mean_ssd_ms


def summarise(results, response_deadline_ms):
    """
    Summarise one block of stop-signal trials.

    Parameters
    ----------
    results : list of StopResult
        Trials of one block.
    response_deadline_ms : float
        Longest possible reaction time; used to replace missed go trials
        when the SSRT is estimated.

    Returns
    -------
    StopSummary
        Go accuracy and speed, stopping success and the SSRT.
    """
    go = [r for r in results if r.trial_type == "go"]
    stop = [r for r in results if r.trial_type == "stop"]
    go_rts = [r.rt_ms for r in go if r.correct]
    responded_rts = [r.rt_ms for r in go if r.rt_ms is not None]
    longest = max(responded_rts, default=response_deadline_ms)
    # Choice errors count as responses; missed go trials get the longest RT.
    all_go_rts = [r.rt_ms if r.rt_ms is not None else longest for r in go]
    stop_success = sum(r.correct for r in stop) / len(stop) if stop else 0.0
    mean_ssd = mean(r.ssd_ms for r in stop) if stop else None
    ssrt = ssrt_integration(all_go_rts, 1 - stop_success, mean_ssd) if stop and go else None
    return StopSummary(
        n_go=len(go),
        n_stop=len(stop),
        go_accuracy=sum(r.correct for r in go) / len(go) if go else 0.0,
        go_omissions=sum(r.response is None for r in go),
        mean_go_rt_ms=mean(go_rts) if go_rts else None,
        stop_success=stop_success,
        mean_ssd_ms=mean_ssd,
        ssrt_ms=ssrt,
    )


def has_passed(summary, min_go_accuracy, min_stop_success):
    """Return True if go responses were accurate enough and some stops succeeded."""
    return summary.n_go > 0 and summary.go_accuracy >= min_go_accuracy and summary.stop_success >= min_stop_success
