"""Data models."""

from dataclasses import asdict, dataclass, field
from functools import cached_property
from pathlib import Path
from queue import Queue
from string import Template
from typing import Self

from pydantic import BaseModel

from dwarf_copier.configuration import (
    ConfigFormat,
    ConfigSource,
    ConfigTarget,
    ConfigTemplate,
)
from dwarf_copier.source_directory import SourceDirectory


@dataclass
class DestinationDirectory:
    """PhotoSession bound to a target and format."""

    source_directory: SourceDirectory
    config_destination: ConfigTarget
    config_format: ConfigFormat

    @cached_property
    def destination(self) -> Path:
        """Compute destination path."""
        dest_path = self.config_destination.path / self.source_directory.format(
            self.config_format.path
        )
        return dest_path

    def format(self, template: Template, name: str = "") -> str:
        return self.source_directory.format(template, name)


@dataclass
class Specials:
    """Handler for special files: darks, flats, and biases."""

    session: DestinationDirectory
    source: ConfigSource
    target: ConfigTarget
    format: ConfigFormat
    templates: list[ConfigTemplate]

    # @cache
    def destination(self, source: Path, template: ConfigTemplate) -> Path | None:
        """Destination path for currently selected source."""
        base = self.session.destination
        return base / source

    @cached_property
    def candidates(self) -> set[Path]:
        masks = [self.session.format(template) for template in self.templates]
        candidates: set[Path] = set()
        driver = self.source.driver
        for m in masks:
            candidates |= set(driver.match_wildcards(self.source.path, m))

        return candidates

    @cached_property
    def best_candidate(self) -> Path | None:
        """Find the best candidate.

        This could be improved but for now we just return the first match found from
        the first mask that has a match. That way at least manual darks should take
        precedence over Dwarf automatic darks.
        """
        masks = [self.session.format(template) for template in self.templates]
        driver = self.source.driver
        for m in masks:
            candidates = list(driver.match_wildcards(self.source.path, m))
            if candidates:
                return candidates[0]
        return None


@dataclass(frozen=True)
class State:
    """Save passing all these values together, group into a single app state."""

    source: ConfigSource
    target: ConfigTarget
    selected: list[SourceDirectory]
    format: ConfigFormat
    ok: bool = False

    @classmethod
    def from_partial(cls, partial: "PartialState") -> Self:
        if partial.is_complete():
            return cls(**asdict(partial))
        raise TypeError("Partial state is incomplete.")


@dataclass(frozen=True)
class PartialState:
    """State but most fields are optional."""

    source: ConfigSource | None = None
    target: ConfigTarget | None = None
    selected: list[SourceDirectory] = field(default_factory=list)
    format: ConfigFormat | None = None
    ok: bool = False

    def is_complete(self) -> bool:
        return (
            self.source is not None
            and self.target is not None
            and self.format is not None
        )

    @classmethod
    def from_state(cls, state: "State") -> Self:
        return cls(**asdict(state))


class QuitCommand(BaseModel):
    """Sent when we're done copying to shut down workers."""

    @property
    def description(self) -> str:
        """Progress tracking."""
        return "Finished"


class CopyOrLinkBase(BaseModel):
    """Common parts of Copy and Link commands."""

    source: Path
    dest: Path
    source_folder: Path
    working_folder: Path

    @property
    def source_relative(self) -> Path:
        """Source file path relative to source folder."""
        return self.source.relative_to(self.source_folder)

    @property
    def dest_relative(self) -> Path:
        """Destination file path relative to working folder."""
        return self.dest.relative_to(self.working_folder)


class CopyCommand(CopyOrLinkBase):
    """Copy a single file."""

    @property
    def description(self) -> str:
        """Progress tracking."""
        return f"[b]Copy[/b] {self.source_relative} -> {self.dest_relative}"


class LinkCommand(CopyOrLinkBase):
    """Create a symlink."""

    @property
    def description(self) -> str:
        """Progress tracking."""
        return f"[b]Link[/b] {self.source_relative} -> {self.dest_relative}"


BaseCommand = QuitCommand | CopyCommand | LinkCommand
CommandQueue = Queue[BaseCommand]
QUIT_COMMAND = QuitCommand()
