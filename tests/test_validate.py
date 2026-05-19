import pytest

from open_sport_taxonomy import Modifier, Sport


class TestAcceptsStandard:
    def test_bare_code(self):
        sport = Sport("cycling.road")
        assert sport.code == "cycling.road"
        assert sport.is_standard is True

    def test_with_modifiers(self):
        sport = Sport("cycling.road+race+virtual")
        assert sport.modifiers == frozenset({Modifier.RACE, Modifier.VIRTUAL})
        assert sport.is_standard is True

    def test_equals_constructor_with_modifiers_kwarg(self):
        assert Sport("cycling.road") == Sport("cycling.road")
        assert Sport("cycling.road+race") == Sport("cycling.road", modifiers={Modifier.RACE})


class TestRejectsNonStandard:
    def test_unknown_code(self):
        with pytest.raises(ValueError, match="Unknown sport code"):
            Sport("cycling.road.criterium")

    def test_unknown_modifier(self):
        with pytest.raises(ValueError):
            Sport("cycling.road+rainy")

    def test_modifier_group_conflict(self):
        with pytest.raises(ValueError, match="conflict"):
            Sport("cycling.road+race+commute")


class TestStructuralErrors:
    def test_empty_string(self):
        with pytest.raises(ValueError):
            Sport("")

    def test_trailing_plus(self):
        with pytest.raises(ValueError):
            Sport("cycling.road+")

    def test_non_string(self):
        with pytest.raises(TypeError):
            Sport(123)  # type: ignore[arg-type]
