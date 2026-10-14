"""Logic of the Tower of London puzzle (Shallice, 1982).

Three balls (red, green and blue) sit on three pegs that hold three, two
and one ball. A ball can only be taken from the top of a peg and put on a
peg that still has room. The goal is to rebuild a target arrangement in as
few moves as possible, which works best when the moves are planned before
the first ball is touched.

A state is a tuple of three tuples, one per peg, listing the balls from
the bottom up. This module contains no pygame code.
"""

import random
from collections import deque
from dataclasses import dataclass

BALLS = ("red", "green", "blue")
CAPACITIES = (3, 2, 1)
START = (("red", "green"), ("blue",), ())
COLUMNS = (
    "participant_id",
    "attempt",
    "problem",
    "min_moves",
    "moves",
    "solved",
    "planning_time_ms",
    "solution_time_ms",
)


@dataclass(frozen=True)
class TowerProblem:
    """A puzzle: rebuild ``goal`` from ``start`` in ``min_moves`` moves or more."""

    start: tuple
    goal: tuple
    min_moves: int


@dataclass(frozen=True)
class TowerResult:
    """
    The outcome of one puzzle.

    ``planning_time_ms`` is the time until the first ball was lifted and
    ``solution_time_ms`` the time until the puzzle was solved (None if the
    player gave up).
    """

    problem: int
    min_moves: int
    moves: int
    solved: bool
    planning_time_ms: int | None
    solution_time_ms: int | None


def can_move(state, source, target):
    """Return True if the top ball of peg ``source`` may go onto peg ``target``."""
    return source != target and bool(state[source]) and len(state[target]) < CAPACITIES[target]


def move(state, source, target):
    """Return the state after moving the top ball from ``source`` to ``target``."""
    if not can_move(state, source, target):
        raise ValueError(f"cannot move from peg {source} to peg {target}")
    pegs = [list(peg) for peg in state]
    pegs[target].append(pegs[source].pop())
    return tuple(tuple(peg) for peg in pegs)


def distances_from(start):
    """Return the minimal number of moves from ``start`` to every reachable state."""
    distances = {start: 0}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        for source in range(3):
            for target in range(3):
                if can_move(state, source, target):
                    following = move(state, source, target)
                    if following not in distances:
                        distances[following] = distances[state] + 1
                        queue.append(following)
    return distances


def min_moves(start, goal):
    """Return the minimal number of moves from ``start`` to ``goal``."""
    return distances_from(start)[goal]


def make_problems(move_counts, rng=None, start=START):
    """
    Pick one puzzle for each requested minimal number of moves.

    Parameters
    ----------
    move_counts : sequence of int
        Minimal number of moves of each puzzle (1 to 8).
    rng : random.Random or None, optional
        Random number generator for the choice of goals.
    start : tuple, optional
        The arrangement every puzzle starts from.

    Returns
    -------
    list of TowerProblem
        The puzzles, in the order of ``move_counts``.
    """
    rng = rng or random.Random()
    distances = distances_from(start)
    problems = []
    for count in move_counts:
        goals = sorted(state for state, distance in distances.items() if distance == count)
        if not goals:
            raise ValueError(f"no Tower of London problem needs exactly {count} moves")
        problems.append(TowerProblem(start, rng.choice(goals), count))
    return problems
