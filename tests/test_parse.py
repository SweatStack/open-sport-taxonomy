import pytest

from open_sports_schema import Modifier, Sport


class TestStandardInput:
    def test_standard_code(self):
        sport = Sport.parse("cycling.road")
        assert sport.code == "cycling.road"
        assert sport.is_standard is True

    def test_standard_with_modifiers(self):
        sport = Sport.parse("cycling.road+race+virtual")
        assert sport.code == "cycling.road"
        assert sport.modifiers == frozenset({Modifier.RACE, Modifier.VIRTUAL})
        assert sport.unknown_modifiers == frozenset()
        assert sport.is_standard is True

    def test_equals_constructor(self):
        assert Sport.parse("cycling.road") == Sport("cycling.road")
        assert Sport.parse("cycling.road+race") == Sport("cycling.road+race")


class TestNonStandardCode:
    def test_unknown_code_preserved(self):
        sport = Sport.parse("cycling.road.criterium")
        assert sport.code == "cycling.road.criterium"
        assert sport.is_standard is False

    def test_unknown_code_label_is_none(self):
        sport = Sport.parse("cycling.road.criterium")
        assert sport.label is None

    def test_unknown_code_parent_derived(self):
        sport = Sport.parse("cycling.road.criterium")
        assert sport.parent == Sport.parse("cycling.road")

    def test_deeply_nested_unknown(self):
        sport = Sport.parse("cycling.road.criterium.u23")
        assert sport.code == "cycling.road.criterium.u23"
        assert sport.parent == Sport.parse("cycling.road.criterium")

    def test_unknown_top_level(self):
        sport = Sport.parse("parkour")
        assert sport.code == "parkour"
        assert sport.parent is None
        assert sport.is_standard is False

    def test_unknown_top_level_nested(self):
        sport = Sport.parse("parkour.freerunning")
        assert sport.parent == Sport.parse("parkour")

    def test_disciplines_empty_for_unknown(self):
        sport = Sport.parse("cycling.road.criterium")
        assert sport.disciplines == ()


class TestNonStandardModifiers:
    def test_unknown_modifier_preserved(self):
        sport = Sport.parse("cycling.road+rainy")
        assert sport.modifiers == frozenset()
        assert sport.unknown_modifiers == frozenset({"rainy"})
        assert sport.is_standard is False

    def test_mixed_known_and_unknown(self):
        sport = Sport.parse("cycling.road+race+rainy")
        assert sport.modifiers == frozenset({Modifier.RACE})
        assert sport.unknown_modifiers == frozenset({"rainy"})

    def test_multiple_unknown(self):
        sport = Sport.parse("cycling.road+foo+rainy")
        assert sport.unknown_modifiers == frozenset({"foo", "rainy"})

    def test_no_group_conflict_check(self):
        # parse does NOT validate group conflicts
        sport = Sport.parse("cycling.road+race+commute")
        assert sport.modifiers == frozenset({Modifier.RACE, Modifier.COMMUTE})
        assert sport.is_standard is True  # both modifiers are known — conflict is semantic, not structural

    def test_all_known_modifiers_with_conflict_accepted(self):
        # parse accepts group conflicts — no raise
        sport = Sport.parse("cycling.road+commute+race")
        assert Modifier.RACE in sport.modifiers
        assert Modifier.COMMUTE in sport.modifiers


class TestBothNonStandard:
    def test_unknown_code_and_modifier(self):
        sport = Sport.parse("parkour.freerunning+relay")
        assert sport.code == "parkour.freerunning"
        assert sport.unknown_modifiers == frozenset({"relay"})
        assert sport.is_standard is False


class TestRoundTrip:
    def test_standard_roundtrip(self):
        raw = "cycling.road+race+virtual"
        assert str(Sport.parse(raw)) == raw

    def test_non_standard_code_roundtrip(self):
        raw = "cycling.road.criterium+race"
        assert str(Sport.parse(raw)) == raw

    def test_non_standard_modifier_roundtrip(self):
        raw = "cycling.road+race+rainy"
        assert str(Sport.parse(raw)) == raw

    def test_both_non_standard_roundtrip(self):
        raw = "cycling.road.criterium+race+rainy"
        assert str(Sport.parse(raw)) == raw

    def test_bare_code_roundtrip(self):
        raw = "cycling.road"
        assert str(Sport.parse(raw)) == raw

    def test_raw_equals_str(self):
        raw = "cycling.road.criterium+race+rainy"
        sport = Sport.parse(raw)
        assert sport.raw == str(sport)


class TestEquality:
    def test_non_standard_not_equal_to_standard(self):
        assert Sport.parse("cycling.road.criterium") != Sport("cycling.road")

    def test_non_standard_equal_to_same_parse(self):
        a = Sport.parse("cycling.road.criterium+rainy")
        b = Sport.parse("cycling.road.criterium+rainy")
        assert a == b

    def test_different_unknown_modifiers_not_equal(self):
        a = Sport.parse("cycling.road+rainy")
        b = Sport.parse("cycling.road+foggy")
        assert a != b

    def test_hash_consistent(self):
        a = Sport.parse("cycling.road.criterium+rainy")
        b = Sport.parse("cycling.road.criterium+rainy")
        assert hash(a) == hash(b)

    def test_usable_in_set(self):
        s = {Sport.parse("cycling.road.criterium"), Sport.parse("cycling.road.criterium")}
        assert len(s) == 1


class TestStructuralErrors:
    def test_empty_string(self):
        with pytest.raises(ValueError):
            Sport.parse("")

    def test_trailing_plus(self):
        with pytest.raises(ValueError):
            Sport.parse("cycling.road+")

    def test_leading_plus(self):
        with pytest.raises(ValueError):
            Sport.parse("+cycling.road")

    def test_double_plus(self):
        with pytest.raises(ValueError):
            Sport.parse("cycling.road++virtual")

    def test_non_string(self):
        with pytest.raises(TypeError):
            Sport.parse(123)  # type: ignore[arg-type]


class TestPlatformTranslation:
    def test_non_standard_code_walks_up(self):
        from open_sports_schema.platforms import strava

        sport = Sport.parse("cycling.road.criterium+race")
        assert strava.translate(sport) == "Ride"

    def test_totally_unknown_falls_to_platform_fallback(self):
        from open_sports_schema.platforms import strava

        sport = Sport.parse("parkour.freerunning")
        assert strava.translate(sport) == "Workout"
