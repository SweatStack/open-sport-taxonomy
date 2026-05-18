import pytest

from open_sport_taxonomy import Modifier, Sport


class TestKnownCodes:
    def test_bare_code(self):
        assert Sport.resolve("cycling.road") == Sport("cycling.road")

    def test_with_modifiers(self):
        assert Sport.resolve("cycling.road+race") == Sport("cycling.road+race")

    def test_multiple_modifiers(self):
        assert Sport.resolve("cycling.road+race+virtual") == Sport("cycling.road+race+virtual")


class TestUnknownSport:
    def test_walks_up_one_level(self):
        assert Sport.resolve("cycling.road.criterium") == Sport("cycling.road")

    def test_walks_up_two_levels(self):
        assert Sport.resolve("cycling.road.criterium.u23") == Sport("cycling.road")

    def test_walks_up_from_unknown_child_of_known_parent(self):
        assert Sport.resolve("running.fell") == Sport("running")

    def test_unknown_top_level_resolves_to_generic(self):
        assert Sport.resolve("parkour") == Sport("generic")

    def test_unknown_nested_under_unknown_top_level(self):
        assert Sport.resolve("parkour.freerunning") == Sport("generic")

    def test_preserves_known_modifiers(self):
        assert Sport.resolve("cycling.road.criterium+race") == Sport("cycling.road+race")

    def test_preserves_multiple_known_modifiers(self):
        result = Sport.resolve("cycling.road.criterium+race+virtual")
        assert result == Sport("cycling.road+race+virtual")


class TestUnknownModifier:
    def test_single_unknown_dropped(self):
        assert Sport.resolve("cycling.road+relay") == Sport("cycling.road")

    def test_unknown_dropped_known_kept(self):
        assert Sport.resolve("cycling.road+race+relay") == Sport("cycling.road+race")

    def test_multiple_unknown_dropped(self):
        assert Sport.resolve("cycling.road+foo+relay") == Sport("cycling.road")

    def test_known_among_multiple_unknown(self):
        result = Sport.resolve("cycling.road+foo+race+relay")
        assert result == Sport("cycling.road+race")


class TestBothUnknown:
    def test_unknown_sport_and_modifier(self):
        assert Sport.resolve("cycling.road.criterium+race+relay") == Sport("cycling.road+race")

    def test_all_unknown(self):
        assert Sport.resolve("parkour.freerunning+foo+bar") == Sport("generic")

    def test_unknown_sport_all_modifiers_unknown(self):
        assert Sport.resolve("cycling.road.criterium+foo") == Sport("cycling.road")


class TestStructuralErrors:
    def test_empty_string(self):
        with pytest.raises(ValueError):
            Sport.resolve("")

    def test_trailing_plus(self):
        with pytest.raises(ValueError, match="Invalid encoded string"):
            Sport.resolve("cycling.road+")

    def test_leading_plus(self):
        with pytest.raises(ValueError, match="Invalid encoded string"):
            Sport.resolve("+cycling.road")

    def test_double_plus(self):
        with pytest.raises(ValueError, match="Invalid encoded string"):
            Sport.resolve("cycling.road++virtual")

    def test_non_string(self):
        with pytest.raises(TypeError):
            Sport.resolve(123)  # type: ignore[arg-type]


class TestModifierConflicts:
    def test_known_conflicting_modifiers_raises(self):
        with pytest.raises(ValueError, match="conflict"):
            Sport.resolve("cycling.road+commute+race")

    def test_conflict_resolved_by_dropping_unknown(self):
        # "race" is known (purpose group), "relay" is unknown — no conflict
        result = Sport.resolve("cycling.road+race+relay")
        assert result == Sport("cycling.road+race")

    def test_one_known_one_unknown_from_same_group(self):
        # Only "race" survives — no conflict since "futuremod" is dropped
        result = Sport.resolve("cycling.road+futuremod+race")
        assert result == Sport("cycling.road+race")
