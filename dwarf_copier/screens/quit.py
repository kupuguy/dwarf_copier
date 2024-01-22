"""Model dialog to confirm leaving the app."""
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class QuitScreen(ModalScreen):
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
            self.dismiss(True)
        else:
            self.dismiss(False)
