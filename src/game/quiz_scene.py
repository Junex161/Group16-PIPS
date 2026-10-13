"""The owl's multiple-choice question at the gate."""

import pygame

from . import ui
from .config import SCREEN_HEIGHT, SCREEN_WIDTH
from .scenes import INPUT_DELAY, Scene

NUMBER_KEYS = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6)


class QuizScene(Scene):
    """
    Ask one multiple-choice question.

    Parameters
    ----------
    game : Game
        The running game.
    question : Question
        The question to ask (see ``content.py``).
    on_finish : callable
        Called as ``on_finish(correct)`` after the player read the feedback.
    """

    is_overlay = True

    def __init__(self, game, question, on_finish):
        super().__init__(game)
        self.question = question
        self.on_finish = on_finish
        self.selected = 0
        self.answer = None
        self.age = 0.0

    @property
    def is_correct(self):
        """True if the chosen answer is the right one."""
        return self.answer == self.question.correct_index

    def update(self, dt):
        self.age += dt

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or self.age < INPUT_DELAY:
            return
        n_options = len(self.question.options)
        confirm = event.key in (pygame.K_SPACE, pygame.K_RETURN)
        if self.answer is not None:
            if confirm:
                self.game.pop_scene()
                self.on_finish(self.is_correct)
        elif event.key in (pygame.K_w, pygame.K_UP):
            self.selected = (self.selected - 1) % n_options
        elif event.key in (pygame.K_s, pygame.K_DOWN):
            self.selected = (self.selected + 1) % n_options
        elif event.key in NUMBER_KEYS[:n_options]:
            self._answer(NUMBER_KEYS.index(event.key))
        elif confirm:
            self._answer(self.selected)

    def _answer(self, index):
        self.selected = self.answer = index
        self.age = 0.0

    def draw(self, surface):
        ui.dim(surface)
        box = pygame.Rect(140, 50, SCREEN_WIDTH - 280, SCREEN_HEIGHT - 100)
        ui.draw_panel(surface, box)
        ui.draw_text(surface, "The owl asks:", (box.left + 40, box.top + 28), 34, ui.SOFT_BLUE)
        y = ui.draw_paragraph(surface, self.question.prompt, (box.left + 40, box.top + 70), box.width - 80, 38, ui.GOLD)
        y += 16
        for index, option in enumerate(self.question.options):
            row = pygame.Rect(box.left + 40, y, box.width - 80, 62)
            color, fill = ui.WHITE, (44, 54, 100, 255)
            if self.answer is None and index == self.selected:
                fill = (70, 90, 170, 255)
            if self.answer is not None and index == self.question.correct_index:
                fill, color = (40, 120, 70, 255), ui.GREEN
            elif self.answer == index:
                fill, color = (130, 50, 60, 255), ui.RED
            ui.draw_panel(surface, row, fill=fill, border=color, radius=12)
            ui.draw_text(surface, f"{index + 1}.  {option}", (row.left + 20, row.centery), 30, color, "midleft")
            y += 74
        if self.answer is None:
            hint = "W/S: choose      SPACE: answer      (or press 1-4)"
            ui.draw_text(surface, hint, (box.centerx, box.bottom - 40), 28, ui.SOFT_BLUE, "center")
            return
        verdict = "Correct!" if self.is_correct else "That is not right."
        ui.draw_text(surface, verdict, (box.left + 40, y + 4), 36, ui.GREEN if self.is_correct else ui.RED, bold=True)
        ui.draw_text(surface, self.question.explanation, (box.left + 40, y + 44), 28)
        if self.age >= INPUT_DELAY:
            ui.draw_text(surface, "SPACE to continue", (box.right - 40, box.bottom - 50), 28, ui.GOLD, "topright")
