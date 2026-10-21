"""
Statistical analysis and task-specific debrief card generation for Mind Quest.

This module provides dedicated post-task performance evaluations and plots for:
1. Level 1: Child's Flanker Task (Attention, visual crowding, and flanker interference).
2. Level 2: Stop-Signal Task (Response inhibition, staircase SSD, and SSRT).
3. Level 3: Letter 2-Back Task (Working memory, signal detection theory d' and criterion).
4. Full Study Questionnaire Regression (Individual differences across all 5 survey items).
"""

from typing import Dict, Tuple
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf

from .bootstrap import flanker_measures, nback_measures, stop_signal_measures

# Published literature normative values (Kaufman et al., 2016; Congdon et al., 2014; Forsberg et al., 2020)
LIT_NORMS = {
    "flanker_effect_ms": {"mean": 117.29, "sd": 22.30, "label": "Flanker Cost (ms)"},
    "ssrt_ms": {"mean": 186.38, "sd": 52.64, "label": "SSRT (ms)"},
    "d_prime": {"mean": 2.25, "sd": 0.94, "label": "2-Back Sensitivity (d')"},
}


# -------------------------------------------------------------------------
# 1. Level 1: Flanker Task Analysis & Debrief Plot
# -------------------------------------------------------------------------

def analyze_and_plot_flanker(
        participant_id: str,
        simulated_data,
        output_dir: str = "data/simulated",
        figsize: Tuple[int, int] = (12, 4.5),
) -> plt.Figure:
    """
    Generate an empirical analysis and two-panel figure for the Flanker task.
    Panel A: Mean RT by Condition and Spacing (visual crowding).
    Panel B: Participant score compared against the literature population norm.
    """
    flanker_df = simulated_data.flanker
    quest_df = simulated_data.questionnaire

    p_trials = flanker_df[flanker_df["participant_id"] == participant_id]
    p_quest = quest_df[quest_df["participant_id"] == participant_id].iloc[0]

    meas = flanker_measures(p_trials)
    cost = meas["flanker_effect_ms"]
    base_rt = meas["baseline_rt_ms"]
    acc = (1.0 - meas["error_rate_incongruent"]) * 100

    sns.set_theme(style="ticks", font_scale=0.95)
    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Panel A: Spacing x Condition RTs
    ax1 = axes[0]
    correct_trials = p_trials[p_trials["correct"] == True]
    cell_means = correct_trials.groupby(["condition", "spacing"])["rt_ms"].mean().reset_index()

    sns.barplot(
        data=cell_means,
        x="condition",
        y="rt_ms",
        hue="spacing",
        palette={"35": "#e74c3c", "85": "#3498db"},
        ax=ax1,
    )
    ax1.set_title(f"A. Reaction Times by Crowding (Subject: {participant_id})", weight="bold")
    ax1.set_xlabel("Condition")
    ax1.set_ylabel("Reaction Time (ms)")
    ax1.legend(title="Spacing (px)")

    # Panel B: Normative Distribution Placement
    ax2 = axes[1]
    norm = LIT_NORMS["flanker_effect_ms"]
    x = np.linspace(norm["mean"] - 3.5 * norm["sd"], norm["mean"] + 3.5 * norm["sd"], 200)
    density = (1 / (norm["sd"] * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - norm["mean"]) / norm["sd"]) ** 2)

    ax2.plot(x, density, color="#333333", linestyle="--", label=f"Literature Norm (μ={norm['mean']:.1f})")
    ax2.axvline(cost, color="#e74c3c", linewidth=2.5, label=f"Player Cost: {cost:.1f} ms")
    ax2.set_title("B. Population Context (Kaufman et al., 2016)", weight="bold")
    ax2.set_xlabel("Flanker Interference Cost (ms)")
    ax2.set_ylabel("Density")
    ax2.legend(loc="upper right")

    # Add Questionnaire Context Box
    fig.text(
        0.5, -0.05,
        f"Screen Time: {p_quest['screen_time_hours']} hrs/day | Alertness: {p_quest['alertness']}/5 | "
        f"Baseline RT: {base_rt:.1f} ms | Incongruent Accuracy: {acc:.1f}%",
        ha="center", fontsize=10, bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8f9fa", edgecolor="#ddd")
    )

    sns.despine(fig=fig)
    plt.tight_layout()

    out_path = Path(output_dir) / f"{participant_id}_flanker_debrief.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    return fig


