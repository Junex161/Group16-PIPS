"""Simulating a group of players from one real player's data.

One game session shows how one person performs, but a statistical analysis
needs a group. This module creates any number of simulated players who
complete the questionnaire and every trial of the flanker, stop-signal and
2-back tasks, in exactly the file format the game writes. Their data can
be analysed with the same code as real data.

Where the numbers come from
---------------------------
* **Typical values (means)** combine the real player with the literature.
  The bootstrap (``src/bootstrap.py``) gives the player's score and its
  standard error (SE). The player's score and the published mean are
  averaged with weights proportional to their precisions (1 / variance;
  Gelman et al., 2013, Section 2.5): the player's weight is
  SD_between^2 / (SD_between^2 + SE^2). A precisely measured player moves
  the simulated group towards their own score; a noisy one barely moves it
  away from the published mean. If the player did not complete a task, the
  published mean is used. Values without a published between-person SD
  (trial-to-trial noise, error rates) take the player's own estimate.
* **How much people differ (between-person SDs)** cannot be estimated from
  one player and always comes from ``LITERATURE``.
* **Values without a suitable published source** are listed in
  ``ASSUMPTIONS``; they are illustrative and should be reported as such.
* **Links between the questionnaire and performance** (for example, more
  screen time goes with a larger flanker effect) are hypothetical effects
  set in ``Effects``. Setting them to 0 simulates a world without them.

How a player is simulated
-------------------------
Every simulated player first gets their own true values, drawn from normal
distributions with the means and between-person SDs above, plus the effects
of their questionnaire answers. The trials are then generated with the
game's own trial lists:

* **Flanker:** RT = the player's baseline RT, plus their flanker effect on
  incongruent trials, plus normal trial-to-trial noise. Errors occur with
  the error rates of the real player; responses slower than the response
  window are timeouts.
* **Stop-signal:** a race between going and stopping (Logan & Cowan, 1984).
  On a stop trial the player responds if their go RT is shorter than the
  stop-signal delay plus their SSRT. The delay follows the game's
  staircase, so stopping succeeds about half of the time.
* **2-back:** signal detection theory. A player with sensitivity d' and
  criterion c presses the key on a target with probability
  Phi(d'/2 - c) and on another letter with probability Phi(-d'/2 - c)
  (Stanislaw & Todorov, 1999).
"""

import random
from dataclasses import dataclass, field
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

from .game import flanker_task, nback_task, stop_signal_task
from .game.config import DATA_DIR, FlankerSettings, NBackSettings, StopSignalSettings

SIMULATED_DIR = Path(DATA_DIR) / "simulated"


@dataclass(frozen=True)
class Value:
    """
    A population value: a ``mean``, the ``sd`` between people, and its ``source``.

    An ``sd`` of 0 means that every simulated player gets the same value.
    When the mean was combined with a real player's score, ``player_estimate``,
    ``player_se`` and ``player_weight`` record how.
    """

    mean: float
    sd: float
    source: str
    player_estimate: float | None = None
    player_se: float | None = None
    player_weight: float | None = None


# Published values; the table, group and statistic are given for each, so
# that they can be checked against the article.
LITERATURE = {
    "flanker": {
        "baseline_rt_ms": Value(485.16, 44.9, "Kaufman et al. (2016), Table 2: mean RT of young adults (N = 19)"),
        "flanker_effect_ms": Value(117.29, 22.3, "Kaufman et al. (2016), Table 2: conflict effect of young adults (N = 19)"),
    },
    "stopsignal": {
        "go_rt_ms": Value(494.06, 106.06, "Congdon et al. (2014), Table 1: mean go RT of healthy controls (N = 62)"),
        "go_rt_sd_ms": Value(111.89, 0.0, "Congdon et al. (2014), Table 1: SD of go RT of healthy controls (N = 62)"),
        "ssrt_ms": Value(186.38, 52.64, "Congdon et al. (2014), Table 1: SSRT of healthy controls (N = 62)"),
    },
    "nback": {
        "d_prime": Value(2.25, 0.94, "Forsberg et al. (2020), Table 3: letter 2-back d' of younger adults, control group at pre-test (N = 29)"),
    },
    "questionnaire": {
        # 419.1 and 123.0 minutes, converted to hours. The study asked about all
        # screen use (TV, phone, computer, tablet), including study and work,
        # while the game asks about free time only, so this likely overestimates
        # leisure screen time; it is the closest published value we found.
        "screen_time_hours": Value(419.1 / 60, 123.0 / 60, "Sedaghat et al. (2025): self-reported daily screen time on all devices, including study and work, of college students (N = 29); the game asks about free time only"),
    },
}

