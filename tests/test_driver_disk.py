from datetime import datetime
from pathlib import Path
from typing import Callable

import pytest
from pytest_mock import MockFixture
from textual import work
from textual.app import App

from dwarf_copier.configuration import BaseDriver
from dwarf_copier.drivers import disk
from dwarf_copier.shots_info import ShotsInfo
from dwarf_copier.source_directory import SourceDirectory

pytestmark = pytest.mark.anyio


class RunApp(App):
    def cb(self, callable: Callable[[SourceDirectory | None], None]) -> None:
        ...

    @work(thread=True)
    def list_dirs(
        self, driver: BaseDriver, callback: Callable[[SourceDirectory | None], None]
    ) -> None:
        driver.list_dirs(callback=callback)


@pytest.fixture
def app() -> RunApp:
    app = RunApp()
    return app


async def test_list_dirs(
    mocker: MockFixture, app: RunApp, astronomy_source: Path
) -> None:
    expected = [
        (
            (
                SourceDirectory(
                    path=Path(
                        astronomy_source
                        / "DWARF_RAW_M1_EXP_15_GAIN_80_2024-01-18-21-04-26-954"
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
            ),
        ),
        (
            (
                SourceDirectory(
                    path=Path(
                        astronomy_source
                        / "DWARF_RAW_M43_EXP_5_GAIN_60_2024-01-22-19-04-10-409"
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
            ),
        ),
        (
            (
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
            ),
        ),
        ((None,),),
    ]
    callback = mocker.Mock(wraps=app.cb)

    async with app.run_test():
        driver = disk.Driver(astronomy_source)
        worker = app.list_dirs(driver, callback=callback)
        await worker.wait()

    assert callback.call_args_list == expected