# -------------------------------------------------------------------------
# 2. Level 2: Stop-Signal Task Analysis & Debrief Plot
# -------------------------------------------------------------------------

def analyze_and_plot_stopsignal(
        participant_id: str,
        simulated_data,
        output_dir: str = "data/simulated",
        figsize: Tuple[int, int] = (12, 4.5),
) -> plt.Figure:
    """
    Generate an empirical analysis and two-panel figure for the Stop-Signal task.
    Panel A: Staircase SSD tracking across trials.
    Panel B: Participant SSRT compared against the literature population norm.
    """
    stop_df = simulated_data.stopsignal
    quest_df = simulated_data.questionnaire

    p_trials = stop_df[stop_df["participant_id"] == participant_id]
    p_quest = quest_df[quest_df["participant_id"] == participant_id].iloc[0]

    meas = stop_signal_measures(p_trials)
    ssrt = meas["ssrt_ms"]
    go_rt = meas["go_rt_ms"]

    sns.set_theme(style="ticks", font_scale=0.95)
    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Panel A: Staircase SSD tracking
    ax1 = axes[0]
    stop_trials = p_trials[p_trials["trial_type"] == "stop"].copy().reset_index()
    ax1.plot(stop_trials.index + 1, stop_trials["ssd_ms"], marker="o", color="#8e44ad", linewidth=1.8)
    ax1.set_title("A. Stop-Signal Delay (SSD) Tracking Staircase", weight="bold")
    ax1.set_xlabel("Stop Trial Number")
    ax1.set_ylabel("SSD (ms)")

    # Panel B: Normative Distribution Placement
    ax2 = axes[1]
    norm = LIT_NORMS["ssrt_ms"]
    x = np.linspace(norm["mean"] - 3.5 * norm["sd"], norm["mean"] + 3.5 * norm["sd"], 200)
    density = (1 / (norm["sd"] * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - norm["mean"]) / norm["sd"]) ** 2)

    ax2.plot(x, density, color="#333333", linestyle="--", label=f"Literature Norm (μ={norm['mean']:.1f})")
    ax2.axvline(ssrt, color="#8e44ad", linewidth=2.5, label=f"Player SSRT: {ssrt:.1f} ms")
    ax2.set_title("B. Population Context (Congdon et al., 2014)", weight="bold")
    ax2.set_xlabel("Stop-Signal Reaction Time (ms)")
    ax2.set_ylabel("Density")
    ax2.legend(loc="upper right")

    fig.text(
        0.5, -0.05,
        f"Screen Time: {p_quest['screen_time_hours']} hrs/day | Gaming Freq: {p_quest['gaming_frequency']}/5 | "
        f"Mean Go RT: {go_rt:.1f} ms | SSRT (Inhibition Speed): {ssrt:.1f} ms",
        ha="center", fontsize=10, bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8f9fa", edgecolor="#ddd")
    )

    sns.despine(fig=fig)
    plt.tight_layout()

    out_path = Path(output_dir) / f"{participant_id}_stopsignal_debrief.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    return fig


# -------------------------------------------------------------------------
# 3. Level 3: 2-Back Working Memory Analysis & Debrief Plot
# -------------------------------------------------------------------------

