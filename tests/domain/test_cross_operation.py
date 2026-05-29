from open_sport_taxonomy import Modifier, Sport


class TestResolveEqualsConstructor:
    def test_standard_input(self):
        assert Sport.parse("cycling.road+race").resolve() == Sport("cycling.road+race")

    def test_resolved_non_standard_equals_standard(self):
        assert Sport.parse("cycling.road.criterium+race").resolve() == Sport("cycling.road+race")

    def test_resolved_with_unknown_modifiers(self):
        assert Sport.parse("cycling.road+race+rainy").resolve() == Sport("cycling.road+race")

    def test_two_different_resolves_same_result(self):
        a = Sport.parse("cycling.road.criterium+race").resolve()
        b = Sport.parse("cycling.road.sprint+race").resolve()
        assert a == b


class TestParseNotEqualsConstructor:
    def test_non_standard_code(self):
        assert Sport.parse("cycling.road.criterium") != Sport("cycling.road")

    def test_non_standard_modifier(self):
        assert Sport.parse("cycling.road+rainy") != Sport("cycling.road")

    def test_standard_parse_equals_constructor(self):
        assert Sport.parse("cycling.road+race") == Sport("cycling.road+race")


class TestStrAlwaysFaithful:
    def test_resolve_str_is_canonical(self):
        sport = Sport.parse("cycling.road.criterium+race+rainy").resolve()
        assert str(sport) == "cycling.road+race"

    def test_parse_str_preserves_input(self):
        sport = Sport.parse("cycling.road.criterium+race+rainy")
        assert str(sport) == "cycling.road.criterium+race+rainy"

    def test_constructor_str(self):
        sport = Sport("cycling.road+race")
        assert str(sport) == "cycling.road+race"


class TestIsStandard:
    def test_constructor_always_standard(self):
        assert Sport("cycling.road").is_standard is True

    def test_resolve_always_standard(self):
        assert Sport.parse("cycling.road.criterium").resolve().is_standard is True

    def test_parse_standard_when_known(self):
        assert Sport.parse("cycling.road+race").is_standard is True

    def test_parse_non_standard_unknown_code(self):
        assert Sport.parse("cycling.road.criterium").is_standard is False

    def test_parse_non_standard_unknown_modifier(self):
        assert Sport.parse("cycling.road+rainy").is_standard is False


class TestUnifiedModifiers:
    def test_parse_mixed_modifiers_in_single_set(self):
        sport = Sport.parse("cycling.road+race+rainy")
        assert Modifier.RACE in sport.modifiers
        assert "rainy" in sport.modifiers
        assert "race" in sport.modifiers  # Modifier.RACE == "race"

    def test_resolve_drops_unknown_modifiers(self):
        sport = Sport.parse("cycling.road+race+rainy")
        resolved = sport.resolve()
        assert Modifier.RACE in resolved.modifiers
        assert "rainy" not in resolved.modifiers

    def test_diff_reveals_unknowns(self):
        sport = Sport.parse("cycling.road+race+rainy")
        resolved = sport.resolve()
        unknowns = sport.modifiers - resolved.modifiers
        assert unknowns == {"rainy"}


class TestPlatformTranslationConsistency:
    def test_resolve_and_parse_same_translation(self):
        from open_sport_taxonomy.platforms import strava

        raw = "cycling.road.criterium+race+rainy"
        assert strava.encode(Sport.parse(raw).resolve()) == strava.encode(Sport.parse(raw))

    def test_non_standard_falls_through(self):
        from open_sport_taxonomy import GarminFitCode
        from open_sport_taxonomy.platforms import apple_healthkit, garmin_fit, strava

        sport = Sport.parse("cycling.road.criterium")
        assert strava.encode(sport) == "Ride"
        assert apple_healthkit.encode(sport) == 13
        assert garmin_fit.encode(sport) == GarminFitCode(sport=2, sub_sport=7)
