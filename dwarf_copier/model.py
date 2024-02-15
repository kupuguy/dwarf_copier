"""Data models."""

from datetime import datetime
from fractions import Fraction
from pathlib import Path
from queue import Queue
from string import Template

from pydantic import BaseModel, Field


class ShotsInfo(BaseModel):
    """Information about shots contained within a session directory."""

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

    def format(self, template: Template, name: str = "") -> str:
        # TODO: make this lazier
        d = {
            "bin": "1" if self.info.binning == "1x1" else "2",
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