# Values without a published source in this project; illustrative only.
ASSUMPTIONS = {
    "flanker": {
        "trial_sd_ms": Value(111.89, 0.0, "Assumption: the trial-to-trial SD of go RTs in Congdon et al. (2014)"),
        "error_rate_congruent": Value(0.03, 0.0, "Assumption"),
        "error_rate_incongruent": Value(0.08, 0.0, "Assumption"),
    },
    "stopsignal": {
        "go_error_rate": Value(0.02, 0.0, "Assumption"),
    },
    "nback": {
        "criterion": Value(0.0, 0.0, "Assumption: no response bias"),
        "hit_rt_ms": Value(700.0, 0.0, "Assumption"),
        "hit_rt_sd_ms": Value(150.0, 0.0, "Assumption"),
    },
}

# Assumed answer distributions of the 1-5 questions (share of answers 1 to 5).
ANSWER_SHARES = {
    "short_video_frequency": (0.05, 0.10, 0.15, 0.35, 0.35),
    "psychology_interest": (0.02, 0.08, 0.25, 0.35, 0.30),
    "gaming_frequency": (0.25, 0.25, 0.15, 0.20, 0.15),
    "alertness": (0.05, 0.15, 0.35, 0.30, 0.15),
}
QUESTIONNAIRE_COLUMNS = ("participant_id", "attempt", "screen_time_hours", *ANSWER_SHARES)


@dataclass(frozen=True)
class Effects:
    """
    Hypothetical effects built into the simulated data.

    They are not taken from the literature: they describe the world the
    simulation assumes, so that an analysis can be checked against known
    effects (or, with 0, against no effect).

    Parameters
    ----------
    screen_time_on_flanker_ms : float
        Change of the flanker effect per hour of screen time above the mean.
    screen_time_on_ssrt_ms : float
        Change of the SSRT per hour of screen time above the mean.
    alertness_on_rt_ms : float
        Change of the baseline flanker RT and the go RT per point of
        alertness above the middle of the scale (3).
    close_spacing_on_flanker_ms : float
        Extra interference on incongruent trials with the smallest spacing
        compared with the largest one.
    flanker_count_on_flanker_ms : float
        Extra interference on incongruent trials per additional flanking fish.
    short_video_screen_time_correlation : float
        Correlation between screen time and short-video use (on the latent scale).
    """

    screen_time_on_flanker_ms: float = 5.0
    screen_time_on_ssrt_ms: float = 5.0
    alertness_on_rt_ms: float = -15.0
    close_spacing_on_flanker_ms: float = 20.0
    flanker_count_on_flanker_ms: float = 2.5
    short_video_screen_time_correlation: float = 0.5

    def __post_init__(self):
        if not -1 <= self.short_video_screen_time_correlation <= 1:
            raise ValueError("short_video_screen_time_correlation must lie between -1 and 1")


@dataclass
class SimulatedData:
    """
    The simulated players.

    ``questionnaire``, ``flanker``, ``stopsignal`` and ``nback`` have the
    columns of the game's data files. ``true_values`` holds every player's
    generating values, and ``parameters`` lists the population values used
    and where they came from.
    """

    questionnaire: pd.DataFrame
    flanker: pd.DataFrame
    stopsignal: pd.DataFrame
    nback: pd.DataFrame
    true_values: pd.DataFrame
    parameters: pd.DataFrame
    seed: int = field(default=None)

    def tasks(self):
        """Return ``{task: DataFrame}`` for the questionnaire and the three experiments."""
        return {"questionnaire": self.questionnaire, "flanker": self.flanker, "stopsignal": self.stopsignal, "nback": self.nback}

    def save(self, folder=SIMULATED_DIR):
        """
        Save every table as ``<name>_simulated.csv`` in ``folder``.

        Returns
        -------
        list of Path
            The written files.
        """
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        tables = {**self.tasks(), "true_values": self.true_values, "parameters": self.parameters}
        paths = []
        for name, table in tables.items():
            path = folder / f"{name}_simulated.csv"
            table.to_csv(path, index=name == "parameters")
            paths.append(path)
        return paths


