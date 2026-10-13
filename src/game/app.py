"""The game window, the main loop and the public ``run_game`` function."""

import random
import uuid

import pygame

from . import ui
from .audio import SAMPLE_RATE, Audio
from .characters import CHARACTERS
from .config import (
    DATA_DIR,
    DEFAULT_DIFFICULTY,
    FPS,
    GAME_TITLE,
    MAX_FRAME_TIME,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    FlankerSettings,
    PlayerSettings,
)
from .flanker_task import clean_participant_id, save_results


class Game:
    """
    The running game: owns the window and a stack of scenes.

    Parameters
    ----------
    participant_id : str or None, optional
        Anonymous label for the flanker data. A random one is made if None.
    data_dir : str or Path, optional
        Folder in which flanker data files are saved.
    seed : int or None, optional
        Random seed for reproducible trial orders and quiz questions.
    player_settings : PlayerSettings, optional
        Physics and health settings of the player.
    flanker_settings : FlankerSettings, optional
        Design and timing of the flanker task.
    allow_admin : bool, optional
        If True, P (or F1) switches the admin mode for testing on and off.
    """

    def __init__(self, participant_id=None, data_dir=DATA_DIR, seed=None, player_settings=PlayerSettings(), flanker_settings=FlankerSettings(), allow_admin=True):
        self.allow_admin = allow_admin
        self.participant_id = clean_participant_id(participant_id or f"p-{uuid.uuid4().hex[:6]}")
        self.data_dir = data_dir
        self.rng = random.Random(seed)
        self.player_settings = player_settings
        self.flanker_settings = flanker_settings
        self.saved_files = []
        self.flanker_attempts = 0
        self.flanker_tutorial_seen = False
        self.scenes = []
        self.running = False

        self.character = CHARACTERS[0]
        self.difficulty = DEFAULT_DIFFICULTY

        pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512)
        pygame.init()
        self.audio = Audio()
        ui.clear_font_cache()  # fonts of an earlier run are no longer valid
        try:
            # SCALED lets the window grow on large or high-resolution screens.
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED | pygame.RESIZABLE)
        except pygame.error:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()

    # ----- scenes ---------------------------------------------------------

    def push_scene(self, scene):
        """Put a scene on top; it receives all input until it is popped."""
        self.scenes.append(scene)

    def pop_scene(self):
        """Close the top scene and resume the one below."""
        self.scenes.pop()
        if self.scenes:
            self.scenes[-1].on_resume()

    def start_level(self):
        """Start Level 1 from the very beginning."""
        from .play_scene import PlayScene

        self.scenes = [PlayScene(self)]

    def show_home(self):
        """Leave the current level, if any, and show the home screen."""
        from .menu_scenes import HomeScene

        self.scenes = [HomeScene(self)]

    def quit(self):
        """Stop the main loop after the current frame."""
        self.running = False

    def save_flanker_results(self, results):
        """Save one flanker attempt to ``data_dir`` and remember the file."""
        self.flanker_attempts += 1
        path = save_results(results, self.participant_id, self.flanker_attempts, self.data_dir)
        self.saved_files.append(path)
        return path

    # ----- main loop ------------------------------------------------------

    def run(self, max_frames=None):
        """
        Run the game until the window is closed.

        Parameters
        ----------
        max_frames : int or None, optional
            Stop after this many frames; used by automated tests.
        """
        from .scenes import TitleScene

        if not self.scenes:
            self.scenes = [TitleScene(self)]
        self.running = True
        frame = 0
        while self.running and (max_frames is None or frame < max_frames):
            dt = min(self.clock.tick(FPS) / 1000, MAX_FRAME_TIME)
            self.step(dt)
            frame += 1

    def step(self, dt):
        """Process input, update the top scene and draw one frame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                self.audio.toggle_mute()
            else:
                self.scenes[-1].handle_event(event)
        for scene in self.scenes[:-1]:
            scene.update_in_background(dt)
        self.scenes[-1].update(dt)
        self.draw()
        pygame.display.flip()

    def draw(self):
        """Draw the top scene and, below overlays, the scenes underneath."""
        first = len(self.scenes) - 1
        while first > 0 and self.scenes[first].is_overlay:
            first -= 1
        for scene in self.scenes[first:]:
            scene.draw(self.screen)


def run_game(participant_id=None, data_dir=DATA_DIR, seed=None, player_settings=PlayerSettings(), flanker_settings=FlankerSettings(), allow_admin=True):
    """
    Open the game window and play until the player quits.

    Parameters
    ----------
    participant_id : str or None, optional
        Anonymous label used in the flanker data and its file names.
        A random label such as "p-3fa2c1" is created if None.
    data_dir : str or Path, optional
        Folder for the flanker data; defaults to the project's ``data`` folder.
    seed : int or None, optional
        Random seed for reproducible trial orders.
    player_settings : PlayerSettings, optional
        Physics and health settings of the player.
    flanker_settings : FlankerSettings, optional
        Design and timing of the flanker task.
    allow_admin : bool, optional
        If True, P (or F1) switches the admin mode on and off: flying, no damage
        and keys to skip the challenges. Set it to False when you collect
        data. A skipped flanker task never writes a data file.

    Returns
    -------
    list of Path
        The flanker data files written in this session, one CSV file per
        attempt at the Pond Challenge (empty if the task was never finished).
    """
    game = Game(participant_id, data_dir, seed, player_settings, flanker_settings, allow_admin)
    try:
        game.run()
    finally:
        pygame.quit()
    return game.saved_files
