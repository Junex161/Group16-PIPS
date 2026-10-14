"""The mini boss: Professor Fin's child flanker task as a pygame scene.

The scene walks through a tutorial, practice trials with detailed feedback,
the test trials and a results screen. Reaction times are measured from the
first frame that shows the fish to the key press, so they are accurate to
about one frame (roughly 17 ms at 60 frames per second).
"""

import math
import random
from time import perf_counter

import pygame

from . import graphics, ui
from .config import SCREEN_HEIGHT, SCREEN_WIDTH, FlankerSettings
from .flanker_task import (
    CONDITIONS,
    DIRECTIONS,
    FlankerTrial,
    TrialResult,
    has_passed,
    make_practice_trials,
    make_trials,
    summarise,
)
from .scenes import INPUT_DELAY, Scene

RESPONSE_KEYS = {
    pygame.K_a: "left",
    pygame.K_LEFT: "left",
    pygame.K_d: "right",
    pygame.K_RIGHT: "right",
}
CENTER = (SCREEN_WIDTH // 2, 330)
FISH_SPACING = 150

# Each tutorial page: title, text and example displays (trial, caption).
TUTORIAL_PAGES = (
    (
        "Feed the hungry fish!",
        "The fish in my pond are hungry. To feed a fish, tell me which way it is "
        "swimming: press A if it swims to the LEFT and D if it swims to the RIGHT.",
        (
            (FlankerTrial("neutral", "left"), "Swims LEFT: press A"),
            (FlankerTrial("neutral", "right"), "Swims RIGHT: press D"),
        ),
    ),
    (
        "Only the MIDDLE fish counts",
        "Sometimes the hungry fish brings four friends. Look only at the fish in the "
        "MIDDLE (circled here). Its friends may swim the same way or the opposite way. "
        "Ignore the friends!",
        (
            (FlankerTrial("congruent", "right"), "Middle fish swims RIGHT: press D"),
            (FlankerTrial("incongruent", "left"), "Middle fish swims LEFT: press A"),
        ),
    ),
)


class FlankerScene(Scene):
    """
    Run the flanker task and report the outcome.

    Parameters
    ----------
    game : Game
        The running game.
    on_finish : callable
        Called as ``on_finish(passed, summary, results)`` when the scene
        closes. ``summary`` is None if the player quit before the end.
    settings : FlankerSettings, optional
        Design and timing of the task.
    rng : random.Random or None, optional
        Random number generator for trial order and fixation times.
    show_tutorial : bool, optional
        If False the task starts with a short reminder instead of the
        tutorial and practice trials (used when the player tries again).
    """

    def __init__(self, game, on_finish, settings=FlankerSettings(), rng=None, show_tutorial=True):
        super().__init__(game)
        self.on_finish = on_finish
        self.settings = settings
        self.rng = rng or random.Random()
        self.background = graphics.vertical_gradient((SCREEN_WIDTH, SCREEN_HEIGHT), graphics.POND_TOP, graphics.POND_BOTTOM)
        self.bubbles = [[self.rng.uniform(0, SCREEN_WIDTH), self.rng.uniform(0, SCREEN_HEIGHT), self.rng.uniform(4, 12)] for _ in range(24)]
        self.n_test_trials = len(CONDITIONS) * len(DIRECTIONS) * settings.n_test_repetitions
        self.results = []
        self.summary = None
        self.time = 0.0
        self.phase = "tutorial" if show_tutorial else "reminder"
        self.phase_age = 0.0
        self.page = 0
        self.block = "practice"
        self.trials = []
        self.trial_index = 0
        self.trial_phase = "fixation"
        self.trial_timer = 0.0
        self.target_onset = None
        self.last_result = None

    # ----- flow -----------------------------------------------------------

    def _set_phase(self, phase):
        self.phase, self.phase_age = phase, 0.0

    def _start_block(self, block):
        """Start the practice or the test block."""
        self.block = block
        if block == "practice":
            self.trials = make_practice_trials(self.settings.n_practice_trials, self.rng)
        else:
            self.trials = make_trials(self.settings.n_test_repetitions, self.rng)
        self.trial_index = 0
        self._set_phase("trials")
        if self.trials:
            self._start_fixation()
        else:
            self._finish_block()

    def _start_fixation(self):
        self.trial_phase = "fixation"
        self.trial_timer = self.rng.uniform(self.settings.fixation_min, self.settings.fixation_max)

    def _record(self, response):
        """Store the response (None = too slow) and show feedback."""
        trial = self.trials[self.trial_index]
        rt_ms = None if response is None else round((perf_counter() - self.target_onset) * 1000)
        self.last_result = TrialResult(
            block=self.block,
            trial=self.trial_index + 1,
            condition=trial.condition,
            target_direction=trial.target_direction,
            response=response,
            correct=response == trial.target_direction,
            rt_ms=rt_ms,
        )
        self.results.append(self.last_result)
        self.trial_phase = "feedback"
        is_practice = self.block == "practice"
        self.trial_timer = self.settings.practice_feedback_time if is_practice else self.settings.test_feedback_time

    def _next_trial(self):
        self.trial_index += 1
        if self.trial_index < len(self.trials):
            self._start_fixation()
        else:
            self._finish_block()

    def _finish_block(self):
        if self.block == "practice":
            self._set_phase("practice_done")
            return
        self.summary = summarise([r for r in self.results if r.block == "test"])
        self.game.save_flanker_results(self.results)
        self._set_phase("results")

    def _close(self):
        passed = self.summary is not None and has_passed(self.summary, self.settings.pass_accuracy)
        self.game.pop_scene()
        self.on_finish(passed, self.summary, self.results)

    # ----- scene interface ------------------------------------------------

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.summary = None
            self._close()
        elif self.phase == "trials":
            if self.trial_phase == "target" and event.key in RESPONSE_KEYS and self.target_onset is not None:
                self._record(RESPONSE_KEYS[event.key])
        elif self.phase_age >= INPUT_DELAY:
            self._handle_menu_key(event.key)

    def _handle_menu_key(self, key):
        confirm = key in (pygame.K_SPACE, pygame.K_RETURN)
        if self.phase == "tutorial" and confirm:
            self.page += 1
            self.phase_age = 0.0
            if self.page > len(TUTORIAL_PAGES):
                self._start_block("practice")
        elif self.phase == "practice_done" and confirm:
            self._start_block("test")
        elif self.phase == "reminder" and confirm:
            self._start_block("test")
        elif self.phase == "reminder" and key == pygame.K_t:
            self.page = 0
            self._set_phase("tutorial")
        elif self.phase == "results" and confirm:
            self._close()

    def update(self, dt):
        self.time += dt
        self.phase_age += dt
        for bubble in self.bubbles:
            bubble[1] -= (20 + bubble[2] * 4) * dt
            if bubble[1] < -20:
                bubble[1] = SCREEN_HEIGHT + 20
        if self.phase != "trials":
            return
        if self.trial_phase == "target" and self.target_onset is None:
            return  # the fish have not been on screen yet
        self.trial_timer -= dt
        if self.trial_timer > 0:
            return
        if self.trial_phase == "fixation":
            self.trial_phase = "target"
            self.trial_timer = self.settings.response_deadline
            self.target_onset = None
        elif self.trial_phase == "target":
            self._record(None)
        else:
            self._next_trial()

    def draw(self, surface):
        surface.blit(self.background, (0, 0))
        for x, y, radius in self.bubbles:
            pygame.draw.circle(surface, (150, 210, 240), (int(x + math.sin(self.time + y * 0.02) * 6), int(y)), int(radius), 2)
        draw_phase = getattr(self, f"_draw_{self.phase}")
        draw_phase(surface)

    # ----- drawing --------------------------------------------------------

    def _draw_display(self, surface, trial, center=CENTER, length=110, mark_target=False):
        """Draw the fish of one trial around ``center``."""
        spacing = FISH_SPACING * length / 110
        if trial.flanker_direction is not None:
            for offset in (-2, -1, 1, 2):
                graphics.draw_fish(surface, (center[0] + offset * spacing, center[1]), trial.flanker_direction, length)
        graphics.draw_fish(surface, center, trial.target_direction, length)
        if mark_target:
            pygame.draw.circle(surface, ui.WHITE, center, int(length * 0.66), 3)

    def _draw_heading(self, surface, title, subtitle=""):
        ui.draw_text(surface, title, (SCREEN_WIDTH // 2, 70), 60, ui.GOLD, "center", bold=True)
        if subtitle:
            ui.draw_text(surface, subtitle, (SCREEN_WIDTH // 2, 120), 30, ui.SOFT_BLUE, "center")

    def _draw_prompt(self, surface, text):
        if self.phase_age >= INPUT_DELAY:
            ui.draw_text(surface, text, (SCREEN_WIDTH // 2, 670), 34, ui.GOLD, "center", bold=True)

    def _draw_tutorial(self, surface):
        if self.page >= len(TUTORIAL_PAGES):
            self._draw_procedure_page(surface)
            return
        title, text, examples = TUTORIAL_PAGES[self.page]
        self._draw_heading(surface, title, f"Professor Fin's Pond Challenge  -  {self.page + 1}/{len(TUTORIAL_PAGES) + 1}")
        ui.draw_paragraph(surface, text, (190, 160), 900, 32, centered=True)
        for index, (trial, caption) in enumerate(examples):
            center = (SCREEN_WIDTH // 2, 365 + index * 150)
            self._draw_display(surface, trial, center, length=80, mark_target=trial.condition != "neutral")
            ui.draw_text(surface, caption, (center[0], center[1] + 58), 30, ui.WHITE, "center")
        self._draw_prompt(surface, "SPACE to continue")

    def _draw_procedure_page(self, surface):
        settings = self.settings
        self._draw_heading(surface, "How a round works", f"Professor Fin's Pond Challenge  -  {len(TUTORIAL_PAGES) + 1}/{len(TUTORIAL_PAGES) + 1}")
        steps = (
            "1.  A cross (+) appears. Keep your eyes on it.",
            "2.  The fish appear. Press A (left) or D (right) for the MIDDLE fish.",
            f"3.  Be as fast as you can without making mistakes. You have {settings.response_deadline:g} seconds.",
            "",
            f"First you get {settings.n_practice_trials} practice rounds with feedback.",
            f"Then the challenge: {self.n_test_trials} rounds. Feed at least {settings.pass_accuracy:.0%} of the fish",
            "correctly and I will build you a bridge and give you a reward!",
        )
        for index, line in enumerate(steps):
            ui.draw_text(surface, line, (220, 190 + index * 52), 34)
        self._draw_prompt(surface, "SPACE to start the practice")

    def _draw_reminder(self, surface):
        self._draw_heading(surface, "Try again!")
        text = (
            "Remember: watch the MIDDLE fish. Press A if it swims LEFT and D if it swims "
            f"RIGHT. Ignore its friends. You need {self.settings.pass_accuracy:.0%} correct."
        )
        ui.draw_paragraph(surface, text, (190, 170), 900, 34, centered=True)
        self._draw_display(surface, FlankerTrial("incongruent", "right"), (SCREEN_WIDTH // 2, 400), 90, mark_target=True)
        ui.draw_text(surface, "Middle fish swims RIGHT: press D", (SCREEN_WIDTH // 2, 470), 30, ui.WHITE, "center")
        self._draw_prompt(surface, "SPACE: start the challenge      T: tutorial and practice")

    def _draw_practice_done(self, surface):
        practice = [r for r in self.results if r.block == "practice"]
        self._draw_heading(surface, "Practice done!")
        lines = (
            f"You fed {sum(r.correct for r in practice)} of {len(practice)} fish correctly.",
            "",
            f"Now the real challenge: {self.n_test_trials} rounds.",
            "The feedback will be shorter, so stay focused on the MIDDLE fish.",
            f"You need at least {self.settings.pass_accuracy:.0%} correct. Good luck!",
        )
        for index, line in enumerate(lines):
            ui.draw_text(surface, line, (SCREEN_WIDTH // 2, 220 + index * 54), 36, ui.WHITE, "center")
        self._draw_prompt(surface, "SPACE to start the challenge")

    def _draw_trials(self, surface):
        label = "Practice" if self.block == "practice" else "Challenge"
        ui.draw_text(surface, f"{label}: round {self.trial_index + 1} of {len(self.trials)}", (40, 30), 30, ui.SOFT_BLUE)
        ui.draw_text(surface, "A = left        D = right", (SCREEN_WIDTH // 2, 670), 30, ui.SOFT_BLUE, "center")
        trial = self.trials[self.trial_index]
        if self.trial_phase == "fixation":
            ui.draw_text(surface, "+", CENTER, 90, ui.WHITE, "center", bold=True)
        elif self.trial_phase == "target":
            self._draw_display(surface, trial)
            if self.target_onset is None:
                self.target_onset = perf_counter()
        else:
            self._draw_feedback(surface, trial)

    def _draw_feedback(self, surface, trial):
        result = self.last_result
        if result.correct:
            message, color = "Yum! Correct!", ui.GREEN
        elif result.response is None:
            message, color = "Too slow!", ui.RED
        else:
            message, color = "Oops, wrong way!", ui.RED
        ui.draw_text(surface, message, (CENTER[0], 190), 64, color, "center", bold=True)
        if self.block == "practice":
            self._draw_display(surface, trial, mark_target=True)
            key = "A" if trial.target_direction == "left" else "D"
            hint = f"The middle fish swims {trial.target_direction.upper()}: press {key}"
            ui.draw_text(surface, hint, (CENTER[0], 470), 34, ui.WHITE, "center")

    def _draw_results(self, surface):
        summary, settings = self.summary, self.settings
        passed = has_passed(summary, settings.pass_accuracy)
        self._draw_heading(surface, "Challenge won!" if passed else "Not quite...")
        accuracy_color = ui.GREEN if passed else ui.RED
        ui.draw_text(
            surface,
            f"You fed {summary.n_correct} of {summary.n_trials} fish correctly: {summary.accuracy:.0%}  (needed: {settings.pass_accuracy:.0%})",
            (SCREEN_WIDTH // 2, 160), 38, accuracy_color, "center", bold=True,
        )
        bars = [
            ("Friends swim the SAME way", summary.mean_rt_ms["congruent"], ui.GREEN),
            ("Friends swim the OPPOSITE way", summary.mean_rt_ms["incongruent"], ui.RED),
            ("Fish alone", summary.mean_rt_ms["neutral"], ui.SOFT_BLUE),
        ]
        ui.draw_bar_chart(surface, pygame.Rect(120, 200, 520, 430), bars, "Your average reaction time (correct rounds)", "ms")
        box = pygame.Rect(680, 200, 480, 430)
        ui.draw_panel(surface, box)
        if summary.flanker_effect_ms is not None:
            effect = summary.flanker_effect_ms
            ui.draw_text(surface, "Your flanker effect:", (box.centerx, box.top + 24), 30, ui.SOFT_BLUE, "midtop")
            ui.draw_text(surface, f"{effect:+.0f} ms", (box.centerx, box.top + 60), 60, ui.GOLD, "midtop", bold=True)
        explanation = (
            "Most people are slower when the friends swim the opposite way, because "
            "the distracting fish create a conflict that attention has to resolve. "
            "This slowdown is called the flanker effect (Eriksen & Eriksen, 1974)."
        )
        ui.draw_paragraph(surface, explanation, (box.left + 24, box.top + 140), box.width - 48, 27)
        self._draw_prompt(surface, "SPACE to continue")
