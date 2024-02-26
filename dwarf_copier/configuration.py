"""dwarf-copy configuration.

Read/write configuration file. Searches locations to find an available file.
"""

import logging
import os
import sys
from abc import ABC, abstractmethod
from enum import StrEnum
from functools import cached_property
from pathlib import Path
from string import Template
from typing import Annotated, Callable, Literal, Self, Sequence

import rich.text
import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    GetPydanticSchema,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_core import core_schema
from pydantic_settings import BaseSettings, SettingsConfigDict

from dwarf_copier.source_directory import SourceDirectory

__all__ = ["config"]

ConfigTemplate = Annotated[
    Template,
    GetPydanticSchema(
        lambda _tp, handler: core_schema.no_info_after_validator_function(
            lambda s: Template(s),
            handler(str),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda t: t.template
            ),
        )
    ),
]


class SourceType(StrEnum):
    """Image source types."""

    DRIVE = "Drive"
    FTP = "FTP"
    MTP = "MTP"


class ConfigCopy(BaseModel):
    """Single copy or link."""

    source: str = Field(description="Wildcard pattern for matching source files")
    destination: ConfigTemplate = Field(description="Target filename")


class ConfigFormat(BaseModel):
    """File layout for target."""

    name: str
    description: str = ""
    path: ConfigTemplate = Field(description="Destination directory")
    darks: ConfigTemplate = Field(
        default=ConfigTemplate("../DWARF_DARK_EXP_${exp}_GAIN_${gain}_*"),
        description="Destination for darks relative to <path>",
    )
    flats: ConfigTemplate = Field(
        default=ConfigTemplate("../DWARF_FLATS_EXP_${exp}_GAIN_${gain}_*"),
        description="Destination for flats relative to <path>",
    )
    biases: ConfigTemplate = Field(
        default=ConfigTemplate("../DWARF_BIASES_EXP_${exp}_GAIN_${gain}_*"),
        description="Destination for biases relative to <path>",
    )
    directories: list[str] = Field(
        default=[], description="List of directories to create relative to <path>"
    )
    link_or_copy: list[ConfigCopy] = Field(
        default=[], description="Groups of files to link or copy"
    )
    copy_only: list[ConfigCopy] = Field(
        default=[], description="List of files to copy, never link"
    )


