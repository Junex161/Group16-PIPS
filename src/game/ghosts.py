"""Ghost races, like the time trials in Mario Kart.

While a level is played, the position of the hero is recorded a few times
per second. When the level is finished faster than ever before (on the same
difficulty), the run is saved as the new "ghost" of that level. The next time
the level is played, the ghost runs along as a see-through copy of the hero,
and the screen shows how far ahead or behind the player is.

Ghosts are saved as small JSON files in the ``ghosts`` folder of the project,
one per level and difficulty. They can be copied to another computer to race
a friend's best run. Ghost races can be switched off on the home screen.
"""

import json
from pathlib import Path

import pygame

from . import graphics, ui
from .characters import CHARACTERS
from .config import PROJECT_ROOT, SCREEN_WIDTH

GHOST_DIR = PROJECT_ROOT / "ghosts"
# Seconds between two recorded positions.
SAMPLE_TIME = 1 / 20
GHOST_ALPHA = 150


def ghost_path(level_key, difficulty_key, folder=GHOST_DIR):
    """Return the file that holds the ghost of a level on one difficulty."""
    return Path(folder) / f"{level_key}_{difficulty_key}.json"


def load_ghost(level_key, difficulty_key, folder=GHOST_DIR):
    """Load a saved ghost; return None if there is none or the file is broken."""
    path = ghost_path(level_key, difficulty_key, folder)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("samples") and data.get("time"):
            return data
    except (OSError, ValueError):
        pass
    return None


