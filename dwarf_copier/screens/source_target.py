"""Model dialog to confirm leaving the app."""
import logging

from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, RadioButton, RadioSet

from dwarf_copier.config import ConfigSource, ConfigTarget, ConfigurationModel
from dwarf_copier.widgets.prev_next import PrevNext


class SelectSourceTarget(Screen[tuple[ConfigSource, ConfigTarget]]):
    """Screen to select source and target."""

    BINDINGS = []
    config: ConfigurationModel
    source: ConfigSource | None = None
    target: ConfigTarget | None = None

    # valid = reactive(False)

    def __init__(
        self,
        config: ConfigurationModel,
        source: ConfigSource | None,
        target: ConfigTarget | None,
    ) -> None:
        self.config = config
        self.source = source
        self.target = target
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="source_selection"):
            yield Label("Select source and destination for image copy:", id="top_text")
            with RadioSet(id="sources") as rs:
                rs.border_title = "Source"
                for src in self.config.sources:
                    logging.info(
                        "Selected: %s, src %r, self.source %r",
                        src == self.source,
                        src,
                        self.source,
                    )
                    yield RadioButton(label=f"{src.name}", value=src == self.source)

            with RadioSet(id="targets") as rs:
                rs.border_title = "Destination"
                for target in self.config.targets:
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
        self.source = self.config.sources[event.radio_set.pressed_index]
        self.form_is_valid()

    @on(RadioSet.Changed, "#targets")
    def target_changed(self, event: RadioSet.Changed) -> None:
        """User selected a target."""
        self.target = self.config.targets[event.radio_set.pressed_index]
        self.form_is_valid()

    def form_is_valid(self) -> None:
        """Form is valid only when both source and target have been selected."""
        if self.source is not None:
            self.query_one("#current_source", Label).update(self.source.describe())

        if self.target is not None:
            self.query_one("#current_target", Label).update(
                self.config.describe_target(self.target)
            )

        button_bar = self.query_one("PrevNext", PrevNext)
        button_bar.valid = self.source is not None and self.target is not None

    @on(PrevNext.Next)
    def next_pressed(self) -> None:
        """Pressing 'next' dismisses this screen."""
        if self.source is not None and self.target is not None:
            self.dismiss((self.source, self.target))
