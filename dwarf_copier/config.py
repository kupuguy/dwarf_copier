"""dwarf-copy configuration.

Read/write configuration file. Searches locations to find an available file.
"""

import logging
import os
from enum import StrEnum
from pathlib import Path
from typing import Sequence

import yaml
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SourceType(StrEnum):
    """Image source types."""

    drive = "Drive"
    ftp = "FTP"


class ConfigGeneral(BaseModel):
    """General configuration."""

    theme: str = Field(default="dark", description="App theme")


class ConfigSource(BaseModel):
    """Defines a source of Dwarf data, may be a local path or a network drive."""

    name: str = Field(description="Displayed name for the source")
    type: SourceType = Field(
        ...,
        description="The type of source, e.g. a filesystem mount or an FTP connection",
    )
    path: str = Field(
        default="/DWARF_II", description="Path to the DWARF_II image files"
    )
    ip_address: str | None = Field(
        None, description="Network address for FTP connections"
    )
    password: str = Field(default="", description="Password for networked source")
    user: str = Field(default="", description="User name for networked drives")


class ConfigTarget(BaseModel):
    """Destination folder to contain the copied images."""

    name: str
    path: str


class ConfigFormat(BaseModel):
    """File layout for target."""

    name: str


class ConfigurationModel(BaseModel):
    """Model for the configuration file."""

    model_config = ConfigDict(use_enum_values=True)

    general: ConfigGeneral = Field(default_factory=ConfigGeneral)
    sources: list[ConfigSource] = Field(
        default_factory=list, description="List of sources"
    )
    targets: list[ConfigTarget] = Field(
        default_factory=list, description="List of targets"
    )
    formats: list[ConfigFormat] = Field(
        default_factory=list, description="List of formats"
    )


class Settings(BaseSettings):
    """Global settings."""

    model_config = SettingsConfigDict(env_prefix="dwarf_copy_")

    config_filename: str = "dwarf-copy.yml"
    config_path: str = Field(
        default="~/AppData/dwarf-copy",
        description=f"Search path for config files (use '{os.pathsep
                                                          }' to separate elements)",
    )


def load_config(
    name: str = "",
    search_path: Sequence[str] = (),
) -> ConfigurationModel:
    """Search for configuration file and load the first one found."""
    settings = Settings()
    if not name:
        name = settings.config_filename
    if not search_path:
        search_path = settings.config_path.split(os.pathsep)

    for dir in [Path(s).expanduser().resolve() for s in search_path] + [
        (Path(__file__).parent.resolve())
    ]:
        config_file = dir / name
        logging.debug(f"config {config_file}")
        if config_file.exists():
            data: dict = yaml.safe_load(config_file.read_text())
            return ConfigurationModel(**data)

    return ConfigurationModel()
