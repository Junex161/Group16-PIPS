"""A short questionnaire at the start of the game.

It asks about leisure screen time, short-video use, interest in psychology,
gaming and current alertness, so that the analysis can relate screen habits
to the performance in the experiments while controlling for gaming
experience and fatigue. The answers are saved as one row in
``data/questionnaire_<participant>_<timestamp>_attempt-<n>.csv``.

Answers are given with A/D (or the arrow keys) and SPACE; ESC skips the
questionnaire, and nothing is saved then.
"""

from dataclasses import dataclass

import pygame

from . import graphics, ui
from .config import SCREEN_HEIGHT, SCREEN_WIDTH
from .scenes import INPUT_DELAY, Scene

COLUMNS = (
    "participant_id",
    "attempt",
    "screen_time_hours",
    "short_video_frequency",
    "psychology_interest",
    "gaming_frequency",
    "alertness",
)


@dataclass(frozen=True)
class Question:
    """
    One question.

    ``labels`` are the five answers of a 1-5 rating scale; a question
    without labels asks for a number between ``minimum`` and ``maximum`` in
    steps of ``step``.
    """

    column: str
    text: str
    labels: tuple = ()
    minimum: float = 1
    maximum: float = 5
    step: float = 1
    start: float = 3
    unit: str = ""


QUESTIONS = (
    Question("screen_time_hours", "On a typical day, how many hours do you spend on screens in your free time?", minimum=0, maximum=16, step=0.5, start=3, unit="hours"),
    Question("short_video_frequency", "How often do you watch short videos (TikTok, Reels, Shorts)?", ("Never", "Rarely", "Weekly", "Daily", "Several times a day")),
    Question("psychology_interest", "How interested are you in psychology?", ("Not at all", "A little", "Somewhat", "Quite", "Very much")),
    Question("gaming_frequency", "How often do you play video games?", ("Never", "Rarely", "Monthly", "Weekly", "Daily")),
    Question("alertness", "How awake and alert do you feel right now?", ("Very tired", "Tired", "OK", "Alert", "Very alert")),
)
LEFT_KEYS = (pygame.K_a, pygame.K_LEFT)
RIGHT_KEYS = (pygame.K_d, pygame.K_RIGHT)
CONFIRM_KEYS = (pygame.K_SPACE, pygame.K_RETURN)
BACK_KEYS = (pygame.K_w, pygame.K_UP, pygame.K_BACKSPACE)


class QuestionnaireScene(Scene):
    """
    Ask the questions one by one and save the answers.

    Parameters
    ----------
    game : Game
        The running game.
    on_finish : callable
        Called without arguments when the questionnaire is done or skipped.
    questions : sequence of Question, optional
        The questions to ask.
    """

    def __init__(self, game, on_finish, questions=QUESTIONS):
        super().__init__(game)
        self.on_finish = on_finish
        self.questions = tuple(questions)
        self.answers = [question.start for question in self.questions]
        self.index = 0
        self.age = 0.0
        self.background = graphics.vertical_gradient((SCREEN_WIDTH, SCREEN_HEIGHT), (30, 40, 80), (10, 12, 30))

    def update(self, dt):
        self.age += dt
        self.game.audio.play_music("title")

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or self.age < INPUT_DELAY:
            return
        question = self.questions[self.index]
        if event.key in LEFT_KEYS + RIGHT_KEYS:
            change = question.step if event.key in RIGHT_KEYS else -question.step
            self.answers[self.index] = min(question.maximum, max(question.minimum, self.answers[self.index] + change))
            self.game.audio.play("select")
        elif event.key in BACK_KEYS and self.index > 0:
            self.index -= 1
        elif event.key in CONFIRM_KEYS:
            self.game.audio.play("correct")
            self.index += 1
            self.age = 0.0
            if self.index >= len(self.questions):
                self._save()
                self._finish()
        elif event.key == pygame.K_ESCAPE:
            self._finish()

    def _save(self):
        row = {question.column: answer for question, answer in zip(self.questions, self.answers)}
        self.game.save_task_results("questionnaire", [row], COLUMNS)
        self.game.questionnaire_answers = row

    def _finish(self):
        self.game.questionnaire_done = True
        self.on_finish()

    def draw(self, surface):
        surface.blit(self.background, (0, 0))
        center_x = SCREEN_WIDTH // 2
        ui.draw_text(surface, "Before we start ...", (center_x, 70), 56, ui.GOLD, "center", bold=True, shadow=True)
        ui.draw_text(surface, f"Question {self.index + 1} of {len(self.questions)}", (center_x, 122), 30, ui.SOFT_BLUE, "center")
        question, answer = self.questions[self.index], self.answers[self.index]
        ui.draw_paragraph(surface, question.text, (190, 190), 900, 40, centered=True)
        if question.labels:
            self._draw_scale(surface, question, answer)
        else:
            self._draw_number(surface, question, answer)
        ui.draw_text(surface, "A/D: choose    SPACE: next    W: back    ESC: skip", (center_x, 640), 30, ui.SOFT_BLUE, "center")
        ui.draw_text(surface, "Your answers are saved anonymously with your participant number.", (center_x, 684), 24, (150, 160, 200), "center")

    def _draw_scale(self, surface, question, answer):
        width = 210
        for index, label in enumerate(question.labels):
            value = index + 1
            box = pygame.Rect(0, 0, width - 14, 110)
            box.center = (SCREEN_WIDTH // 2 + (index - 2) * width, 420)
            chosen = value == answer
            ui.draw_panel(surface, box, fill=(60, 70, 130, 240) if chosen else (22, 28, 60, 235), border=ui.GOLD if chosen else (90, 96, 140))
            ui.draw_text(surface, str(value), (box.centerx, box.top + 14), 40, ui.GOLD if chosen else ui.WHITE, "midtop", bold=True)
            for line_number, line in enumerate(ui.wrap_text(label, ui.get_font(24), box.width - 16)):
                ui.draw_text(surface, line, (box.centerx, box.top + 60 + line_number * 22), 24, ui.WHITE, "midtop")

    def _draw_number(self, surface, question, answer):
        bar = pygame.Rect(0, 0, 760, 16)
        bar.center = (SCREEN_WIDTH // 2, 470)
        pygame.draw.rect(surface, (60, 66, 110), bar, border_radius=8)
        share = (answer - question.minimum) / (question.maximum - question.minimum)
        pygame.draw.rect(surface, ui.GOLD, (bar.x, bar.y, int(bar.width * share), bar.height), border_radius=8)
        pygame.draw.circle(surface, ui.WHITE, (bar.x + bar.width * share, bar.centery), 16)
        ui.draw_text(surface, f"{answer:g} {question.unit}", (SCREEN_WIDTH // 2, 380), 64, ui.GOLD, "center", bold=True)
        ui.draw_text(surface, f"{question.minimum:g}", (bar.left, bar.bottom + 14), 26, ui.SOFT_BLUE, "midtop")
        ui.draw_text(surface, f"{question.maximum:g}", (bar.right, bar.bottom + 14), 26, ui.SOFT_BLUE, "midtop")
