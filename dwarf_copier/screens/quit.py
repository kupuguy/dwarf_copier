"""Model dialog to confirm leaving the app."""
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import Button, Label


class QuitScreen(Screen):
    """Screen with a dialog to quit."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Are you sure you want to quit?", id="question"),
            Button("[underline]Q[/underline]uit", variant="error", id="quit"),
            Button("[underline]C[/underline]ancel", variant="primary", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()

    def action_quit(self) -> None:
        self.app.exit()

    def action_cancel(self) -> None:
        self.app.pop_screen()
