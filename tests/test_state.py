from dwarf_copier.configuration import DEFAULT_CONFIG
from dwarf_copier.model import PartialState, State
from dwarf_copier.models.destination_directory import DestinationDirectory
from dwarf_copier.models.source_directory import SourceDirectory


def test_empty_partial() -> None:
    pstate = PartialState()
    assert not pstate.is_complete()


def test_partial_to_state(source_directories: list[SourceDirectory]) -> None:
    config = DEFAULT_CONFIG
    source = config.sources[0]
    target = config.targets[0]
    format = config.get_format(target.format)
    pstate = PartialState(
        source=source,
        target=target,
        selected=[DestinationDirectory(d, target, format) for d in source_directories],
        format=format,
    )
    assert pstate.is_complete()
    state = State.from_partial(pstate)
    assert isinstance(state, State)
    assert state.selected == pstate.selected


def test_state_to_partial(source_directories: list[SourceDirectory]) -> None:
    config = DEFAULT_CONFIG
    source = config.sources[0]
    target = config.targets[0]
    format = config.get_format(target.format)
    state = State(
        source=source,
        target=target,
        selected=[DestinationDirectory(d, target, format) for d in source_directories],
        format=format,
    )

    pstate = PartialState.from_state(state)
    assert isinstance(pstate, PartialState)
    assert pstate.selected == state.selected
