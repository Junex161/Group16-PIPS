"""Mind Quest: an educational jump-and-run game about psychology.

Level 1 ("Focus Fields") combines a platformer with playable experiments
on attention, a child flanker task as mini boss and a quiz with pipes. Start the game
with ``run_game()``; flanker data are saved as CSV files in the ``data``
folder. ``REFERENCES`` lists the scientific sources of the content.
"""

from .app import run_game
from .config import FlankerSettings, PlayerSettings
from .content import REFERENCES

__all__ = ["run_game", "FlankerSettings", "PlayerSettings", "REFERENCES"]