def precision_weighted_mean(estimate, standard_error, population):
    """
    Combine one player's score with a published population value.

    The posterior mean of a normal model with known variances (Gelman et
    al., 2013, Section 2.5, Eq. 2.10): the population value acts as the
    prior, the player's score as one observation with the bootstrap SE as
    its sampling error. Each is weighted by its precision.

    Parameters
    ----------
    estimate : float
        The player's observed score.
    standard_error : float
        Its bootstrap standard error.
    population : Value
        The published mean and between-person SD (``sd`` must be above 0).

    Returns
    -------
    tuple of float
        ``(mean, weight)``: the combined mean and the weight of the player,
        SD^2 / (SD^2 + SE^2), between 0 and 1.
    """
    if population.sd <= 0:
        raise ValueError("the population value needs a between-person SD above 0")
    if standard_error < 0:
        raise ValueError("standard_error must not be negative")
    weight = population.sd**2 / (population.sd**2 + standard_error**2)
    return weight * estimate + (1 - weight) * population.mean, weight


def population_values(bootstrap=None, participant_id=None):
    """
    Combine the bootstrap results with the literature and the assumptions.

    Parameters
    ----------
    bootstrap : dict or None
        As returned by ``src.bootstrap.bootstrap_session``; None uses only
        published values and assumptions.
    participant_id : str or None
        The real player, only used to describe the source.

    Returns
    -------
    dict
        ``{task: {measure: Value}}``. Measures with a published
        between-person SD get the precision-weighted mean of the player's
        score and the published mean (``precision_weighted_mean``); the other
        measures (trial-to-trial noise, error rates) get the player's own
        estimate. Measures the player has no score for keep the published
        value or the assumption. The between-person SD always comes from the
        literature (or the assumption).
    """
    bootstrap = bootstrap or {}
    player = participant_id or "the player"
    values = {}
    for task in ("flanker", "stopsignal", "nback", "questionnaire"):
        defaults = {**ASSUMPTIONS.get(task, {}), **LITERATURE.get(task, {})}
        values[task] = {}
        for measure, default in defaults.items():
            result = bootstrap.get(task, {}).get(measure)
            if result is None or not np.isfinite(result.estimate):
                values[task][measure] = default
                continue
            estimate, se = result.estimate, result.sd
            if default.sd > 0 and np.isfinite(se):
                mean, weight = precision_weighted_mean(estimate, se, default)
                source = f"mean: precision-weighted average of {player} and {default.source}; SD: {default.source}"
            else:
                mean, weight = estimate, 1.0
                source = f"mean: estimate of {player}; SD: {default.source}"
            values[task][measure] = Value(mean, default.sd, source, estimate, se, weight)
    return values


def parameter_table(values):
    """Return the population values as a table with one row per measure."""
    rows = [
        {
            "task": task,
            "measure": measure,
            "mean": value.mean,
            "between_person_sd": value.sd,
            "player_estimate": value.player_estimate,
            "player_se": value.player_se,
            "player_weight": value.player_weight,
            "source": value.source,
        }
        for task, measures in values.items()
        for measure, value in measures.items()
    ]
    return pd.DataFrame(rows).set_index(["task", "measure"])


def _likert(latent, shares):
    """Turn standard normal scores into answers 1-5 with the given answer shares."""
    cut_points = [NormalDist().inv_cdf(share) for share in np.cumsum(shares)[:-1]]
    return np.searchsorted(cut_points, latent) + 1


def simulate_questionnaire(participant_ids, values, effects, rng):
    """Simulate one questionnaire per player (see ``ANSWER_SHARES`` and ``Effects``)."""
    n = len(participant_ids)
    screen = values["questionnaire"]["screen_time_hours"]
    screen_z = rng.standard_normal(n)
    hours = np.clip(np.round((screen.mean + screen.sd * screen_z) * 2) / 2, 0, 16)
    rho = effects.short_video_screen_time_correlation
    answers = {"participant_id": participant_ids, "attempt": 1, "screen_time_hours": hours}
    for column, shares in ANSWER_SHARES.items():
        latent = rng.standard_normal(n)
        if column == "short_video_frequency":
            latent = rho * screen_z + np.sqrt(1 - rho**2) * latent
        answers[column] = _likert(latent, shares)
    return pd.DataFrame(answers, columns=QUESTIONNAIRE_COLUMNS)


