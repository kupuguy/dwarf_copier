from rich.console import Console
from textual.render import measure

from dwarf_copier.screens.show_sessions import Shots


def test_rich() -> None:
    value: Shots = Shots(123, 456)
    expected = "123/456"
    console = Console()

    assert str(value) == expected

    assert measure(console, value, 1) == 7
