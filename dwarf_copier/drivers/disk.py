"""Driver for photo files accessible via a file path."""

import re
import shutil
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import Callable

from dwarf_copier.configuration import BaseDriver, ConfigFormat
from dwarf_copier.shots_info import ShotsInfo
from dwarf_copier.source_directory import SourceDirectory

FOLDER_PATTERN = (
    "DWARF_RAW_<target>_EXP_<exp>_GAIN_<gain>_"
    "<year>-<mon>-<day>-<hour>-<min>-<sec>-<millisec>"
)
SHOTS_INFO = "shotsInfo.json"


class Driver(BaseDriver):
    """Class used to access photo files.

    The work happens in a threaded worker so it cannot block the main display.
    A queue is used to send commands to the worker. Results are delivered by
    callbacks (which must be thread-safe) e.g. post_message.
    """

    def __init__(self, root: Path) -> None:
        self.root = root

    def _folder_regex(self, template: str) -> re.Pattern:
        """Convert the 'friendly' folder pattern into a regex."""
        pattern = re.compile(
            re.sub("<([a-zA-Z0-9]+)>", "(?P<\\1>.*?)", re.escape(template)) + "$"
        )
        return pattern

    @cached_property
    def pattern(self) -> re.Pattern:
        """Pre-compiled regex to match our template."""
        return self._folder_regex(FOLDER_PATTERN)

    def list_dirs(self, callback: Callable[[SourceDirectory | None], None]) -> None:
        for p in self.root.glob("DWARF_RAW*"):
            session = self.create_session(p)
            if session is not None:
                callback(session)
        callback(None)

    def create_session(self, p: Path) -> SourceDirectory | None:
        if (
            p.is_dir()
            and (p / SHOTS_INFO).exists()
            and (m := self.pattern.match(p.name)) is not None
        ):
            info = ShotsInfo.model_validate_json((p / SHOTS_INFO).read_text())

            year, mon, day, hour, min, sec, millisec = [
                int(s)
                for s in m.group("year", "mon", "day", "hour", "min", "sec", "millisec")
            ]
            return SourceDirectory(
                path=p,
                info=info,
                date=datetime(year, mon, day, hour, min, sec, millisec * 1000),
            )
        return None

    def prepare(
        self,
        format: ConfigFormat,
        session: SourceDirectory,
        target_path: Path,
    ) -> tuple[list[Path], dict[Path, str], dict[Path, str]]:
        """Build maps of files to be copied or linked."""
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

    def match_wildcards(self, base: Path, filename: str) -> list[Path]:
        """Match files in base."""
        return list(base.glob(filename))
