import pytest

from open_sport_taxonomy import Modifier, Sport


class TestStandardInput:
    def test_standard_code(self):
        sport = Sport.parse("cycling.road")
        assert sport.code == "cycling.road"
        assert sport.is_standard is True

    def test_standard_with_modifiers(self):
        sport = Sport.parse("cycling+stationary+virtual")
        assert sport.code == "cycling"
        assert Modifier.STATIONARY in sport.modifiers
        assert Modifier.VIRTUAL in sport.modifiers
        assert sport.is_standard is True

    def test_equals_constructor(self):
        assert Sport.parse("cycling.road") == Sport("cycling.road")
        assert Sport.parse("cycling.road+race") == Sport("cycling.road+race")


class TestNonStandardCode:
    def test_unknown_code_preserved(self):
        sport = Sport.parse("cycling.road.criterium")
        assert sport.code == "cycling.road.criterium"
        assert sport.is_standard is False

    def test_unknown_code_label_is_composed(self):
        # label is always a string; for an unknown code it composes from the
        # token (dots/underscores → spaces). is_standard signals it's not curated.
        sport = Sport.parse("cycling.road.criterium")
        assert sport.label == "cycling road criterium"
        assert sport.is_standard is False
        assert sport.uses_known_atoms is False

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
        assert "rainy" in sport.modifiers
        assert sport.is_standard is False

    def test_mixed_known_and_unknown(self):
        sport = Sport.parse("cycling.road+race+rainy")
        assert Modifier.RACE in sport.modifiers
        assert "rainy" in sport.modifiers

    def test_group_conflicts_not_enforced(self):
        # Unlike Sport(...), Sport.parse does NOT raise on group conflicts —
        # it preserves whatever the caller provided.
        sport = Sport.parse("cycling.road+race+commute")
        assert Modifier.RACE in sport.modifiers
        assert Modifier.COMMUTE in sport.modifiers


class TestBothNonStandard:
    def test_unknown_code_and_modifier(self):
        sport = Sport.parse("parkour.freerunning+relay")
        assert sport.code == "parkour.freerunning"
        assert "relay" in sport.modifiers
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

    def test_str_roundtrip_parse(self):
        raw = "cycling.road.criterium+race+rainy"
        sport = Sport.parse(raw)
        assert Sport.parse(str(sport)) == sport


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
        from open_sport_taxonomy.platforms import strava

        sport = Sport.parse("cycling.road.criterium+race")
        assert strava.encode(sport) == "Ride"

    def test_totally_unknown_falls_to_platform_fallback(self):
        from open_sport_taxonomy.platforms import strava

        sport = Sport.parse("parkour.freerunning")
        assert strava.encode(sport) == "Workout"
