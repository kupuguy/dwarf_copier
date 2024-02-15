from pathlib import Path

import pytest

from dwarf_copier.config import (
    ConfigCopy,
    ConfigFormat,
    ConfigGeneral,
    ConfigSourceDrive,
    ConfigTarget,
    ConfigurationModel,
)


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
            ConfigSourceDrive(name="TestEnv", path=astronomy_source),
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
