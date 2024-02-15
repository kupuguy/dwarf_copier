"""Model dialog to confirm leaving the app."""

from dataclasses import dataclass, field
from typing import Callable

from rich.text import Text
from textual import on, work
from textual.app import ComposeResult
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header
from textual.widgets.data_table import ColumnKey, RowKey

from dwarf_copier.config import ConfigSource, ConfigTarget, ConfigurationModel
from dwarf_copier.drivers import disk
from dwarf_copier.model import PhotoSession
from dwarf_copier.widgets.prev_next import PrevNext
from dwarf_copier.widgets.sortable_table import SortableDataTable


class Toggle:
    """Rich renderable checkable box."""

    value: bool = False

    def __init__(self, v: bool) -> None:
        self.value = v

    def toggle(self) -> "Toggle":
        return Toggle(not self.value)

    def __rich__(self) -> str:
        """A toggleable check box."""
        return "\N{Ballot Box with Check}" if self.value else "\N{Ballot Box}"


@dataclass(order=True, frozen=True)
class Shots:
    """Rich renderable renders with custom separator."""

    stacked: int
    taken: int
    sep: str = field(default="/", kw_only=True)

    def _color(self) -> str:
        if self.stacked * 10 >= self.taken * 9:
            return ""
        return "orange3"

    def __str__(self) -> str:
        """String for display."""
        return f"{self.stacked}{self.sep}{self.taken}"

    def __rich__(self) -> Text:
        """Render tuple with custom separator."""
        s = f"{self.stacked}{self.sep}{self.taken}"
        color = self._color()
        return Text(s, style=color)


class ShowSessions(Screen[list[PhotoSession] | None]):
    """Screen to display sessions present on a source."""

    selected_keys: set[RowKey]
    sessions: dict[RowKey, PhotoSession]
    column_keys: list[ColumnKey]

    @dataclass
    class SessionFound(Message):
        """Message when we find a folder containing images.

        None indicates the worker has finished.
        """

        session: PhotoSession | None

    def __init__(
        self,
        config: ConfigurationModel,
        source: ConfigSource,
        target: ConfigTarget,
    ) -> None:
        self.config = config
        self.source = source
        self.target = target
        self.selected_keys = set()
        self.sessions = {}
        self.column_keys = []
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create our widgets."""
        yield Header()
        data = SortableDataTable[str | int | float | Shots | Toggle]()
        self.column_keys = data.add_columns(
            "", "Target", "Date", "Exp", "Gain", "IR", "Bin", "Shots", "Directory"
        )
        data.loading = True
        data.cursor_type = "row"
        yield data
        yield PrevNext()
        yield Footer()

    def on_mount(self) -> None:
        self.sort_column_key = None
        self.populate()

    def populate(self) -> None:
        def callback(session: PhotoSession | None) -> None:
            self.post_message(self.SessionFound(session))

        self.list_dirs(self.source, callback)

    @property
    def selected(self) -> list[PhotoSession]:
        return [self.sessions[k] for k in self.selected_keys]

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
        if event.row_key is not None and event.row_key in self.sessions:
            datatable = event.data_table
            cell: Toggle = datatable.get_cell(
                event.row_key, self.column_keys[0]
            ).toggle()
            datatable.update_cell(event.row_key, self.column_keys[0], cell)

            if cell.value:
                self.selected_keys.add(event.row_key)
            else:
                self.selected_keys.remove(event.row_key)
            self.log(f"Selected sessions: {self.selected_keys}")
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
            info = session.info
            key = data.add_row(
                Toggle(False),
                info.target,
                session.date.strftime("%y/%m/%d %H:%M"),
                info.exp_fraction,
                info.gain,
                info.ir,
                info.binning,
                Shots(info.shotsStacked, info.shotsTaken),
                session.path.name,
                key=session.path.name,
            )
            self.sessions[key] = session
