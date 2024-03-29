"""
Test command line usage
"""
# pylint: disable=redefined-outer-name,missing-function-docstring unused-argument, protected-access

import pytest

from dwarf_copier import app
from dwarf_copier.configuration import DEFAULT_CONFIG, ConfigurationModel
from dwarf_copier.screens.quit import QuitScreen

pytestmark = pytest.mark.anyio


@pytest.fixture
def mock_config(monkeypatch: pytest.MonkeyPatch) -> ConfigurationModel:
    """Fixture to stop tests picking up actual configs."""
    config = DEFAULT_CONFIG.model_copy(deep=True)
    monkeypatch.setattr("dwarf_copier.configuration.config", config)
    return config


async def test_app_run(mock_config: ConfigurationModel) -> None:
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
