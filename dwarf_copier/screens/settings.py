"""Settings screen."""
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Placeholder


class SettingsScreen(Screen):
    """Setting screen.

    This screen allows editing the application settings (usually $HOME/dwarf-copy.json)
    """

    BINDINGS = [Binding("q", "app.pop_screen", description="Cancel")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()
        yield Placeholder("Settings Screen")
        yield Footer()
