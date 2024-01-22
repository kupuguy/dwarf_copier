"""dwarf-copy configuration.

Read/write configuration file. Searches locations to find an available file.
"""

import logging
import os
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Sequence

import rich
import yaml
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SourceType(StrEnum):
    """Image source types."""

    DRIVE = "Drive"
    FTP = "FTP"


class ConfigGeneral(BaseModel):
    """General configuration."""

    theme: str = Field(default="dark", description="App theme")


class ConfigSource(BaseModel):
    """Defines a source of Dwarf data, may be a local path or a network drive."""

    name: Annotated[str, Field(description="Displayed name for the source")]
    type: Annotated[
        SourceType,
        Field(
            default=SourceType.DRIVE,
            description="The type of source, e.g. a filesystem or an FTP connection",
        ),
    ] = SourceType.DRIVE
    path: Annotated[
        str, Field(default="/DWARF_II", description="Path to the DWARF_II image files")
    ]
    ip_address: Annotated[
        str | None, Field("", description="Network address for FTP connections")
    ] = ""
    password: Annotated[
        str, Field(default="", description="Password for networked source")
    ] = ""
    user: Annotated[
        str, Field(default="", description="User name for networked drives")
    ] = ""

    def describe(self) -> str:
        """Return formatted description of the source for display to the user."""
        return "\n".join(
            [
                s
                for s in [
                    f" Source: [b]{self.name}[/b]",
                    f"IP Addr: [i]{self.ip_address}[/i]"
                    if self.type == SourceType.FTP
                    else None,
                    f"   Path: [i]{self.path}[/i]",
                ]
                if s is not None
            ]
        )


class ConfigTarget(BaseModel):
    """Destination folder to contain the copied images."""

    name: str
    path: str
    format: str


class ConfigFormat(BaseModel):
    """File layout for target."""

    name: str
    description: str = ""


class ConfigurationModel(BaseModel):
    """Model for the configuration file."""

    model_config = ConfigDict(use_enum_values=True)

    general: Annotated[
        ConfigGeneral, Field(default_factory=ConfigGeneral)
    ] = ConfigGeneral()
    sources: Annotated[
        list[ConfigSource], Field(default_factory=list, description="List of sources")
    ] = [ConfigSource(name="MicroSD", path="D:\\DWARF_II\\Astronomy")]
    targets: Annotated[
        list[ConfigTarget], Field(default_factory=list, description="List of targets")
    ] = [
        ConfigTarget(
            name="Astrophotography", path="C:\\Astrophotography", format="Siril"
        )
    ]
    formats: Annotated[
        list[ConfigFormat], Field(default_factory=list, description="List of formats")
    ] = [ConfigFormat(name="Siril")]

    def describe_target(self, target: ConfigTarget) -> rich.text.Text:
        """Return formatted description of the source for display to the user."""
        fmt = next(
            (f for f in self.formats if f.name.lower() == target.format.lower()), None
        )

        text = rich.text.Text()
        text.append("Target: ")
        text.append(target.name, style="bold")
        text.append("\n   Path: ")
        text.append(target.path, style="italic")
        if fmt is None:
            text.append("\nBad format", style="error")
        else:
            text.append("\n" + fmt.description, style="italic")
        return text


class Settings(BaseSettings):
    """Global settings."""

    model_config = SettingsConfigDict(env_prefix="dwarf_copy_")

    config_filename: str = "dwarf-copy.yml"
    config_path: Annotated[
        str,
        Field(
            default="~/AppData/dwarf-copy",
            description=f"Search path for config files (use '{os.pathsep
                                                          }' to separate elements)",
        ),
    ]


DEFAULT_CONFIG = r"""
general:
  theme: dark

sources:
  - name: MicroSD
    type: Drive
    path: D:\DWARF_II\Astronomy
  - name: WiFi Direct
    type: FTP
    ip_address: 192.168.88.1
    path: /Astronomy
  - name: Home WiFi
    type: FTP
    ip_address: 192.168.1.217
    path: /Astronomy
targets:
  - name: Backup
    path: C:\Backup\Dwarf_II\
    format: Backup
  - name: Astrophotography
    path: C:\Astrophotography\
    format: Siril
formats:
  - name: Backup
  - name: Siril
"""


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

    for directory in [Path(s).expanduser().resolve() for s in search_path] + [
        (Path(__file__).parent.resolve())
    ]:
        config_file = directory / name
        logging.debug("config %s", config_file)
        if config_file.exists():
            data: dict = yaml.safe_load(config_file.read_text())
            logging.info("Using config %r", data)
            return ConfigurationModel(**data)

    logging.warning("No configuration found, using default")
    default_data = yaml.safe_load(DEFAULT_CONFIG)
    config = ConfigurationModel(**default_data)
    logging.warning("Config %r", config)
    return config
