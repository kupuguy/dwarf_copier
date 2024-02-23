"""Custom widget for the button bar with Prev/Next buttons."""


from dataclasses import dataclass

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Label
from textual.worker import Worker, get_current_worker

from dwarf_copier.model import (
    QUIT_COMMAND,
    BaseCommand,
    BaseDriver,
    CommandQueue,
    CopyCommand,
    LinkCommand,
    QuitCommand,
)


class Copier(Horizontal):
    """Widget to display status of background worker that copies files."""

    DEFAULT_CSS = """
        PrevNext {
            align: right top;
            color: $text;
            dock: bottom;
            height: 4;
        }
        """

    @dataclass
    class Progress(Message):
        """Starting to copy a file."""

        text: str
        bytes: int

    valid = reactive(False)

    def __init__(
        self, driver: BaseDriver, queue: CommandQueue, id: str | None = None
    ) -> None:
        self.driver = driver
        self.queue = queue
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        """Create the widgets."""
        yield Label(id="status")

    @on(Progress)
    def copy_file(self, message: Progress) -> None:
        """Update label to show current action."""
        self.query_one("#status", Label).update(message.text)

    @work(thread=True)
    def single_copy_worker(self) -> None:
        action: BaseCommand
        bytes: int = 0
        worker = get_current_worker()

        for action in iter(self.queue.get, QUIT_COMMAND):
            if worker.is_cancelled:
                break
            match action:
                case CopyCommand():
                    self.post_message(Copier.Progress(action.description, bytes))
                    bytes = action.source.stat().st_size
                    self.driver.copy_file(action.source, action.dest)

                case LinkCommand():
                    self.post_message(Copier.Progress(action.description, bytes))
                    bytes = 0
                    self.driver.link_file(action.source, action.dest)

                # Here for type checking, the for loop will just break on receiving QUIT
                case QuitCommand():
                    break

        if not worker.is_cancelled:
            self.post_message(Copier.Progress("Finished", bytes))


class CopyGroup(Vertical):
    """Group of copier widgets."""

    driver: BaseDriver
    queue: CommandQueue
    copiers: list[Copier]
    copy_workers: list[Worker[None]]

    def __init__(
        self,
        num_workers: int,
        driver: BaseDriver,
        queue: CommandQueue,
        id: str | None = None,
    ) -> None:
        self.num_workers = num_workers
        self.driver = driver
        self.queue = queue
        self.copiers = []
        self.copy_workers = []
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        """Create our widgets."""
        for i in range(self.num_workers):
            copier = Copier(self.driver, self.queue, id=f"copy_{i}")
            self.copiers.append(copier)
            yield copier

    def on_mount(self) -> None:
        """Kick off the child workers."""
        self.copy_workers = [copier.single_copy_worker() for copier in self.copiers]

    async def shutdown(self) -> None:
        if self.copy_workers:
            for _ in range(self.num_workers):
                self.queue.put(QUIT_COMMAND)

            await self.workers.wait_for_complete(self.copy_workers)
            self.copy_workers = []
