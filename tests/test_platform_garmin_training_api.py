from open_sport_taxonomy import Sport
from open_sport_taxonomy.platforms import garmin_training_api


class TestMappings:
    def test_cycling(self):
        assert garmin_training_api.translate(Sport("cycling")) == "CYCLING"

    def test_running(self):
        assert garmin_training_api.translate(Sport("running")) == "RUNNING"

    def test_swimming(self):
        assert garmin_training_api.translate(Sport("swimming")) == "LAP_SWIMMING"

    def test_generic(self):
        assert garmin_training_api.translate(Sport("generic")) == "GENERIC"


class TestFallbackHierarchy:
    def test_cycling_discipline(self):
        assert garmin_training_api.translate(Sport("cycling.road")) == "CYCLING"

    def test_running_discipline(self):
        assert garmin_training_api.translate(Sport("running.trail")) == "RUNNING"

    def test_swimming_discipline(self):
        assert garmin_training_api.translate(Sport("swimming.pool")) == "LAP_SWIMMING"


class TestFallbackModifiers:
    def test_modifiers_ignored(self):
        assert garmin_training_api.translate(Sport("cycling.road+stationary")) == "CYCLING"


class TestFallbackDefault:
    def test_unmapped_sport(self):
        assert garmin_training_api.translate(Sport("rowing")) == "CYCLING"

    def test_unmapped_walking(self):
        assert garmin_training_api.translate(Sport("walking")) == "CYCLING"

    def test_unmapped_xc_skiing(self):
        assert garmin_training_api.translate(Sport("xc_skiing")) == "CYCLING"


class TestExhaustive:
    def test_every_sport_translates(self):
        for sport in Sport.all():
            result = garmin_training_api.translate(sport)
            assert isinstance(result, str)
