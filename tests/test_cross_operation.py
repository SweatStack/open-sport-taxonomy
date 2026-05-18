import pytest

from open_sport_taxonomy import Modifier, Sport


class TestResolveEqualsValidate:
    def test_standard_input(self):
        assert Sport.resolve("cycling.road+race") == Sport.validate("cycling.road+race")

    def test_resolved_non_standard_equals_standard(self):
        assert Sport.resolve("cycling.road.criterium+race") == Sport.validate("cycling.road+race")

    def test_resolved_with_unknown_modifiers(self):
        assert Sport.resolve("cycling.road+race+rainy") == Sport.validate("cycling.road+race")

    def test_two_different_resolves_same_result(self):
        a = Sport.resolve("cycling.road.criterium+race")
        b = Sport.resolve("cycling.road.sprint+race")
        assert a == b


class TestParseNotEqualsValidate:
    def test_non_standard_code(self):
        assert Sport.parse("cycling.road.criterium") != Sport.validate("cycling.road")

    def test_non_standard_modifier(self):
        assert Sport.parse("cycling.road+rainy") != Sport.validate("cycling.road")

    def test_standard_parse_equals_validate(self):
        assert Sport.parse("cycling.road+race") == Sport.validate("cycling.road+race")


class TestRawPreservation:
    def test_resolve_raw_differs_from_str(self):
        sport = Sport.resolve("cycling.road.criterium+race+rainy")
        assert str(sport) == "cycling.road+race"
        assert sport.raw == "cycling.road.criterium+race+rainy"

    def test_resolve_standard_raw_equals_str(self):
        sport = Sport.resolve("cycling.road+race")
        assert sport.raw == str(sport)

    def test_parse_raw_equals_str(self):
        sport = Sport.parse("cycling.road.criterium+race+rainy")
        assert sport.raw == str(sport)

    def test_validate_raw_equals_str(self):
        sport = Sport.validate("cycling.road+race")
        assert sport.raw == str(sport)

    def test_class_constant_raw(self):
        assert Sport.CYCLING_ROAD.raw == "cycling.road"


class TestIsStandard:
    def test_validate_always_standard(self):
        assert Sport.validate("cycling.road").is_standard is True

    def test_resolve_always_standard(self):
        assert Sport.resolve("cycling.road.criterium").is_standard is True

    def test_parse_standard_when_known(self):
        assert Sport.parse("cycling.road+race").is_standard is True

    def test_parse_non_standard_unknown_code(self):
        assert Sport.parse("cycling.road.criterium").is_standard is False

    def test_parse_non_standard_unknown_modifier(self):
        assert Sport.parse("cycling.road+rainy").is_standard is False

    def test_class_constant_standard(self):
        assert Sport.CYCLING_ROAD.is_standard is True


class TestRawDoesNotAffectEquality:
    def test_different_raw_same_identity(self):
        a = Sport.resolve("cycling.road.criterium+race")
        b = Sport.resolve("cycling.road+race")
        assert a == b
        assert a.raw != b.raw

    def test_same_hash_different_raw(self):
        a = Sport.resolve("cycling.road.criterium+race")
        b = Sport.resolve("cycling.road+race")
        assert hash(a) == hash(b)

    def test_dict_key_works(self):
        a = Sport.resolve("cycling.road.criterium+race")
        b = Sport.resolve("cycling.road+race")
        d = {a: "value"}
        assert d[b] == "value"


class TestPlatformTranslationConsistency:
    def test_resolve_and_parse_same_translation(self):
        from open_sport_taxonomy.platforms import strava

        raw = "cycling.road.criterium+race+rainy"
        assert strava.translate(Sport.resolve(raw)) == strava.translate(Sport.parse(raw))

    def test_non_standard_falls_through(self):
        from open_sport_taxonomy.platforms import strava, apple_healthkit, garmin_fit
        from open_sport_taxonomy import GarminFitCode

        sport = Sport.parse("cycling.road.criterium")
        assert strava.translate(sport) == "Ride"
        assert apple_healthkit.translate(sport) == 13
        assert garmin_fit.translate(sport) == GarminFitCode(sport=2, sub_sport=7)
