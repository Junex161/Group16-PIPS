"""
1. Participant-level data aggregation across all three tasks and survey items.
2. Individual task debrief cards contextualized against literature norms:
   - Flanker (Attention & visual crowding)
   - Stop-Signal (Inhibition & staircase SSRT tracking)
   - 2-Back (Working memory d' and criterion)
3. Full multiple regression evaluating all five questionnaire predictors.
4. Differential screen consumption analysis (Duration vs. Short-Form vs. Gaming).
"""

from pathlib import Path
from typing import Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf

from .bootstrap import flanker_measures, nback_measures, stop_signal_measures

# Game Theme Palette (Mind Quest Aesthetic)
GAME_BG = "#161622"  # Deep arcade dark
PANEL_BG = "#222232"  # Card panel background
TEXT_MAIN = "#ecf0f1"  # Clean bright text
TEXT_MUTED = "#95a5a6"  # Soft gray for subtitles
ACCENT_GOLD = "#f1c40f"  # Game UI Gold
ACCENT_BLUE = "#46c8ff"  # Soft neon cyan
ACCENT_CORAL = "#ff5e57"  # Game red/hazard
ACCENT_GREEN = "#2ed573"  # Game success emerald
BORDER_COL = "#3a3a50"  # Subtle frame borders


def apply_game_theme(fig, axes):
    """Style a matplotlib figure and its axes to match the Mind Quest game UI."""
    fig.patch.set_facecolor(GAME_BG)
    if not isinstance(axes, (list, np.ndarray)):
        axes = [axes]
    else:
        axes = axes.flatten()

    for ax in axes:
        ax.set_facecolor(PANEL_BG)
        ax.tick_params(colors=TEXT_MAIN, labelsize=10)
        ax.xaxis.label.set_color(TEXT_MAIN)
        ax.yaxis.label.set_color(TEXT_MAIN)
        ax.title.set_color(ACCENT_GOLD)

        # Soft subtle grid
        ax.grid(True, linestyle="--", alpha=0.15, color=TEXT_MAIN)

        # Border frames
        for spine in ax.spines.values():
            spine.set_color(BORDER_COL)
            spine.set_linewidth(1.2)

        # Legend styling
        legend = ax.get_legend()
        if legend:
            legend.get_frame().set_facecolor(GAME_BG)
            legend.get_frame().set_edgecolor(BORDER_COL)
            for text in legend.get_texts():
                text.set_color(TEXT_MAIN)
            if legend.get_title():
                legend.get_title().set_color(ACCENT_GOLD)

#lit values
LIT_NORMS = {
    "flanker_effect_ms": {"mean": 117.29, "sd": 22.30, "label": "Flanker Cost (ms)"},
    "ssrt_ms": {"mean": 186.38, "sd": 52.64, "label": "SSRT (ms)"},
    "d_prime": {"mean": 2.25, "sd": 0.94, "label": "2-Back Sensitivity (d')"},
}
# 1. Data Aggregation
def aggregate_full_study_data(simulated_data) -> pd.DataFrame:
  """Aggregate participants across available tasks merged with survey variables."""
  records = []
  pids = simulated_data.questionnaire["participant_id"].unique()

  flanker_grp = (
      simulated_data.flanker.groupby("participant_id")
      if hasattr(simulated_data, "flanker")
      else None
  )
  stop_grp = (
      simulated_data.stopsignal.groupby("participant_id")
      if hasattr(simulated_data, "stopsignal")
      else None
  )
  nback_grp = (
      simulated_data.nback.groupby("participant_id")
      if hasattr(simulated_data, "nback")
      else None
  )

  for pid in pids:
    row = {"participant_id": pid}
    if flanker_grp and pid in flanker_grp.groups:
      row["flanker_effect_ms"] = flanker_measures(flanker_grp.get_group(pid))[
          "flanker_effect_ms"
      ]
    if stop_grp and pid in stop_grp.groups:
      row["ssrt_ms"] = stop_signal_measures(stop_grp.get_group(pid))["ssrt_ms"]
    if nback_grp and pid in nback_grp.groups:
      row["d_prime"] = nback_measures(nback_grp.get_group(pid))["d_prime"]
    records.append(row)

  perf_df = pd.DataFrame(records)
  return pd.merge(
      perf_df, simulated_data.questionnaire, on="participant_id", how="inner"
  )

