"""
Test command line usage
"""

import pytest

from dwarf_copier import app
from dwarf_copier.screens.quit import QuitScreen

pytestmark = pytest.mark.anyio


async def test_app_run() -> None:
    """
    Simulate a call to the command line tool by mocking arguments
    """
    app_test = app.DwarfCopyApp()
    async with app_test.run_test() as pilot:
        # Test pressing the D key to toggle dark mode
        assert app_test.has_class("-dark-mode") and not app_test.has_class(
            "-light-mode"
        )
        await pilot.press("d")
        assert not app_test.has_class("-dark-mode") and not app_test.has_class(
            "-dark-mode"
        )

        await pilot.press("q")
        assert isinstance(app_test.screen, QuitScreen)
        await pilot.press("q")
        assert app_test._exit
