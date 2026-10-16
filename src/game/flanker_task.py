"""Logic of the child flanker task: trial lists, scoring and data export.

This module contains no pygame code, so the design of the task can be tested
and reused (for example in a simulation) without opening a window. The task is
modelled on the flanker part of the child Attention Network Test (Rueda et
al., 2004): a central fish is shown alone (neutral) or with flanking fish
that swim the same way (congruent) or the opposite way (incongruent).

To make the task less easy and to vary how strongly the flankers interfere,
every flanker display also varies the gap between neighbouring fish
(``spacing``, in pixels) and the number of flanking fish (``nr_flankers``,
split evenly to the left and right of the middle fish). Both are crossed
with condition and direction, so every combination appears equally often.
"""

import csv
import random
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean

from .config import DATA_DIR

CONDITIONS = ("congruent", "incongruent", "neutral")
DIRECTIONS = ("left", "right")
# Gaps between neighbouring fish in pixels, and numbers of flanking fish.
SPACINGS = (35, 85)
FLANKER_COUNTS = (4, 6, 8)
COLUMNS = (
    "participant_id",
    "attempt",
    "block",
    "trial",
    "condition",
    "target_direction",
    "spacing",
    "nr_flankers",
    "response",
    "correct",
    "rt_ms",
)


@dataclass(frozen=True)
class FlankerTrial:
    """
    One flanker display.

    ``spacing`` is the gap between neighbouring fish in pixels and
    ``nr_flankers`` the number of flanking fish (an even number, half on each
    side). A neutral display has no flankers: its spacing is None and its
    number of flankers 0.
    """

    condition: str
    target_direction: str
    spacing: int | None = SPACINGS[-1]
    nr_flankers: int = FLANKER_COUNTS[0]

    def __post_init__(self):
        if self.condition not in CONDITIONS:
            raise ValueError(f"condition must be one of {CONDITIONS}")
        if self.target_direction not in DIRECTIONS:
            raise ValueError(f"target_direction must be one of {DIRECTIONS}")
        if self.condition == "neutral":
            object.__setattr__(self, "spacing", None)
            object.__setattr__(self, "nr_flankers", 0)
        elif self.nr_flankers < 2 or self.nr_flankers % 2:
            raise ValueError("nr_flankers must be an even number of at least 2")

    @property
    def flanker_direction(self):
        """Direction of the flanking fish, or None when the target is alone."""
        if self.condition == "neutral":
            return None
        if self.condition == "congruent":
            return self.target_direction
        return "left" if self.target_direction == "right" else "right"


@dataclass(frozen=True)
class TrialResult:
    """
    The outcome of one trial. ``response`` and ``rt_ms`` are None on a timeout.

    ``spacing`` and ``nr_flankers`` repeat the display of the trial (None and
    0 for neutral trials).
    """

    block: str
    trial: int
    condition: str
    target_direction: str
    response: str | None
    correct: bool
    rt_ms: int | None
    spacing: int | None = None
    nr_flankers: int = 0


@dataclass(frozen=True)
class FlankerSummary:
    """Performance in one block of trials.

    ``mean_rt_ms`` maps each condition to the mean reaction time of its correct
    trials (None if there were none). ``flanker_effect_ms`` is the incongruent
    minus the congruent mean reaction time.
    """

    n_trials: int
    n_correct: int
    accuracy: float
    mean_rt_ms: dict
    flanker_effect_ms: float | None


def make_cells(spacings=SPACINGS, flanker_counts=FLANKER_COUNTS):
    """
    Return one balanced set of trials.

    Congruent and incongruent displays cross direction, spacing and number
    of flankers. Neutral displays (no flankers) are repeated as often, so
    that all three conditions have the same number of trials.
    """
    n_layouts = len(spacings) * len(flanker_counts)
    cells = [
        FlankerTrial(condition, direction, spacing, count)
        for condition in ("congruent", "incongruent")
        for direction in DIRECTIONS
        for spacing in spacings
        for count in flanker_counts
    ]
    cells += [FlankerTrial("neutral", direction) for direction in DIRECTIONS for _ in range(n_layouts)]
    return cells


