pydantic = __import__("pytest").importorskip("pydantic")

from pydantic import BaseModel, ValidationError

from open_sport_taxonomy import Modifier, Sport
from open_sport_taxonomy.pydantic import SportField, StrictSportField


class PermissiveModel(BaseModel):
    sport: SportField


class StrictModel(BaseModel):
    sport: StrictSportField


# ---------------------------------------------------------------------------
# SportField (permissive)
# ---------------------------------------------------------------------------


class TestSportFieldValidation:
    def test_string_input(self):
        m = PermissiveModel(sport="cycling.road+stationary")
        assert m.sport.code == "cycling.road"
        assert Modifier.STATIONARY in m.sport.modifiers

    def test_sport_instance_passthrough(self):
        m = PermissiveModel(sport=Sport.CYCLING_ROAD)
        assert m.sport == Sport.CYCLING_ROAD

    def test_non_standard_preserved(self):
        m = PermissiveModel(sport="cycling.road.criterium+race+rainy")
        assert m.sport.code == "cycling.road.criterium"
        assert "rainy" in m.sport.modifiers
        assert m.sport.is_standard is False

    def test_empty_string_raises(self):
        with __import__("pytest").raises(ValidationError):
            PermissiveModel(sport="")

    def test_non_string_raises(self):
        with __import__("pytest").raises(ValidationError):
            PermissiveModel(sport=123)

    def test_none_raises(self):
        with __import__("pytest").raises(ValidationError):
            PermissiveModel(sport=None)


class TestSportFieldSerialization:
    def test_model_dump(self):
        m = PermissiveModel(sport="cycling.road+race")
        assert m.model_dump() == {"sport": "cycling.road+race"}

    def test_model_dump_json(self):
        m = PermissiveModel(sport="cycling.road+race")
        assert '"cycling.road+race"' in m.model_dump_json()

    def test_roundtrip(self):
        m = PermissiveModel(sport="cycling.road.criterium+race+rainy")
        data = m.model_dump()
        m2 = PermissiveModel(**data)
        assert m2.sport == m.sport


class TestSportFieldSchema:
    def test_json_schema_type(self):
        schema = PermissiveModel.model_json_schema()
        sport_schema = schema["properties"]["sport"]
        assert sport_schema["type"] == "string"

    def test_json_schema_description(self):
        schema = PermissiveModel.model_json_schema()
        sport_schema = schema["properties"]["sport"]
        assert "description" in sport_schema


# ---------------------------------------------------------------------------
# StrictSportField
# ---------------------------------------------------------------------------


class TestStrictSportFieldValidation:
    def test_standard_accepted(self):
        m = StrictModel(sport="cycling.road+race")
        assert m.sport.code == "cycling.road"
        assert m.sport.is_standard is True

    def test_unknown_code_raises(self):
        with __import__("pytest").raises(ValidationError):
            StrictModel(sport="cycling.road.criterium")

    def test_unknown_modifier_raises(self):
        with __import__("pytest").raises(ValidationError):
            StrictModel(sport="cycling.road+rainy")

    def test_empty_string_raises(self):
        with __import__("pytest").raises(ValidationError):
            StrictModel(sport="")

    def test_non_string_raises(self):
        with __import__("pytest").raises(ValidationError):
            StrictModel(sport=123)


class TestStrictSportFieldSerialization:
    def test_model_dump(self):
        m = StrictModel(sport="cycling.road+race")
        assert m.model_dump() == {"sport": "cycling.road+race"}


class TestStrictSportFieldSchema:
    def test_json_schema_same_as_permissive(self):
        permissive = PermissiveModel.model_json_schema()["properties"]["sport"]
        strict = StrictModel.model_json_schema()["properties"]["sport"]
        assert permissive == strict
