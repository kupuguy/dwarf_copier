"""Main dashboard screen."""
from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header
from textual.worker import Worker

from dwarf_copier.config import ConfigSource, ConfigTarget, ConfigurationModel
from dwarf_copier.screens.show_sessions import ShowSessions

from .source_target import SelectSourceTarget


class DashboardScreen(Screen):
    """Main screen for the app.

    This screen shows a list of Dwarf Telescopes from which we can copy files.
    """

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        """Dashboard screen actually just controls the screens in the workflow."""
        self.workflow()

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Called when the worker state changes."""
        self.log(event)
        if event.worker.is_finished:
            self.app.exit()

    @work(exclusive=True)
    async def workflow(self) -> None:
        """Main app workflow.

        This worker kicks off each screen in turn but because some screens have a 'prev'
        option we also have to allow going back.
        """
        source: ConfigSource | None = None
        target: ConfigTarget | None = None

        step = 1
        while True:
            config: ConfigurationModel = self.app.config  # type:ignore
            match step:
                case 1:
                    res = await self.app.push_screen(
                        screen=SelectSourceTarget(config, source, target),
                        wait_for_dismiss=True,
                    )
                    source, target = res
                    step += 1

                case 2:
                    sessions = await self.app.push_screen(
                        screen=ShowSessions(config, source, target),
                        wait_for_dismiss=True,
                    )
                    if sessions is None:
                        step -= 1
                    else:
                        step += 1
                case _:
                    break
