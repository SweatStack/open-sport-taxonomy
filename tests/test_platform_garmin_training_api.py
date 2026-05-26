from open_sport_taxonomy import Sport
from open_sport_taxonomy.platforms import garmin_training_api


class TestMappings:
    def test_cycling(self):
        assert garmin_training_api.encode(Sport("cycling")) == "CYCLING"

    def test_running(self):
        assert garmin_training_api.encode(Sport("running")) == "RUNNING"

    def test_swimming(self):
        assert garmin_training_api.encode(Sport("swimming")) == "LAP_SWIMMING"

    def test_generic(self):
        assert garmin_training_api.encode(Sport("generic")) == "GENERIC"


class TestFallbackHierarchy:
    def test_cycling_discipline(self):
        assert garmin_training_api.encode(Sport("cycling.road")) == "CYCLING"

    def test_running_discipline(self):
        assert garmin_training_api.encode(Sport("running.trail")) == "RUNNING"

    def test_swimming_discipline(self):
        assert garmin_training_api.encode(Sport("swimming.pool")) == "LAP_SWIMMING"


class TestFallbackModifiers:
    def test_modifiers_ignored(self):
        assert garmin_training_api.encode(Sport("cycling.road+stationary")) == "CYCLING"


class TestFallbackDefault:
    def test_unmapped_sport(self):
        assert garmin_training_api.encode(Sport("rowing")) == "GENERIC"

    def test_unmapped_walking(self):
        assert garmin_training_api.encode(Sport("walking")) == "GENERIC"

    def test_unmapped_xc_skiing(self):
        assert garmin_training_api.encode(Sport("xc_skiing")) == "GENERIC"


class TestDecode:
    def test_cycling(self):
        assert garmin_training_api.decode("CYCLING") == Sport.CYCLING

    def test_running(self):
        assert garmin_training_api.decode("RUNNING") == Sport.RUNNING

    def test_swimming(self):
        assert garmin_training_api.decode("LAP_SWIMMING") == Sport.SWIMMING

    def test_generic(self):
        assert garmin_training_api.decode("GENERIC") == Sport.GENERIC

    def test_unknown_falls_back_to_generic(self):
        assert garmin_training_api.decode("NOT_A_REAL_TYPE") == Sport.GENERIC


class TestExhaustive:
    def test_every_sport_encodes(self):
        for sport in Sport.all():
            result = garmin_training_api.encode(sport)
            assert isinstance(result, str)
