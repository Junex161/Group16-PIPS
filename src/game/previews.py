"""Small preview pictures of the levels for the level select.

A preview is the first screen of a level, drawn by the level itself (without
the HUD) and scaled down. Previews are drawn once and then kept.
"""

import pygame

from .config import SCREEN_HEIGHT, SCREEN_WIDTH

PREVIEW_SIZE = (224, 126)
_cache = {}


def level_preview(game, key, size=PREVIEW_SIZE):
    """
    Return a preview picture of level ``key`` for the current hero.

    Parameters
    ----------
    game : Game
        The running game (the level is built with its settings).
    key : str
        Key of the level (see ``levels.LEVEL_ORDER``).
    size : tuple of int, optional
        Size of the picture in pixels.
    """
    cache_key = (key, game.character.key, size)
    if cache_key not in _cache:
        from .levels import make_level_scene

        scene = make_level_scene(game, key)
        # Only the world itself: no HUD, hints or labels.
        for name in ("_draw_hud", "_draw_hint", "_draw_pipe_labels"):
            setattr(scene, name, lambda *args: None)
        scene.ghost.enabled = False
        full = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        scene.time = 1.0
        scene.draw(full)
        _cache[cache_key] = pygame.transform.smoothscale(full, size)
    return _cache[cache_key]


def locked_preview(preview):
    """A darkened copy of a preview with a padlock, for locked levels."""
    picture = preview.copy()
    shade = pygame.Surface(picture.get_size(), pygame.SRCALPHA)
    shade.fill((10, 10, 30, 170))
    picture.blit(shade, (0, 0))
    x, y = picture.get_width() // 2, picture.get_height() // 2
    pygame.draw.arc(picture, (230, 230, 240), (x - 18, y - 38, 36, 44), 0, 3.1416, 6)
    pygame.draw.rect(picture, (255, 214, 92), (x - 26, y - 14, 52, 40), border_radius=6)
    pygame.draw.circle(picture, (60, 50, 30), (x, y + 2), 6)
    pygame.draw.rect(picture, (60, 50, 30), (x - 3, y + 2, 6, 14))
    return picture


def clear_cache():
    """Forget all previews (e.g. after pygame was restarted)."""
    _cache.clear()
