"""Help screen."""
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.reactive import var
from textual.screen import ModalScreen
from textual.widgets import Footer, MarkdownViewer


class HelpScreen(ModalScreen):
    """Need some help? Find it here."""

    BINDINGS = [
        ("q", "app.pop_screen", "Done"),
        Binding(
            key="question_mark",
            show=False,
            action="stop",
        ),
        ("t", "toggle_table_of_contents", "TOC"),
        Binding(key="s", show=False, action="noop"),
    ]

    path = var(Path(__file__).parent.parent / "help-text.md")

    @property
    def markdown_viewer(self) -> MarkdownViewer:
        """Get the Markdown widget."""
        return self.query_one(MarkdownViewer)

    def compose(self) -> ComposeResult:
        """Show the help-text.md file."""
        yield Footer()
        yield MarkdownViewer()

    async def on_mount(self) -> None:
        """When the help screen is opened load the help text."""
        self.markdown_viewer.focus()
        try:
            await self.markdown_viewer.go(self.path)
        except FileNotFoundError:
            self.app.exit(message=f"Unable to load {self.path!r}")

    def action_toggle_table_of_contents(self) -> None:
        """Toggle ToC."""
        self.markdown_viewer.show_table_of_contents = (
            not self.markdown_viewer.show_table_of_contents
        )

    async def action_noop(self) -> None:
        """Do nothing."""
        self.log.info("Just lazing around...")

    def action_done(self) -> None:
        """Dismiss the help."""
        self.log.info("I'm out of here!")
        self.app.pop_screen()
