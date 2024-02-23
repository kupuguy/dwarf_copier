# pylint: disable=redefined-outer-name,missing-module-docstring,missing-function-docstring
import json
from pathlib import Path
from string import Template

import pytest

from dwarf_copier.configuration import load_config


@pytest.fixture
def config_text() -> str:
    from dwarf_copier.configuration import DEFAULT_CONFIG

    return DEFAULT_CONFIG.model_dump_json()


@pytest.fixture
def config_json(config_text: str) -> dict:
    from yaml import safe_load

    json: dict = safe_load(config_text.replace("\\", "/"))
    return json


@pytest.fixture
def config_file(tmp_path: Path, config_text: str) -> Path:
    config_path = tmp_path / "dwarf-copy.yml"
    config_path.write_text(config_text)
    return config_path


def test_load_config(config_file: Path) -> None:
    config = load_config(name=config_file.name, search_path=[str(config_file.parent)])

    assert config.general.theme == "dark"
    assert type(config.sources[2].darks[0]) is Template


def test_save_config(config_file: Path, config_json: dict) -> None:
    """Test the data round-trips correctly."""
    expected = config_json
    config = load_config(name=config_file.name, search_path=[str(config_file.parent)])
    actual = config.model_dump_json(exclude_unset=True)
    assert json.loads(actual.replace("\\", "/")) == expected
