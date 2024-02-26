"""Data models."""

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from fractions import Fraction
from functools import cached_property
from pathlib import Path
from queue import Queue
from string import Template
from typing import Callable, Self

from pydantic import BaseModel, Field

from dwarf_copier.configuration import (
    ConfigFormat,
    ConfigSource,
    ConfigTarget,
    ConfigTemplate,
)


class ShotsInfo(BaseModel):
    """Use shotsinfo.json to describe a session."""

    dec: float = Field(
        description="Declination (or 0.0 if not set). Example: 22.01469444", alias="DEC"
    )
    ra: float = Field(
        description="Right ascension (or 0.0 if not set). Example: 5.575916667",
        alias="RA",
    )
    binning: str = Field(description="1x1 for 4k, 2x2 for 2k images.")
    exp: str = Field(description="Exposure, e.g.: 15 or 0.001")
    format: str = Field(description="Format: FITS or TIFF")
    gain: int = Field(description="Gain. Example: 80")
    ir: str = Field(description="IR filter CUT or PASS")
    shotsStacked: int = Field(description="Number of shots stacked by Dwarf e.g.: 286")
    shotsTaken: int = Field(description="Number of shots taken e.g. 287")
    shotsToTake: int = Field(description="Number of shots programmed to take e.g.: 300")
    target: str = Field(description='Name of target, e.g. "M1"')

    @property
    def exp_fraction(self) -> Fraction:
        return Fraction(self.exp)

    @property
    def exp_decimal(self) -> str:
        exp = Fraction(self.exp)
        return str(int(exp) if exp.is_integer() else float(exp))


class PhotoSession(BaseModel):
    """Data for a single photo session.

    i.e. a folder containing many nnnn.fits files,
     also stacked.jpg, stacked16.png and shotsinfo.json.
    """

    path: Path
    info: ShotsInfo
    date: datetime

    darks: Path | None = Field(
        default=None, description="Dark frames, optional, Dwarf's own or taken manually"
    )
    flats: Path | None = Field(
        default=None, description="Biases (optional, must be taken manually)"
    )
    biases: Path | None = Field(
        default=None, description="Flats (optional, must be taken manually)"
    )

    def format(self, template: Template, name: str = "") -> str:
        # TODO: make this lazier
        d = {
            "bin": "1" if self.info.binning == "1*1" else "2",
            "exp": self.info.exp_decimal,
            "gain": self.info.gain,
            "Y": f"{self.date.year:02}",
            "M": f"{self.date.month:02}",
            "d": f"{self.date.day:02}",
            "H": f"{self.date.hour:02}",
            "m": f"{self.date.minute:02}",
            "S": f"{self.date.second:02}",
            "ms": f"{self.date.microsecond//1000:03}",
            "target": self.info.target,
            "target_": f"{self.info.target}_" if self.info.target else "",
            "name": name,
        }
        return template.safe_substitute(d)


@dataclass
class CopySession:
    """PhotoSession bound to a target and format."""

    photo_session: PhotoSession
    config_destination: ConfigTarget
    config_format: ConfigFormat

    @cached_property
    def destination(self) -> Path:
        """Compute destination path."""
        dest_path = self.config_destination.path / self.photo_session.format(
            self.config_format.path
        )
        return dest_path

    def format(self, template: Template, name: str = "") -> str:
        return self.photo_session.format(template, name)


@dataclass
class Specials:
    """Handler for special files: darks, flats, and biases."""

    session: CopySession
    source: ConfigSource
    target: ConfigTarget
    driver: "BaseDriver"
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
        for m in masks:
            candidates |= set(self.driver.match_wildcards(self.source.path, m))

        return candidates

    @cached_property
    def best_candidate(self) -> Path | None:
        """Find the best candidate.

        This could be improved but for now we just return the first match found from
        the first mask that has a match. That way at least manual darks should take
        precedence over Dwarf automatic darks.
        """
        masks = [self.session.format(template) for template in self.templates]
        for m in masks:
            candidates = list(self.driver.match_wildcards(self.source.path, m))
            if candidates:
                return candidates[0]
        return None


@dataclass(frozen=True)
class State:
    """Save passing all these values together, group into a single app state."""

    source: ConfigSource
    target: ConfigTarget
    selected: list[PhotoSession]
    format: ConfigFormat
    driver: "BaseDriver"
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
    selected: list[PhotoSession] = field(default_factory=list)
    format: ConfigFormat | None = None
    driver: "BaseDriver | None" = None
    ok: bool = False

    def is_complete(self) -> bool:
        return (
            self.source is not None
            and self.target is not None
            and self.format is not None
            and self.driver is not None
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


class BaseDriver(ABC):
    """Interface used to access photo files.

    Different concrete implementations are used for disk drives, ftp, etc.
    """

    def __init__(self, root: Path) -> None:
        pass

    @abstractmethod
    def list_dirs(self, callback: Callable[[PhotoSession | None], None]) -> None:
        ...

    @abstractmethod
    def prepare(
        self,
        format: ConfigFormat,
        session: PhotoSession,
        target_path: Path,
    ) -> tuple[list[Path], dict[Path, str], dict[Path, str]]:
        """Build maps of files to be copied or linked."""

    @abstractmethod
    def copy_file(self, src: Path, dest: Path) -> None:
        """Copy a single file."""

    @abstractmethod
    def link_file(self, src: Path, dest: Path) -> None:
        """Create a link from dest back to src."""

    @abstractmethod
    def match_wildcards(self, base: Path, filename: str) -> list[Path]:
        """Expand a wildcard pattern."""
