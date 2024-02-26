from pathlib import Path

import pytest

from dwarf_copier.model import CopySession, PhotoSession, Specials, State


@pytest.fixture
def photo_session(
    request: pytest.FixtureRequest, photo_sessions: list[PhotoSession]
) -> PhotoSession:
    assert isinstance(request.param, str)
    matches = [p for p in photo_sessions if f"_{request.param}_" in str(p.path)]
    assert len(matches) == 1
    return matches[0]


@pytest.fixture
def expected_paths(request: pytest.FixtureRequest, astronomy_source: Path) -> set[Path]:
    if isinstance(request.param, set):
        return set(astronomy_source / s for s in request.param)
    raise TypeError("expected_paths expects set[str].")


@pytest.fixture
def expected_path(
    request: pytest.FixtureRequest, astronomy_source: Path
) -> Path | None:
    if isinstance(request.param, str):
        return astronomy_source / request.param
    elif request.param is None:
        return None
    raise TypeError("expected_path expects str.")


@pytest.mark.parametrize(
    "photo_session,expected_paths",
    [
        ("M1", set(["DWARF_DARK/exp_15_gain_80_bin_1"])),
        (
            "M43",
            set(
                [
                    "DWARF_DARK/exp_5_gain_60_bin_1",
                    "DWARF_RAW_EXP_5_GAIN_60_2024-02-24-22-31-52-161",
                ]
            ),
        ),
        ("Moon", set()),
    ],
    indirect=True,
)
def test_darks(
    state_dummy: State, photo_session: PhotoSession, expected_paths: set[Path]
) -> None:
    special = Specials(
        CopySession(photo_session, state_dummy.target, state_dummy.format),
        state_dummy.source,
        state_dummy.target,
        state_dummy.driver,
        state_dummy.format,
        state_dummy.source.darks,
    )
    assert special.candidates == expected_paths


@pytest.mark.parametrize(
    "photo_session,expected_paths",
    [
        ("M1", set(["DWARF_RAW_M1_EXP_0.0001_GAIN_80_2024-02-12-22-11-17-881"])),
        ("M43", set()),
        ("Moon", set()),
    ],
    indirect=True,
)
def test_biases(
    state_dummy: State, photo_session: PhotoSession, expected_paths: set[Path]
) -> None:
    special = Specials(
        CopySession(photo_session, state_dummy.target, state_dummy.format),
        state_dummy.source,
        state_dummy.target,
        state_dummy.driver,
        state_dummy.format,
        state_dummy.source.biases,
    )
    assert special.candidates == expected_paths


@pytest.mark.parametrize(
    "photo_session,expected_paths",
    [
        ("M1", set([])),
        (
            "M43",
            set(
                [
                    "DWARF_RAW_EXP_5_GAIN_60_2024-02-24-22-31-52-161",
                ]
            ),
        ),
        ("Moon", set()),
    ],
    indirect=True,
)
def test_flats(
    state_dummy: State, photo_session: PhotoSession, expected_paths: set[Path]
) -> None:
    special = Specials(
        CopySession(photo_session, state_dummy.target, state_dummy.format),
        state_dummy.source,
        state_dummy.target,
        state_dummy.driver,
        state_dummy.format,
        state_dummy.source.flats,
    )
    assert special.candidates == expected_paths


@pytest.mark.parametrize(
    "photo_session,expected_path",
    [
        ("M1", "DWARF_DARK/exp_15_gain_80_bin_1"),
        (
            "M43",
            "DWARF_RAW_EXP_5_GAIN_60_2024-02-24-22-31-52-161",
        ),
        ("Moon", None),
    ],
    indirect=True,
)
def test_best_candidate(
    state_dummy: State, photo_session: PhotoSession, expected_path: Path | None
) -> None:
    special = Specials(
        CopySession(photo_session, state_dummy.target, state_dummy.format),
        state_dummy.source,
        state_dummy.target,
        state_dummy.driver,
        state_dummy.format,
        state_dummy.source.darks,
    )
    assert special.best_candidate == expected_path


@pytest.mark.parametrize(
    "photo_session,expected_path",
    [
        ("M1", "DWARF_RAW_M1_EXP_15_GAIN_80_2024-01-18-21-04-26-954"),
        (
            "M43",
            "DWARF_RAW_M43_EXP_5_GAIN_60_2024-01-22-19-04-10-409",
        ),
        ("Moon", "DWARF_RAW_Moon_EXP_0.0025_GAIN_0_2024-01-16-15-02-35-270"),
    ],
    indirect=["photo_session"],
)
def test_destination(
    state_dummy: State, photo_session: PhotoSession, expected_path: str
) -> None:
    session = CopySession(photo_session, state_dummy.target, state_dummy.format)
    destination = session.destination
    assert destination == state_dummy.target.path / expected_path
