from open_sport_taxonomy import Sport
from open_sport_taxonomy._sport import _LABELS as TAXONOMY
from open_sport_taxonomy.platforms import apple_healthkit


class TestMappings:
    def test_cycling_road(self):
        assert apple_healthkit.encode(Sport.CYCLING_ROAD) == 13

    def test_all_cycling_maps_to_13(self):
        cycling_codes = [c for c in TAXONOMY if c.startswith("cycling")]
        for code in cycling_codes:
            assert apple_healthkit.encode(Sport(code)) == 13

    def test_running(self):
        assert apple_healthkit.encode(Sport.RUNNING) == 37

    def test_walking_hiking_distinct(self):
        assert apple_healthkit.encode(Sport.WALKING) == 52
        assert apple_healthkit.encode(Sport.WALKING_HIKING) == 24

    def test_swimming(self):
        assert apple_healthkit.encode(Sport.SWIMMING) == 46

    def test_rowing(self):
        assert apple_healthkit.encode(Sport.ROWING) == 35

    def test_generic(self):
        assert apple_healthkit.encode(Sport.GENERIC) == 3000

    def test_xc_skiing(self):
        assert apple_healthkit.encode(Sport.XC_SKIING) == 60

    def test_roller_skiing_maps_to_skating(self):
        assert apple_healthkit.encode(Sport("xc_skiing.classic+roller")) == 30


class TestFallback:
    def test_modifiers_ignored(self):
        # HealthKit has no modifier-specific entries
        from open_sport_taxonomy import Modifier

        assert apple_healthkit.encode(Sport("cycling.road+virtual")) == 13


class TestDecode:
    def test_cycling(self):
        assert apple_healthkit.decode(13) == Sport.CYCLING

    def test_running(self):
        assert apple_healthkit.decode(37) == Sport.RUNNING

    def test_swimming(self):
        assert apple_healthkit.decode(46) == Sport.SWIMMING

    def test_walking_hiking_distinct(self):
        assert apple_healthkit.decode(52) == Sport.WALKING
        assert apple_healthkit.decode(24) == Sport.WALKING_HIKING

    def test_rowing(self):
        assert apple_healthkit.decode(35) == Sport.ROWING

    def test_generic(self):
        assert apple_healthkit.decode(3000) == Sport.GENERIC

    def test_xc_skiing(self):
        assert apple_healthkit.decode(60) == Sport.XC_SKIING

    def test_roller_skating_preserves_modifier(self):
        assert apple_healthkit.decode(30) == Sport("xc_skiing+roller")

    def test_unknown_value_falls_back_to_generic(self):
        assert apple_healthkit.decode(99999) == Sport.GENERIC


class TestExhaustive:
    def test_every_sport_encodes(self):
        for code in TAXONOMY:
            result = apple_healthkit.encode(Sport(code))
            assert isinstance(result, int)
