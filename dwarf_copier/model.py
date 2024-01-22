"""Data models."""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class ShotsInfo(BaseModel):
    """Information about shots contained within a session directory."""

    dec: float = Field(
        description="Declination (or 0.0 if not set). Example: 22.01469444"
    )
    ra: float = Field(
        description="Right ascension (or 0.0 if not set). Example: 5.575916667"
    )
    binning: str = Field(description="1x1 for 4k, 2x2 for 2k images.")
    exp: float = Field(description="Exposure, e.g.: 15 or 0.001")
    format: str = Field(description="Format: FITS or TIFF")
    gain: int = Field(description="Gain. Example: 80")
    ir: str = Field(description="IR filter CUT or PASS")
    shotsStacked: int = Field(description="Number of shots stacked by Dwarf e.g.: 286")
    shotsTaken: int = Field(description="Number of shots taken e.g. 287")
    shotsToTake: int = Field(description="Number of shots programmed to take e.g.: 300")
    target: str = Field(description='Name of target, e.g. "M1"')


class PhotoSession(BaseModel):
    """Data for a single photo session.

    i.e. a folder containing many nnnn.fits files,
     also stacked.jpg, stacked16.png and shotsinfo.json.
    """

    path: Path
    info: ShotsInfo | None = None
    date: datetime
