# pylint: disable=redefined-outer-name,missing-module-docstring,missing-function-docstring
import json
import textwrap
from pathlib import Path
from string import Template

import pytest

from dwarf_copier.config import load_config


@pytest.fixture
def config_text() -> str:
    text = r"""
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
        - name: Backup
          type: Drive
          darks:
          - "../DWARF_RAW_EXP_${exp}_GAIN_${gain}_${Y}-${M}-${d}*"
          - "../DWARF_DARK/exp_${exp}_gain_${gain}_bin_${bin}"
          link: true
          path: "C:\\Backup"
        targets:
        - name: Backup
          path: C:\Backup\Dwarf_II\
          format: Backup
        - name: Astrophotography
          path: C:\Astrophotography\
          format: Siril
        formats:
        - name: Backup
        - name: Siril"""
    text = textwrap.dedent(text)
    return text


@pytest.fixture
def config_json(config_text: str) -> dict:
    from yaml import safe_load

    json: dict = safe_load(config_text)
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


def test_save_config(config_file: Path) -> None:
    """Test the data round-trips correctly."""
    expected = {
        "general": {"theme": "dark"},
        "sources": [
            {
                "name": "MicroSD",
                "path": "D:\\DWARF_II\\Astronomy",
                "type": "Drive",
            },
            {
                "name": "WiFi Direct",
                "path": "\\Astronomy",
                "type": "FTP",
                "ip_address": "192.168.88.1",
            },
            {
                "name": "Backup",
                "path": "C:\\Backup",
                "link": True,
                "darks": [
                    "../DWARF_RAW_EXP_${exp}_GAIN_${gain}_${Y}-${M}-${d}*",
                    "../DWARF_DARK/exp_${exp}_gain_${gain}_bin_${bin}",
                ],
                "type": "Drive",
            },
        ],
        "targets": [
            {
                "name": "Backup",
                "path": "C:\\Backup\\Dwarf_II\\",
                "format": "Backup",
            },
            {
                "name": "Astrophotography",
                "path": "C:\\Astrophotography\\",
                "format": "Siril",
            },
        ],
        "formats": [
            {"name": "Backup"},
            {"name": "Siril"},
        ],
    }
    config = load_config(name=config_file.name, search_path=[str(config_file.parent)])
    actual = config.model_dump_json(exclude_unset=True)
    assert json.loads(actual) == expected
    assert json.loads(actual) == expected
