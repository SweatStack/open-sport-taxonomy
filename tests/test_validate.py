import pytest

from open_sports_schema import Modifier, Sport


class TestAcceptsStandard:
    def test_bare_code(self):
        sport = Sport.validate("cycling.road")
        assert sport.code == "cycling.road"
        assert sport.is_standard is True

    def test_with_modifiers(self):
        sport = Sport.validate("cycling.road+race+virtual")
        assert sport.modifiers == frozenset({Modifier.RACE, Modifier.VIRTUAL})
        assert sport.is_standard is True

    def test_equals_constructor(self):
        assert Sport.validate("cycling.road") == Sport("cycling.road")
        assert Sport.validate("cycling.road+race") == Sport("cycling.road+race")

    def test_raw_equals_str(self):
        sport = Sport.validate("cycling.road+race")
        assert sport.raw == str(sport)

    def test_unknown_modifiers_empty(self):
        sport = Sport.validate("cycling.road+race")
        assert sport.unknown_modifiers == frozenset()


class TestRejectsNonStandard:
    def test_unknown_code(self):
        with pytest.raises(ValueError, match="Unknown sport code"):
            Sport.validate("cycling.road.criterium")

    def test_unknown_modifier(self):
        with pytest.raises(ValueError):
            Sport.validate("cycling.road+rainy")

    def test_modifier_group_conflict(self):
        with pytest.raises(ValueError, match="conflict"):
            Sport.validate("cycling.road+race+commute")


class TestStructuralErrors:
    def test_empty_string(self):
        with pytest.raises(ValueError):
            Sport.validate("")

    def test_trailing_plus(self):
        with pytest.raises(ValueError):
            Sport.validate("cycling.road+")

    def test_non_string(self):
        with pytest.raises(TypeError):
            Sport.validate(123)  # type: ignore[arg-type]
