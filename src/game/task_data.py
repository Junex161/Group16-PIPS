"""Saving the trials of an experiment as a CSV file.

Every experiment in the game (the flanker task, the stop-signal task, the
2-back task and the Tower of London) writes one file per attempt to the
``data`` folder, named ``<task>_<participant>_<timestamp>_attempt-<n>.csv``.
"""

import csv
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path

from .config import DATA_DIR
from .flanker_task import clean_participant_id


def save_rows(task, rows, columns, participant_id, attempt=1, data_dir=DATA_DIR):
    """
    Save the trials of one attempt at an experiment as a timestamped CSV file.

    Parameters
    ----------
    task : str
        Short name of the experiment, used at the start of the file name.
    rows : list of dataclass or dict
        One entry per trial; ``participant_id`` and ``attempt`` are added.
    columns : sequence of str
        Column names in the order they are written.
    participant_id : str
        Anonymous participant label used in the data and the file name.
    attempt : int, optional
        Number of this attempt within the game session (1 = first try).
    data_dir : str or Path, optional
        Folder for the file; it is created if it does not exist.

    Returns
    -------
    Path
        Location of the written file.
    """
    participant_id = clean_participant_id(participant_id)
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = data_dir / f"{task}_{participant_id}_{timestamp}_attempt-{attempt}.csv"
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            values = asdict(row) if is_dataclass(row) else dict(row)
            values = {"participant_id": participant_id, "attempt": attempt, **values}
            # Missing values (e.g. no response) are written as empty cells.
            writer.writerow({column: "" if values.get(column) is None else values[column] for column in columns})
    return path
