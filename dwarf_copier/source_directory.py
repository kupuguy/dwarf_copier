"""Model for a single directory on the source. Used to format target names."""
from datetime import datetime
from pathlib import Path
from string import Template

from pydantic import BaseModel, Field

from dwarf_copier.shots_info import ShotsInfo


class SourceDirectory(BaseModel):
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