def analyze_and_plot_nback(
        participant_id: str,
        simulated_data,
        output_dir: str = "data/simulated",
        figsize: Tuple[int, int] = (12, 4.5),
) -> plt.Figure:
    """
    Generate an empirical analysis and two-panel figure for the 2-Back task.
    Panel A: Response rates (Hits vs False Alarms).
    Panel B: Participant sensitivity (d') compared against the literature norm.
    """
    nback_df = simulated_data.nback
    quest_df = simulated_data.questionnaire

    p_trials = nback_df[nback_df["participant_id"] == participant_id]
    p_quest = quest_df[quest_df["participant_id"] == participant_id].iloc[0]

    meas = nback_measures(p_trials)
    d_pr = meas["d_prime"]
    crit = meas["criterion"]

    sns.set_theme(style="ticks", font_scale=0.95)
    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Panel A: Hits vs False Alarms
    ax1 = axes[0]
    targets = p_trials[p_trials["is_target"] == True]
    non_targets = p_trials[p_trials["is_target"] == False]
    hit_rate = targets["responded"].mean()
    fa_rate = non_targets["responded"].mean()

    ax1.bar(["Hit Rate (Targets)", "False Alarm Rate (Non-Targets)"], [hit_rate, fa_rate], color=["#27ae60", "#c0392b"],
            width=0.5)
    ax1.set_ylim(0, 1.05)
    ax1.set_title("A. Signal Detection Response Rates", weight="bold")
    ax1.set_ylabel("Proportion of Trials")

    # Panel B: Normative Sensitivity Placement
    ax2 = axes[1]
    norm = LIT_NORMS["d_prime"]
    x = np.linspace(max(0, norm["mean"] - 3.5 * norm["sd"]), norm["mean"] + 3.5 * norm["sd"], 200)
    density = (1 / (norm["sd"] * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - norm["mean"]) / norm["sd"]) ** 2)

    ax2.plot(x, density, color="#333333", linestyle="--", label=f"Literature Norm (μ={norm['mean']:.2f})")
    ax2.axvline(d_pr, color="#27ae60", linewidth=2.5, label=f"Player d': {d_pr:.2f}")
    ax2.set_title("B. Population Context (Forsberg et al., 2020)", weight="bold")
    ax2.set_xlabel("Working Memory Sensitivity (d')")
    ax2.set_ylabel("Density")
    ax2.legend(loc="upper right")

    fig.text(
        0.5, -0.05,
        f"Screen Time: {p_quest['screen_time_hours']} hrs/day | Alertness: {p_quest['alertness']}/5 | "
        f"Sensitivity (d'): {d_pr:.2f} | Response Criterion (c): {crit:.2f}",
        ha="center", fontsize=10, bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8f9fa", edgecolor="#ddd")
    )

    sns.despine(fig=fig)
    plt.tight_layout()

    out_path = Path(output_dir) / f"{participant_id}_nback_debrief.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    return fig


# -------------------------------------------------------------------------
# 4. Cohort Questionnaire Regression Model
# -------------------------------------------------------------------------

def aggregate_full_study_data(simulated_data) -> pd.DataFrame:
    """Aggregate all 50 participants across all tasks merged with survey variables."""
    records = []
    pids = simulated_data.questionnaire["participant_id"].unique()

    flanker_grp = simulated_data.flanker.groupby("participant_id")
    stop_grp = simulated_data.stopsignal.groupby("participant_id")
    nback_grp = simulated_data.nback.groupby("participant_id")

    for pid in pids:
        row = {"participant_id": pid}
        if pid in flanker_grp.groups:
            row["flanker_effect_ms"] = flanker_measures(flanker_grp.get_group(pid))["flanker_effect_ms"]
        if pid in stop_grp.groups:
            row["ssrt_ms"] = stop_signal_measures(stop_grp.get_group(pid))["ssrt_ms"]
        if pid in nback_grp.groups:
            row["d_prime"] = nback_measures(nback_grp.get_group(pid))["d_prime"]
        records.append(row)

    perf_df = pd.DataFrame(records)
    return pd.merge(perf_df, simulated_data.questionnaire, on="participant_id", how="inner")


def run_full_questionnaire_regression(cohort_df: pd.DataFrame):
    """Multiple regression evaluating all 5 questionnaire predictors on Flanker cost."""
    formula = (
        "flanker_effect_ms ~ screen_time_hours + short_video_frequency + "
        "gaming_frequency + psychology_interest + alertness"
    )
    return smf.ols(formula=formula, data=cohort_df).fit()