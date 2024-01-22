"""Model dialog to confirm leaving the app."""
from textual import on
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header

from dwarf_copier.config import ConfigSource, ConfigTarget, ConfigurationModel
from dwarf_copier.model import PhotoSession
from dwarf_copier.widgets.prev_next import PrevNext


class ShowSessions(Screen[list[PhotoSession] | None]):
    """Screen to display sessions present on a source."""

    selected: list[PhotoSession]

    def __init__(
        self,
        config: ConfigurationModel,
        source: ConfigSource | None,
        target: ConfigTarget | None,
    ) -> None:
        self.config = config
        self.source = source
        self.target = target
        self.selected = []
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create our widgets."""
        yield Header()
        data = DataTable[str | int | float]()
        data.add_columns("Target", "Exp", "Gain", "IR", "Bin", "Shots")
        data.loading = True
        yield data
        yield PrevNext()
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Pressing 'next' dismisses this screen."""
        if event.button.id == "next":
            self.dismiss(self.selected)
        else:
            self.dismiss(None)

    def form_is_valid(self) -> None:
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
