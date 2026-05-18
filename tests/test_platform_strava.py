import pytest

from open_sport_taxonomy import Modifier, Sport
from open_sport_taxonomy._sport import _LABELS as TAXONOMY
from open_sport_taxonomy.platforms import strava


class TestExactMatches:
    def test_cycling_gravel(self):
        assert strava.translate(Sport.CYCLING_GRAVEL) == "GravelRide"

    def test_cycling_mountain(self):
        assert strava.translate(Sport.CYCLING_MOUNTAIN) == "MountainBikeRide"

    def test_running_trail(self):
        assert strava.translate(Sport.RUNNING_TRAIL) == "TrailRun"

    def test_walking_hiking(self):
        assert strava.translate(Sport.WALKING_HIKING) == "Hike"

    def test_xc_skiing_backcountry(self):
        assert strava.translate(Sport.XC_SKIING_BACKCOUNTRY) == "BackcountrySki"


class TestModifierMatches:
    def test_cycling_road_virtual(self):
        assert strava.translate(Sport("cycling.road+virtual")) == "VirtualRide"

    def test_cycling_road_assisted(self):
        assert strava.translate(Sport("cycling.road+assisted")) == "EBikeRide"

    def test_cycling_mountain_assisted(self):
        assert strava.translate(Sport("cycling.mountain+assisted")) == "EMountainBikeRide"

    def test_rowing_virtual(self):
        assert strava.translate(Sport("rowing+virtual")) == "VirtualRow"

    def test_running_road_virtual(self):
        assert strava.translate(Sport("running.road+virtual")) == "VirtualRun"


class TestFallbackDropModifiers:
    def test_unknown_modifier_combo_drops_to_base(self):
        # stationary has no Strava-specific entry for cycling.road
        assert strava.translate(Sport("cycling.road+stationary")) == "Ride"

    def test_race_modifier_drops_to_base(self):
        assert strava.translate(Sport("cycling.gravel+race")) == "GravelRide"


class TestFallbackParent:
    def test_generic(self):
        assert strava.translate(Sport.GENERIC) == "Workout"


class TestExhaustive:
    def test_every_sport_translates(self):
        for code in TAXONOMY:
            result = strava.translate(Sport(code))
            assert isinstance(result, str)
            assert len(result) > 0
