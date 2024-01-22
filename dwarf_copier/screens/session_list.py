"""Screen for display and selection of astrophotography sessions present in a source."""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header


class SessionList(Screen):
    """Display available astrophotography sessions in the source."""

    datatable: DataTable

    def compose(self) -> ComposeResult:
        yield Header()
        self.datatable = DataTable()
        yield self.datatable
        yield Footer()
