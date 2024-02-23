from dwarf_copier.configuration import DEFAULT_CONFIG
from dwarf_copier.drivers import disk
from dwarf_copier.model import PartialState, PhotoSession, State


def test_empty_partial() -> None:
    pstate = PartialState()
    assert not pstate.is_complete()


def test_partial_to_state(photo_sessions: list[PhotoSession]) -> None:
    config = DEFAULT_CONFIG
    source = config.sources[0]
    target = config.targets[0]
    pstate = PartialState(
        source=source,
        target=target,
        selected=photo_sessions,
        format=config.get_format(target.format),
        driver=disk.Driver(source.path),
    )
    assert pstate.is_complete()
    state = State.from_partial(pstate)
    assert isinstance(state, State)
    assert state.selected == pstate.selected


def test_state_to_partial(photo_sessions: list[PhotoSession]) -> None:
    config = DEFAULT_CONFIG
    source = config.sources[0]
    target = config.targets[0]
    state = State(
        source=source,
        target=target,
        selected=photo_sessions,
        format=config.get_format(target.format),
        driver=disk.Driver(source.path),
    )

    pstate = PartialState.from_state(state)
    assert isinstance(pstate, PartialState)
    assert pstate.selected == state.selected
