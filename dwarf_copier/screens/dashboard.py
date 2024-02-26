"""Main dashboard screen."""


from dataclasses import replace
from typing import Awaitable, Callable

from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header
from textual.worker import Worker

from dwarf_copier.configuration import config
from dwarf_copier.model import PartialState, State
from dwarf_copier.screens.copy_files import CopyFiles
from dwarf_copier.screens.pre_copy import PreCopy
from dwarf_copier.screens.show_sessions import ShowSessions

from .source_target import SelectSourceTarget

StateMachineStep = Callable[[], Awaitable["StateMachineStep | None"]]


class DashboardScreen(Screen):
    """Main screen for the app.

    This screen shows a list of Dwarf Telescopes from which we can copy files.
    """

    state: PartialState

    _current: StateMachineStep

    def __init__(
        self, name: str | None = None, id: str | None = None, classes: str | None = None
    ) -> None:
        self.state = PartialState(
            source=None,
            target=None,
            selected=[],
            format=None,
        )
        super().__init__(name=name, id=id, classes=classes)

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

    @work
    async def workflow(self) -> None:
        """Main app workflow.

        This worker kicks off each screen in turn but because some screens have a 'prev'
        option we also have to allow going back.
        """
        self._current = self.when_copy_files

        self.log.warning("State step complete")

        while await self.step():
            self.log.info(self.state)
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
        new_state = await self.app.push_screen(
            screen=SelectSourceTarget(self.state),
            wait_for_dismiss=True,
        )
        if new_state.source is not None and new_state.target is not None:
            self.state = replace(
                new_state,
                format=config.get_format(new_state.target.format),
            )
            return self.when_select_sessions
        return self.when_select_source

    async def when_select_sessions(self) -> StateMachineStep:
        state = self.state
        if state.source is None or state.target is None:
            return self.when_select_source

        new_state: State = await self.app.push_screen_wait(
            screen=ShowSessions(State.from_partial(state)),
        )
        if not (new_state.ok and new_state.selected):
            return self.when_select_source

        self.state = PartialState.from_state(new_state)
        return self.when_pre_copy

    async def when_pre_copy(self) -> StateMachineStep | None:
        if not self.state.is_complete():
            return self.when_select_sessions

        screen = PreCopy(State.from_partial(self.state))
        new_state = await self.app.push_screen_wait(screen=screen)
        if new_state.ok:
            return self.when_copy_files
        return self.when_select_sessions

    async def when_copy_files(self) -> StateMachineStep | None:
        if not self.state.is_complete():
            return self.when_select_sessions

        screen = CopyFiles(State.from_partial(self.state))
        result = await self.app.push_screen_wait(screen=screen)
        self.notify(str(result))
        return None
