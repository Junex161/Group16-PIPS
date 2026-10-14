"""Mind Quest: an educational jump-and-run game about psychology.

A prologue on Open Science and three levels on attention, response
inhibition and executive control combine a platformer with short
animations, real experiments (flanker, stop-signal, 2-back and Tower of
London tasks), boss fights and quizzes. Start the game with ``run_game()``;
the experiment data are saved as CSV files in the ``data`` folder.
``REFERENCES`` lists the scientific sources of the content.
"""

from .app import run_game
from .config import FlankerSettings, NBackSettings, PlayerSettings, StopSignalSettings, TowerSettings
from .content import REFERENCES

__all__ = ["run_game", "FlankerSettings", "NBackSettings", "PlayerSettings", "StopSignalSettings", "TowerSettings", "REFERENCES"]
