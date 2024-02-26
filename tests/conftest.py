from datetime import datetime
from pathlib import Path

import pytest

from dwarf_copier.configuration import (
    ConfigCopy,
    ConfigFormat,
    ConfigGeneral,
    ConfigSourceDrive,
    ConfigTarget,
    ConfigurationModel,
)
from dwarf_copier.model import State
from dwarf_copier.shots_info import ShotsInfo
from dwarf_copier.source_directory import SourceDirectory


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def test_folder() -> Path:
    return Path(__file__).parent


@pytest.fixture
def astronomy_source(test_folder: Path) -> Path:
    return test_folder / "data" / "Astronomy"


@pytest.fixture
def config_dummy(tmp_path: Path, astronomy_source: Path) -> ConfigurationModel:
    return ConfigurationModel(
        general=ConfigGeneral(),
        sources=[
            ConfigSourceDrive(
                name="TestEnv",
                path=astronomy_source,
                darks=[
                    "DWARF_RAW_EXP_${exp}_GAIN_${gain}_*",
                    "DWARF_DARK/exp_${exp}_gain_${gain}_bin_${bin}",
                ],
            ),
        ],
        targets=[
            ConfigTarget(name="Backup", path=tmp_path / "backup", format="Backup"),
            ConfigTarget(name="Siril", path=tmp_path / "siril", format="Siril"),
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
                directories=["darks", "lights", "flats", "biases"],
                link_or_copy=[
                    ConfigCopy(source="shotsInfo.json", destination="shotsInfo.json"),
                    ConfigCopy(source="*.fits", destination="lights/${name}"),
                    ConfigCopy(source="*.jpg", destination="${target}-${name}"),
                    ConfigCopy(source="*.png", destination="${target}-${name}"),
                ],
            ),
        ],
    )


@pytest.fixture
def source_directories(astronomy_source: Path) -> list[SourceDirectory]:
    return [
        SourceDirectory(
            path=Path(
                astronomy_source / "DWARF_RAW_M1_EXP_15_GAIN_80_2024-01-18-21-04-26-954"
            ),
            info=ShotsInfo(
                DEC=22.01469444,
                RA=5.575916667,
                binning="1*1",
                exp="15",
                format="FITS",
                gain=80,
                ir="PASS",
                shotsStacked=286,
                shotsTaken=287,
                shotsToTake=300,
                target="M1",
            ),
            date=datetime(2024, 1, 18, 21, 4, 26, 954000),
        ),
        SourceDirectory(
            path=Path(
                astronomy_source / "DWARF_RAW_M43_EXP_5_GAIN_60_2024-01-22-19-04-10-409"
            ),
            info=ShotsInfo(
                DEC=-5.270722222,
                RA=5.592305556,
                binning="1*1",
                exp="5",
                format="FITS",
                gain=60,
                ir="CUT",
                shotsStacked=16,
                shotsTaken=113,
                shotsToTake=999,
                target="M43",
            ),
            date=datetime(2024, 1, 22, 19, 4, 10, 409000),
        ),
        SourceDirectory(
            path=Path(
                astronomy_source
                / "DWARF_RAW_Moon_EXP_0.0025_GAIN_0_2024-01-16-15-02-35-270"
            ),
            info=ShotsInfo(
                DEC=0.0,
                RA=0.0,
                binning="1*1",
                exp="1/400",
                format="FITS",
                gain=0,
                ir="CUT",
                shotsStacked=1,
                shotsTaken=9,
                shotsToTake=999,
                target="Moon",
            ),
            date=datetime(2024, 1, 16, 15, 2, 35, 270000),
        ),
    ]


@pytest.fixture
def state_dummy(
    config_dummy: ConfigurationModel, source_directories: list[SourceDirectory]
) -> State:
    config = config_dummy
    source = config.sources[0]
    target = config.targets[0]
    state = State(
        source=source,
        target=target,
        selected=source_directories,
        format=config.get_format(target.format),
    )
    return state