class BaseDriver(ABC):
    """Interface used to access photo files.

    Different concrete implementations are used for disk drives, ftp, etc.
    """

    def __init__(self, root: Path) -> None:
        pass

    @abstractmethod
    def list_dirs(self, callback: Callable[[SourceDirectory | None], None]) -> None:
        ...

    @abstractmethod
    def prepare(
        self,
        format: ConfigFormat,
        session: SourceDirectory,
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

    @abstractmethod
    def create_session(self, p: Path) -> SourceDirectory | None:
        """Create reference to a source directory."""


class ConfigGeneral(BaseModel):
    """General configuration."""

    theme: str = Field(default="dark", description="App theme")
    workers: int = Field(default=4, description="Number of workers to copy files.")


class ConfigSourceBase(BaseModel):
    """Defines a source of Dwarf data, may be a local path or a network drive."""

    name: Annotated[str, Field(description="Displayed name for the source")]
    path: Annotated[
        Path, Field(default="/DWARF_II", description="Path to the DWARF_II image files")
    ]
    link: Annotated[
        bool,
        Field(
            default=False,
            description="Try to create links instead of copying if link is true "
            "for both source and target.",
        ),
    ] = False

    darks: list[ConfigTemplate] = Field(
        default=[
            ConfigTemplate("DWARF_DARK_EXP_${exp}_GAIN_${gain}_*"),
            ConfigTemplate("DWARF_RAW_EXP_${exp}_GAIN_${gain}_*"),
            ConfigTemplate("DWARF_DARK/exp_${exp}_gain_${gain}_bin_${bin}"),
        ],
        description="List of templated paths that may contain darks",
    )
    flats: list[ConfigTemplate] = Field(
        default=[
            ConfigTemplate("DWARF_FLAT_EXP_${exp}_GAIN_${gain}_*"),
            ConfigTemplate("DWARF_RAW_EXP_${exp}_GAIN_${gain}_*"),
        ],
        description="List of templated paths that may contain flats",
    )
    biases: list[ConfigTemplate] = Field(
        default=[
            ConfigTemplate("DWARF_RAW_${target}_EXP_0.0001_GAIN_${gain}_*"),
            ConfigTemplate("DWARF_BIASES_EXP_0.0001_GAIN_${gain}_*"),
            ConfigTemplate("DWARF_RAW_EXP_0.0001_GAIN_${gain}_*"),
        ],
        description="List of templated paths that may contain biases",
    )

    def describe(self) -> str:
        """Return formatted description of the source for display to the user."""
        return "\n".join(
            [
                f" Source: [b]{self.name}[/b]",
                f"   Path: [i]{self.path}[/i]",
            ]
        )

    @cached_property
    def driver(self) -> BaseDriver:
        raise NotImplementedError()


class ConfigSourceDrive(ConfigSourceBase):
    """Defines a source of Dwarf data, may be a local path or a network drive."""

    type: Literal[SourceType.DRIVE] = SourceType.DRIVE

    @cached_property
    def driver(self) -> "BaseDriver":
        """Return the appropriate driver for this source."""
        from dwarf_copier.drivers import disk

        return disk.Driver(self.path)


class ConfigSourceFTP(ConfigSourceBase):
    """Defines a source of Dwarf data, may be a local path or a network drive."""

    type: Literal[SourceType.FTP] = SourceType.FTP
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
                f" Source: [b]{self.name}[/b]",
                f"IP Addr: [i]{self.ip_address}[/i]",
                f"   Path: [i]{self.path}[/i]",
            ]
        )


class ConfigSourceMTP(ConfigSourceBase):
    """Defines a source of Dwarf data, may be a local path or a network drive."""

    type: Literal[SourceType.FTP] = SourceType.FTP


ConfigSource = ConfigSourceDrive | ConfigSourceFTP | ConfigSourceMTP


class ConfigTarget(BaseModel):
    """Destination folder to contain the copied images."""

    name: str
    path: Path
    format: str
    link: Annotated[
        bool,
        Field(
            default=True,
            description="Try to create links instead of copying if link is true "
            "for both source and target.",
        ),
    ] = False

    @field_validator("path")
    @classmethod
    def valid_path(cls, v: str | Path) -> Path:
        return Path(v).expanduser().resolve()


class ConfigurationModel(BaseModel):
    """Model for the configuration file."""

    model_config = ConfigDict(use_enum_values=True)

    general: Annotated[
        ConfigGeneral, Field(default_factory=ConfigGeneral)
    ] = ConfigGeneral()

    sources: Annotated[
        list[ConfigSource],
        Field(default_factory=list, description="List of sources"),
    ] = [ConfigSourceDrive(name="MicroSD", path="D:\\DWARF_II")]

    targets: Annotated[
        list[ConfigTarget], Field(default_factory=list, description="List of targets")
    ] = [
        ConfigTarget(
            name="Astrophotography", path="C:\\Astrophotography", format="Siril"
        )
    ]
    formats: Annotated[
        list[ConfigFormat],
        Field(default_factory=list, description="List of formats"),
    ] = [ConfigFormat(name="Siril", path="${name}", darks="darks")]

    _formats: dict[str, ConfigFormat]

    def get_source(self, name: str) -> ConfigSource:
        for s in self.sources:
            if s.name == name:
                return s
        raise KeyError(f"Source {name} does not exist")

    def get_target(self, name: str) -> ConfigTarget:
        for t in self.targets:
            if t.name == name:
                return t
        raise KeyError(f"Target {name} does not exist")

    def get_format(self, name: str) -> ConfigFormat:
        return self._formats[name]

    def describe_target(self, target: ConfigTarget) -> rich.text.Text:
        """Return formatted description of the source for display to the user."""
        fmt = next(
            (f for f in self.formats if f.name.lower() == target.format.lower()), None
        )

        text = rich.text.Text()
        text.append("Target: ")
        text.append(target.name, style="bold")
        text.append("\n   Path: ")
        text.append(str(target.path), style="italic")
        if fmt is None:
            text.append("\nBad format", style="error")
        else:
            text.append("\n" + fmt.description, style="italic")
        return text

    @model_validator(mode="after")
    def validate_targets(self) -> Self:
        self._formats: dict[str, ConfigFormat] = {f.name: f for f in self.formats}
        for t in self.targets:
            if t.format not in self._formats:
                raise ValueError(f"Target {t.name} ahas invalid format {t.format}")

        return self


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


