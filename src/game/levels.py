"""All levels of the game in the order they are played.

Importing this module also registers the content of the Prologue and
Levels 2 and 3 (worlds, enemies, insights, animations and music) with the
tables of the Level 1 modules, so that the whole game knows about them.
"""

from . import guide_animations, hackula_boss, story_animations, story_content, story_entities, story_music, worlds
from .finale import build_finale
from .level_one import build_level_one
from .level_three import build_level_three
from .level_two import build_level_two
from .prologue import build_prologue

worlds.register()
story_entities.register()
story_content.register()
story_animations.register()
guide_animations.register()
hackula_boss.register()
story_music.register()

# Level keys in story order; the keys match content.LEVELS.
LEVEL_ORDER = ("prologue", "level_1", "level_2", "level_3", "finale")
LEVEL_BUILDERS = {
    "prologue": build_prologue,
    "level_1": build_level_one,
    "level_2": build_level_two,
    "level_3": build_level_three,
    "finale": build_finale,
}


def make_level_scene(game, key):
    """
    Create the scene that plays the level ``key`` from its start.

    Parameters
    ----------
    game : Game
        The running game.
    key : str
        One of ``LEVEL_ORDER``.

    Returns
    -------
    PlayScene
        A fresh run through the level.
    """
    from .play_scene import PlayScene
    from .story_scene import StoryPlayScene

    if key not in LEVEL_BUILDERS:
        raise ValueError(f"unknown level: {key}")
    if key == "level_1":
        return PlayScene(game, build_level_one)
    return StoryPlayScene(game, LEVEL_BUILDERS[key])


def next_level(key):
    """Return the key of the level after ``key``, or None after the last one."""
    index = LEVEL_ORDER.index(key)
    return LEVEL_ORDER[index + 1] if index + 1 < len(LEVEL_ORDER) else None
