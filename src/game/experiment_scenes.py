"""The experiments of Levels 2 and 3 as pygame scenes.

* ``StopSignalScene``: Signal Sam's stop-signal race (response inhibition).
* ``NBackScene``: the Memory Machine's 2-back task (working-memory updating).
* ``TowerScene``: the Tower of London puzzle gate (planning).

Each scene walks through a short illustrated tutorial, practice with
feedback, the test and a results screen with a picture of the player's own
result, and saves the trials as a CSV file through ``game.save_task_results``.
Reaction times are measured from the first frame that shows a stimulus.
"""

import math
import random
from dataclasses import replace
from time import perf_counter

import pygame

from . import graphics, ui
from . import nback_task, stop_signal_task, tower_task
from .config import SCREEN_HEIGHT, SCREEN_WIDTH, NBackSettings, StopSignalSettings, TowerSettings
from .scenes import INPUT_DELAY, Scene

CONFIRM_KEYS = (pygame.K_SPACE, pygame.K_RETURN)
LEFT_KEYS = (pygame.K_a, pygame.K_LEFT)
RIGHT_KEYS = (pygame.K_d, pygame.K_RIGHT)
CENTER = (SCREEN_WIDTH // 2, 340)
ROAD_TOP = 430


class ExperimentScene(Scene):
    """
    Shared parts of the experiment scenes: phases, headings and prompts.

    Subclasses draw each phase in a method called ``_draw_<phase>``.

    Parameters
    ----------
    game : Game
        The running game.
    on_finish : callable
        Called as ``on_finish(passed, summary, results)`` when the scene
        closes; ``summary`` is None if the player left early.
    top_color, bottom_color : tuple of int
        Colours of the background gradient.
    """

    stops_clock = False

    def __init__(self, game, on_finish, top_color, bottom_color):
        super().__init__(game)
        self.on_finish = on_finish
        self.background = graphics.vertical_gradient((SCREEN_WIDTH, SCREEN_HEIGHT), top_color, bottom_color)
        self.time = 0.0
        self.phase = "tutorial"
        self.phase_age = 0.0
        self.page = 0
        self.summary = None
        self.results = []

    def _set_phase(self, phase):
        self.phase, self.phase_age = phase, 0.0

    def passed(self):
        """Return True if the summary reaches the pass mark."""
        return False

    def _close(self):
        passed = self.summary is not None and self.passed()
        self.game.pop_scene()
        self.on_finish(passed, self.summary, self.results)

    def update(self, dt):
        self.time += dt
        self.phase_age += dt

    def draw(self, surface):
        surface.blit(self.background, (0, 0))
        self._draw_backdrop(surface)
        getattr(self, f"_draw_{self.phase}")(surface)

    def _draw_backdrop(self, surface):
        """Decorations behind every phase."""

    def _draw_heading(self, surface, title, subtitle=""):
        ui.draw_text(surface, title, (SCREEN_WIDTH // 2, 66), 60, ui.GOLD, "center", bold=True, shadow=True)
        if subtitle:
            ui.draw_text(surface, subtitle, (SCREEN_WIDTH // 2, 116), 30, ui.SOFT_BLUE, "center")

    def _draw_prompt(self, surface, text):
        if self.phase_age >= INPUT_DELAY:
            ui.draw_text(surface, text, (SCREEN_WIDTH // 2, 676), 34, ui.GOLD, "center", bold=True, shadow=True)

    def _draw_lines(self, surface, lines, top, size=34, gap=50):
        for index, line in enumerate(lines):
            ui.draw_text(surface, line, (SCREEN_WIDTH // 2, top + index * gap), size, ui.WHITE, "center")


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------


def draw_race_car(surface, center, direction, length=150, color=(70, 200, 255)):
    """Draw a race car pointing "left" or "right", the go stimulus."""
    x, y = center
    sign = 1 if direction == "right" else -1
    height = length * 0.32
    body = [
        (x - sign * length * 0.5, y + height * 0.2),
        (x - sign * length * 0.5, y - height * 0.25),
        (x - sign * length * 0.15, y - height * 0.35),
        (x + sign * length * 0.05, y - height * 0.85),
        (x + sign * length * 0.3, y - height * 0.85),
        (x + sign * length * 0.5, y - height * 0.1),
        (x + sign * length * 0.5, y + height * 0.2),
    ]
    pygame.draw.polygon(surface, color, body)
    pygame.draw.polygon(surface, graphics.OUTLINE, body, 3)
    window = [(x + sign * length * 0.08, y - height * 0.72), (x + sign * length * 0.27, y - height * 0.72), (x + sign * length * 0.38, y - height * 0.3), (x + sign * length * 0.02, y - height * 0.3)]
    pygame.draw.polygon(surface, (200, 240, 255), window)
    # A big arrow on the side makes the direction obvious at a glance.
    arrow = [(x - sign * length * 0.28, y - height * 0.08), (x + sign * length * 0.05, y - height * 0.08), (x + sign * length * 0.05, y - height * 0.22), (x + sign * length * 0.22, y + height * 0.02), (x + sign * length * 0.05, y + height * 0.26), (x + sign * length * 0.05, y + height * 0.12), (x - sign * length * 0.28, y + height * 0.12)]
    pygame.draw.polygon(surface, ui.WHITE, arrow)
    for wheel_x in (x - sign * length * 0.3, x + sign * length * 0.3):
        pygame.draw.circle(surface, (30, 30, 40), (wheel_x, y + height * 0.25), length * 0.11)
        pygame.draw.circle(surface, (170, 170, 190), (wheel_x, y + height * 0.25), length * 0.05)


def draw_stop_sign(surface, center, radius=70):
    """Draw a red octagonal STOP sign, the stop signal."""
    x, y = center
    points = [(x + math.cos(math.pi / 8 + index * math.pi / 4) * radius, y + math.sin(math.pi / 8 + index * math.pi / 4) * radius) for index in range(8)]
    pygame.draw.polygon(surface, (220, 40, 50), points)
    pygame.draw.polygon(surface, ui.WHITE, points, max(2, radius // 12))
    ui.draw_text(surface, "STOP", center, max(12, int(radius * 0.6)), ui.WHITE, "center", bold=True)


def draw_monitor(surface, rect, letter="", glow=None):
    """Draw the screen of the Memory Machine with an optional letter."""
    pygame.draw.rect(surface, (70, 74, 96), rect.inflate(30, 30), border_radius=24)
    pygame.draw.rect(surface, (20, 40, 30), rect, border_radius=14)
    if glow:
        pygame.draw.rect(surface, glow, rect, 8, border_radius=14)
    for y in range(rect.top + 6, rect.bottom, 8):
        pygame.draw.line(surface, (26, 52, 38), (rect.left + 6, y), (rect.right - 6, y), 2)
    if letter:
        ui.draw_text(surface, letter, rect.center, int(rect.height * 0.8), (120, 255, 160), "center", bold=True)


def draw_ball(surface, center, color_name, radius):
    """Draw one ball of the Tower of London."""
    color = {"red": (230, 70, 80), "green": (90, 200, 110), "blue": (80, 140, 240)}[color_name]
    pygame.draw.circle(surface, color, center, radius)
    pygame.draw.circle(surface, graphics.OUTLINE, center, radius, max(1, radius // 9))
    pygame.draw.circle(surface, (255, 255, 255), (center[0] - radius * 0.35, center[1] - radius * 0.35), max(1, radius // 4))


def draw_tower(surface, state, base_center, scale=1.0, cursor=None, held=None, time=0.0):
    """
    Draw the three pegs of the Tower of London with their balls.

    Parameters
    ----------
    state : tuple
        The balls on each peg, bottom up.
    base_center : tuple of int
        Middle of the wooden base.
    scale : float, optional
        Size; 1 fills most of the screen width.
    cursor : int or None, optional
        Peg under the player's hand.
    held : str or None, optional
        Ball the player is holding above the cursor.
    """
    radius = int(34 * scale)
    gap = int(240 * scale)
    base = pygame.Rect(0, 0, int(720 * scale), int(26 * scale))
    base.midtop = base_center
    corner = max(1, min(base.height // 2, int(8 * scale)))
    pygame.draw.rect(surface, graphics.WOOD, base, border_radius=corner)
    pygame.draw.rect(surface, graphics.WOOD_DARK, base, max(1, int(3 * scale)), border_radius=corner)
    for peg, capacity in enumerate(tower_task.CAPACITIES):
        x = base_center[0] + (peg - 1) * gap
        height = capacity * radius * 2 + int(16 * scale)
        pole = pygame.Rect(0, 0, int(12 * scale), height)
        pole.midbottom = (x, base.top)
        pygame.draw.rect(surface, graphics.WOOD_DARK, pole, border_radius=max(1, min(pole.width // 2, 4)))
        for index, ball in enumerate(state[peg]):
            draw_ball(surface, (x, base.top - radius - index * radius * 2), ball, radius - 2)
        if cursor == peg:
            top = base.top - height - int(40 * scale) + math.sin(time * 6) * 4
            if held:
                draw_ball(surface, (x, top - radius), held, radius - 2)
            hand = [(x, top + int(20 * scale)), (x - int(16 * scale), top), (x + int(16 * scale), top)]
            pygame.draw.polygon(surface, ui.GOLD, hand)


# ---------------------------------------------------------------------------
# The stop-signal race (Level 2)
# ---------------------------------------------------------------------------

SS_RESPONSE_KEYS = {pygame.K_a: "left", pygame.K_LEFT: "left", pygame.K_d: "right", pygame.K_RIGHT: "right"}


class StopSignalScene(ExperimentScene):
    """
    Run the stop-signal task (see ``stop_signal_task``).

    Parameters
    ----------
    game : Game
        The running game.
    on_finish : callable
        Called as ``on_finish(passed, summary, results)``.
    settings : StopSignalSettings, optional
        Design and timing of the task.
    rng : random.Random or None, optional
        Random number generator for the trial order.
    show_tutorial : bool, optional
        If False, a short reminder replaces tutorial and practice.
    """

    TUTORIAL = (
        ("Race to the garage!", "A car appears. Press A if it points LEFT, D if it points RIGHT. As fast as you can!"),
        ("... unless you see STOP!", "Sometimes a STOP sign pops up just after the car. Then press NOTHING."),
        ("Don't wait for the sign!", "Always go fast. Stopping will sometimes fail - that is normal and part of the game."),
    )

    def __init__(self, game, on_finish, settings=StopSignalSettings(), rng=None, show_tutorial=True):
        super().__init__(game, on_finish, (20, 18, 52), (60, 30, 90))
        self.settings = settings
        self.rng = rng or random.Random()
        self.staircase = stop_signal_task.Staircase(settings.ssd_start, settings.ssd_step, settings.ssd_min, settings.ssd_max)
        self.phase = "tutorial" if show_tutorial else "reminder"
        self.block = "practice"
        self.trials = []
        self.trial_index = 0
        self.trial_phase = "fixation"
        self.trial_timer = 0.0
        self.target_onset = None
        self.ssd = None
        self.signal_shown = False
        self.last_result = None

    def passed(self):
        settings = self.settings
        return stop_signal_task.has_passed(self.summary, settings.pass_go_accuracy, settings.pass_stop_success)

    # ----- flow -----------------------------------------------------------

    def _start_block(self, block):
        settings = self.settings
        self.block = block
        n_trials = settings.n_practice_trials if block == "practice" else settings.n_test_trials
        self.trials = stop_signal_task.make_trials(n_trials, settings.stop_share, self.rng)
        self.trial_index = 0
        self._set_phase("trials")
        self._start_fixation()

    def _start_fixation(self):
        self.trial_phase = "fixation"
        self.trial_timer = self.settings.fixation_time
        self.target_onset = None
        self.signal_shown = False
        trial = self.trials[self.trial_index]
        self.ssd = self.staircase.value if trial.trial_type == "stop" else None

    def _record(self, response):
        trial = self.trials[self.trial_index]
        rt_ms = None if response is None else round((perf_counter() - self.target_onset) * 1000)
        if trial.trial_type == "go":
            correct = response == trial.direction
        else:
            correct = response is None
            self.staircase.update(stopped=correct)
        self.last_result = stop_signal_task.StopResult(
            block=self.block,
            trial=self.trial_index + 1,
            trial_type=trial.trial_type,
            direction=trial.direction,
            ssd_ms=None if self.ssd is None else round(self.ssd * 1000),
            response=response,
            correct=correct,
            rt_ms=rt_ms,
        )
        self.results.append(self.last_result)
        if trial.trial_type == "stop":
            self.game.audio.play("correct" if correct else "wrong")
        self.trial_phase = "feedback"
        settings = self.settings
        self.trial_timer = settings.practice_feedback_time if self.block == "practice" else settings.test_feedback_time

    def _next_trial(self):
        self.trial_index += 1
        if self.trial_index < len(self.trials):
            self._start_fixation()
        elif self.block == "practice":
            self._set_phase("practice_done")
        else:
            test = [r for r in self.results if r.block == "test"]
            self.summary = stop_signal_task.summarise(test, self.settings.response_deadline * 1000)
            self.game.save_task_results("stopsignal", self.results, stop_signal_task.COLUMNS)
            #debrief
            from ..analysis import trigger_live_task_debrief
            trigger_live_task_debrief("stopsignal", self.game.participant_id, self.game.screen)
            self._set_phase("results")

    # ----- scene interface ------------------------------------------------

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.summary = None
            self._close()
        elif self.phase == "trials":
            if self.trial_phase == "target" and event.key in SS_RESPONSE_KEYS and self.target_onset is not None:
                self._record(SS_RESPONSE_KEYS[event.key])
        elif self.phase_age >= INPUT_DELAY and event.key in CONFIRM_KEYS + (pygame.K_t,):
            self._menu_key(event.key)

    def _menu_key(self, key):
        if self.phase == "tutorial" and key in CONFIRM_KEYS:
            self.page += 1
            self.phase_age = 0.0
            if self.page >= len(self.TUTORIAL):
                self._start_block("practice")
        elif self.phase in ("practice_done", "reminder") and key in CONFIRM_KEYS:
            self._start_block("test")
        elif self.phase == "reminder" and key == pygame.K_t:
            self.page = 0
            self._set_phase("tutorial")
        elif self.phase == "results" and key in CONFIRM_KEYS:
            self._close()

    def update(self, dt):
        super().update(dt)
        if self.phase != "trials":
            return
        if self.trial_phase == "target":
            if self.target_onset is None:
                return  # the car has not been on screen yet
            elapsed = perf_counter() - self.target_onset
            if self.ssd is not None and not self.signal_shown and elapsed >= self.ssd:
                self.signal_shown = True
                self.game.audio.play("whistle")
            if elapsed >= self.settings.response_deadline:
                self._record(None)
            return
        self.trial_timer -= dt
        if self.trial_timer > 0:
            return
        if self.trial_phase == "fixation":
            self.trial_phase = "target"
        else:
            self._next_trial()

    # ----- drawing --------------------------------------------------------

    def _draw_backdrop(self, surface):
        for index in range(14):
            x = (index * 97 + 40) % SCREEN_WIDTH
            height = 120 + (index * 53) % 160
            building = pygame.Rect(x, ROAD_TOP - height, 80, height)
            pygame.draw.rect(surface, (40, 30, 80), building)
            for row in range(building.top + 12, building.bottom - 10, 24):
                for col in range(building.left + 10, building.right - 10, 22):
                    lit = (row * 7 + col * 3 + index) % 5 != 0
                    pygame.draw.rect(surface, (255, 220, 120) if lit else (60, 50, 100), (col, row, 10, 12))
        # Fade the city, so that the text in front of it stays readable.
        shade = pygame.Surface((SCREEN_WIDTH, ROAD_TOP), pygame.SRCALPHA)
        shade.fill((14, 10, 36, 170))
        surface.blit(shade, (0, 0))
        pygame.draw.rect(surface, (44, 44, 60), (0, ROAD_TOP, SCREEN_WIDTH, SCREEN_HEIGHT - ROAD_TOP))
        for x in range(0, SCREEN_WIDTH, 80):
            pygame.draw.rect(surface, (230, 220, 120), (x + int(self.time * 40) % 80, ROAD_TOP + 60, 40, 6))

    def _draw_example(self, surface, page):
        if page == 0:
            for index, direction in enumerate(("left", "right")):
                center = (SCREEN_WIDTH // 2 - 220 + index * 440, 380)
                draw_race_car(surface, center, direction, 150)
                ui.draw_text(surface, f"{direction.upper()}: press {'A' if direction == 'left' else 'D'}", (center[0], center[1] + 80), 32, ui.WHITE, "center", bold=True, shadow=True)
        elif page == 1:
            draw_race_car(surface, (SCREEN_WIDTH // 2 - 120, 400), "right", 150)
            draw_stop_sign(surface, (SCREEN_WIDTH // 2 + 140, 340), 64 + int(math.sin(self.time * 6) * 4))
            ui.draw_text(surface, "Hands off the keys!", (SCREEN_WIDTH // 2, 520), 34, ui.WHITE, "center", bold=True, shadow=True)
        else:
            lines = (
                f"1.  A '+' appears: get ready.",
                f"2.  The car: press A or D within {self.settings.response_deadline:g} seconds.",
                "3.  STOP sign: press nothing.",
                "The better you stop, the LATER the STOP sign comes - so expect mistakes.",
                f"First {self.settings.n_practice_trials} practice rounds, then {self.settings.n_test_trials} for real.",
            )
            for index, line in enumerate(lines):
                ui.draw_text(surface, line, (180, 260 + index * 48), 32, ui.WHITE, shadow=True)

    def _draw_tutorial(self, surface):
        title, text = self.TUTORIAL[self.page]
        self._draw_heading(surface, title, f"Signal Sam's Stop-Signal Race  -  {self.page + 1}/{len(self.TUTORIAL)}")
        ui.draw_paragraph(surface, text, (190, 150), 900, 32, centered=True)
        self._draw_example(surface, self.page)
        self._draw_prompt(surface, "SPACE to continue")

    def _draw_reminder(self, surface):
        self._draw_heading(surface, "Try again!")
        ui.draw_paragraph(surface, "Car LEFT: A.  Car RIGHT: D.  STOP sign: nothing. Go fast - don't wait for the sign!", (190, 170), 900, 34, centered=True)
        draw_race_car(surface, (SCREEN_WIDTH // 2 - 120, 400), "left", 140)
        draw_stop_sign(surface, (SCREEN_WIDTH // 2 + 140, 350), 56)
        self._draw_prompt(surface, "SPACE: start the race      T: tutorial and practice")

    def _draw_practice_done(self, surface):
        practice = [r for r in self.results if r.block == "practice"]
        go = [r for r in practice if r.trial_type == "go"]
        go_rts = [r.rt_ms for r in go if r.correct]
        slow = bool(go_rts) and sum(go_rts) / len(go_rts) > 750
        self._draw_heading(surface, "Practice done!")
        lines = [
            f"Cars right: {sum(r.correct for r in go)} of {len(go)}",
            f"Stops: {sum(r.correct for r in practice if r.trial_type == 'stop')} of {sum(r.trial_type == 'stop' for r in practice)}",
            "",
            "You were a bit slow - don't wait for the STOP sign!" if slow else "Keep it up: fast on cars, hands off on STOP.",
            f"Now {self.settings.n_test_trials} rounds for real.",
        ]
        self._draw_lines(surface, lines, 200, 36, 54)
        self._draw_prompt(surface, "SPACE to start the race")

    def _draw_trials(self, surface):
        label = "Practice" if self.block == "practice" else "Race"
        ui.draw_text(surface, f"{label}: round {self.trial_index + 1} of {len(self.trials)}", (40, 30), 30, ui.SOFT_BLUE)
        ui.draw_text(surface, "A = left     D = right     STOP = hands off", (SCREEN_WIDTH // 2, 676), 30, ui.SOFT_BLUE, "center")
        trial = self.trials[self.trial_index]
        if self.trial_phase == "fixation":
            ui.draw_text(surface, "+", CENTER, 90, ui.WHITE, "center", bold=True)
        elif self.trial_phase == "target":
            draw_race_car(surface, (CENTER[0], CENTER[1] + 40), trial.direction, 190)
            if self.target_onset is None:
                self.target_onset = perf_counter()
            if self.signal_shown:
                draw_stop_sign(surface, (CENTER[0], CENTER[1] - 150), 70)
        else:
            self._draw_feedback(surface, trial)

    def _draw_feedback(self, surface, trial):
        result = self.last_result
        if trial.trial_type == "stop":
            message, color = ("Stopped!", ui.GREEN) if result.correct else ("STOP means stop!", ui.RED)
        elif result.correct:
            message, color = "Vroom! Correct", ui.GREEN
        elif result.response is None:
            message, color = "Too slow!", ui.RED
        else:
            message, color = "Wrong way!", ui.RED
        if self.block == "practice":
            ui.draw_text(surface, message, CENTER, 64, color, "center", bold=True, shadow=True)
        else:
            pygame.draw.circle(surface, color, CENTER, 18)

    def _draw_results(self, surface):
        summary, settings = self.summary, self.settings
        passed = self.passed()
        self._draw_heading(surface, "Race won!" if passed else "Not quite...")
        color = ui.GREEN if passed else ui.RED
        line = f"Cars right: {summary.go_accuracy:.0%} (needed {settings.pass_go_accuracy:.0%})     Stops: {summary.stop_success:.0%}"
        ui.draw_text(surface, line, (SCREEN_WIDTH // 2, 150), 36, color, "center", bold=True)
        box = pygame.Rect(90, 190, SCREEN_WIDTH - 180, 420)
        ui.draw_panel(surface, box)
        ui.draw_text(surface, "The race in your head", (box.centerx, box.top + 20), 34, ui.GOLD, "midtop", bold=True)
        scale = 0.55  # pixels per millisecond
        left = box.left + 280
        go_rt, ssd, ssrt = summary.mean_go_rt_ms, summary.mean_ssd_ms, summary.ssrt_ms
        rows = [("GO runner", 0, go_rt, (90, 200, 255), "your average reaction")]
        if ssd is not None and ssrt is not None:
            rows.append(("STOP runner", ssd, ssrt, (240, 80, 90), "starts at the STOP sign"))
        for index, (label, start, length, bar_color, note) in enumerate(rows):
            y = box.top + 100 + index * 90
            ui.draw_text(surface, label, (box.left + 40, y), 34, bar_color, bold=True)
            if length is None:
                ui.draw_text(surface, "-", (left, y), 34)
                continue
            bar = pygame.Rect(left + start * scale, y - 4, max(4, length * scale), 34)
            pygame.draw.rect(surface, bar_color, bar, border_radius=10)
            ui.draw_text(surface, f"{length:.0f} ms", (bar.right + 12, y), 30, ui.WHITE, bold=True)
            ui.draw_text(surface, note, (box.left + 40, y + 36), 22, ui.SOFT_BLUE)
            if start:
                pygame.draw.line(surface, ui.WHITE, (left, y + 15), (bar.left, y + 15), 2)
                draw_stop_sign(surface, (bar.left, y - 18), 16)
        pygame.draw.line(surface, ui.WHITE, (left, box.top + 80), (left, box.top + 270), 2)
        ui.draw_text(surface, "car appears", (left, box.top + 276), 22, ui.SOFT_BLUE, "midtop")
        if ssrt is not None:
            text = (
                f"Your stopping process (SSRT) took about {ssrt:.0f} ms. Whichever runner finishes "
                "first wins: if STOP is faster than GO, the action is cancelled."
            )
        else:
            text = "Without stop rounds there is no stopping time to show."
        ui.draw_paragraph(surface, text, (box.left + 40, box.bottom - 110), box.width - 80, 28)
        self._draw_prompt(surface, "SPACE to continue")


# ---------------------------------------------------------------------------
# The Memory Machine's n-back task (Level 3)
# ---------------------------------------------------------------------------

MONITOR = pygame.Rect(0, 0, 300, 240)
MONITOR.center = (SCREEN_WIDTH // 2, 340)
EXAMPLE = ("K", "B", "K", "D", "B", "D")


class NBackScene(ExperimentScene):
    """
    Run the n-back task (see ``nback_task``).

    Parameters
    ----------
    game : Game
        The running game.
    on_finish : callable
        Called as ``on_finish(passed, summary, results)``.
    settings : NBackSettings, optional
        Design and timing of the task.
    rng : random.Random or None, optional
        Random number generator for the letter sequences.
    show_tutorial : bool, optional
        If False, a short reminder replaces tutorial and practice.
    """

    def __init__(self, game, on_finish, settings=NBackSettings(), rng=None, show_tutorial=True):
        super().__init__(game, on_finish, (30, 46, 50), (14, 20, 26))
        self.settings = settings
        self.rng = rng or random.Random()
        self.phase = "tutorial" if show_tutorial else "reminder"
        self.block = "practice"
        self.sequence = []
        self.trial_index = 0
        self.trial_phase = "blank"
        self.trial_timer = 0.0
        self.onset = None
        self.response_rt = None
        self.last_result = None

    @property
    def tutorial(self):
        """Pages of the tutorial: title and text."""
        n = self.settings.n
        steps = "ONE letter" if n == 1 else f"{n} letters"
        return (
            ("Feed the Memory Machine!", f"Letters appear one by one. Press SPACE when a letter is the same as the one {steps} before."),
            ("Example", f"Watch the arrows: a letter that matches the one {steps} back is a hit. Otherwise press nothing."),
            ("Keep updating!", "With every new letter, forget the oldest one. That updating is what working memory does."),
        )

    def passed(self):
        return nback_task.has_passed(self.summary, self.settings.pass_accuracy, self.settings.pass_hit_rate)

    def _start_block(self, block):
        settings = self.settings
        self.block = block
        if block == "practice":
            self.sequence = nback_task.make_sequence(settings.n, settings.n_practice_trials, settings.n_practice_targets, settings.letters, self.rng)
        else:
            self.sequence = nback_task.make_sequence(settings.n, settings.n_test_trials, settings.n_test_targets, settings.letters, self.rng)
        self.trial_index = 0
        self._set_phase("trials")
        self._start_trial()

    def _start_trial(self):
        self.trial_phase = "letter"
        self.trial_timer = self.settings.stimulus_time
        self.onset = None
        self.response_rt = None

    def _record(self):
        letter, is_target = self.sequence[self.trial_index]
        responded = self.response_rt is not None
        self.last_result = nback_task.NBackResult(
            block=self.block,
            n=self.settings.n,
            trial=self.trial_index + 1,
            letter=letter,
            is_target=is_target,
            responded=responded,
            correct=responded == is_target,
            rt_ms=self.response_rt,
        )
        self.results.append(self.last_result)
        if self.block == "practice":
            self.trial_phase = "feedback"
            self.trial_timer = self.settings.practice_feedback_time
        else:
            self._next_trial()

    def _next_trial(self):
        self.trial_index += 1
        if self.trial_index < len(self.sequence):
            self._start_trial()
        elif self.block == "practice":
            self._set_phase("practice_done")
        else:
            self.summary = nback_task.summarise([r for r in self.results if r.block == "test"])
            self.game.save_task_results("nback", self.results, nback_task.COLUMNS)
            #debrief
            from ..analysis import trigger_live_task_debrief
            trigger_live_task_debrief("nback", self.game.participant_id, self.game.screen)
            #media footprint
            trigger_live_task_debrief("media_impact", self.game.participant_id, self.game.screen)
            self._set_phase("results")

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.summary = None
            self._close()
        elif self.phase == "trials":
            if event.key == pygame.K_SPACE and self.trial_phase in ("letter", "blank") and self.onset is not None and self.response_rt is None:
                self.response_rt = round((perf_counter() - self.onset) * 1000)
                self.game.audio.play("select")
        elif self.phase_age >= INPUT_DELAY and event.key in CONFIRM_KEYS + (pygame.K_t,):
            if self.phase == "tutorial" and event.key in CONFIRM_KEYS:
                self.page += 1
                self.phase_age = 0.0
                if self.page >= len(self.tutorial):
                    self._start_block("practice")
            elif self.phase in ("practice_done", "reminder") and event.key in CONFIRM_KEYS:
                self._start_block("test")
            elif self.phase == "reminder" and event.key == pygame.K_t:
                self.page = 0
                self._set_phase("tutorial")
            elif self.phase == "results" and event.key in CONFIRM_KEYS:
                self._close()

    def update(self, dt):
        super().update(dt)
        if self.phase != "trials" or (self.trial_phase == "letter" and self.onset is None):
            return
        self.trial_timer -= dt
        if self.trial_timer > 0:
            return
        if self.trial_phase == "letter":
            self.trial_phase = "blank"
            self.trial_timer = self.settings.blank_time
        elif self.trial_phase == "blank":
            self._record()
        else:
            self._next_trial()

    def _draw_backdrop(self, surface):
        for index in range(6):
            x = 80 + index * 230
            angle = self.time * (0.8 if index % 2 else -0.8)
            center = (x, 640)
            for tooth in range(8):
                a = angle + tooth * math.pi / 4
                pygame.draw.circle(surface, (60, 70, 76), (center[0] + math.cos(a) * 60, center[1] + math.sin(a) * 60), 16)
            pygame.draw.circle(surface, (70, 80, 86), center, 56)
            pygame.draw.circle(surface, (40, 46, 50), center, 18)

    def _draw_example_strip(self, surface):
        n = self.settings.n
        sequence = EXAMPLE if n == 2 else EXAMPLE[:4]
        shown = min(len(sequence), int(self.phase_age / 0.8) + 1)
        for index, letter in enumerate(sequence[:shown]):
            x = SCREEN_WIDTH // 2 + (index - (len(sequence) - 1) / 2) * 120
            target = index >= n and sequence[index - n] == letter
            box = pygame.Rect(0, 0, 90, 90)
            box.center = (x, 380)
            draw_monitor(surface, box, letter, ui.GREEN if target else None)
            if target:
                start = SCREEN_WIDTH // 2 + (index - n - (len(sequence) - 1) / 2) * 120
                pygame.draw.arc(surface, ui.GREEN, (start, 270, x - start, 90), 0.3, math.pi - 0.3, 4)
                ui.draw_text(surface, "SPACE!", (x, 460), 30, ui.GREEN, "midtop", bold=True)

    def _draw_tutorial(self, surface):
        title, text = self.tutorial[self.page]
        self._draw_heading(surface, title, f"The Memory Machine ({self.settings.n}-back)  -  {self.page + 1}/{len(self.tutorial)}")
        ui.draw_paragraph(surface, text, (190, 150), 900, 32, centered=True)
        if self.page == 1:
            self._draw_example_strip(surface)
        else:
            draw_monitor(surface, MONITOR, "K" if self.page == 0 else "?")
        self._draw_prompt(surface, "SPACE to continue")

    def _draw_reminder(self, surface):
        self._draw_heading(surface, "Try again!")
        text = f"Press SPACE when the letter matches the one {self.settings.n} back. You need {self.settings.pass_accuracy:.0%} correct and half of the matches."
        ui.draw_paragraph(surface, text, (190, 170), 900, 34, centered=True)
        self._draw_example_strip(surface)
        self._draw_prompt(surface, "SPACE: start      T: tutorial and practice")

    def _draw_practice_done(self, surface):
        practice = [r for r in self.results if r.block == "practice"]
        self._draw_heading(surface, "Practice done!")
        lines = (
            f"You were right on {sum(r.correct for r in practice)} of {len(practice)} letters.",
            "",
            f"Now {self.settings.n_test_trials} letters, without feedback.",
            f"You need {self.settings.pass_accuracy:.0%} correct and must catch half of the matches.",
        )
        self._draw_lines(surface, lines, 220, 36, 54)
        self._draw_prompt(surface, "SPACE to start")

    def _draw_trials(self, surface):
        label = "Practice" if self.block == "practice" else "Test"
        ui.draw_text(surface, f"{label}: letter {self.trial_index + 1} of {len(self.sequence)}", (40, 30), 30, ui.SOFT_BLUE)
        ui.draw_text(surface, f"SPACE = same as {self.settings.n} back", (SCREEN_WIDTH // 2, 676), 30, ui.SOFT_BLUE, "center")
        letter, is_target = self.sequence[self.trial_index]
        glow = ui.GOLD if self.response_rt is not None and self.trial_phase != "feedback" else None
        if self.trial_phase == "letter":
            draw_monitor(surface, MONITOR, letter, glow)
            if self.onset is None:
                self.onset = perf_counter()
        elif self.trial_phase == "blank":
            draw_monitor(surface, MONITOR, "", glow)
        else:
            result = self.last_result
            draw_monitor(surface, MONITOR, letter, ui.GREEN if result.correct else ui.RED)
            if result.correct:
                message = "Hit!" if is_target else "Right - no match."
            else:
                message = "That was a match!" if is_target else f"No match: {self.settings.n} back was different."
            ui.draw_text(surface, message, (SCREEN_WIDTH // 2, 520), 40, ui.GREEN if result.correct else ui.RED, "center", bold=True, shadow=True)

    def _draw_results(self, surface):
        summary, settings = self.summary, self.settings
        passed = self.passed()
        self._draw_heading(surface, "Memory Machine powered up!" if passed else "Not quite...")
        color = ui.GREEN if passed else ui.RED
        ui.draw_text(surface, f"Correct: {summary.accuracy:.0%} (need {settings.pass_accuracy:.0%})   Matches caught: {summary.hit_rate:.0%} (need {settings.pass_hit_rate:.0%})", (SCREEN_WIDTH // 2, 150), 32, color, "center", bold=True)
        bars = [
            ("Hits (matches you caught)", summary.hit_rate * 100, ui.GREEN),
            ("False alarms (wrong presses)", summary.false_alarm_rate * 100, ui.RED),
        ]
        ui.draw_bar_chart(surface, pygame.Rect(120, 200, 520, 430), bars, "Your answers", "%")
        box = pygame.Rect(680, 200, 480, 430)
        ui.draw_panel(surface, box)
        ui.draw_text(surface, "Your sensitivity d':", (box.centerx, box.top + 24), 30, ui.SOFT_BLUE, "midtop")
        ui.draw_text(surface, f"{summary.d_prime:.2f}", (box.centerx, box.top + 60), 60, ui.GOLD, "midtop", bold=True)
        text = (
            "d' compares hits with false alarms: 0 means guessing, higher values mean you told "
            "matches apart from other letters. Holding and updating letters is working memory at work."
        )
        ui.draw_paragraph(surface, text, (box.left + 24, box.top + 140), box.width - 48, 27)
        self._draw_prompt(surface, "SPACE to continue")


# ---------------------------------------------------------------------------
# The Tower of London puzzle gate (Level 3)
# ---------------------------------------------------------------------------


class TowerScene(ExperimentScene):
    """
    Solve Tower of London puzzles (see ``tower_task``).

    A/D moves the hand, SPACE lifts or drops a ball, R starts the current
    puzzle over. Every puzzle has to be solved; with too many moves it
    starts over by itself.

    Parameters
    ----------
    game : Game
        The running game.
    on_finish : callable
        Called as ``on_finish(passed, summary, results)``; ``summary`` is a
        list of ``TowerResult`` (one per puzzle).
    settings : TowerSettings, optional
        The puzzles to play.
    rng : random.Random or None, optional
        Random number generator for the choice of puzzles.
    """

    def __init__(self, game, on_finish, settings=TowerSettings(), rng=None):
        super().__init__(game, on_finish, (40, 30, 70), (16, 14, 36))
        self.settings = settings
        self.problems = tower_task.make_problems(settings.problem_moves, rng or random.Random())
        self.problem_index = 0
        self.message = ""
        self._reset_problem(new=True)

    def passed(self):
        return all(result.solved for result in self.summary)

    def _reset_problem(self, new=False):
        problem = self.problems[self.problem_index]
        self.state = problem.start
        self.cursor = 0
        self.held = None
        self.held_from = None
        self.moves = 0
        if new:
            self.problem_start = None
            self.first_move = None

    def _finish_problem(self):
        problem = self.problems[self.problem_index]
        now = perf_counter()
        self.results.append(
            tower_task.TowerResult(
                problem=self.problem_index + 1,
                min_moves=problem.min_moves,
                moves=self.moves,
                solved=True,
                planning_time_ms=round((self.first_move - self.problem_start) * 1000),
                solution_time_ms=round((now - self.problem_start) * 1000),
            )
        )
        self.game.audio.play("correct")
        self._set_phase("solved")

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.summary = None
            self._close()
            return
        if self.phase_age < INPUT_DELAY and self.phase != "puzzle":
            return
        if self.phase == "tutorial" and event.key in CONFIRM_KEYS:
            self._set_phase("puzzle")
        elif self.phase == "puzzle":
            self._puzzle_key(event.key)
        elif self.phase == "solved" and event.key in CONFIRM_KEYS:
            self.problem_index += 1
            if self.problem_index < len(self.problems):
                self._reset_problem(new=True)
                self._set_phase("puzzle")
            else:
                self.summary = list(self.results)
                self.game.save_task_results("tower", self.results, tower_task.COLUMNS)
                #debrief
                self.game.save_task_results("tower", self.results, tower_task.COLUMNS)
                from ..analysis import trigger_live_task_debrief
                trigger_live_task_debrief("tower", self.game.participant_id, self.game.screen)
                self._set_phase("results")
        elif self.phase == "results" and event.key in CONFIRM_KEYS:
            self._close()

    def _puzzle_key(self, key):
        if self.problem_start is None:
            self.problem_start = perf_counter()
        if key in LEFT_KEYS:
            self.cursor = max(0, self.cursor - 1)
        elif key in RIGHT_KEYS:
            self.cursor = min(2, self.cursor + 1)
        elif key == pygame.K_r:
            self._reset_problem()
            self.message = "Back to the start."
        elif key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_s, pygame.K_w):
            self._lift_or_drop()

    def _lift_or_drop(self):
        state = self.state
        if self.held is None:
            if not state[self.cursor]:
                self.message = "This peg is empty."
                return
            if self.first_move is None:
                self.first_move = perf_counter()
            pegs = [list(peg) for peg in state]
            self.held, self.held_from = pegs[self.cursor].pop(), self.cursor
            self.state = tuple(tuple(peg) for peg in pegs)
            self.message = ""
            self.game.audio.play("select")
            return
        if len(state[self.cursor]) >= tower_task.CAPACITIES[self.cursor]:
            self.message = "This peg is full."
            self.game.audio.play("wrong")
            return
        pegs = [list(peg) for peg in state]
        pegs[self.cursor].append(self.held)
        self.state = tuple(tuple(peg) for peg in pegs)
        if self.cursor != self.held_from:
            self.moves += 1
        self.held = self.held_from = None
        self.game.audio.play("jump")
        problem = self.problems[self.problem_index]
        if self.state == problem.goal:
            self._finish_problem()
        elif self.moves >= problem.min_moves + self.settings.max_extra_moves:
            self._reset_problem()
            self.message = "Too many moves - the puzzle starts over. Plan first!"
            self.game.audio.play("wrong")

    def update(self, dt):
        super().update(dt)
        if self.phase == "puzzle" and self.problem_start is None:
            self.problem_start = perf_counter()

    def _draw_goal(self, surface, goal):
        box = pygame.Rect(SCREEN_WIDTH - 330, 150, 290, 190)
        ui.draw_panel(surface, box)
        ui.draw_text(surface, "GOAL", (box.centerx, box.top + 12), 30, ui.GOLD, "midtop", bold=True)
        draw_tower(surface, goal, (box.centerx, box.bottom - 30), scale=0.35)

    def _draw_tutorial(self, surface):
        self._draw_heading(surface, "The Tower of London", "A planning puzzle gate")
        text = "Rebuild the GOAL picture in as few moves as possible. Take one ball at a time from the top. The pegs hold 3, 2 and 1 ball. Plan all moves BEFORE you start!"
        ui.draw_paragraph(surface, text, (190, 150), 900, 32, centered=True)
        draw_tower(surface, tower_task.START, (SCREEN_WIDTH // 2, 560), scale=0.8, cursor=int(self.time) % 3, time=self.time)
        self._draw_prompt(surface, "A/D: move hand    SPACE: lift / drop    R: restart      SPACE to begin")

    def _draw_puzzle(self, surface):
        problem = self.problems[self.problem_index]
        self._draw_heading(surface, f"Puzzle {self.problem_index + 1} of {len(self.problems)}", f"Possible in {problem.min_moves} moves")
        self._draw_goal(surface, problem.goal)
        draw_tower(surface, self.state, (SCREEN_WIDTH // 2 - 120, 580), scale=0.9, cursor=self.cursor, held=self.held, time=self.time)
        ui.draw_text(surface, f"Moves: {self.moves}", (60, 170), 40, ui.WHITE, bold=True, shadow=True)
        thinking = self.first_move is None and self.problem_start is not None
        if thinking:
            ui.draw_text(surface, f"Planning... {perf_counter() - self.problem_start:.0f} s", (60, 220), 30, ui.SOFT_BLUE)
        if self.message:
            ui.draw_text(surface, self.message, (60, 270), 30, ui.RED)
        ui.draw_text(surface, "A/D: move hand    SPACE: lift / drop    R: restart", (SCREEN_WIDTH // 2, 676), 30, ui.SOFT_BLUE, "center")

    def _draw_solved(self, surface):
        result = self.results[-1]
        perfect = result.moves == result.min_moves
        self._draw_heading(surface, "Perfect plan!" if perfect else "Solved!")
        lines = (
            f"Moves: {result.moves}  (best possible: {result.min_moves})",
            f"Thinking before the first move: {result.planning_time_ms / 1000:.1f} s",
        )
        self._draw_lines(surface, lines, 200, 36, 54)
        draw_tower(surface, self.state, (SCREEN_WIDTH // 2, 560), scale=0.8)
        self._draw_prompt(surface, "SPACE to continue")

    def _draw_results(self, surface):
        self._draw_heading(surface, "Gate unlocked!")
        bars = [(f"Puzzle {r.problem}: {r.moves} moves (best {r.min_moves})", r.planning_time_ms / 1000, ui.SOFT_BLUE) for r in self.results]
        ui.draw_bar_chart(surface, pygame.Rect(120, 160, 620, 470), bars, "Thinking time before your first move", "s")
        box = pygame.Rect(780, 160, 380, 470)
        ui.draw_panel(surface, box)
        text = (
            "Thinking the moves through BEFORE touching a ball usually saves moves. "
            "Harder puzzles need more of this planning time."
        )
        ui.draw_paragraph(surface, text, (box.left + 24, box.top + 30), box.width - 48, 30)
        self._draw_prompt(surface, "SPACE to continue")


def easier(settings, difficulty_key):
    """Lower the pass marks of an experiment's settings in Easy mode."""
    if difficulty_key != "easy":
        return settings
    if isinstance(settings, StopSignalSettings):
        return replace(settings, pass_go_accuracy=0.7, pass_stop_success=0.15)
    if isinstance(settings, NBackSettings):
        return replace(settings, pass_accuracy=0.7)
    return settings