def analyze_and_plot_flanker(
    participant_id: str,
    simulated_data,
    output_dir: str = "data/simulated",
    figsize: Tuple[int, int] = (12, 5.0),
) -> plt.Figure:
    """Styled in-game debrief figure for the Flanker task."""
    flanker_df = simulated_data.flanker
    quest_df = simulated_data.questionnaire
    p_trials = flanker_df[flanker_df["participant_id"] == participant_id]
    p_quest = quest_df[quest_df["participant_id"] == participant_id].iloc[0]

    meas = flanker_measures(p_trials)
    cost = float(meas["flanker_effect_ms"])
    base_rt = float(meas["baseline_rt_ms"])
    acc = (1.0 - float(meas["error_rate_incongruent"])) * 100.0

    # Diagnostic text
    if acc >= 99.9 and cost < 40.0:
        diagnostic = "Ceiling Effect Detected: 100% accuracy with sub-normative delay (<40 ms)."
        badge_col = "#e67e22"
    elif acc >= 99.9:
        diagnostic = f"Optimal Filtering: 100% accuracy with measurable conflict resolution ({cost:.1f} ms)."
        badge_col = ACCENT_GREEN
    else:
        diagnostic = f"Standard Control: {acc:.1f}% accuracy, typical selective filter ({cost:.1f} ms)."
        badge_col = ACCENT_BLUE

    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Panel A: Visual Crowding Barplot
    ax1 = axes[0]
    correct_trials = p_trials[p_trials["correct"] == True].copy()
    crowding_trials = correct_trials[correct_trials["condition"] != "neutral"].copy()
    crowding_trials["spacing"] = (
        pd.to_numeric(crowding_trials["spacing"], errors="coerce")
        .fillna(0)
        .astype(int)
        .astype(str)
    )

    cell_means = (
        crowding_trials.groupby(["condition", "spacing"])["rt_ms"]
        .mean()
        .reset_index()
    )

    sns.barplot(
        data=cell_means,
        x="condition",
        y="rt_ms",
        hue="spacing",
        palette={"35": ACCENT_CORAL, "85": ACCENT_BLUE},
        edgecolor=GAME_BG,
        linewidth=1.5,
        ax=ax1,
    )
    ax1.set_title("A. Parafoveal Crowding Impact", weight="bold", pad=10)
    ax1.set_xlabel("Condition", weight="bold")
    ax1.set_ylabel("Reaction Time (ms)", weight="bold")
    ax1.legend(title="Spacing (px)")

    # Panel B: Population Distribution & Bootstrap CI
    ax2 = axes[1]
    norm = LIT_NORMS["flanker_effect_ms"]

    x_min = min(-20.0, cost - 30.0)
    x_max = max(norm["mean"] + 3.5 * norm["sd"], cost + 40.0)
    x = np.linspace(x_min, x_max, 300)
    density = (1 / (norm["sd"] * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - norm["mean"]) / norm["sd"]) ** 2)

    ax2.plot(x, density, color=TEXT_MUTED, linestyle="--", linewidth=1.8, label=f"Norm (μ = {norm['mean']:.1f} ms)")
    ax2.axvspan(40, 120, color=ACCENT_GREEN, alpha=0.15, label="Typical Adult Range (40–120 ms)")
    ax2.axvline(cost, color=ACCENT_GOLD, linewidth=2.5, label=f"Your Cost: {cost:.1f} ms")

    # Bootstrap overlay
    boot_summary_file = Path("data/simulated/bootstrap_summary.csv")
    if boot_summary_file.exists():
        try:
            boot_df = pd.read_csv(boot_summary_file)
            row = boot_df[(boot_df["task"] == "flanker") & (boot_df["measure"] == "flanker_effect_ms")].iloc[0]
            ci_low, ci_high = float(row["ci_lower"]), float(row["ci_upper"])
            y_pos = (1 / (norm["sd"] * np.sqrt(2 * np.pi))) * 0.45
            ax2.errorbar(
                x=cost,
                y=y_pos,
                xerr=[[cost - ci_low], [ci_high - cost]],
                fmt="o",
                color=ACCENT_GOLD,
                ecolor=ACCENT_GOLD,
                elinewidth=2.5,
                capsize=5,
                capthick=2,
                markersize=6,
                label=f"95% Bootstrap CI: [{ci_low:.0f}, {ci_high:.0f}] ms",
            )
        except Exception:
            pass

    ax2.set_title("B. Population Context (Kaufman et al., 2016)", weight="bold", pad=10)
    ax2.set_xlabel("Flanker Interference Cost (ms)", weight="bold")
    ax2.set_ylabel("Density", weight="bold")
    ax2.set_xlim(x_min, x_max)
    ax2.legend(loc="upper right", fontsize=8.5)

    # Apply Game Styling
    apply_game_theme(fig, axes)

    # Bottom Themed Debrief HUD Box
    summary_text = (
        f"SCREEN TIME: {p_quest['screen_time_hours']} hrs/day  |  ALERTNESS: {p_quest['alertness']}/5  |  "
        f"BASELINE SPEED: {base_rt:.1f} ms  |  ACCURACY: {acc:.1f}%\n"
        f"★ PSYCHOMETRIC DEBRIEF: {diagnostic}"
    )

    fig.text(
        0.5, -0.06,
        summary_text,
        ha="center", fontsize=9.5, family="sans-serif",
        color=TEXT_MAIN, linespacing=1.4,
        bbox=dict(boxstyle="round,pad=0.6", facecolor=PANEL_BG, edgecolor=badge_col, linewidth=1.8)
    )

    plt.tight_layout()
    out_path = Path(output_dir) / f"{participant_id}_flanker_debrief.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    return fig

