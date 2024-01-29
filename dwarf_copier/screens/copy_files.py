"""Model dialog to confirm leaving the app."""

from typing import Callable

from textual import work
from textual.app import ComposeResult
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Footer, Header, Log

from dwarf_copier.config import ConfigSource, ConfigTarget, ConfigurationModel
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
    ) -> None:
        self.config = config
        self.source = source
        self.target = target
        self.selected = selected
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create our widgets."""
        yield Header()
        yield Log()
        yield PrevNext()
        yield Footer()

    def on_mount(self) -> None:
        self.populate()

    def populate(self) -> None:
        def callback(session: PhotoSession | None) -> None:
            self.post_message(self.TargetPrepared(session))

        self.list_dirs(self.source, callback)

    @work(thread=True)
    def list_dirs(
        self, source: ConfigSource, callback: Callable[[PhotoSession | None], None]
    ) -> None:
        driver = disk.Driver(source.path)
        driver.list_dirs(callback=callback)
        return
