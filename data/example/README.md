# Example playthrough

This folder holds the data of one complete playthrough. `main.ipynb` uses it when nobody has played the flanker, stop-signal or 2-back task yet (for example, right after cloning the repository), so the bootstrap and the simulation always start from real data.

To replace it, play the whole game once with admin mode off and copy the new files of that session from `data/` into this folder: the questionnaire and the flanker, stop-signal and 2-back files (`attempt-1`), and optionally the Tower of London and card-sorting files. Remove the previous example files, so that the folder holds a single player.
