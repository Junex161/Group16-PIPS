"""Bootstrapping the experiment data of one player.

A single game session gives one estimate per measure, for example a flanker
effect of 70 ms. The bootstrap (Efron, 1979) shows how precise that
estimate is: the player's trials are drawn again with replacement, the
measure is recomputed, and this is repeated many times. The spread of the
recomputed values (the bootstrap distribution) gives a standard error and
a 95% percentile confidence interval.

Trials are resampled within their condition (congruent / incongruent /
neutral, go / stop, target / non-target), so every bootstrap sample keeps
the design of the task. The SSRT and d' are computed with the same
functions the game uses (``src/game/stop_signal_task.py`` and
``src/game/nback_task.py``).

The bootstrap describes the uncertainty about *this* player's scores. It
says nothing about how much different people differ from each other; the
simulation (``src/simulation.py``) takes that from the literature.
"""

from dataclasses import dataclass
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

from .game.config import DATA_DIR, StopSignalSettings
from .game.nback_task import d_prime
from .game.stop_signal_task import ssrt_integration

# The measures that are bootstrapped for each task, with a short description.
MEASURES = {
    "flanker": {
        "baseline_rt_ms": "mean correct RT on congruent trials",
        "flanker_effect_ms": "incongruent minus congruent mean correct RT",
        "trial_sd_ms": "SD of correct RTs within a condition (trial-to-trial noise)",
        "error_rate_congruent": "share of errors on congruent and neutral trials",
        "error_rate_incongruent": "share of errors on incongruent trials",
    },
    "stopsignal": {
        "go_rt_ms": "mean correct go RT",
        "go_rt_sd_ms": "SD of correct go RTs (trial-to-trial noise)",
        "go_error_rate": "share of go trials with the wrong key",
        "ssrt_ms": "stop-signal reaction time (integration method)",
    },
    "nback": {
        "d_prime": "sensitivity d' (log-linear correction)",
        "criterion": "response criterion c (positive = cautious)",
        "hit_rt_ms": "mean RT of hits",
        "hit_rt_sd_ms": "SD of hit RTs (trial-to-trial noise)",
    },
}
# Column that defines the conditions trials are resampled within.
STRATA = {"flanker": "condition", "stopsignal": "trial_type", "nback": "is_target"}


@dataclass(frozen=True)
class BootstrapResult:
    """
    The bootstrap distribution of one measure.

    ``estimate`` is the value in the observed trials, ``samples`` the values
    in the bootstrap samples (NaN where a sample did not allow the measure,
    for example without any correct congruent trial).
    """

    task: str
    measure: str
    estimate: float
    samples: np.ndarray

    @property
    def mean(self):
        """Mean of the bootstrap distribution."""
        return float(np.nanmean(self.samples))

    @property
    def sd(self):
        """SD of the bootstrap distribution, i.e. the standard error of the estimate."""
        return float(np.nanstd(self.samples, ddof=1))

    def ci(self, level=0.95):
        """Percentile confidence interval as ``(lower, upper)``."""
        tail = (1 - level) / 2 * 100
        lower, upper = np.nanpercentile(self.samples, [tail, 100 - tail])
        return float(lower), float(upper)


def _mean(values):
    return float(np.mean(values)) if len(values) else np.nan


def _sd(values):
    return float(np.std(values, ddof=1)) if len(values) > 1 else np.nan


