"""Logic of the child flanker task: trial lists, scoring and data export.

This module contains no pygame code, so the design of the task can be tested
and reused (for example in a simulation) without opening a window. The task is
modelled on the flanker part of the child Attention Network Test (Rueda et
al., 2004): a central fish is shown alone (neutral) or with four flanking fish
that swim the same way (congruent) or the opposite way (incongruent).
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
COLUMNS = (
    "participant_id",
    "attempt",
    "block",
    "trial",
    "condition",
    "target_direction",
    "response",
    "correct",
    "rt_ms",
)


@dataclass(frozen=True)
class FlankerTrial:
    """One flanker display: a condition and the direction of the middle fish."""

    condition: str
    target_direction: str

    def __post_init__(self):
        if self.condition not in CONDITIONS:
            raise ValueError(f"condition must be one of {CONDITIONS}")
        if self.target_direction not in DIRECTIONS:
            raise ValueError(f"target_direction must be one of {DIRECTIONS}")

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
    """The outcome of one trial. ``response`` and ``rt_ms`` are None on a timeout."""

    block: str
    trial: int
    condition: str
    target_direction: str
    response: str | None
    correct: bool
    rt_ms: int | None


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


def make_trials(n_repetitions, rng=None):
    """
    Create a balanced, shuffled list of flanker trials.

    Parameters
    ----------
    n_repetitions : int
        How often each of the six condition x direction cells is shown.
    rng : random.Random or None, optional
        Random number generator; pass a seeded one for reproducible orders.

    Returns
    -------
    list of FlankerTrial
        ``6 * n_repetitions`` trials in random order.
    """
    if n_repetitions < 1:
        raise ValueError("n_repetitions must be at least 1")
    rng = rng or random.Random()
    cells = [FlankerTrial(c, d) for c in CONDITIONS for d in DIRECTIONS]
    trials = cells * n_repetitions
    rng.shuffle(trials)
    return trials


def make_practice_trials(n_trials, rng=None):
    """
    Create practice trials that cover the conditions as evenly as possible.

    Parameters
    ----------
    n_trials : int
        Number of practice trials (0 or more).
    rng : random.Random or None, optional
        Random number generator; pass a seeded one for reproducible orders.

    Returns
    -------
    list of FlankerTrial
        ``n_trials`` trials in random order.
    """
    if n_trials < 0:
        raise ValueError("n_trials must not be negative")
    n_cells = len(CONDITIONS) * len(DIRECTIONS)
    n_repetitions = max(1, -(-n_trials // n_cells))
    return make_trials(n_repetitions, rng)[:n_trials]


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
