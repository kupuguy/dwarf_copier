"""Model dialog to confirm leaving the app."""
import logging

from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, RadioButton, RadioSet

from dwarf_copier.configuration import (
    ConfigSource,
    ConfigTarget,
    config,
)
from dwarf_copier.model import PartialState
from dwarf_copier.widgets.prev_next import PrevNext


class SelectSourceTarget(Screen[PartialState]):
    """Screen to select source and target."""

    BINDINGS = []
    source: ConfigSource | None = None
    target: ConfigTarget | None = None

    # valid = reactive(False)

    def __init__(
        self,
        state: PartialState,
    ) -> None:
        self.source = state.source
        self.target = state.target
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="source_selection"):
            yield Label("Select source and destination for image copy:", id="top_text")
            with RadioSet(id="sources") as rs:
                rs.border_title = "Source"
                for src in config.sources:
                    logging.info(
                        "Selected: %s, src %r, self.source %r",
                        src == self.source,
                        src,
                        self.source,
                    )
                    yield RadioButton(label=f"{src.name}", value=src == self.source)

            with RadioSet(id="targets") as rs:
                rs.border_title = "Destination"
                for target in config.targets:
                    yield RadioButton(target.name, value=target == self.target)

            yield Label(id="current_source")
            yield Label(id="current_target")

        yield PrevNext(show_prev=False)
        yield Footer()

    def on_mount(self) -> None:
        """Set initial focus."""
        self.query_one("#sources").focus()
        self.form_is_valid()

    @on(RadioSet.Changed, "#sources")
    def source_change(self, event: RadioSet.Changed) -> None:
        """User selected a source."""
        self.source = config.sources[event.radio_set.pressed_index]
        self.form_is_valid()

    @on(RadioSet.Changed, "#targets")
    def target_changed(self, event: RadioSet.Changed) -> None:
        """User selected a target."""
        self.target = config.targets[event.radio_set.pressed_index]
        self.form_is_valid()

    def form_is_valid(self) -> None:
        """Form is valid only when both source and target have been selected."""
        if self.source is not None:
            self.query_one("#current_source", Label).update(self.source.describe())

        if self.target is not None:
            self.query_one("#current_target", Label).update(
                config.describe_target(self.target)
            )

        button_bar = self.query_one("PrevNext", PrevNext)
        button_bar.valid = self.source is not None and self.target is not None

    @on(PrevNext.Next)
    def next_pressed(self) -> None:
        """Pressing 'next' dismisses this screen."""
        if self.source is not None and self.target is not None:
            self.dismiss(
                PartialState(source=self.source, target=self.target)
            )
