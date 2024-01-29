"""Main dashboard screen."""


from typing import Awaitable, Callable

from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header
from textual.worker import Worker

from dwarf_copier.config import ConfigSource, ConfigTarget
from dwarf_copier.drivers import disk
from dwarf_copier.model import PhotoSession
from dwarf_copier.screens.show_sessions import ShowSessions

from .source_target import SelectSourceTarget

StateMachineStep = Callable[[], Awaitable["StateMachineStep | None"]]


class DashboardScreen(Screen):
    """Main screen for the app.

    This screen shows a list of Dwarf Telescopes from which we can copy files.
    """

    source: ConfigSource | None = None
    target: ConfigTarget | None = None
    driver: disk.Driver | None = None
    sessions: list[PhotoSession]

    _current: StateMachineStep

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        """Dashboard screen actually just controls the screens in the workflow."""
        self.config = self.app.config  # type: ignore
        self.workflow()

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Called when the worker state changes."""
        self.log(event)
        if event.worker.is_finished:
            self.app.exit()

    @work
    async def workflow(self) -> None:
        """Main app workflow.

        This worker kicks off each screen in turn but because some screens have a 'prev'
        option we also have to allow going back.
        """
        self.source: ConfigSource | None = None
        self.target: ConfigTarget | None = None
        self.driver: disk.Driver | None = None
        self._current = self.when_copy_files

        self.log.warning("State step complete")

        while await self.step():
            pass

    async def step(self) -> bool:
        if self._current is None:
            return False

        next = await self._current()
        if next is not None:
            self._current = next
            return True

        return False

    async def when_select_source(self) -> StateMachineStep:
        self.driver = None
        res = await self.app.push_screen(
            screen=SelectSourceTarget(self.config, self.source, self.target),
            wait_for_dismiss=True,
        )
        if res is not None:
            self.source, self.target = res
            return self.when_select_sessions
        return self.when_select_source

    async def when_select_sessions(self) -> StateMachineStep:
        if self.source is None or self.target is None:
            return self.when_select_source

        if self.driver is None:
            self.driver = disk.Driver(self.source.path)

        sessions = await self.app.push_screen_wait(
            screen=ShowSessions(self.config, self.source, self.target),
        )
        if sessions is None:
            self.notify(f"No image sessions found in {self.source.path}")
            return self.when_select_source

        self.sessions = list(sessions)
        return self.when_copy_files

    async def when_copy_files(self) -> StateMachineStep | None:
        if not (self.source and self.target and self.sessions):
            return self.when_select_sessions
        self.log.error("Not yet implemented!")
        return None