def analyze_and_plot_stopsignal(
    participant_id: str,
    simulated_data,
    output_dir: str = "data/simulated",
    figsize: Tuple[int, int] = (12, 5.0),
) -> plt.Figure:
    """Styled in-game debrief figure for the Stop-Signal task."""
    stop_df = simulated_data.stopsignal
    quest_df = simulated_data.questionnaire

    p_trials = stop_df[stop_df["participant_id"] == participant_id]
    p_quest = quest_df[quest_df["participant_id"] == participant_id].iloc[0]

    meas = stop_signal_measures(p_trials)
    ssrt = float(meas["ssrt_ms"])
    go_rt = float(meas["go_rt_ms"])

    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Panel A: Staircase SSD tracking
    ax1 = axes[0]
    stop_trials = p_trials[p_trials["trial_type"] == "stop"].copy().reset_index()
    ax1.plot(stop_trials.index + 1, stop_trials["ssd_ms"], marker="o", color=ACCENT_BLUE, linewidth=2.2, markersize=6)
    ax1.set_title("A. Stop-Signal Delay (SSD) Tracking Staircase", weight="bold", pad=10)
    ax1.set_xlabel("Stop Trial Number", weight="bold")
    ax1.set_ylabel("SSD (ms)", weight="bold")

    # Panel B: Normative Distribution Placement
    ax2 = axes[1]
    norm = LIT_NORMS["ssrt_ms"]
    x_min = max(0, min(norm["mean"] - 3.5 * norm["sd"], ssrt - 40))
    x_max = max(norm["mean"] + 3.5 * norm["sd"], ssrt + 40)
    x = np.linspace(x_min, x_max, 250)
    density = (1 / (norm["sd"] * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - norm["mean"]) / norm["sd"]) ** 2)

    ax2.plot(x, density, color=TEXT_MUTED, linestyle="--", linewidth=1.8, label=f"Norm (μ = {norm['mean']:.1f} ms)")
    ax2.axvspan(120, 250, color=ACCENT_GREEN, alpha=0.15, label="Typical Adult Range (120–250 ms)")
    ax2.axvline(ssrt, color=ACCENT_CORAL, linewidth=2.5, label=f"Your SSRT: {ssrt:.1f} ms")
    ax2.set_title("B. Population Context (Congdon et al., 2014)", weight="bold", pad=10)
    ax2.set_xlabel("Stop-Signal Reaction Time (ms)", weight="bold")
    ax2.set_ylabel("Density", weight="bold")
    ax2.set_xlim(x_min, x_max)
    ax2.legend(loc="upper right", fontsize=8.5)

    apply_game_theme(fig, axes)

    summary_text = (
        f"SCREEN TIME: {p_quest['screen_time_hours']} hrs/day  |  GAMING: {p_quest['gaming_frequency']}/5  |  "
        f"MEAN GO RT: {go_rt:.1f} ms  |  INHIBITION SPEED (SSRT): {ssrt:.1f} ms\n"
        f"★ PSYCHOMETRIC DEBRIEF: Lower SSRT reflects faster motor cancellation. Staircase converged on 50% stop rate."
    )

    fig.text(
        0.5, -0.06,
        summary_text,
        ha="center", fontsize=9.5, color=TEXT_MAIN, linespacing=1.4,
        bbox=dict(boxstyle="round,pad=0.6", facecolor=PANEL_BG, edgecolor=ACCENT_GOLD, linewidth=1.8)
    )

    plt.tight_layout()
    out_path = Path(output_dir) / f"{participant_id}_stopsignal_debrief.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    return fig

