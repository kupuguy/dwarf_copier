"""Summary widget for a single session."""
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable, Sequence

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, DirectoryTree, Label, Static

from dwarf_copier.configuration import ConfigSource
from dwarf_copier.model import PhotoSession


class FilteredDirectoryTree(DirectoryTree):
    """DirectoryTree filtered to only matching patterns."""

    def __init__(
        self,
        patterns: list[str],
        path: str | Path,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        self.patterns = patterns
        self.parents: set[str] = set()
        for p in patterns:
            p = p.replace("\\", "/")
            parts = p.split("/")
            for i in range(len(parts) - 1):
                self.parents.add("/".join(parts[: i + 1]))

        super().__init__(
            path=path, name=name, id=id, classes=classes, disabled=disabled
        )

    def matches(self, p: Path, include_parents: bool = True) -> bool:
        filename = str(p.relative_to(self.path))
        self.app.log.info(f"{filename=}")

        if include_parents:
            return any(fnmatch(filename, pattern) for pattern in self.patterns) or any(
                fnmatch(filename, parent) for parent in self.parents
            )
        else:
            return any(fnmatch(filename, pattern) for pattern in self.patterns)

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        self.app.log.info(f"{self.patterns=}")

        paths = [path for path in paths if self.matches(path)]
        if not paths:
            self.notify("No matching directories found.", severity="error")
        return paths

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        if not self.matches(event.path, include_parents=False):
            event.stop()


class DirSelectScreen(ModalScreen[Path | None]):
    """Modal dialog to select a single directory."""

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
        masks: list[str],
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        self.caption = caption
        self.base = base
        self.masks = masks
        super().__init__(name=name, id=id, classes=classes)

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield FilteredDirectoryTree(
                self.masks,
                self.base,
            )
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
        def update_path(path: Path | None) -> None:
            self.path = path
            path_control: Static = self.query_one("#path", Static)
            path_control.update(self.message)

        self.app.push_screen(
            DirSelectScreen(self.label.lower(), self.base, self.masks),
            callback=update_path,
        )

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
        source: ConfigSource,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        self.session = session
        self.source_path = source.path
        self.source = source
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)

    def compose(self) -> ComposeResult:
        """Create the widgets."""
        with Container(classes="single_session"):
            yield Label("Copy")
            yield Static(str(self.session.path))
            yield Label("To")
            yield Static("...")
            dark_masks = [
                self.session.format(template) for template in self.source.darks
            ]
            yield DirSelector(
                "Darks", self.session.darks, self.source_path, masks=dark_masks
            )
            yield DirSelector("Flats", self.session.darks, self.source_path)
            yield DirSelector("Biases", self.session.darks, self.source_path)