class GhostRun:
    """
    Records the current run and plays back the best earlier run.

    Parameters
    ----------
    level_key : str
        Key of the level (see ``levels.LEVEL_ORDER``).
    difficulty_key : str
        "easy", "medium" or "hard"; every difficulty has its own ghost.
    enabled : bool, optional
        If False, nothing is recorded or shown.
    folder : str or Path, optional
        Folder of the ghost files.
    """

    def __init__(self, level_key, difficulty_key, enabled=True, folder=GHOST_DIR):
        self.level_key, self.difficulty_key = level_key, difficulty_key
        self.enabled = enabled
        self.folder = Path(folder)
        self.best = load_ghost(level_key, difficulty_key, folder) if enabled else None
        self.samples = []
        # Recorded states of the boss while the hero fought it: [time, state].
        self.boss_samples = []
        self.next_sample = 0.0
        self.new_record = False
        # A second, see-through boss that the ghost fights (created when needed).
        self.fake_boss = None

    @property
    def best_time(self):
        """Time of the saved ghost in seconds, or None."""
        return self.best["time"] if self.best else None

    def record(self, time, player, character, busy=False, boss=None):
        """
        Store the hero's position if it is time for the next sample.

        ``busy`` marks moments in a minigame or a text box (the ghost waits
        there); ``boss`` is recorded while it fights, so the ghost can fight a
        copy of it later.
        """
        if not self.enabled or time < self.next_sample:
            return
        self.next_sample = time + SAMPLE_TIME
        moving = int(abs(player.vx) > 20) and not busy
        self.samples.append([round(time, 3), round(player.x, 1), round(player.y, 1), player.facing, int(moving), int(player.on_ground), int(busy)])
        self.character = character.key
        if boss is not None and boss.active and not boss.defeated:
            self.boss_samples.append([round(time, 3), boss.ghost_state()])

    def finish(self, time):
        """
        The level was completed in ``time`` seconds: keep the run if it is the best.

        Returns
        -------
        bool
            True if this run is the new ghost.
        """
        if not self.enabled or not self.samples or (self.best_time is not None and time >= self.best_time):
            return False
        data = {"level": self.level_key, "difficulty": self.difficulty_key, "time": round(time, 3), "character": getattr(self, "character", CHARACTERS[0].key), "samples": self.samples, "boss": self.boss_samples}
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
            ghost_path(self.level_key, self.difficulty_key, self.folder).write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
        except OSError:
            return False
        self.new_record = True
        return True

    def position(self, time):
        """
        Where the ghost is at ``time`` seconds: (x, y, facing, moving, on_ground, busy) or None.

        Positions between two samples are interpolated; after its finish the
        ghost waits at the goal.
        """
        if not self.best:
            return None
        samples = self.best["samples"]
        low, high = 0, len(samples) - 1
        if time >= samples[-1][0]:
            return (*samples[-1][1:6], 0)
        while low < high:
            middle = (low + high) // 2
            if samples[middle][0] < time:
                low = middle + 1
            else:
                high = middle
        after = samples[low]
        before = samples[max(0, low - 1)]
        span = after[0] - before[0]
        share = 0.0 if span <= 0 else (time - before[0]) / span
        x = before[1] + (after[1] - before[1]) * share
        y = before[2] + (after[2] - before[2]) * share
        busy = before[6] if len(before) > 6 else 0
        return (x, y, before[3], before[4], before[5], busy)

    def _image(self, facing, moving, on_ground, time):
        """A see-through, bluish picture of the ghost's hero."""
        character = next((c for c in CHARACTERS if c.key == self.best.get("character")), CHARACTERS[0])
        image = pygame.Surface((80, 80), pygame.SRCALPHA)
        graphics.draw_hero(image, character, 23, 15, facing, time, bool(moving), bool(on_ground))
        # Tint it blue, so it never looks like the real hero.
        tint = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        tint.fill((120, 150, 255, 255))
        image.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        image.set_alpha(GHOST_ALPHA)
        return image

    def draw(self, surface, scene, camera):
        """Draw the ghost if it is in the same world as the hero."""
        if not self.enabled:
            return
        state = self.position(scene.total_time)
        if state is None:
            return
        x, y, facing, moving, on_ground, busy = state
        level = scene.level
        if level.zone_at(x + 17) is not level.zone_at(scene.player.center_x):
            return
        self._draw_fake_boss(surface, scene, camera)
        image = self._image(facing, moving, on_ground, scene.time)
        surface.blit(image, (x - camera - 23, y - 15))
        ui.draw_text(surface, "GHOST", (x - camera + 17, y - 22), 22, (190, 220, 255), "midbottom", bold=True, shadow=True)
        if busy:
            # The ghost is busy with a minigame or a text box: it waits.
            bubble = pygame.Rect(0, 0, 54, 30)
            bubble.midbottom = (x - camera + 17, y - 48)
            pygame.draw.rect(surface, (190, 220, 255), bubble, border_radius=12)
            dots = "." * (1 + int(scene.time * 3) % 3)
            ui.draw_text(surface, dots, bubble.center, 30, ui.INK, "center", bold=True)

    def boss_state(self, time):
        """The recorded state of the ghost's boss at ``time``, or None if it was not fighting."""
        samples = self.best.get("boss") if self.best else None
        if not samples or not samples[0][0] <= time <= samples[-1][0]:
            return None
        low, high = 0, len(samples) - 1
        while low < high:
            middle = (low + high + 1) // 2
            if samples[middle][0] <= time:
                low = middle
            else:
                high = middle - 1
        sample_time, state = samples[low]
        # A gap means the ghost was busy (e.g. the boss was not on screen).
        return state if time - sample_time < 4 * SAMPLE_TIME else None

    def _draw_fake_boss(self, surface, scene, camera):
        """Draw the see-through copy of the boss that the ghost fights."""
        state = self.boss_state(scene.total_time)
        if state is None or not hasattr(scene, "make_boss"):
            return
        if self.fake_boss is None:
            self.fake_boss = scene.make_boss()
        if self.fake_boss is None:
            return
        self.fake_boss.apply_ghost_state(state)
        self.fake_boss.active = True
        layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        self.fake_boss.draw(layer, camera, scene.time)
        tint = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        tint.fill((140, 170, 255, 255))
        layer.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        layer.set_alpha(GHOST_ALPHA - 30)
        surface.blit(layer, (0, 0))

    def draw_hud(self, surface, scene):
        """Show the ghost's best time below the level timer."""
        if not self.enabled or not self.best:
            return
        minutes, seconds = divmod(int(self.best_time), 60)
        ui.draw_text(surface, f"Ghost {minutes}:{seconds:02d}", (SCREEN_WIDTH - 24, 116), 28, (190, 220, 255), "topright", shadow=True)


def ghost_stats(ghost):
    """Lines for the level-complete screen: a new record or the time to beat."""
    if not ghost.enabled:
        return []
    if ghost.new_record:
        return [("Ghost race", "New record!")]
    if ghost.best_time is not None:
        minutes, seconds = divmod(int(ghost.best_time), 60)
        return [("Ghost to beat", f"{minutes}:{seconds:02d}")]
    return []
