import pytest

from open_sport_taxonomy import GarminFitCode, Sport
from open_sport_taxonomy._sport import _LABELS as TAXONOMY
from open_sport_taxonomy.platforms import garmin_fit


class TestEncode:
    def test_cycling_road(self):
        assert garmin_fit.encode(Sport.CYCLING_ROAD) == GarminFitCode(2, 7)

    def test_cycling_gravel(self):
        assert garmin_fit.encode(Sport.CYCLING_GRAVEL) == GarminFitCode(2, 46)

    def test_cycling_mountain(self):
        assert garmin_fit.encode(Sport.CYCLING_MOUNTAIN) == GarminFitCode(2, 8)

    def test_running(self):
        assert garmin_fit.encode(Sport.RUNNING) == GarminFitCode(1, 0)

    def test_running_trail(self):
        assert garmin_fit.encode(Sport.RUNNING_TRAIL) == GarminFitCode(1, 3)

    def test_walking_hiking_distinct_sport(self):
        assert garmin_fit.encode(Sport.WALKING) == GarminFitCode(11, 0)
        assert garmin_fit.encode(Sport.WALKING_HIKING) == GarminFitCode(17, 0)

    def test_swimming_pool(self):
        assert garmin_fit.encode(Sport.SWIMMING_POOL) == GarminFitCode(5, 17)

    def test_xc_skiing_skate(self):
        assert garmin_fit.encode(Sport.XC_SKIING_SKATE) == GarminFitCode(12, 42)

    def test_generic(self):
        assert garmin_fit.encode(Sport.GENERIC) == GarminFitCode(0, 0)

    def test_time_trial_falls_back_to_cycling(self):
        # FIT has no time_trial sub_sport — encode walks up to plain cycling.
        assert garmin_fit.encode(Sport.CYCLING_TIME_TRIAL) == GarminFitCode(2, 0)

    def test_xc_classic_roller_walks_to_parent_with_modifier(self):
        # No xc_skiing.classic+roller entry; parent xc_skiing+roller exists.
        # Relies on parent-walk preserving modifiers.
        assert garmin_fit.encode(Sport("xc_skiing.classic+roller")) == GarminFitCode(30, 0)


class TestDecode:
    def test_int_pair(self):
        assert garmin_fit.decode(2, 7) == Sport.CYCLING_ROAD

    def test_name_pair(self):
        assert garmin_fit.decode("cycling", "road") == Sport.CYCLING_ROAD

    def test_mixed_int_and_name(self):
        assert garmin_fit.decode(2, "road") == Sport.CYCLING_ROAD
        assert garmin_fit.decode("cycling", 7) == Sport.CYCLING_ROAD

    def test_keyword_args(self):
        assert garmin_fit.decode(sport=2, sub_sport=7) == Sport.CYCLING_ROAD

    def test_sub_sport_defaults_to_zero(self):
        assert garmin_fit.decode(2) == Sport.CYCLING

    def test_unknown_sub_sport_reduces(self):
        # sport=2 known, sub_sport=99 not in mapping — reduce to (2, 0).
        assert garmin_fit.decode(2, 99) == Sport.CYCLING

    def test_unknown_sport_falls_back_to_generic(self):
        # FIT sport=7 is soccer — not modelled by OST.
        assert garmin_fit.decode(7, 0) == Sport.GENERIC

    def test_unknown_name_raises(self):
        with pytest.raises(ValueError, match="Unknown FIT sport name"):
            garmin_fit.decode("cyling", "road")

    def test_unknown_sub_sport_name_raises(self):
        with pytest.raises(ValueError, match="Unknown FIT sub_sport name"):
            garmin_fit.decode("cycling", "raod")

    def test_modifier_preserved_in_decode(self):
        # FIT sport=30 is inline_skating, mapped from xc_skiing+roller.
        assert garmin_fit.decode(30, 0) == Sport("xc_skiing+roller")

    def test_none_sub_sport_treated_as_generic(self):
        # FIT parsers commonly return None for fields not set in a session.
        assert garmin_fit.decode(2, None) == Sport.CYCLING

    def test_none_sport_falls_back(self):
        # Malformed FIT with no sport field at all — graceful, not an error.
        assert garmin_fit.decode(None, None) == Sport.GENERIC

    def test_none_sport_with_known_sub_sport(self):
        # No matching pair, no reducer hit (sub_sport=7 alone isn't reverse-mapped),
        # falls through to GENERIC.
        assert garmin_fit.decode(None, 7) == Sport.GENERIC


class TestRoundTrip:
    @pytest.mark.parametrize("sport", [
        Sport.CYCLING,
        Sport.CYCLING_ROAD,
        Sport.CYCLING_GRAVEL,
        Sport.CYCLING_MOUNTAIN,
        Sport.RUNNING,
        Sport.RUNNING_TRAIL,
        Sport.SWIMMING_POOL,
        Sport.XC_SKIING_SKATE,
        Sport("xc_skiing+roller"),
        Sport.WALKING_HIKING,
    ])
    def test_round_trip(self, sport):
        encoded = garmin_fit.encode(sport)
        decoded = garmin_fit.decode(*encoded)
        assert decoded == sport


class TestGarminFitCode:
    def test_attribute_access(self):
        code = garmin_fit.encode(Sport.CYCLING_ROAD)
        assert code.sport == 2
        assert code.sub_sport == 7
        assert code.sport_name == "cycling"
        assert code.sub_sport_name == "road"

    def test_tuple_unpacking(self):
        sport_id, sub_sport_id = garmin_fit.encode(Sport.CYCLING_ROAD)
        assert sport_id == 2
        assert sub_sport_id == 7

    def test_construct_from_names(self):
        assert GarminFitCode("cycling", "road") == GarminFitCode(2, 7)

    def test_construct_mixed(self):
        assert GarminFitCode(2, "road") == GarminFitCode(2, 7)
        assert GarminFitCode("cycling", 7) == GarminFitCode(2, 7)

    def test_unknown_name_raises(self):
        with pytest.raises(ValueError, match="Unknown FIT sport name"):
            GarminFitCode("not_a_sport", 0)

    def test_unknown_int_accepted(self):
        # Forward-compat: unknown ids may be future SDK additions.
        code = GarminFitCode(999, 0)
        assert code.sport == 999
        assert code.sport_name is None

    def test_type(self):
        result = garmin_fit.encode(Sport.CYCLING_ROAD)
        assert isinstance(result, GarminFitCode)
        assert isinstance(result, tuple)

    def test_bool_rejected(self):
        with pytest.raises(TypeError):
            GarminFitCode(True, 0)


class TestExhaustive:
    def test_every_sport_encodes(self):
        for code in TAXONOMY:
            result = garmin_fit.encode(Sport(code))
            assert isinstance(result, GarminFitCode)

    def test_every_known_fit_sport_decodes(self):
        from open_sport_taxonomy._platforms import FIT_SPORT_IDS
        for sport_id in FIT_SPORT_IDS.values():
            result = garmin_fit.decode(sport_id, 0)
            assert isinstance(result, Sport)
