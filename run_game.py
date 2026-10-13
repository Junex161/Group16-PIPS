"""Start the game: run this file in PyCharm or with ``python run_game.py``."""

from src.game import run_game

if __name__ == "__main__":
    for path in run_game():
        print(f"Saved flanker data: {path}")