def flanker_measures(trials):
    """
    Compute the flanker measures of one set of test trials.

    Parameters
    ----------
    trials : pandas.DataFrame
        Columns ``condition``, ``correct`` and ``rt_ms`` as written by the game.

    Returns
    -------
    dict
        One value per measure in ``MEASURES["flanker"]``.
    """
    correct = trials[trials["correct"]]
    rts = {condition: correct.loc[correct["condition"] == condition, "rt_ms"].to_numpy(float) for condition in ("congruent", "incongruent", "neutral")}
    # Pooled within-condition SD: the trial-to-trial noise without the condition differences.
    groups = [values for values in rts.values() if len(values) > 1]
    pooled = np.sqrt(sum((len(v) - 1) * np.var(v, ddof=1) for v in groups) / sum(len(v) - 1 for v in groups)) if groups else np.nan
    incongruent = trials["condition"] == "incongruent"
    return {
        "baseline_rt_ms": _mean(rts["congruent"]),
        "flanker_effect_ms": _mean(rts["incongruent"]) - _mean(rts["congruent"]),
        "trial_sd_ms": float(pooled),
        "error_rate_congruent": float(1 - trials.loc[~incongruent, "correct"].mean()) if (~incongruent).any() else np.nan,
        "error_rate_incongruent": float(1 - trials.loc[incongruent, "correct"].mean()) if incongruent.any() else np.nan,
    }


def stop_signal_measures(trials, response_deadline_ms=StopSignalSettings().response_deadline * 1000):
    """
    Compute the stop-signal measures of one set of test trials.

    The SSRT follows ``stop_signal_task.summarise``: choice errors count as
    responses and missed go trials get the longest go RT (Verbruggen et
    al., 2019).

    Parameters
    ----------
    trials : pandas.DataFrame
        Columns ``trial_type``, ``ssd_ms``, ``response``, ``correct`` and ``rt_ms``.
    response_deadline_ms : float, optional
        Used for missed go trials when no go trial had a response.

    Returns
    -------
    dict
        One value per measure in ``MEASURES["stopsignal"]``.
    """
    go = trials[trials["trial_type"] == "go"]
    stop = trials[trials["trial_type"] == "stop"]
    correct_rts = go.loc[go["correct"], "rt_ms"].to_numpy(float)
    responded = go["rt_ms"].notna()
    longest = go.loc[responded, "rt_ms"].max() if responded.any() else response_deadline_ms
    ssrt = np.nan
    if len(go) and len(stop):
        all_go_rts = go["rt_ms"].fillna(longest).tolist()
        ssrt = ssrt_integration(all_go_rts, 1 - stop["correct"].mean(), stop["ssd_ms"].mean())
    return {
        "go_rt_ms": _mean(correct_rts),
        "go_rt_sd_ms": _sd(correct_rts),
        "go_error_rate": float((responded & ~go["correct"]).mean()) if len(go) else np.nan,
        "ssrt_ms": float(ssrt),
    }


def criterion(hits, misses, false_alarms, correct_rejections):
    """
    Response criterion c with the same log-linear correction as ``d_prime``.

    c = -(z(hit rate) + z(false-alarm rate)) / 2 (Stanislaw & Todorov, 1999);
    positive values mean the player rarely presses the key.
    """
    hit_rate = (hits + 0.5) / (hits + misses + 1)
    false_alarm_rate = (false_alarms + 0.5) / (false_alarms + correct_rejections + 1)
    normal = NormalDist()
    return -(normal.inv_cdf(hit_rate) + normal.inv_cdf(false_alarm_rate)) / 2


def nback_measures(trials):
    """
    Compute the n-back measures of one set of test trials.

    Parameters
    ----------
    trials : pandas.DataFrame
        Columns ``is_target``, ``responded`` and ``rt_ms``.

    Returns
    -------
    dict
        One value per measure in ``MEASURES["nback"]``.
    """
    target, responded = trials["is_target"].astype(bool), trials["responded"].astype(bool)
    counts = ((target & responded).sum(), (target & ~responded).sum(), (~target & responded).sum(), (~target & ~responded).sum())
    hit_rts = trials.loc[target & responded, "rt_ms"].to_numpy(float)
    return {
        "d_prime": d_prime(*counts),
        "criterion": criterion(*counts),
        "hit_rt_ms": _mean(hit_rts),
        "hit_rt_sd_ms": _sd(hit_rts),
    }


MEASURE_FUNCTIONS = {"flanker": flanker_measures, "stopsignal": stop_signal_measures, "nback": nback_measures}


