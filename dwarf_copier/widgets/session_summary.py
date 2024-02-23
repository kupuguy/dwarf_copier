"""Summary widget for a single session."""
from pathlib import Path
from typing import Sequence, TypeVar

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, DirectoryTree, Label, Static

from dwarf_copier.model import PhotoSession

CellType = TypeVar("CellType")
"""Type used for cells in the DataTable."""

"""Model dialog to select a directory."""


class DirSelectScreen(ModalScreen[Path | None]):
    """Screen with a dialog to quit."""

    DEFAULT_CSS = """
        DirSelectScreen {
            align: center middle;
            #dialog {
                padding: 0 1;
                width: 60;
                height: 20;
                border: thick $secondary-background 80%;
                background: $surface;
            }
            #buttons {
                height: 3;
                width: 1fr;
                content-align: right middle;
            }
        }
    """
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        caption: str,
        base: Path,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        self.caption = caption
        self.base = base
        super().__init__(name=name, id=id, classes=classes)

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield DirectoryTree(self.base)
            yield Container(Button("Clear", variant="error", id="clear"), id="buttons")

    def on_mount(self) -> None:
        self.title = f"Select folder for {self.caption}"

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        self.dismiss(event.path)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "clear":
            self.dismiss(None)


class DirSelector(Widget):
    """Display a directory, allow changing it using popup."""

    def __init__(
        self,
        label: str,
        path: Path | None,
        base: Path,
        masks: Sequence[str] = ("*",),
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        self.label = label
        self.path = path
        self.base = base
        self.masks = list(masks)
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)

    def compose(self) -> ComposeResult:
        yield Button(self.label)
        yield Container(Static(self.message, id="path"), id="message")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        self.path = await self.app.push_screen_wait(
            DirSelectScreen(self.label.lower(), self.base)
        )
        path_control: Static = self.query_one("#path", Static)
        path_control.update(self.message)

    @property
    def message(self) -> str:
        if self.path is None:
            msg = "--- none selected ---"
        else:
            src = (
                "-None-" if self.path is None else str(self.path.relative_to(self.base))
            )
            dest = "hello!"
            msg = f"{src}\n->\n{dest}"
        return msg


class SessionSummary(Widget):
    """Just like DataTable except column headers are clickable to sort."""

    def __init__(
        self,
        session: PhotoSession,
        source_path: Path,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        self.session = session
        self.source_path = source_path
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)

    def compose(self) -> ComposeResult:
        """Create the widgets."""
        with Container(classes="single_session"):
            yield Label("Copy")
            yield Static(str(self.session.path))
            yield Label("To")
            yield Static("...")
            yield DirSelector("Darks", self.session.darks, self.source_path)
            yield DirSelector("Flats", self.session.darks, self.source_path)
            yield DirSelector("Biases", self.session.darks, self.source_path)