def _draw(value, rng):
    return rng.normal(value.mean, value.sd) if value.sd > 0 else value.mean


def _rt(mean, sd, rng, minimum=150):
    return max(minimum, rng.normal(mean, sd))


def simulate_flanker(participant_id, truth, values, effects, settings, rng, trial_rng):
    """Simulate the flanker test block of one player; returns rows in ``flanker_task.COLUMNS`` order."""
    flanker = values["flanker"]
    trials = flanker_task.make_trials(settings.n_test_repetitions, trial_rng, settings.spacings, settings.flanker_counts)
    smallest, largest = min(settings.spacings), max(settings.spacings)
    mean_count = np.mean(settings.flanker_counts)
    deadline = settings.response_deadline * 1000
    rows = []
    for number, trial in enumerate(trials, start=1):
        interference = 0.0
        if trial.condition == "incongruent":
            # Centred, so that the mean interference equals the player's flanker effect.
            closeness = (largest - trial.spacing) / (largest - smallest) - 0.5 if largest > smallest else 0.0
            interference = (
                truth["flanker_effect_ms"]
                + effects.close_spacing_on_flanker_ms * closeness
                + effects.flanker_count_on_flanker_ms * (trial.nr_flankers - mean_count)
            )
        rt = _rt(truth["baseline_rt_ms"] + interference, flanker["trial_sd_ms"].mean, rng)
        error_rate = flanker["error_rate_incongruent" if trial.condition == "incongruent" else "error_rate_congruent"].mean
        correct = rng.random() >= error_rate
        response = trial.target_direction if correct else ("left" if trial.target_direction == "right" else "right")
        if rt > deadline:
            response, correct, rt = None, False, None
        rows.append((participant_id, 1, "test", number, trial.condition, trial.target_direction, trial.spacing, trial.nr_flankers, response, correct, None if rt is None else round(rt)))
    return rows


def simulate_stop_signal(participant_id, truth, values, settings, rng, trial_rng):
    """Simulate the stop-signal test block of one player as a horse race; rows in ``stop_signal_task.COLUMNS`` order."""
    stop = values["stopsignal"]
    trials = stop_signal_task.make_trials(settings.n_test_trials, settings.stop_share, trial_rng)
    staircase = stop_signal_task.Staircase(settings.ssd_start, settings.ssd_step, settings.ssd_min, settings.ssd_max)
    deadline = settings.response_deadline * 1000
    rows = []
    for number, trial in enumerate(trials, start=1):
        go_time = _rt(truth["go_rt_ms"], stop["go_rt_sd_ms"].mean, rng, minimum=100)
        choice_error = rng.random() < stop["go_error_rate"].mean
        key = ("left" if trial.direction == "right" else "right") if choice_error else trial.direction
        ssd = staircase.value if trial.trial_type == "stop" else None
        if trial.trial_type == "go":
            responded = go_time <= deadline
            correct = responded and not choice_error
        else:
            # The go process wins the race if it finishes before the stop process.
            responded = go_time <= deadline and go_time < ssd * 1000 + truth["ssrt_ms"]
            correct = not responded
            staircase.update(stopped=correct)
        rows.append((
            participant_id, 1, "test", number, trial.trial_type, trial.direction,
            None if ssd is None else round(ssd * 1000),
            key if responded else None, correct, round(go_time) if responded else None,
        ))
    return rows


def simulate_nback(participant_id, truth, values, settings, rng, trial_rng):
    """Simulate the n-back test block of one player with signal detection theory; rows in ``nback_task.COLUMNS`` order."""
    nback = values["nback"]
    sequence = nback_task.make_sequence(settings.n, settings.n_test_trials, settings.n_test_targets, settings.letters, trial_rng)
    normal = NormalDist()
    p_hit = normal.cdf(truth["d_prime"] / 2 - truth["criterion"])
    p_false_alarm = normal.cdf(-truth["d_prime"] / 2 - truth["criterion"])
    longest = (settings.stimulus_time + settings.blank_time) * 1000 - 1
    rows = []
    for number, (letter, is_target) in enumerate(sequence, start=1):
        responded = rng.random() < (p_hit if is_target else p_false_alarm)
        rt = round(min(longest, _rt(nback["hit_rt_ms"].mean, nback["hit_rt_sd_ms"].mean, rng))) if responded else None
        rows.append((participant_id, 1, "test", settings.n, number, letter, is_target, responded, responded == is_target, rt))
    return rows