def bootstrap_task(task, trials, n_resamples=5000, seed=2026):
    """
    Bootstrap every measure of one task.

    Parameters
    ----------
    task : str
        ``"flanker"``, ``"stopsignal"`` or ``"nback"``.
    trials : pandas.DataFrame
        The test trials of one player, as written by the game.
    n_resamples : int, optional
        Number of bootstrap samples.
    seed : int, optional
        Seed of the random number generator, for reproducible results.

    Returns
    -------
    dict
        ``{measure: BootstrapResult}``.
    """
    if task not in MEASURE_FUNCTIONS:
        raise ValueError(f"task must be one of {tuple(MEASURE_FUNCTIONS)}, not {task!r}")
    if trials.empty:
        raise ValueError(f"there are no {task} trials to bootstrap")
    if n_resamples < 2:
        raise ValueError("n_resamples must be at least 2")
    compute = MEASURE_FUNCTIONS[task]
    rng = np.random.default_rng(seed)
    trials = trials.reset_index(drop=True)
    strata = [group.index.to_numpy() for _, group in trials.groupby(STRATA[task])]
    observed = compute(trials)
    samples = {measure: np.empty(n_resamples) for measure in observed}
    for index in range(n_resamples):
        rows = np.concatenate([rng.choice(stratum, size=len(stratum), replace=True) for stratum in strata])
        for measure, value in compute(trials.loc[rows]).items():
            samples[measure][index] = value
    return {measure: BootstrapResult(task, measure, observed[measure], samples[measure]) for measure in observed}


def bootstrap_session(session, n_resamples=5000, seed=2026):
    """
    Bootstrap every experiment of one game session.

    Parameters
    ----------
    session : dict
        As returned by ``src.data.load_session``.
    n_resamples : int, optional
        Number of bootstrap samples per task.
    seed : int, optional
        Seed of the random number generator.

    Returns
    -------
    dict
        ``{task: {measure: BootstrapResult}}`` for the flanker, stop-signal
        and n-back tasks the player completed.
    """
    return {
        task: bootstrap_task(task, session[task], n_resamples, seed)
        for task in MEASURE_FUNCTIONS
        if task in session and not session[task].empty
    }


def summary_table(results, level=0.95):
    """
    Summarise bootstrap results as a table.

    Returns
    -------
    pandas.DataFrame
        One row per task and measure: the observed estimate, the mean and SD
        (standard error) of the bootstrap distribution and the confidence
        interval.
    """
    rows = []
    for task, measures in results.items():
        for result in measures.values():
            lower, upper = result.ci(level)
            rows.append({
                "task": task,
                "measure": result.measure,
                "estimate": result.estimate,
                "bootstrap_mean": result.mean,
                "standard_error": result.sd,
                "ci_lower": lower,
                "ci_upper": upper,
            })
    return pd.DataFrame(rows).set_index(["task", "measure"])



def save_bootstrap(results, participant_id=None, folder=Path(DATA_DIR) / "simulated"):
    """
    Save the bootstrap results of one player.

    Two files are written: ``bootstrap_summary.csv`` with one row per
    measure (see ``summary_table``) and ``bootstrap_samples.csv`` with every
    bootstrap value (columns ``task``, ``measure``, ``sample`` and ``value``).

    Parameters
    ----------
    results : dict
        As returned by ``bootstrap_session``.
    participant_id : str or None, optional
        The player, added as a column to both files.
    folder : str or Path, optional
        Where to save the files; it is created if needed.

    Returns
    -------
    list of Path
        The written files; empty if there were no results.
    """
    if not results:
        return []
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    summary = summary_table(results).reset_index()
    samples = pd.DataFrame([
        {"task": result.task, "measure": result.measure, "sample": index, "value": value}
        for measures in results.values()
        for result in measures.values()
        for index, value in enumerate(result.samples, start=1)
    ])
    paths = [folder / "bootstrap_summary.csv", folder / "bootstrap_samples.csv"]
    for table, path in zip((summary, samples), paths):
        table.insert(0, "participant_id", participant_id)
        table.to_csv(path, index=False)
    return paths