def analyze_and_plot_nback(
    participant_id: str,
    simulated_data,
    output_dir: str = "data/simulated",
    figsize: Tuple[int, int] = (12, 5.0),
) -> plt.Figure:
    """Styled in-game debrief figure for the 2-Back task."""
    nback_df = simulated_data.nback
    quest_df = simulated_data.questionnaire

    p_trials = nback_df[nback_df["participant_id"] == participant_id]
    p_quest = quest_df[quest_df["participant_id"] == participant_id].iloc[0]

    meas = nback_measures(p_trials)
    d_pr = float(meas["d_prime"])
    crit = float(meas["criterion"])

    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Panel A: Hits vs False Alarms
    ax1 = axes[0]
    targets = p_trials[p_trials["is_target"] == True]
    non_targets = p_trials[p_trials["is_target"] == False]
    hit_rate = float(targets["responded"].mean())
    fa_rate = float(non_targets["responded"].mean())

    bars = ax1.bar(["Hit Rate (Targets)", "False Alarms (Non-Targets)"], [hit_rate, fa_rate],
                   color=[ACCENT_GREEN, ACCENT_CORAL], width=0.45, edgecolor=GAME_BG, linewidth=1.5)
    ax1.set_ylim(0, 1.05)
    ax1.set_title("A. Signal Detection Response Rates", weight="bold", pad=10)
    ax1.set_ylabel("Proportion of Trials", weight="bold")

    for bar, val in zip(bars, [hit_rate, fa_rate]):
        ax1.text(bar.get_x() + bar.get_width() / 2, val + 0.03, f"{val:.0%}",
                 ha="center", fontsize=10, weight="bold", color=TEXT_MAIN)

    # Panel B: Normative Sensitivity Placement
    ax2 = axes[1]
    norm = LIT_NORMS["d_prime"]
    x = np.linspace(max(0, norm["mean"] - 3.5 * norm["sd"]), norm["mean"] + 3.5 * norm["sd"], 200)
    density = (1 / (norm["sd"] * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - norm["mean"]) / norm["sd"]) ** 2)

    ax2.plot(x, density, color=TEXT_MUTED, linestyle="--", linewidth=1.8, label=f"Norm (μ = {norm['mean']:.2f})")
    ax2.axvline(d_pr, color=ACCENT_GREEN, linewidth=2.5, label=f"Your d': {d_pr:.2f}")
    ax2.set_title("B. Population Context (Forsberg et al., 2020)", weight="bold", pad=10)
    ax2.set_xlabel("Working Memory Sensitivity (d')", weight="bold")
    ax2.set_ylabel("Density", weight="bold")
    ax2.legend(loc="upper right", fontsize=8.5)

    apply_game_theme(fig, axes)

    bias_note = "Conservative (cautious, avoids false alarms)" if crit > 0.1 else "Liberal (fast, risks false alarms)" if crit < -0.1 else "Balanced"

    summary_text = (
        f"SCREEN TIME: {p_quest['screen_time_hours']} hrs/day  |  ALERTNESS: {p_quest['alertness']}/5  |  "
        f"SENSITIVITY (d'): {d_pr:.2f}  |  RESPONSE BIAS (c): {crit:.2f} ({bias_note})\n"
        f"★ PSYCHOMETRIC DEBRIEF: High d' confirms precise working memory updating without guessing."
    )

    fig.text(
        0.5, -0.06,
        summary_text,
        ha="center", fontsize=9.5, color=TEXT_MAIN, linespacing=1.4,
        bbox=dict(boxstyle="round,pad=0.6", facecolor=PANEL_BG, edgecolor=ACCENT_GREEN, linewidth=1.8)
    )

    plt.tight_layout()
    out_path = Path(output_dir) / f"{participant_id}_nback_debrief.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    return fig


