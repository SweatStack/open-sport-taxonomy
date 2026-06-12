"""Property-based tests for the :class:`Sport` class.

Each property asserts a universal claim about Sport's contract and
explores the input space via Hypothesis. The example-based tests in
``tests/domain/test_sport.py`` cover targeted cases; these cover the
shape of the function across all valid inputs.
"""

from __future__ import annotations

from hypothesis import given

from open_sport_taxonomy import Sport
from tests.properties.conftest import standard_sports


@given(sport=standard_sports())
def test_str_roundtrips_through_constructor(sport: Sport) -> None:
    """For any standard sport ``s``: ``Sport(str(s)) == s``."""
    assert Sport(str(sport)) == sport


@given(sport=standard_sports())
def test_str_roundtrips_through_parse(sport: Sport) -> None:
    """For any standard sport ``s``: ``Sport.parse(str(s)) == s``.

    parse is permissive but must produce the same value as the strict
    constructor when the input is standard.
    """
    assert Sport.parse(str(sport)) == sport


@given(sport=standard_sports())
def test_str_sorts_modifiers_alphabetically(sport: Sport) -> None:
    """``str(sport)`` always lists modifiers in alphabetical order."""
    rendered = str(sport)
    if "+" not in rendered:
        return  # no modifiers — nothing to sort
    _code, *mods = rendered.split("+")
    assert mods == sorted(mods)


@given(sport=standard_sports())
def test_hash_consistent_with_equality(sport: Sport) -> None:
    """Equal sports have equal hashes; reconstructed sports compare equal."""
    other = Sport(str(sport))
    assert sport == other
    assert hash(sport) == hash(other)


@given(sport=standard_sports())
def test_parent_preserves_modifiers(sport: Sport) -> None:
    """``sport.parent`` (when non-None) has the same modifier set."""
    parent = sport.parent
    if parent is None:
        return
    assert parent.modifiers == sport.modifiers


@given(sport=standard_sports())
def test_is_subsport_of_is_reflexive(sport: Sport) -> None:
    """Every sport is a subsport of itself."""
    assert sport.is_subsport_of(sport)