DEFAULT_SD_PATH = Path(r"D:\DWARF_II\Astronomy" if os.name == "nt" else "/mnt/sdcard")
DEFAULT_BACKUP_PATH = (
    Path(r"C:\Backup\Dwarf_II" if os.name == "nt" else "~/Backup/Dwarf_II")
    .expanduser()
    .resolve()
)
DEFAULT_SIRIL_PATH = (
    Path(r"C:\Astrophotography" if os.name == "nt" else "~/Astrophotography")
    .expanduser()
    .resolve()
)
DEFAULT_CONFIG = ConfigurationModel(
    general=ConfigGeneral(),
    sources=[
        ConfigSourceDrive(name="MicroSD", path=DEFAULT_SD_PATH),
        ConfigSourceFTP(
            name="WiFi Direct",
            ip_address="192.168.88.1",
            path=Path("/Astronomy"),
            type=SourceType.FTP,
        ),
        ConfigSourceDrive(
            name="Backup",
            path=DEFAULT_BACKUP_PATH,
            darks=["../DWARF_DARKS_EXP_${exp}_GAIN_${gain}_${Y}-${M}-${d}"],
        ),
    ],
    targets=[
        ConfigTarget(name="Backup", path=DEFAULT_BACKUP_PATH, format="Backup"),
        ConfigTarget(
            name="Astrophotography", path=DEFAULT_SIRIL_PATH, format="Siril", link=True
        ),
    ],
    formats=[
        ConfigFormat(
            name="Backup",
            description="Copy files without changes",
            path="DWARF_RAW_${target_}EXP_${exp}_GAIN_${gain}_${Y}-${M}-${d}-${H}-${m}-${S}-${ms}",
            darks="../DWARF_DARKS_EXP_${exp}_GAIN_${gain}_${Y}-${M}-${d}",
            copy_only=[ConfigCopy(source="*", destination="${name}")],
        ),
        ConfigFormat(
            name="Siril",
            description="Copy into Siril directory structure",
            path="${name}_EXP_${exp}_GAIN_${gain}_${Y}_${M}_${d}",
            darks="darks",
            flats="flats",
            biases="biases",
            directories=["darks", "lights", "flats", "biases"],
            link_or_copy=[
                ConfigCopy(
                    source="stacked-16_*.fits", destination="${name}"
                ),  # New stacked image.
                ConfigCopy(source="shotsInfo.json", destination="shotsInfo.json"),
                ConfigCopy(source="*.fits", destination="lights/${name}"),
                ConfigCopy(source="*.jpg", destination="${target}-${name}"),
                ConfigCopy(
                    source="*.png", destination="${target}-${name}"
                ),  # Old stacked image.
            ],
        ),
    ],
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

    for directory in [Path(s).expanduser().resolve() for s in search_path] + [
        (Path(__file__).parent.resolve())
    ]:
        config_file = directory / name
        logging.debug("config %s", config_file)
        if config_file.exists():
            data: dict = yaml.safe_load(config_file.read_text())
            logging.info("Using config %r", data)
            try:
                return ConfigurationModel(**data)
            except ValidationError as e:
                sys.exit(f"Invalid configuration {config_file}\n{str(e)}")

    logging.warning("No configuration found, using default")

    config = DEFAULT_CONFIG.model_copy(deep=True)
    logging.warning("Config %r", config)
    return config


config = load_config()
