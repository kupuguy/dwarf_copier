"""Represents a single directory destination for files."""
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from string import Template

import dwarf_copier.configuration
from dwarf_copier.models.source_directory import SourceDirectory


@dataclass
class DestinationDirectory:
    """Destination directory combines SourceDirectory with a target and format."""

    source_directory: SourceDirectory
    config_destination: "dwarf_copier.configuration.ConfigTarget"
    config_format: "dwarf_copier.configuration.ConfigFormat"

    darks: Path | None = None
    flats: Path | None = None
    biases: Path | None = None

    def __post_init__(self) -> None:
        """Post initialisation."""
        self.darks = None
        self.flats = None
        self.biases = None

    @cached_property
    def destination(self) -> Path:
        """Compute destination path."""
        dest_path = (
            self.config_destination.path
            / self.source_directory.format_filename(self.config_format.path)
        )
        return dest_path

    def format_filename(self, template: Template, name: str = "") -> str:
        return self.source_directory.format_filename(template, name)
