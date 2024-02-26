"""Model for the shotsInfo.json file present in Dwarf II photo directories."""
from fractions import Fraction

from pydantic import BaseModel, Field


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
