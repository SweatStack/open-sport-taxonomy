from open_sport_taxonomy import Sport
from open_sport_taxonomy._sport import _LABELS as TAXONOMY
from open_sport_taxonomy.platforms import apple_healthkit


class TestMappings:
    def test_cycling_road(self):
        assert apple_healthkit.translate(Sport.CYCLING_ROAD) == 13

    def test_all_cycling_maps_to_13(self):
        cycling_codes = [c for c in TAXONOMY if c.startswith("cycling")]
        for code in cycling_codes:
            assert apple_healthkit.translate(Sport(code)) == 13

    def test_running(self):
        assert apple_healthkit.translate(Sport.RUNNING) == 37

    def test_walking_hiking_distinct(self):
        assert apple_healthkit.translate(Sport.WALKING) == 52
        assert apple_healthkit.translate(Sport.WALKING_HIKING) == 24

    def test_swimming(self):
        assert apple_healthkit.translate(Sport.SWIMMING) == 46

    def test_rowing(self):
        assert apple_healthkit.translate(Sport.ROWING) == 35

    def test_generic(self):
        assert apple_healthkit.translate(Sport.GENERIC) == 3000

    def test_xc_skiing(self):
        assert apple_healthkit.translate(Sport.XC_SKIING) == 60

    def test_roller_skiing_maps_to_skating(self):
        assert apple_healthkit.translate(Sport("xc_skiing.classic+roller")) == 30


class TestFallback:
    def test_modifiers_ignored(self):
        # HealthKit has no modifier-specific entries
        from open_sport_taxonomy import Modifier

        assert apple_healthkit.translate(Sport("cycling.road+virtual")) == 13


class TestExhaustive:
    def test_every_sport_translates(self):
        for code in TAXONOMY:
            result = apple_healthkit.translate(Sport(code))
            assert isinstance(result, int)
