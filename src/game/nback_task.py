"""Logic of the n-back task: letter sequences, scoring and sensitivity.

Letters appear one at a time. The player presses a key whenever the letter
is the same as the one ``n`` steps back (a target) and does nothing
otherwise (Kirchner, 1958). Keeping the last ``n`` letters in mind and
updating them with every new letter is a classic measure of working-memory
updating (Owen et al., 2005).

This module contains no pygame code.
"""

import random
from dataclasses import dataclass
from statistics import NormalDist, mean

COLUMNS = (
    "participant_id",
    "attempt",
    "block",
    "n",
    "trial",
    "letter",
    "is_target",
    "responded",
    "correct",
    "rt_ms",
)


@dataclass(frozen=True)
class NBackResult:
    """The outcome of one letter; ``rt_ms`` is None if no key was pressed."""

    block: str
    n: int
    trial: int
    letter: str
    is_target: bool
    responded: bool
    correct: bool
    rt_ms: int | None


@dataclass(frozen=True)
class NBackSummary:
    """
    Performance in one block.

    ``accuracy`` counts hits and correct rejections. ``d_prime`` is the
    signal-detection sensitivity: how well targets are told apart from the
    other letters, independent of how often the player presses the key.
    """

    n_trials: int
    hits: int
    misses: int
    false_alarms: int
    correct_rejections: int
    accuracy: float
    hit_rate: float
    false_alarm_rate: float
    d_prime: float
    mean_hit_rt_ms: float | None


def make_sequence(n, n_trials, n_targets, letters, rng=None):
    """
    Create a letter sequence with an exact number of n-back targets.

    Parameters
    ----------
    n : int
        How many steps back a target repeats a letter.
    n_trials : int
        Length of the sequence.
    n_targets : int
        Number of targets; they can only occur after the first ``n`` letters.
    letters : str
        The letters to choose from.
    rng : random.Random or None, optional
        Random number generator; pass a seeded one for reproducible orders.

    Returns
    -------
    list of tuple
        ``(letter, is_target)`` for every trial. Letters that are not targets
        never repeat the letter ``n`` steps back.
    """
    if not 0 <= n_targets <= n_trials - n:
        raise ValueError("n_targets must fit after the first n letters")
    rng = rng or random.Random()
    target_positions = set(rng.sample(range(n, n_trials), n_targets))
    sequence = []
    for index in range(n_trials):
        if index in target_positions:
            sequence.append(sequence[index - n])
            continue
        # Avoid accidental targets and immediate repeats.
        forbidden = {sequence[index - n]} if index >= n else set()
        if index >= 1:
            forbidden.add(sequence[index - 1])
        sequence.append(rng.choice([letter for letter in letters if letter not in forbidden]))
    return [(letter, index in target_positions) for index, letter in enumerate(sequence)]


def d_prime(hits, misses, false_alarms, correct_rejections):
    """
    Sensitivity d' with the log-linear correction (Hautus, 1995).

    Adding 0.5 to every count keeps the rates away from 0 and 1, so d'
    stays finite even for perfect performance.
    """
    hit_rate = (hits + 0.5) / (hits + misses + 1)
    false_alarm_rate = (false_alarms + 0.5) / (false_alarms + correct_rejections + 1)
    normal = NormalDist()
    return normal.inv_cdf(hit_rate) - normal.inv_cdf(false_alarm_rate)


def summarise(results):
    """
    Summarise one block of n-back trials.

    Parameters
    ----------
    results : list of NBackResult
        Trials of one block.

    Returns
    -------
    NBackSummary
        Hits, false alarms, accuracy, d' and the mean reaction time of hits.
    """
    hits = sum(r.is_target and r.responded for r in results)
    misses = sum(r.is_target and not r.responded for r in results)
    false_alarms = sum(not r.is_target and r.responded for r in results)
    correct_rejections = sum(not r.is_target and not r.responded for r in results)
    hit_rts = [r.rt_ms for r in results if r.is_target and r.responded]
    n_targets, n_others = hits + misses, false_alarms + correct_rejections
    return NBackSummary(
        n_trials=len(results),
        hits=hits,
        misses=misses,
        false_alarms=false_alarms,
        correct_rejections=correct_rejections,
        accuracy=(hits + correct_rejections) / len(results) if results else 0.0,
        hit_rate=hits / n_targets if n_targets else 0.0,
        false_alarm_rate=false_alarms / n_others if n_others else 0.0,
        d_prime=d_prime(hits, misses, false_alarms, correct_rejections),
        mean_hit_rt_ms=mean(hit_rts) if hit_rts else None,
    )


def has_passed(summary, pass_accuracy, min_hit_rate=0.5):
    """
    Return True if the accuracy reaches ``pass_accuracy`` and enough targets were caught.

    The hit rate is checked as well because a player who never presses the
    key is right on every non-target and would otherwise pass by doing nothing.
    """
    return summary.n_trials > 0 and summary.hit_rate >= min_hit_rate and summary.accuracy >= pass_accuracy
