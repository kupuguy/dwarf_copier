"""Custom widget for the button bar with Prev/Next buttons."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button


class PrevNext(Horizontal):
    """Button bar with <Prev Next> buttons."""

    DEFAULT_CSS = """
        PrevNext {
            align: right top;
            color: $text;
            dock: bottom;
            height: 4;
        }
        """

    class Next(Message):
        """Sent when 'Next' is pressed."""

    class Prev(Message):
        """Sent when 'Prev' is pressed."""

    valid = reactive(False)

    def __init__(self, show_prev: bool = True, show_next: bool = True) -> None:
        self.show_prev = show_prev
        self.show_next = show_next
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create the widgets."""
        btn_prev = Button("< Prev", disabled=False, id="btn_prev")
        if not self.show_prev:
            btn_prev.visible = False
        yield btn_prev
        btn_next = Button(
            "Next >", variant="success", disabled=not self.valid, id="btn_next"
        )
        btn_next.tooltip = "Press 'Next' to continue"
        if not self.show_next:
            btn_next.visible = False
        yield btn_next

    @on(Button.Pressed, "#btn_prev")
    def prev_pressed(self, message: Button.Pressed) -> None:
        """Notify 'Prev' was pressed."""
        message.stop()
        self.post_message(self.Prev())

    @on(Button.Pressed, "#btn_next")
    def next_pressed(self, message: Button.Pressed) -> None:
        """Notify 'Next' was pressed."""
        message.stop()
        self.post_message(self.Next())

    def watch_valid(self) -> None:
        """Enable/disable Next as appropriate."""
        try:
            self.query_one("#btn_next", Button).disabled = not self.valid
        except NoMatches:
            pass
