import pytest

from open_sport_taxonomy import Sport


class TestKnownCodes:
    def test_bare_code(self):
        assert Sport.parse("cycling.road").resolve() == Sport("cycling.road")

    def test_with_modifiers(self):
        assert Sport.parse("cycling.road+race").resolve() == Sport("cycling.road+race")


class TestUnknownSport:
    def test_walks_up_one_level(self):
        assert Sport.parse("cycling.road.criterium").resolve() == Sport("cycling.road")

    def test_walks_up_from_unknown_child_of_known_parent(self):
        assert Sport.parse("running.fell").resolve() == Sport("running")

    def test_unknown_top_level_resolves_to_generic(self):
        assert Sport.parse("parkour").resolve() == Sport("generic")

    def test_unknown_nested_under_unknown_top_level(self):
        assert Sport.parse("parkour.freerunning").resolve() == Sport("generic")

    def test_preserves_known_modifiers(self):
        assert Sport.parse("cycling.road.criterium+race").resolve() == Sport("cycling.road+race")


class TestUnknownModifier:
    def test_single_unknown_dropped(self):
        assert Sport.parse("cycling.road+relay").resolve() == Sport("cycling.road")

    def test_unknown_dropped_known_kept(self):
        assert Sport.parse("cycling.road+race+relay").resolve() == Sport("cycling.road+race")

    def test_known_among_multiple_unknown(self):
        result = Sport.parse("cycling.road+foo+race+relay").resolve()
        assert result == Sport("cycling.road+race")


class TestBothUnknown:
    def test_unknown_sport_and_modifier(self):
        assert Sport.parse("cycling.road.criterium+race+relay").resolve() == Sport(
            "cycling.road+race"
        )

    def test_all_unknown(self):
        assert Sport.parse("parkour.freerunning+foo+bar").resolve() == Sport("generic")

    def test_unknown_sport_all_modifiers_unknown(self):
        assert Sport.parse("cycling.road.criterium+foo").resolve() == Sport("cycling.road")


class TestStandardReturnsSelf:
    def test_standard_sport_returns_self(self):
        sport = Sport("cycling.road+race")
        assert sport.resolve() is sport


class TestResolveIsStandard:
    def test_resolved_is_always_standard(self):
        assert Sport.parse("cycling.road.criterium+race+rainy").resolve().is_standard is True

    def test_resolved_all_unknown(self):
        assert Sport.parse("parkour.freerunning+foo").resolve().is_standard is True


class TestStructuralErrors:
    def test_empty_string(self):
        with pytest.raises(ValueError):
            Sport.parse("").resolve()

    def test_trailing_plus(self):
        with pytest.raises(ValueError, match="Invalid encoded string"):
            Sport.parse("cycling.road+").resolve()

    def test_leading_plus(self):
        with pytest.raises(ValueError, match="Invalid encoded string"):
            Sport.parse("+cycling.road").resolve()

    def test_double_plus(self):
        with pytest.raises(ValueError, match="Invalid encoded string"):
            Sport.parse("cycling.road++virtual").resolve()

    def test_non_string(self):
        with pytest.raises(TypeError):
            Sport.parse(123).resolve()  # type: ignore[arg-type]


class TestModifierConflicts:
    def test_known_conflicting_modifiers_raises(self):
        with pytest.raises(ValueError, match="conflict"):
            Sport.parse("cycling.road+commute+race").resolve()

    def test_conflict_resolved_by_dropping_unknown(self):
        # "race" is known (purpose group), "relay" is unknown — no conflict
        result = Sport.parse("cycling.road+race+relay").resolve()
        assert result == Sport("cycling.road+race")

    def test_one_known_one_unknown_from_same_group(self):
        # Only "race" survives — no conflict since "futuremod" is dropped
        result = Sport.parse("cycling.road+futuremod+race").resolve()
        assert result == Sport("cycling.road+race")
