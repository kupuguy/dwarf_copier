"""Main application class for dwarf-copy."""


from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from dwarf_copier import configuration
from dwarf_copier.screens import DashboardScreen, HelpScreen, QuitScreen, SettingsScreen


class DwarfCopyApp(App):
    """Utility to copy files from Dwarf II telescope to PC."""

    CSS_PATH = "dwarf-copy.css"

    BINDINGS = [
        Binding(
            key="d", action="toggle_dark", description="Toggle dark mode", show=False
        ),
        ("s", "push_screen('settings')", "Settings"),
        Binding(
            key="question_mark",
            action="push_screen('help')",
            description="Help",
            key_display="?",
        ),
        (
            "q",
            "request_quit",
            "Quit",
        ),
    ]
    MODES = {
        "dashboard": DashboardScreen,
    }
    SCREENS = {
        "settings": SettingsScreen,
        "help": HelpScreen,
    }

    def __init__(self, *args: Any, **kw: Any) -> None:
        super().__init__(*args, **kw)
        self.dark = configuration.config.general.theme == "dark"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        """Triggered when the app is opened."""
        self.dark = configuration.config.general.theme == "dark"
        self.title = "Dwarf Copy"
        # self.sub_title = "[no source]"
        self.switch_mode("dashboard")

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_request_quit(self) -> None:
        """Action to display the quit dialog."""

        def check_quit(confirm_quit: bool) -> None:
            """Called when QuitScreen is dismissed."""
            if confirm_quit:
                self.exit()

        self.push_screen(QuitScreen(), check_quit)


def run() -> None:
    """Run the app."""
    app = DwarfCopyApp()
    app.run()


if __name__ == "__main__":
    run()
