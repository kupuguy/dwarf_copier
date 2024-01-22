"""Driver for photo files accessible via a file path."""


import multiprocessing as mp
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

from dwarf_copier.model import PhotoSession


class Cmd(Enum):
    """Queue commands."""

    QUIT = 0
    LIST_SESSIONS = 1
    COPY_SESSION = 2


@dataclass
class Command:
    """Command and associated parameters."""

    cmd: Cmd
    path: Path | None = None
    callback: Callable | None = None


class Driver:
    """Class used to access photo files.

    The work happens in a threaded worker so it cannot block the main display.
    A queue is used to send commands to the worker. Results are delivered by
    callbacks (which must be thread-safe) e.g. post_message.
    """

    queue: mp.queues.Queue[Command]

    def __init__(self) -> None:
        self.queue = mp.Queue()

    def send_dirlist(
        self, path: Path, callback: Callable[[PhotoSession | None], None]
    ) -> None:
        """Get a list of photo session folders at the target.

        The callback is triggered once per folder.
        """
        self.queue.put(Command(Cmd.LIST_SESSIONS, path=path, callback=callback))

    def run(self, num_workers: int = 1) -> None:
        ...
