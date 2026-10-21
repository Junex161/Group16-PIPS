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

#lit values
LIT_NORMS = {
    "flanker_effect_ms": {"mean": 117.29, "sd": 22.30, "label": "Flanker Cost (ms)"},
    "ssrt_ms": {"mean": 186.38, "sd": 52.64, "label": "SSRT (ms)"},
    "d_prime": {"mean": 2.25, "sd": 0.94, "label": "2-Back Sensitivity (d')"},
}
# 1. Data Aggregation
def aggregate_full_study_data(simulated_data) -> pd.DataFrame:
    """Aggregate all simulated participants across all tasks merged with survey variables."""
    records = []
    pids = simulated_data.questionnaire["participant_id"].unique()

    flanker_grp = simulated_data.flanker.groupby("participant_id")
    stop_grp = simulated_data.stopsignal.groupby("participant_id")
    nback_grp = simulated_data.nback.groupby("participant_id")

    for pid in pids:
        row = {"participant_id": pid}
        if pid in flanker_grp.groups:
            f_meas = flanker_measures(flanker_grp.get_group(pid))
            row["flanker_effect_ms"] = f_meas["flanker_effect_ms"]
            row["flanker_baseline_rt_ms"] = f_meas["baseline_rt_ms"]
        if pid in stop_grp.groups:
            s_meas = stop_signal_measures(stop_grp.get_group(pid))
            row["ssrt_ms"] = s_meas["ssrt_ms"]
            row["go_rt_ms"] = s_meas["go_rt_ms"]
        if pid in nback_grp.groups:
            n_meas = nback_measures(nback_grp.get_group(pid))
            row["d_prime"] = n_meas["d_prime"]
        records.append(row)

    perf_df = pd.DataFrame(records)
    return pd.merge(perf_df, simulated_data.questionnaire, on="participant_id", how="inner")

# 2.Task Debrief Plots
def analyze_and_plot_flanker(
    participant_id: str,
    simulated_data,
    output_dir: str = "data/simulated",
    figsize: Tuple[int, int] = (12, 4.5),
) -> plt.Figure:
    """Analysis debrief figure for Flanker task."""
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
    correct_trials = p_trials[p_trials["correct"] == True].copy()
    # Format spacing cleanly as integer strings to match the color palette
    correct_trials["spacing"] = (
        pd.to_numeric(correct_trials["spacing"], errors="coerce")
        .fillna(0)
        .astype(int)
        .astype(str)
    )
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

    fig.text(
        0.5, -0.05,
        f"Screen Time: {p_quest['screen_time_hours']} hrs/day | Alertness: {p_quest['alertness']}/5 | "
        f"Baseline RT: {base_rt:.1f} ms | Incongruent Accuracy: {acc:.1f}%",
        ha="center", fontsize=10, bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8f9fa", edgecolor="#ddd")
    )

    sns.despine(fig=fig)
    plt.tight_layout()

    out_path = Path(output_dir) / f"{participant_id}_flanker_debrief.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    return fig


def analyze_and_plot_stopsignal(
        participant_id: str,
        simulated_data,
        output_dir: str = "data/simulated",
        figsize: Tuple[int, int] = (12, 4.5),
) -> plt.Figure:
    """Analysis and debrief figure for Stop-Signal task."""
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
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    return fig


def analyze_and_plot_nback(
        participant_id: str,
        simulated_data,
        output_dir: str = "data/simulated",
        figsize: Tuple[int, int] = (12, 4.5),
) -> plt.Figure:
    """Analysis and debrief figure for 2-Back task."""
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
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    return fig

#3. Questionnaires, Regressions, Media
def run_full_questionnaire_regression(cohort_df: pd.DataFrame):
    """Multiple regression evaluating all 5 questionnaire predictors on Flanker cost."""
    formula = (
        "flanker_effect_ms ~ screen_time_hours + short_video_frequency + "
        "gaming_frequency + psychology_interest + alertness"
    )
    return smf.ols(formula=formula, data=cohort_df).fit()


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
        else:
            return

        active_screen = screen or pygame.display.get_surface()
        if active_screen is not None:
            show_plot_in_pygame(active_screen, img_path)
    except Exception as e:
        import traceback
        traceback.print_exc()