"""Model dialog to confirm leaving the app."""

from dataclasses import dataclass, field, replace
from typing import Callable

from rich.text import Text
from textual import on, work
from textual.app import ComposeResult
from textual.message import Message
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header
from textual.widgets.data_table import ColumnKey, RowKey

from dwarf_copier.configuration import ConfigSource, config
from dwarf_copier.drivers import disk
from dwarf_copier.model import PhotoSession, State
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
        return "orange3 on grey70"

    def __str__(self) -> str:
        """String for display."""
        return f"{self.stacked}{self.sep}{self.taken}"

    def __rich__(self) -> Text:
        """Render tuple with custom separator."""
        s = f"{self.stacked}{self.sep}{self.taken}"
        color = self._color()
        return Text(s, style=color)


class ShowSessions(Screen[State]):
    """Screen to display sessions present on a source."""

    COMPONENT_CLASSES = {
        "sessions--new-folder",
        "sessions--existing",
        "shots--good",
        "shots--poor",
    }

    DEFAULT_CSS = """
    ShowSessions .sessions--new-folder {}
    ShowSessions .sessions--existing { color: $text-disabled; }
    .sessions--new-folder {  }
    .sessions--existing { color: $text-disabled; }
    """

    state: State
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
        state: State,
    ) -> None:
        self.state = state
        self.source = state.source
        self.target = state.target
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

    @on(DataTable.RowSelected)
    def row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        if event.row_key is not None and event.row_key in self.sessions:
            datatable = event.data_table
            cell: Toggle | str = datatable.get_cell(event.row_key, self.column_keys[0])
            if isinstance(cell, Toggle):
                cell = cell.toggle()
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
        self.dismiss(replace(self.state, ok=False))

    @on(PrevNext.Next)
    def next_pressed(self) -> None:
        """Pressing 'next' dismisses this screen."""
        self.dismiss(replace(self.state, selected=list(self.selected), ok=True))

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
            fmt = self.target.format
            format = config.get_format(fmt)

            if session.destination_exists(self.target.path, format.path):
                style = self.get_component_rich_style(
                    "sessions--existing", partial=True
                )

                directory = Text(
                    session.path.name,
                    style=style,
                )
                self.log.info(f"sessions--existing={style}")
                checkbox: Toggle | str = ""
            else:
                style = self.get_component_rich_style(
                    "sessions--new-folder", partial=True
                )

                directory = Text(
                    session.path.name,
                    style=style,
                )
                self.log.info(f"sessions--new-folder={style}")
                checkbox = Toggle(False)
            key = data.add_row(
                checkbox,
                info.target,
                session.date.strftime("%y/%m/%d %H:%M"),
                info.exp_fraction,
                info.gain,
                info.ir,
                info.binning,
                Shots(info.shotsStacked, info.shotsTaken),
                directory,
                key=session.path.name,
            )
            self.sessions[key] = session
