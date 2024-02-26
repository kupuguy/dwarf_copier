"""Pre copy screen.

After selecting sessions we display the details of each session to be copied and allow
selecting darks, biases and flats.
"""

from dataclasses import replace
from pathlib import Path

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Log

from dwarf_copier import configuration
from dwarf_copier.configuration import ConfigTarget
from dwarf_copier.model import State
from dwarf_copier.widgets.prev_next import PrevNext
from dwarf_copier.widgets.session_summary import SessionSummary


class PreCopy(Screen[State]):
    """Screen to display sessions present on a source."""

    state: State

    def __init__(
        self,
        state: State,
    ) -> None:
        self.state = state
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create our widgets."""
        yield Header()
        with VerticalScroll(classes="selected_sessions"):
            for index, ps in enumerate(self.state.selected):
                yield SessionSummary(ps, self.state.source, id=f"session_{index}")
        self.log_widget = Log()
        yield self.log_widget
        pn = PrevNext()
        pn.valid = True
        yield pn
        yield Footer()

    def on_mount(self) -> None:
        self.log_widget.write_line(f"Loaded with {len(self.state.selected)} selected.")

    @on(PrevNext.Prev)
    def prev_pressed(self) -> None:
        """Pressing 'next' dismisses this screen."""
        self.dismiss(replace(self.state, ok=False))

    @on(PrevNext.Next)
    def next_pressed(self) -> None:
        """Pressing 'next' dismisses this screen."""
        self.dismiss(replace(self.state, ok=True))


if __name__ == "__main__":

    class TestApp(App[State]):
        """Dummy app for testing this screen."""

        CSS_PATH = "../dwarf-copy.css"

        def on_mount(self) -> None:
            self.run_dummy()

        @work
        async def run_dummy(self) -> None:
            source_path = Path("C:\\Backup\\Dwarf_II_2024_01_18\\Astronomy")
            source = configuration.ConfigSourceDrive(
                name="Test Source",
                path=source_path,
                darks=[
                    "DWARF_RAW_EXP_${exp}_GAIN_${gain}_${Y}-${M}-${d}*",
                    "DWARF_DARK/exp_${exp}_gain_${gain}_bin_${bin}",
                ],
            )
            target = ConfigTarget(
                name="Test Target",
                path="C:/TEST_TARGET",
                format="Backup",
            )
            driver = source.driver
            selected_paths = [
                source_path
                / "DWARF_RAW_Jupiter_EXP_0.0008_GAIN_0_2024-01-16-22-16-30-229",
                source_path / "DWARF_RAW_M1_EXP_15_GAIN_80_2024-01-18-21-04-26-954",
            ]
            selected = [
                s for p in selected_paths if (s := driver.create_session(p)) is not None
            ]
            format = configuration.config.get_format("Backup")
            state = State(source, target, selected, format)
            screen = PreCopy(state)
            new_state = await self.app.push_screen_wait(screen=screen)
            self.exit(new_state)

    app = TestApp()
    result = app.run()

    from rich import print

    print(result)
