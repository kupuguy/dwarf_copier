"""
tests for user class
"""
from dwarf_copier.model import User


def test_user() -> None:
    """
    just a test
    """
    user = User("foo")
    assert user.name == "foo"
    assert user.name_upper == "FOO"
