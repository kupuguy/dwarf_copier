"""Main dashboard screen."""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Placeholder


class DashboardScreen(Screen):
    """Main screen for the app.

    This screen shows a list of Dwarf Telescopes from which we can copy files.
    """

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()
        yield Placeholder("Dashboard Screen")
        yield Footer()