def simulate_participants(
    n=50,
    bootstrap=None,
    participant_id=None,
    seed=2026,
    effects=Effects(),
    flanker_settings=FlankerSettings(),
    stop_signal_settings=StopSignalSettings(),
    nback_settings=NBackSettings(),
):
    """
    Simulate a group of players.

    Parameters
    ----------
    n : int, optional
        Number of simulated players.
    bootstrap : dict or None, optional
        Bootstrap results of a real player (``src.bootstrap.bootstrap_session``);
        each score is combined with the published mean by precision
        (``precision_weighted_mean``). None uses published values only.
    participant_id : str or None, optional
        The real player, used to describe the sources.
    seed : int, optional
        Seed for reproducible data: the same inputs and seed give the same players.
    effects : Effects, optional
        Hypothetical effects of the questionnaire answers and the flanker layout.
    flanker_settings, stop_signal_settings, nback_settings : optional
        Designs of the tasks, as in the game (``src/game/config.py``). Raise
        the number of trials here to simulate longer tasks.

    Returns
    -------
    SimulatedData
        Questionnaire and trial data in the game's format, the true values
        of every player and the population values used.
    """
    if n < 1:
        raise ValueError("n must be at least 1")
    rng = np.random.default_rng(seed)
    values = population_values(bootstrap, participant_id)
    ids = [f"sim-{number:03d}" for number in range(1, n + 1)]
    questionnaire = simulate_questionnaire(ids, values, effects, rng)
    screen_mean = values["questionnaire"]["screen_time_hours"].mean

    rows = {"flanker": [], "stopsignal": [], "nback": []}
    truths = []
    for answers in questionnaire.itertuples(index=False):
        screen_offset = answers.screen_time_hours - screen_mean
        alertness_shift = effects.alertness_on_rt_ms * (answers.alertness - 3)
        truth = {
            "participant_id": answers.participant_id,
            "baseline_rt_ms": _draw(values["flanker"]["baseline_rt_ms"], rng) + alertness_shift,
            "flanker_effect_ms": _draw(values["flanker"]["flanker_effect_ms"], rng) + effects.screen_time_on_flanker_ms * screen_offset,
            "go_rt_ms": _draw(values["stopsignal"]["go_rt_ms"], rng) + alertness_shift,
            "ssrt_ms": max(50.0, _draw(values["stopsignal"]["ssrt_ms"], rng) + effects.screen_time_on_ssrt_ms * screen_offset),
            "d_prime": _draw(values["nback"]["d_prime"], rng),
            "criterion": _draw(values["nback"]["criterion"], rng),
        }
        truths.append(truth)
        trial_rng = random.Random(int(rng.integers(2**32)))
        rows["flanker"] += simulate_flanker(answers.participant_id, truth, values, effects, flanker_settings, rng, trial_rng)
        rows["stopsignal"] += simulate_stop_signal(answers.participant_id, truth, values, stop_signal_settings, rng, trial_rng)
        rows["nback"] += simulate_nback(answers.participant_id, truth, values, nback_settings, rng, trial_rng)

    columns = {"flanker": flanker_task.COLUMNS, "stopsignal": stop_signal_task.COLUMNS, "nback": nback_task.COLUMNS}
    tables = {task: pd.DataFrame(task_rows, columns=columns[task]) for task, task_rows in rows.items()}
    for table in tables.values():
        # Integer columns with empty cells, as in the game's CSV files.
        for column in ("spacing", "ssd_ms", "rt_ms"):
            if column in table:
                table[column] = table[column].astype("Int64")
    return SimulatedData(
        questionnaire=questionnaire,
        flanker=tables["flanker"],
        stopsignal=tables["stopsignal"],
        nback=tables["nback"],
        true_values=pd.DataFrame(truths),
        parameters=parameter_table(values),
        seed=seed,
    )
