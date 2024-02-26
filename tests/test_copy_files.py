from datetime import datetime
from pathlib import Path

import pytest
from pytest_mock import MockFixture
from textual.app import App

from dwarf_copier.configuration import ConfigurationModel
from dwarf_copier.model import State
from dwarf_copier.screens.copy_files import CopyFiles
from dwarf_copier.shots_info import ShotsInfo
from dwarf_copier.source_directory import SourceDirectory

pytestmark = pytest.mark.anyio


class RunApp(App):
    pass


@pytest.fixture
def app() -> RunApp:
    app = RunApp()
    return app


async def test_copy_files(
    mocker: MockFixture,
    app: RunApp,
    astronomy_source: Path,
    config_dummy: ConfigurationModel,
) -> None:
    source: str = "TestEnv"
    target: str = "Backup"
    config_source = config_dummy.get_source(source)
    config_target = config_dummy.get_target(target)

    selected: list[SourceDirectory] = [
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
    ]

    expected_target = (
        config_target.path / "DWARF_RAW_M1_EXP_15_GAIN_80_2024-01-18-21-04-26-954"
    )
    expected = [expected_target / "0000.fits"]

    async with app.run_test():
        state = State(
            config_source,
            config_target,
            selected,
            config_dummy.get_format(config_target.format),
        )
        copy_screen = CopyFiles(state)
        await app.push_screen(
            copy_screen,
        )

        if copy_screen.controller is not None:
            await app.workers.wait_for_complete([copy_screen.controller])

        for file in expected:
            assert file.exists()
