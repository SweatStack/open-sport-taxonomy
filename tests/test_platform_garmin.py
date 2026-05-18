from open_sport_taxonomy import GarminFitCode, Sport
from open_sport_taxonomy._sport import _LABELS as TAXONOMY
from open_sport_taxonomy.platforms import garmin_fit


class TestMappings:
    def test_cycling_road(self):
        assert garmin_fit.translate(Sport.CYCLING_ROAD) == GarminFitCode(sport=2, sub_sport=7)

    def test_cycling_gravel(self):
        assert garmin_fit.translate(Sport.CYCLING_GRAVEL) == GarminFitCode(sport=2, sub_sport=46)

    def test_cycling_mountain(self):
        assert garmin_fit.translate(Sport.CYCLING_MOUNTAIN) == GarminFitCode(sport=2, sub_sport=8)

    def test_running(self):
        assert garmin_fit.translate(Sport.RUNNING) == GarminFitCode(sport=1, sub_sport=0)

    def test_running_trail(self):
        assert garmin_fit.translate(Sport.RUNNING_TRAIL) == GarminFitCode(sport=1, sub_sport=3)

    def test_walking_hiking_distinct_sport(self):
        assert garmin_fit.translate(Sport.WALKING) == GarminFitCode(sport=11, sub_sport=0)
        assert garmin_fit.translate(Sport.WALKING_HIKING) == GarminFitCode(sport=17, sub_sport=0)

    def test_swimming_pool(self):
        assert garmin_fit.translate(Sport.SWIMMING_POOL) == GarminFitCode(sport=5, sub_sport=17)

    def test_xc_skiing_skate(self):
        assert garmin_fit.translate(Sport.XC_SKIING_SKATE) == GarminFitCode(sport=12, sub_sport=42)

    def test_generic(self):
        assert garmin_fit.translate(Sport.GENERIC) == GarminFitCode(sport=0, sub_sport=0)


class TestNamedTuple:
    def test_attribute_access(self):
        result = garmin_fit.translate(Sport.CYCLING_ROAD)
        assert result.sport == 2
        assert result.sub_sport == 7

    def test_tuple_unpacking(self):
        sport, sub_sport = garmin_fit.translate(Sport.CYCLING_ROAD)
        assert sport == 2
        assert sub_sport == 7

    def test_type(self):
        result = garmin_fit.translate(Sport.CYCLING_ROAD)
        assert isinstance(result, GarminFitCode)
        assert isinstance(result, tuple)


class TestExhaustive:
    def test_every_sport_translates(self):
        for code in TAXONOMY:
            result = garmin_fit.translate(Sport(code))
            assert isinstance(result, GarminFitCode)
            assert isinstance(result.sport, int)
            assert isinstance(result.sub_sport, int)
