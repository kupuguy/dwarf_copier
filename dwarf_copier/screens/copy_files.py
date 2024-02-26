"""Screen showing progress as files are copied/linked."""

import shutil
from dataclasses import replace
from pathlib import Path
from queue import Queue
from tempfile import mkdtemp

from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Log
from textual.worker import Worker

from dwarf_copier.configuration import (
    ConfigFormat,
    ConfigSource,
    ConfigTarget,
    ConfigurationModel,
    config,
)
from dwarf_copier.model import (
    BaseDriver,
    CommandQueue,
    CopyCommand,
    CopySession,
    LinkCommand,
    PhotoSession,
    State,
)
from dwarf_copier.widgets.copier import Copier, CopyGroup
from dwarf_copier.widgets.prev_next import PrevNext


class CopyFiles(Screen[State]):
    """Screen to display sessions present on a source."""

    state: State
    config: ConfigurationModel
    selected: list[PhotoSession]
    sessions: dict[str, PhotoSession]
    driver: BaseDriver
    queue: CommandQueue
    session: PhotoSession | None
    controller: Worker[None] | None = None
    total_copied: int = 0

    def __init__(
        self,
        state: State,
    ) -> None:
        self.state = state
        self.source = state.source
        self.target = state.target
        self.selected = state.selected
        self.format = state.format
        self.driver = state.driver
        self.queue = Queue()
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create our widgets."""
        yield Header()
        yield CopyGroup(config.general.workers, self.driver, self.queue, id="copier")
        self.log_widget = Log()
        yield self.log_widget
        yield PrevNext()
        yield Footer()

    def on_mount(self) -> None:
        self.controller = self.copy_controller(
            self.selected, self.source, self.target, self.format
        )

    async def on_unmount(self) -> None:
        await self.workers.wait_for_complete()

    def trace(self, message: str) -> None:
        # rich.print(message)
        self.log_widget.write_line(message)

    @work
    async def copy_controller(
        self,
        sessions: list[PhotoSession],
        source: ConfigSource,
        target: ConfigTarget,
        format: ConfigFormat,
    ) -> None:
        copier = self.query_one("#copier", CopyGroup)
        try:
            await self.copy_controller_impl(sessions, source, target, format)
        finally:
            await copier.shutdown()
        self.dismiss(replace(self.state, ok=True))

    async def copy_controller_impl(
        self,
        sessions: list[PhotoSession],
        source: ConfigSource,
        target: ConfigTarget,
        format: ConfigFormat,
    ) -> None:
        for photo_session in sessions:
            self.trace("")
            session = CopySession(photo_session, target, format)
            destination_path = session.destination
            destination_path.parent.mkdir(exist_ok=True, parents=True)
            self.trace(f"Final destination {destination_path}")
            working_path = Path(mkdtemp(dir=str(destination_path.parent)))
            try:
                mkdirs, links, copies = self.driver.prepare(
                    format, session.photo_session, working_path
                )
                for md in mkdirs:
                    self.trace(f"mkdir {md}")
                for ln in links:
                    self.trace(f"link {ln} -> {links[ln]}")
                    self.queue.put(
                        LinkCommand(
                            source=ln,
                            dest=working_path / links[ln],
                            source_folder=source.path,
                            working_folder=working_path,
                        )
                    )
                for cp in copies:
                    self.trace(f"copy {cp} -> {copies[cp]}")
                    self.queue.put(
                        CopyCommand(
                            source=cp,
                            dest=working_path / copies[cp],
                            source_folder=source.path,
                            working_folder=working_path,
                        )
                    )

                await self.query_one("#copier", CopyGroup).shutdown()

                self.trace(f"move {working_path} {destination_path}")
                working_path.rename(destination_path)
            finally:
                shutil.rmtree(working_path, ignore_errors=True)

    async def on_copier_progress(self, event: Copier.Progress) -> None:
        self.trace(event.text)
        self.total_copied += event.bytes
        event.stop()
