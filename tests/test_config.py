# pylint: disable=redefined-outer-name,missing-module-docstring,missing-function-docstring
import textwrap
from pathlib import Path

import pytest

from dwarf_copier.config import load_config


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    text = """\
        general:
          theme: dark

        sources:
        - name: MicroSD
          type: Drive
          path: D:\\DWARF_II\\Astronomy
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
          path: C:\\Backup\\Dwarf_II\\
          format: Backup
        - name: Astrophotography
          path: C:\\Astrophotography\\
          format: Siril
        formats:
        - name: Backup
        - name: Siril"""
    text = textwrap.dedent(text)
    config_path = tmp_path / "dwarf-copy.yml"
    config_path.write_text(text)
    return config_path


def test_load_config(config_file: Path) -> None:
    config = load_config(name=config_file.name, search_path=[str(config_file.parent)])

    assert config.general.theme == "dark"
