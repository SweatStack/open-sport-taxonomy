import pytest

from open_sport_taxonomy import Modifier, Sport
from open_sport_taxonomy._sport import _LABELS as TAXONOMY
from open_sport_taxonomy.platforms import strava


class TestExactMatches:
    def test_cycling_gravel(self):
        assert strava.encode(Sport.CYCLING_GRAVEL) == "GravelRide"

    def test_cycling_mountain(self):
        assert strava.encode(Sport.CYCLING_MOUNTAIN) == "MountainBikeRide"

    def test_running_trail(self):
        assert strava.encode(Sport.RUNNING_TRAIL) == "TrailRun"

    def test_walking_hiking(self):
        assert strava.encode(Sport.WALKING_HIKING) == "Hike"

    def test_xc_skiing_roller(self):
        assert strava.encode(Sport("xc_skiing.classic+roller")) == "RollerSki"


class TestModifierMatches:
    def test_cycling_road_virtual(self):
        assert strava.encode(Sport("cycling.road+virtual")) == "VirtualRide"

    def test_cycling_road_assisted(self):
        assert strava.encode(Sport("cycling.road+assisted")) == "EBikeRide"

    def test_cycling_mountain_assisted(self):
        assert strava.encode(Sport("cycling.mountain+assisted")) == "EMountainBikeRide"

    def test_rowing_virtual(self):
        assert strava.encode(Sport("rowing+virtual")) == "VirtualRow"

    def test_running_road_virtual(self):
        assert strava.encode(Sport("running.road+virtual")) == "VirtualRun"


class TestFallbackDropModifiers:
    def test_unknown_modifier_combo_drops_to_base(self):
        # stationary has no Strava-specific entry for cycling.road
        assert strava.encode(Sport("cycling.road+stationary")) == "Ride"

    def test_race_modifier_drops_to_base(self):
        assert strava.encode(Sport("cycling.gravel+race")) == "GravelRide"


class TestFallbackParent:
    def test_generic(self):
        assert strava.encode(Sport.GENERIC) == "Workout"


class TestDecode:
    def test_unique_target(self):
        assert strava.decode("VirtualRide") == Sport("cycling.road+virtual")

    def test_collapsed_target(self):
        # "Ride" is the canonical target for plain cycling; all cycling
        # disciplines that previously had explicit "Ride" entries now
        # collapse here via parent-walk on encode.
        assert strava.decode("Ride") == Sport.CYCLING

    def test_run_collapses_to_running(self):
        assert strava.decode("Run") == Sport.RUNNING

    def test_swim_collapses_to_swimming(self):
        assert strava.decode("Swim") == Sport.SWIMMING

    def test_modifier_preserved(self):
        assert strava.decode("RollerSki") == Sport("xc_skiing+roller")

    def test_unknown_falls_back_to_generic(self):
        assert strava.decode("NotARealStravaSportType") == Sport.GENERIC


class TestExhaustive:
    def test_every_sport_encodes(self):
        for code in TAXONOMY:
            result = strava.encode(Sport(code))
            assert isinstance(result, str)
            assert len(result) > 0
