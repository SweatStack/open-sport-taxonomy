"""Property-based tests for encode/decode across all four platforms.

These complement ``tests/algorithm/test_encode.py`` and
``tests/algorithm/test_decode.py`` (which exercise distinct code paths
with hand-chosen inputs) by asserting universal claims across the
generated input space.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from open_sport_taxonomy import GarminFitCode, Sport
from open_sport_taxonomy.platforms import (
    apple_healthkit,
    garmin_fit,
    garmin_training_api,
    strava,
)
from tests.properties.conftest import standard_sports

ALL_PLATFORMS = [garmin_fit, strava, apple_healthkit, garmin_training_api]


def _decode(platform, target):
    """Decode dispatch that handles FIT's tuple-unpacking signature."""
    if platform is garmin_fit:
        return platform.decode(*target)
    return platform.decode(target)


@given(sport=standard_sports(), platform_index=st.integers(min_value=0, max_value=3))
def test_encode_returns_correct_target_type(sport: Sport, platform_index: int) -> None:
    """For any standard sport on any platform, encode returns a value of
    the platform's native target type — never raises, never returns ``None``."""
    platform = ALL_PLATFORMS[platform_index]
    result = platform.encode(sport)
    assert result is not None
    # Type assertion per platform.
    if platform is garmin_fit:
        assert isinstance(result, GarminFitCode)
    elif platform in (strava, garmin_training_api):
        assert isinstance(result, str)
    elif platform is apple_healthkit:
        assert isinstance(result, int)


@given(sport=standard_sports(), platform_index=st.integers(min_value=0, max_value=3))
def test_encode_is_deterministic(sport: Sport, platform_index: int) -> None:
    """Calling encode twice on the same input yields the same target."""
    platform = ALL_PLATFORMS[platform_index]
    assert platform.encode(sport) == platform.encode(sport)


@given(sport=standard_sports(), platform_index=st.integers(min_value=0, max_value=3))
def test_decode_of_encode_is_a_standard_sport(sport: Sport, platform_index: int) -> None:
    """decode(encode(sport)) always returns a *standard* Sport.

    The decoded sport may be coarser than the input (modifiers dropped,
    discipline collapsed via parent walk), but it must always parse to a
    valid taxonomy entry.
    """
    platform = ALL_PLATFORMS[platform_index]
    target = platform.encode(sport)
    assert _decode(platform, target).is_standard


@given(sport=standard_sports(), platform_index=st.integers(min_value=0, max_value=3))
def test_decode_is_deterministic(sport: Sport, platform_index: int) -> None:
    """decode is a pure function — same input, same output."""
    platform = ALL_PLATFORMS[platform_index]
    target = platform.encode(sport)
    assert _decode(platform, target) == _decode(platform, target)


@given(sport=standard_sports(), platform_index=st.integers(min_value=0, max_value=3))
def test_round_trip_is_idempotent(sport: Sport, platform_index: int) -> None:
    """decode(encode(decode(encode(sport)))) == decode(encode(sport)).

    Encoding may be lossy, but the loss converges in one round — encoding
    the decoded value produces the same target as before.
    """
    platform = ALL_PLATFORMS[platform_index]
    target1 = platform.encode(sport)
    target2 = platform.encode(_decode(platform, target1))
    assert target1 == target2
