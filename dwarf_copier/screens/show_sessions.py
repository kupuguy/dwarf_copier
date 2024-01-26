"""Model dialog to confirm leaving the app."""

from typing import Callable

from textual import on, work
from textual.app import ComposeResult
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header

from dwarf_copier.config import ConfigSource, ConfigTarget, ConfigurationModel
from dwarf_copier.drivers import disk
from dwarf_copier.model import PhotoSession
from dwarf_copier.widgets.prev_next import PrevNext


class ShowSessions(Screen[list[PhotoSession] | None]):
    """Screen to display sessions present on a source."""

    selected: list[PhotoSession]
    sessions: dict[str, PhotoSession]

    class SessionFound(Message):
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
    ) -> None:
        self.config = config
        self.source = source
        self.target = target
        self.selected = []
        self.sessions = {}
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create our widgets."""
        yield Header()
        data = DataTable[str | int | float]()
        data.add_columns(
            "Target", "Date", "Exp", "Gain", "IR", "Bin", "Shots", "Directory"
        )
        data.loading = True
        data.cursor_type = "row"
        yield data
        yield PrevNext()
        yield Footer()

    def on_mount(self) -> None:
        self.populate()

    def populate(self) -> None:
        def callback(session: PhotoSession | None) -> None:
            self.post_message(self.SessionFound(session))

        self.list_dirs(self.source, callback)

    @work(thread=True)
    def list_dirs(
        self, source: ConfigSource, callback: Callable[[PhotoSession | None], None]
    ) -> None:
        driver = disk.Driver(source.path)
        driver.list_dirs(callback=callback)
        return

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Pressing 'next' dismisses this screen."""
        if event.button.id == "next":
            self.dismiss(self.selected)
        else:
            self.dismiss(None)

    @on(DataTable.RowSelected)
    def row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        if event.row_key is not None and event.row_key.value in self.sessions:
            self.selected = [self.sessions[event.row_key.value]]
            self.log(f"Selected session: {event.row_key.value}")
        self.check_form_valid()

    @on(DataTable.RowHighlighted)
    def row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        event.stop()
        if event.row_key is not None and event.row_key.value in self.sessions:
            self.selected = [self.sessions[event.row_key.value]]
            self.log(f"Selected session: {event.row_key.value}")
        self.check_form_valid()

    def check_form_valid(self) -> None:
        """Form is valid only when both source and target have been selected."""
        button_bar = self.query_one("PrevNext", PrevNext)
        button_bar.valid = bool(self.selected)

    @on(PrevNext.Prev)
    def prev_pressed(self) -> None:
        """Pressing 'next' dismisses this screen."""
        self.dismiss(None)

    @on(PrevNext.Next)
    def next_pressed(self) -> None:
        """Pressing 'next' dismisses this screen."""
        self.dismiss((self.selected))

    @on(SessionFound)
    def session_found(self, msg: SessionFound) -> None:
        msg.stop()

        data = self.query_one(DataTable)
        if msg.session is None:
            data.loading = False
        else:
            session = msg.session
            self.log(f"Session: {session.path.name}")
            self.sessions[session.path.name] = session
            info = session.info
            data.add_row(
                info.target,
                session.date.strftime("%y/%m/%d %H:%M"),
                info.exp,
                info.gain,
                info.ir,
                info.binning,
                f"{info.shotsStacked}/{info.shotsTaken}",
                session.path.name,
                key=session.path.name,
            )
