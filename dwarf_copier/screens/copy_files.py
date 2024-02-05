"""Model dialog to confirm leaving the app."""

import shutil
from pathlib import Path
from tempfile import mkdtemp

from textual import work
from textual.app import ComposeResult
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Footer, Header, Log

from dwarf_copier.config import (
    ConfigFormat,
    ConfigSource,
    ConfigTarget,
    ConfigurationModel,
)
from dwarf_copier.drivers import disk
from dwarf_copier.model import PhotoSession
from dwarf_copier.widgets.prev_next import PrevNext


class CopyFiles(Screen[list[PhotoSession] | None]):
    """Screen to display sessions present on a source."""

    selected: list[PhotoSession]
    sessions: dict[str, PhotoSession]

    class TargetPrepared(Message):
        """Message when we find a folder containing images.

        None indicates the worker has finished.
        """

        session: PhotoSession | None

        def __init__(self, session: PhotoSession | None):
            self.session = session
            super().__init__()

    def __init__(
        self,
        config: ConfigurationModel,
        source: ConfigSource,
        target: ConfigTarget,
        selected: list[PhotoSession],
        format: ConfigFormat,
    ) -> None:
        self.config = config
        self.source = source
        self.target = target
        self.selected = selected
        self.format = format
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create our widgets."""
        yield Header()
        self.log_widget = Log()
        yield self.log_widget
        yield PrevNext()
        yield Footer()

    def on_mount(self) -> None:
        self.do_copy(self.selected, self.source, self.target, self.format)

    @work(thread=True)
    def do_copy(
        self,
        sessions: list[PhotoSession],
        source: ConfigSource,
        target: ConfigTarget,
        format: ConfigFormat,
        # callback: Callable[[PhotoSession | None], None],
    ) -> None:
        driver = disk.Driver(source.path)
        target_path = Path(target.path)

        for session in sessions:
            self.log_widget.write_line("")
            destination_path = target_path / session.format(format.path)
            self.log_widget.write_line(f"Final destination {destination_path}")
            working_path = Path(mkdtemp(dir=str(target_path)))
            try:
                mkdirs, links, copies = driver.prepare(format, session, working_path)
                for md in mkdirs:
                    self.log_widget.write_line(f"mkdir {md}")
                for ln in links:
                    self.log_widget.write_line(f"link {ln} -> {links[ln]}")
                for cp in copies:
                    self.log_widget.write_line(f"copy {cp} -> {copies[cp]}")
            finally:
                shutil.rmtree(working_path, ignore_errors=True)
        return