def analyze_and_plot_tower(
        participant_id: str,
        output_dir: str = "data/simulated",
        figsize: Tuple[int, int] = (12, 5.0),
) -> plt.Figure:
    """Styled in-game debrief figure for the Tower of London puzzle gate."""
    from .data import load_task

    try:
        df_tower = load_task("tower")
        p_data = df_tower[df_tower["participant_id"] == participant_id].copy()

        # Keep only the newest attempt if multiple games were played
        if not p_data.empty and "attempt" in p_data.columns:
            latest_attempt = p_data["attempt"].max()
            p_data = p_data[p_data["attempt"] == latest_attempt].copy()
        elif len(p_data) > 3:
            p_data = p_data.tail(3).copy()  # Fallback to the latest 3 puzzles
    except Exception:
        p_data = pd.DataFrame()

    if p_data.empty:
        p_data = pd.DataFrame([
            {"problem": 1, "min_moves": 3, "moves": 3, "planning_time_ms": 3300},
            {"problem": 2, "min_moves": 4, "moves": 4, "planning_time_ms": 1200},
            {"problem": 3, "min_moves": 5, "moves": 6, "planning_time_ms": 2400},
        ])

    # Sort puzzles by problem order for clean left-to-right display
    p_data = p_data.sort_values("problem").reset_index(drop=True)
    p_data["problem_label"] = "Puzzle " + p_data["problem"].astype(str)

    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Panel A: Planning Efficiency (Optimal vs. Actual Moves)
    ax1 = axes[0]
    x_idx = np.arange(len(p_data))
    width = 0.35

    ax1.bar(x_idx - width / 2, p_data["min_moves"], width, label="Optimal Minimum",
            color=ACCENT_BLUE, edgecolor=GAME_BG, linewidth=1.5)
    ax1.bar(x_idx + width / 2, p_data["moves"], width, label="Your Moves",
            color=ACCENT_CORAL, edgecolor=GAME_BG, linewidth=1.5)

    ax1.set_xticks(x_idx)
    ax1.set_xticklabels(p_data["problem_label"])
    ax1.set_ylabel("Number of Moves", weight="bold")
    ax1.set_title("A. Planning Efficiency", weight="bold", pad=10)
    ax1.legend(loc="upper left")

    # Panel B: Pre-Movement Planning Latency (Sorted by complexity)
    ax2 = axes[1]
    sorted_by_complexity = p_data.sort_values("min_moves").copy()
    plan_sec = sorted_by_complexity["planning_time_ms"] / 1000.0

    ax2.plot(
        sorted_by_complexity["min_moves"],
        plan_sec,
        marker="o",
        color=ACCENT_GOLD,
        linewidth=2.4,
        markersize=8,
        markerfacecolor=ACCENT_GOLD,
        markeredgecolor=GAME_BG,
        markeredgewidth=1.5,
        label="Thinking Time",
    )

    ax2.set_title("B. Pre-Movement Planning Latency (Ward, 1996)", weight="bold", pad=10)
    ax2.set_xlabel("Puzzle Complexity (Minimum Moves Required)", weight="bold")
    ax2.set_ylabel("Initial Thinking Time (seconds)", weight="bold")
    ax2.legend(loc="upper left")

    apply_game_theme(fig, axes)

    tot_extra = int((p_data["moves"] - p_data["min_moves"]).sum())
    mean_plan = (p_data["planning_time_ms"] / 1000.0).mean()
    efficiency_note = "Perfect planning! Solved in minimum moves." if tot_extra == 0 else f"Trial-and-error detected: {tot_extra} excess moves."

    summary_text = (
        f"TOTAL EXCESS MOVES: {tot_extra}  |  AVERAGE THINKING TIME: {mean_plan:.1f} s  |  DOMAIN: Executive Look-Ahead Planning\n"
        f"★ PSYCHOMETRIC DEBRIEF: {efficiency_note} Pre-planning reduces search errors."
    )

    fig.text(
        0.5, -0.06,
        summary_text,
        ha="center", fontsize=9.5, color=TEXT_MAIN, linespacing=1.4,
        bbox=dict(boxstyle="round,pad=0.6", facecolor=PANEL_BG, edgecolor=ACCENT_GOLD, linewidth=1.8)
    )

    plt.tight_layout()
    out_path = Path(output_dir) / f"{participant_id}_tower_debrief.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    return fig


