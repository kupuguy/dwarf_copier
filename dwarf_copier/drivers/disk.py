"""Driver for photo files accessible via a file path."""

import multiprocessing as mp
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable

from dwarf_copier.config import ConfigFormat
from dwarf_copier.model import PhotoSession, ShotsInfo

FOLDER_PATTERN = (
    "DWARF_RAW_<target>_EXP_<exp>_GAIN_<gain>_"
    "<year>-<mon>-<day>-<hour>-<min>-<sec>-<millisec>"
)
SHOTS_INFO = "shotsInfo.json"


class Driver:
    """Class used to access photo files.

    The work happens in a threaded worker so it cannot block the main display.
    A queue is used to send commands to the worker. Results are delivered by
    callbacks (which must be thread-safe) e.g. post_message.
    """

    queue: mp.Queue

    def __init__(self, root: Path) -> None:
        self.queue = mp.Queue()
        self.root = root

    def _folder_regex(self, template: str) -> re.Pattern:
        """Convert the 'friendly' folder pattern into a regex."""
        pattern = re.compile(
            re.sub("<([a-zA-Z0-9]+)>", "(?P<\\1>.*?)", re.escape(template)) + "$"
        )
        return pattern

    def list_dirs(self, callback: Callable[[PhotoSession | None], None]) -> None:
        pattern = self._folder_regex(FOLDER_PATTERN)
        for p in self.root.glob("Astronomy/DWARF_RAW*"):
            if (
                not p.is_dir()
                or not (p / SHOTS_INFO).exists()
                or (m := pattern.match(p.name)) is None
            ):
                continue
            info = ShotsInfo.model_validate_json((p / SHOTS_INFO).read_text())

            year, mon, day, hour, min, sec, millisec = [
                int(s)
                for s in m.group("year", "mon", "day", "hour", "min", "sec", "millisec")
            ]
            session = PhotoSession(
                path=p,
                info=info,
                date=datetime(year, mon, day, hour, min, sec, millisec * 1000),
            )
            callback(session)
        callback(None)

    def prepare(
        self,
        format: ConfigFormat,
        session: PhotoSession,
        target_path: Path,
    ) -> tuple[list[Path], dict[Path, str], dict[Path, str]]:
        """Build maps of files to be copied or linked."""
        # target_path = target.path / session.format(format.path)
        mkdirs = [target_path / d for d in format.directories]
        links: dict[Path, str] = {}
        for op in format.link_or_copy:
            for p in session.path.glob(op.source):
                if p not in links:
                    links[p] = session.format(op.destination, name=p.name)

        copies: dict[Path, str] = {}
        for op in format.copy_only:
            for p in session.path.glob(op.source):
                if p not in copies and p not in links:
                    copies[p] = session.format(op.destination, name=p.name)

        return mkdirs, links, copies

    def copy_file(self, src: Path, dest: Path) -> None:
        """Copy a single file."""
        shutil.copyfile(src, dest)

    def link_file(self, src: Path, dest: Path) -> None:
        """Create a link from dest back to src."""
        dest.symlink_to(src)
