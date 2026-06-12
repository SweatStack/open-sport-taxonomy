"""GarminFitCode NamedTuple and decode argument-form tests.

Two concerns covered here that are platform-specific and not exercised
by the generic encode/decode/round-trip tests:

  - The :class:`GarminFitCode` NamedTuple's construction API
    (ints, names, mixed, kwargs, bool rejection, unknown-int
    forward-compat).
  - The :meth:`_GarminFitPlatform.decode` override's flexible argument
    handling (ints/names/None in either position, kwargs, defaults).

The decode-argument-form tests are platform-specific because only FIT's
target is a struct with field semantics; other platforms decode a single
opaque value.
"""

import pytest

from open_sport_taxonomy import GarminFitCode, Sport
from open_sport_taxonomy.platforms import garmin_fit


class TestGarminFitCode:
    """NamedTuple construction, identity, and forward-compat."""

    def test_attribute_access(self):
        # CYCLING_GRAVEL has a dedicated FIT sub_sport (46), so it exercises the
        # named-field accessors. (CYCLING_ROAD now encodes to generic 2/0.)
        code = garmin_fit.encode(Sport("cycling.gravel"))
        assert code.sport == 2
        assert code.sub_sport == 46
        assert code.sport_name == "cycling"
        assert code.sub_sport_name == "gravel_cycling"

    def test_tuple_unpacking(self):
        sport_id, sub_sport_id = garmin_fit.encode(Sport("cycling.gravel"))
        assert sport_id == 2
        assert sub_sport_id == 46

    def test_construct_from_names(self):
        assert GarminFitCode("cycling", "road") == GarminFitCode(2, 7)

    def test_sub_sport_defaults_to_zero(self):
        # Single-arg construction defaults sub_sport to 0 (FIT generic).
        # Exercised via the public NamedTuple API even though the decode
        # override always provides both args.
        assert GarminFitCode(2) == GarminFitCode(2, 0)

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
        result = garmin_fit.encode(Sport("cycling.road"))
        assert isinstance(result, GarminFitCode)
        assert isinstance(result, tuple)

    def test_bool_rejected(self):
        # bool is a subclass of int; reject explicitly to avoid surprises.
        with pytest.raises(TypeError):
            GarminFitCode(True, 0)


class TestDecodeArgumentForms:
    """`_GarminFitPlatform.decode` accepts flexible input forms.

    The signature is ``decode(sport, sub_sport=0)`` where each argument
    may be ``int | str | None``. The override exists because FIT parsers
    return ``(sport, sub_sport)`` as separate values, and the names are
    interchangeable with the integer ids at the protocol level.
    """

    def test_int_pair(self):
        assert garmin_fit.decode(2, 7) == Sport("cycling.road")

    def test_name_pair(self):
        assert garmin_fit.decode("cycling", "road") == Sport("cycling.road")

    def test_mixed_int_and_name(self):
        assert garmin_fit.decode(2, "road") == Sport("cycling.road")
        assert garmin_fit.decode("cycling", 7) == Sport("cycling.road")

    def test_keyword_args(self):
        assert garmin_fit.decode(sport=2, sub_sport=7) == Sport("cycling.road")

    def test_sub_sport_defaults_to_zero(self):
        # (2, 0) is the opinionated generic→road default.
        assert garmin_fit.decode(2) == Sport("cycling.road")

    def test_unknown_name_raises(self):
        with pytest.raises(ValueError, match="Unknown FIT sport name"):
            garmin_fit.decode("cyling", "road")

    def test_unknown_sub_sport_name_raises(self):
        with pytest.raises(ValueError, match="Unknown FIT sub_sport name"):
            garmin_fit.decode("cycling", "raod")

    def test_none_sub_sport_treated_as_generic(self):
        # FIT parsers commonly return None for fields not set in a session.
        # (2, 0) is the opinionated generic→road default.
        assert garmin_fit.decode(2, None) == Sport("cycling.road")

    def test_none_sport_falls_back(self):
        # Malformed FIT with no sport field at all — graceful, not an error.
        assert garmin_fit.decode(None, None) == Sport("generic")

    def test_none_sport_with_known_sub_sport(self):
        # No matching pair, coarsening to (0, 0) hits the generic preferred entry.
        assert garmin_fit.decode(None, 7) == Sport("generic")


class TestDecodeExhaustiveSmoke:
    """Every FIT sport id from the SDK enum decodes to a Sport.

    Catches integer-key edge cases that the parametrized round-trip
    suite (which iterates over the *mapped* entries, not the full FIT
    enum) does not reach.
    """

    def test_every_known_fit_sport_decodes(self):
        from open_sport_taxonomy._platforms import FIT_SPORT_IDS

        for sport_id in FIT_SPORT_IDS.values():
            result = garmin_fit.decode(sport_id, 0)
            assert isinstance(result, Sport)