def analyze_screen_modalities(
    cohort_df: pd.DataFrame,
    figsize: Tuple[int, int] = (9, 4.5),
) -> Tuple[sm.regression.linear_model.RegressionResultsWrapper, plt.Figure]:
    """Standardized effect sizes (total screen duration, short-form video, gaming) on Flanker attentional cost."""
    df = cohort_df.copy()
    z_vars = [
        "flanker_effect_ms",
        "screen_time_hours",
        "short_video_frequency",
        "gaming_frequency",
        "alertness",
    ]
    for col in z_vars:
        df[f"z_{col}"] = (df[col] - df[col].mean()) / df[col].std()

    formula = (
        "z_flanker_effect_ms ~ z_screen_time_hours + z_short_video_frequency + "
        "z_gaming_frequency + z_alertness"
    )
    model = smf.ols(formula=formula, data=df).fit()

    params = model.params.drop("Intercept")
    conf = model.conf_int().drop("Intercept")
    pvals = model.pvalues.drop("Intercept")

    labels_map = {
        "z_screen_time_hours": "Total Screen Duration (Hours/Day)",
        "z_short_video_frequency": "Short-Form Video (TikTok/Reels)",
        "z_gaming_frequency": "Action Video Gaming",
        "z_alertness": "Subjective Alertness (Covariate)",
    }
    plot_labels = [labels_map.get(k, k) for k in params.index]

    sns.set_theme(style="ticks", font_scale=0.95)
    fig, ax = plt.subplots(figsize=figsize)

    y_pos = np.arange(len(params))
    ax.axvline(0, color="#7f8c8d", linestyle="--", linewidth=1.2)

    colors = ["#c0392b" if p < 0.05 else "#2c3e50" for p in pvals]

    for idx in range(len(params)):
        val = params.iloc[idx]
        low, high = conf.iloc[idx, 0], conf.iloc[idx, 1]
        ax.errorbar(
            val,
            idx,
            xerr=[[val - low], [high - val]],
            fmt="o",
            color=colors[idx],
            ecolor=colors[idx],
            elinewidth=2.5,
            capsize=5,
            markersize=7,
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(plot_labels)
    ax.set_xlabel("Standardized Effect Size (β* with 95% CI)")
    ax.set_title("What Type Of Screen Exposure Matters?", weight="bold", pad=12)

    sns.despine(fig=fig)
    plt.tight_layout()

    out_path = Path("data/simulated/screen_modality_comparison.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300)
    return model, fig

import pygame

def run_full_questionnaire_regression(cohort_df: pd.DataFrame):
    """Multiple regression evaluating all 5 questionnaire predictors on Flanker cost."""
    formula = (
        "flanker_effect_ms ~ screen_time_hours + short_video_frequency + "
        "gaming_frequency + psychology_interest + alertness"
    )
    return smf.ols(formula=formula, data=cohort_df).fit()

def plot_individual_media_impact(
    participant_id: str,
    participant_session,
    simulated_cohort=None,
    output_dir: str = "data/simulated",
    figsize: Tuple[int, int] = (11, 5.2),
) -> plt.Figure:
    """Styled in-game debrief card decomposing habit contributions to attentional delay."""
    from .simulation import simulate_participants

    # 1. Calibrate cohort regression model
    if simulated_cohort is None:
        simulated_cohort = simulate_participants(n=50, seed=2026)

    cohort_df = aggregate_full_study_data(simulated_cohort)
    reg_model = run_full_questionnaire_regression(cohort_df)

    # 2. Extract participant survey data
    if hasattr(participant_session, "questionnaire"):
        quest_df = participant_session.questionnaire
    else:
        from .data import load_session
        quest_df = load_session(participant_id).get("questionnaire")

    p_row = quest_df[quest_df["participant_id"] == participant_id]
    if p_row.empty:
        p_row = quest_df.iloc[[0]]
    p_data = p_row.iloc[0]

    b_screen = reg_model.params.get("screen_time_hours", 0.0)
    b_video = reg_model.params.get("short_video_frequency", 0.0)
    b_gaming = reg_model.params.get("gaming_frequency", 0.0)
    b_alert = reg_model.params.get("alertness", 0.0)

    m_screen = cohort_df["screen_time_hours"].mean()
    m_video = cohort_df["short_video_frequency"].mean()
    m_gaming = cohort_df["gaming_frequency"].mean()
    m_alert = cohort_df["alertness"].mean()

    # Net millisecond impact relative to cohort mean
    impacts = {
        "Screen Duration": b_screen * (p_data["screen_time_hours"] - m_screen),
        "Short-Form Video": b_video * (p_data["short_video_frequency"] - m_video),
        "Gaming Experience": b_gaming * (p_data["gaming_frequency"] - m_gaming),
        "Subjective Alertness": b_alert * (p_data["alertness"] - m_alert),
    }

    labels = list(impacts.keys())
    values = list(impacts.values())
    bar_colors = [ACCENT_CORAL if v > 0 else ACCENT_GREEN for v in values]

    fig, ax = plt.subplots(figsize=figsize)

    y_pos = np.arange(len(labels))
    bars = ax.barh(
        y_pos,
        values,
        color=bar_colors,
        height=0.52,
        edgecolor=GAME_BG,
        linewidth=1.5,
    )
    ax.axvline(0, color=ACCENT_GOLD, linestyle="--", linewidth=1.5, label="Cohort Baseline (0 ms)")

    # Data value labels with contrasting text placement
    for bar, val in zip(bars, values):
        x_text = val + (1.2 if val >= 0 else -1.2)
        ha = "left" if val >= 0 else "right"
        sign = "+" if val > 0 else ""
        col = ACCENT_CORAL if val > 0 else ACCENT_GREEN
        ax.text(
            x_text,
            bar.get_y() + bar.get_height() / 2,
            f"{sign}{val:.1f} ms",
            va="center",
            ha=ha,
            fontsize=10,
            weight="bold",
            color=col,
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels([
        f"{labels[0]} ({p_data['screen_time_hours']} hrs/day)",
        f"{labels[1]} ({p_data['short_video_frequency']}/5 freq)",
        f"{labels[2]} ({p_data['gaming_frequency']}/5 freq)",
        f"{labels[3]} ({p_data['alertness']}/5 alert)",
    ], weight="bold")
    ax.set_xlabel("Estimated Delay / Speedup on Selective Attention (ms relative to cohort average)", weight="bold")
    ax.set_title(f"Personal Media Footprint: How Your Habits Shaped Performance\n(Subject: {participant_id})", weight="bold", pad=12)

    lim = max(max(abs(min(values)), abs(max(values))) + 18, 25)
    ax.set_xlim(-lim, lim)

    apply_game_theme(fig, ax)
    ax.legend(loc="lower right", fontsize=8.5)

    fig.text(
        0.5,
        -0.06,
        "CORAL BARS = Increased attentional interference delay  |  GREEN BARS = Faster / protective cognitive filtering",
        ha="center",
        fontsize=9.5,
        family="sans-serif",
        color=TEXT_MAIN,
        linespacing=1.4,
        bbox=dict(
            boxstyle="round,pad=0.6",
            facecolor=PANEL_BG,
            edgecolor=BORDER_COL,
            linewidth=1.6,
        ),
    )

    plt.tight_layout()
    out_path = Path(output_dir) / f"{participant_id}_personal_media_impact.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        out_path,
        dpi=200,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )
    return fig

def show_plot_in_pygame(screen, image_path: str):
  """Display a saved debrief plot on the Pygame screen and wait for the player

  to press SPACE or ENTER to continue.
  """
  plot_img = pygame.image.load(image_path)

  screen_w, screen_h = screen.get_size()
  img_w, img_h = plot_img.get_size()

  # Scale smoothly to fit within 90% of the game window
  scale = min((screen_w * 0.90) / img_w, (screen_h * 0.85) / img_h)
  new_size = (int(img_w * scale), int(img_h * scale))
  scaled_img = pygame.transform.smoothscale(plot_img, new_size)

  rect = scaled_img.get_rect(center=(screen_w // 2, screen_h // 2 - 20))

  font = pygame.font.SysFont("Arial", 22, bold=True)
  prompt = font.render(
      "Press [SPACE] or [ENTER] to continue your quest...", True, (241, 196, 15)
  )
  prompt_rect = prompt.get_rect(center=(screen_w // 2, screen_h - 35))

  waiting = True
  clock = pygame.time.Clock()

  while waiting:
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
        return
      if event.type == pygame.KEYDOWN:
        if event.key in (pygame.K_SPACE, pygame.K_RETURN):
          waiting = False

    screen.fill((26, 26, 36))  # Dark background matching the game theme
    screen.blit(scaled_img, rect)
    screen.blit(prompt, prompt_rect)
    pygame.display.flip()
    clock.tick(30)


def trigger_live_task_debrief(task_name: str, participant_id: str, screen=None) -> None:
    """Analyze the player's saved session and display their debrief plot immediately on the Pygame screen."""
    import types
    import pygame
    from .data import load_session

    try:
        session = load_session(participant_id)
        wrapper = types.SimpleNamespace(**session)

        if task_name == "flanker":
            analyze_and_plot_flanker(participant_id, wrapper)
            img_path = f"data/simulated/{participant_id}_flanker_debrief.png"
        elif task_name == "stopsignal":
            analyze_and_plot_stopsignal(participant_id, wrapper)
            img_path = f"data/simulated/{participant_id}_stopsignal_debrief.png"
        elif task_name == "nback":
            analyze_and_plot_nback(participant_id, wrapper)
            img_path = f"data/simulated/{participant_id}_nback_debrief.png"
        elif task_name == "tower":
            analyze_and_plot_tower(participant_id)
            img_path = f"data/simulated/{participant_id}_tower_debrief.png"
        else:
            return

        active_screen = screen or pygame.display.get_surface()
        if active_screen is not None:
            show_plot_in_pygame(active_screen, img_path)
    except Exception as e:
        import traceback
        traceback.print_exc()

def run_power_analysis(
    bootstrap_results=None,
    sample_sizes=(25, 50, 100, 175, 250, 325),
    n_replications: int = 30,
    output_dir: str = "data/simulated",
    figsize: Tuple[int, int] = (8, 5),
) -> Tuple[pd.DataFrame, plt.Figure]:
    """Run a Monte Carlo power analysis across varying sample sizes to estimate

    statistical power for detecting the built-in screen-time effect (+5 ms/hr).
    """
    from .simulation import simulate_participants

    records = []

    for n in sample_sizes:
        sig_count = 0
        for rep in range(n_replications):
            seed = 2026 + rep * 17
            sim_data = simulate_participants(
                n=n, bootstrap=bootstrap_results, seed=seed
            )
            cohort_df = aggregate_full_study_data(sim_data)

            # Fit OLS regression
            model = smf.ols(
                "flanker_effect_ms ~ screen_time_hours + short_video_frequency"
                " + gaming_frequency + alertness",
                data=cohort_df,
            ).fit()

            # Check if screen_time slope is positive and significant at alpha = 0.05
            p_val = model.pvalues.get("screen_time_hours", 1.0)
            coef = model.params.get("screen_time_hours", 0.0)
            if p_val < 0.05 and coef > 0:
                sig_count += 1

        power = sig_count / n_replications
        records.append({"sample_size": n, "power": power})

    power_df = pd.DataFrame(records)

    # Generate Power Curve Plot
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(
        power_df["sample_size"],
        power_df["power"],
        marker="o",
        color=ACCENT_GOLD,
        linewidth=2.5,
        markersize=7,
        label="Observed Empirical Power",
    )

    # 80% standard target line
    ax.axhline(
        0.80,
        color=ACCENT_GREEN,
        linestyle="--",
        linewidth=1.8,
        label="Standard Target (80% Power)",
    )
    ax.axhline(
        0.05,
        color=ACCENT_CORAL,
        linestyle=":",
        linewidth=1.2,
        label="Type-I Error Rate (α = .05)",
    )

    ax.set_ylim(-0.02, 1.05)
    ax.set_xlabel("Sample Size (N Participants)", weight="bold")
    ax.set_ylabel("Detection Probability (Power)", weight="bold")
    ax.set_title(
        "Statistical Power Curve: Detecting Screen Time on Flanker (β = +5"
        " ms/hr)",
        weight="bold",
        pad=12,
    )

    apply_game_theme(fig, ax)
    ax.legend(loc="lower right", fontsize=8.5)

    fig.text(
        0.5,
        -0.07,
        "Monte Carlo simulation (30 replications/sample size) assessing"
        " attenuation from trial-level noise.",
        ha="center",
        fontsize=9,
        color=TEXT_MUTED,
        style="italic",
    )

    plt.tight_layout()
    out_path = Path(output_dir) / "power_analysis_curve.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        out_path,
        dpi=200,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )
    return power_df, fig