def make_trials(n_repetitions, rng=None, spacings=SPACINGS, flanker_counts=FLANKER_COUNTS):
    """
    Create a balanced, shuffled list of flanker trials.

    Parameters
    ----------
    n_repetitions : int
        How often the balanced set of trials (see ``make_cells``) is shown.
    rng : random.Random or None, optional
        Random number generator; pass a seeded one for reproducible orders.
    spacings : sequence of int, optional
        Gaps between neighbouring fish in pixels.
    flanker_counts : sequence of int, optional
        Numbers of flanking fish (even numbers).

    Returns
    -------
    list of FlankerTrial
        ``n_repetitions * 3 * 2 * len(spacings) * len(flanker_counts)``
        trials in random order (36 per repetition with the defaults).
    """
    if n_repetitions < 1:
        raise ValueError("n_repetitions must be at least 1")
    rng = rng or random.Random()
    trials = make_cells(spacings, flanker_counts) * n_repetitions
    rng.shuffle(trials)
    return trials


def make_practice_trials(n_trials, rng=None, spacings=SPACINGS, flanker_counts=FLANKER_COUNTS):
    """
    Create practice trials that cover the conditions as evenly as possible.

    Parameters
    ----------
    n_trials : int
        Number of practice trials (0 or more).
    rng : random.Random or None, optional
        Random number generator; pass a seeded one for reproducible orders.
    spacings, flanker_counts : sequence of int, optional
        As in ``make_trials``.

    Returns
    -------
    list of FlankerTrial
        ``n_trials`` trials in random order; every condition and direction
        appears before any of them appears twice.
    """
    if n_trials < 0:
        raise ValueError("n_trials must not be negative")
    rng = rng or random.Random()
    by_cell = {}
    for trial in make_trials(1, rng, spacings, flanker_counts):
        by_cell.setdefault((trial.condition, trial.target_direction), []).append(trial)
    rounds = []
    while len(rounds) < n_trials:
        batch = [trials[len(rounds) // len(by_cell) % len(trials)] for trials in by_cell.values()]
        rng.shuffle(batch)
        rounds += batch
    return rounds[:n_trials]


def summarise(results):
    """
    Summarise accuracy and reaction times of a list of trial results.

    Parameters
    ----------
    results : list of TrialResult
        Trials of one block. Timeouts count as errors.

    Returns
    -------
    FlankerSummary
        Accuracy, mean correct reaction time per condition and flanker effect.
    """
    n_correct = sum(result.correct for result in results)
    mean_rt_ms = {}
    for condition in CONDITIONS:
        rts = [r.rt_ms for r in results if r.condition == condition and r.correct]
        mean_rt_ms[condition] = mean(rts) if rts else None
    congruent, incongruent = mean_rt_ms["congruent"], mean_rt_ms["incongruent"]
    effect = None if congruent is None or incongruent is None else incongruent - congruent
    return FlankerSummary(
        n_trials=len(results),
        n_correct=n_correct,
        accuracy=n_correct / len(results) if results else 0.0,
        mean_rt_ms=mean_rt_ms,
        flanker_effect_ms=effect,
    )


def has_passed(summary, pass_accuracy):
    """Return True if the accuracy in ``summary`` reaches ``pass_accuracy``."""
    return summary.n_trials > 0 and summary.accuracy >= pass_accuracy


def clean_participant_id(participant_id):
    """Strip everything except letters, digits, '-' and '_' from an ID."""
    cleaned = "".join(c for c in str(participant_id) if c.isalnum() or c in "-_")
    if not cleaned:
        raise ValueError("participant_id must contain letters or digits")
    return cleaned


def save_results(results, participant_id, attempt=1, data_dir=DATA_DIR):
    """
    Save the trials of one flanker attempt as a timestamped CSV file.

    Parameters
    ----------
    results : list of TrialResult
        Practice and test trials in the order they were run.
    participant_id : str
        Anonymous participant label used in the data and the file name.
    attempt : int, optional
        Number of this attempt within the game session (1 = first try).
    data_dir : str or Path, optional
        Folder for the file; it is created if it does not exist.

    Returns
    -------
    Path
        Location of the written file, with the columns listed in ``COLUMNS``.
    """
    participant_id = clean_participant_id(participant_id)
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = data_dir / f"flanker_{participant_id}_{timestamp}_attempt-{attempt}.csv"
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        for result in results:
            row = {"participant_id": participant_id, "attempt": attempt, **asdict(result)}
            # Timeouts are stored as empty cells, which pandas reads as missing.
            writer.writerow({k: "" if v is None else v for k, v in row.items()})
    return path
