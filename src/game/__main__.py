"""Start the game with ``python -m src.game``."""

from .app import run_game

if __name__ == "__main__":
    for path in run_game():
        print(f"Saved flanker data: {path}")
