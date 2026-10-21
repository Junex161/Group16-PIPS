"""Loading the data files that the game writes to ``data/``.

Every attempt at an experiment is saved as
``<task>_<participant>_<timestamp>_attempt-<n>.csv`` (see
``src/game/task_data.py``). These helpers read those files back as pandas
tables, either for all participants or for one game session.
"""

import shutil
from pathlib import Path

import pandas as pd

from .game.config import DATA_DIR, PROJECT_ROOT

TASKS = ("questionnaire", "flanker", "stopsignal", "nback", "tower", "cardsort")


def parse_file_name(path):
    """
    Split a data file name into its parts.

    Returns
    -------
    tuple
        ``(task, participant_id, timestamp, attempt)``; participant labels
        may themselves contain underscores.
    """
    task, rest = Path(path).stem.split("_", 1)
    participant_id, timestamp, attempt = rest.rsplit("_", 2)
    return task, participant_id, timestamp, int(attempt.removeprefix("attempt-"))


def _timestamp(path):
    """The timestamp in a game file name, or "" for other files (such as simulated data)."""
    try:
        return parse_file_name(path)[2]
    except ValueError:
        return ""


def task_files(task, data_dir=DATA_DIR):
    """
    Return the data files of one task, oldest first.

    Parameters
    ----------
    task : str
        One of ``TASKS``.
    data_dir : str or Path, optional
        Folder with the data files.

    Returns
    -------
    list of Path
        Sorted by the timestamp in the file name.
    """
    if task not in TASKS:
        raise ValueError(f"task must be one of {TASKS}, not {task!r}")
    return sorted(Path(data_dir).glob(f"{task}_*.csv"), key=_timestamp)


def load_task(task, data_dir=DATA_DIR, test_only=True):
    """
    Read all data files of one task into one table.

    Parameters
    ----------
    task : str
        One of ``TASKS``.
    data_dir : str or Path, optional
        Folder with the data files.
    test_only : bool, optional
        Keep only the trials of the test block (practice trials are dropped).

    Returns
    -------
    pandas.DataFrame
        One row per trial (per answer for the questionnaire) with an extra
        ``file`` column; empty if there are no files.
    """
    files = task_files(task, data_dir)
    if not files:
        return pd.DataFrame()
    data = pd.concat([pd.read_csv(path).assign(file=path.name) for path in files], ignore_index=True)
    if test_only and "block" in data.columns:
        data = data[data["block"] == "test"].reset_index(drop=True)
    return data


def latest_participant(data_dir=DATA_DIR):
    """
    Return the participant who played most recently, or None without data.

    This is the participant of the newest data file of any experiment.
    """
    files = [path for task in TASKS for path in task_files(task, data_dir) if _timestamp(path)]
    if not files:
        return None
    return parse_file_name(max(files, key=_timestamp))[1]


def clear_game_progress(project_root=PROJECT_ROOT):
    """
    Delete the unlocked levels (``save/``) and the ghost races (``ghosts/``).

    Both are shared by everyone who plays on the same computer, so a new
    participant would otherwise start with levels unlocked and race the
    previous player's ghost. The experiment data in ``data/`` are not touched.

    Returns
    -------
    list of Path
        The folders that were deleted.
    """
    removed = []
    for name in ("save", "ghosts"):
        folder = Path(project_root) / name
        if folder.exists():
            shutil.rmtree(folder)
            removed.append(folder)
    return removed


def load_session(participant_id=None, data_dir=DATA_DIR, attempt=1):
    """
    Read the data of one participant's most recent game session.

    A participant may play several sessions, and may need several attempts
    at a task within a session. For every task this takes the newest file
    with the requested attempt number, by default the first attempt (later
    attempts are affected by practice).

    Parameters
    ----------
    participant_id : str or None, optional
        The participant label; None takes the participant who played last.
    data_dir : str or Path, optional
        Folder with the data files.
    attempt : int, optional
        Which attempt to use within the session.

    Returns
    -------
    dict
        ``{task: DataFrame}`` with the test trials of every task this
        participant completed; tasks without data are left out. The
        participant label is stored under the key ``"participant_id"``.
    """
    participant_id = participant_id or latest_participant(data_dir)
    session = {"participant_id": participant_id}
    if participant_id is None:
        return session
    for task in TASKS:
        files = [path for path in task_files(task, data_dir) if _timestamp(path) and parse_file_name(path)[1::2] == (participant_id, attempt)]
        if files:
            data = pd.read_csv(files[-1])
            if "block" in data.columns:
                data = data[data["block"] == "test"].reset_index(drop=True)
            session[task] = data
    return session
