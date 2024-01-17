"""model."""
from dataclasses import dataclass


@dataclass
class User:
    """just a sample model class."""

    name: str

    @property
    def name_upper(self) -> str:
        """Name in upper case."""
        return self.name.upper()
