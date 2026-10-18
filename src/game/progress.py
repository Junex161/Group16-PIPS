"""Which levels the player has finished, and which are unlocked.

Like the worlds of a Super Mario game, a level only opens once the level
before it has been finished. The progress is saved in a small JSON file, so
it is still there the next time the game starts. Admin mode on the home
screen opens every level for testing.
"""

import json
from pathlib import Path


class Progress:
    """
    The finished levels, saved in ``path``.

    Parameters
    ----------
    path : str or Path
        JSON file of the progress; it is created when a level is finished.
    order : sequence of str
        Level keys in the order they are played.
    """

    def __init__(self, path, order):
        self.path = Path(path)
        self.order = tuple(order)
        self.completed = set()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.completed = {key for key in data.get("completed", ()) if key in self.order}
        except (OSError, ValueError, AttributeError):
            pass

    def is_unlocked(self, key):
        """The first level is always open; every other one after the level before it."""
        index = self.order.index(key)
        return index == 0 or self.order[index - 1] in self.completed

    def complete(self, key):
        """Remember that ``key`` was finished (and so unlock the next level)."""
        if key not in self.order or key in self.completed:
            return
        self.completed.add(key)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({"completed": sorted(self.completed, key=self.order.index)}), encoding="utf-8")
        except OSError:
            pass  # the game still works, it only forgets the progress

    def next_open(self):
        """The first unlocked level that is not finished yet (the last level if all are)."""
        for key in self.order:
            if key not in self.completed and self.is_unlocked(key):
                return key
        return self.order[-1]
