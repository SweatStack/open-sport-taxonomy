"""Algorithm-regression safety net for encode + decode round-trips.

The exhaustive guarantee — that every preferred entry in every mapping
file round-trips — is enforced by ``scripts/generate.py`` validation
rules 10 and 11 at *generation* time. That check exercises every entry
against the runtime built from the same data.

What lives here is a hand-curated set of *representative* cases per
platform that exercise the encode and decode code paths once each.
Six cases per platform × five platforms = 30 tests. If an algorithm
change breaks any of these, the failure points at one code path, not
292 data points.

The six per-platform cases:

  1. Preferred-entry exact round-trip — the canonical happy path.
  2. Non-preferred synonym decode — multiple platform targets that
     mean the same OST concept decode to the canonical sport.
  3. Null-sport decode — entries with ``sport: null`` route to
     ``fallback.decode``.
  4. Parent-walk encode — a sport without an exact preferred match
     finds one via the OST hierarchy walk.
  5. Modifier-drop encode — a sport whose modifier combination has no
     preferred entry falls back to its bare-sport entry.
  6. Coarsening decode (FIT only — others substitute "unmapped
     decode → fallback") — a target absent from the table is rewritten
     via ``target_coarsening`` and re-looked-up.

Each case is annotated with the code path it covers so future readers
can see, at a glance, what is being tested and why.
"""

from open_sport_taxonomy import GarminFitCode, Sport
from open_sport_taxonomy.platforms import (
    apple_healthkit,
    garmin_fit,
    garmin_training_api,
    strava,
    wahoo,
)

# --------------------------------------------------------------------------
# Garmin FIT — struct target, uses target_coarsening for forward-compat.
# --------------------------------------------------------------------------


class TestGarminFitRoundTrip:
    """Six representative cases exercising every encode/decode code path."""

    def test_preferred_round_trip(self):
        # Case 1: canonical entry round-trips both directions.
        sport = Sport("cycling.road")
        assert garmin_fit.encode(sport) == GarminFitCode(2, 7)
        assert garmin_fit.decode(2, 7) == sport

    def test_synonym_decode_to_canonical(self):
        # Case 2: (2, 5) spin and (4, 6) fitness_equipment/indoor_cycling
        # both decode to cycling+stationary; only (2, 6) is preferred.
        canonical = Sport("cycling+stationary")
        assert garmin_fit.decode(2, 5) == canonical
        assert garmin_fit.decode(4, 6) == canonical

    def test_null_sport_decodes_to_fallback(self):
        # Case 3: (4, 15) fitness_equipment/elliptical has sport: null.
        assert garmin_fit.decode(4, 15) == Sport("generic")

    def test_parent_walk_encode(self):
        # Case 4: cycling.cyclocross has no preferred entry with modifiers;
        # cycling.cyclocross+race walks up to cycling.cyclocross.
        # NOTE: cycling.cyclocross IS in the FIT mapping, so this exercises
        # the modifier-drop step, not the OST-tree walk. Use a deeper
        # combo to hit the tree walk.
        assert garmin_fit.encode(Sport("cycling.gravel+race")) == GarminFitCode(2, 46)

    def test_modifier_drop_encode(self):
        # Case 5: cycling+commute has no preferred entry; drops +commute,
        # then encodes plain cycling.
        assert garmin_fit.encode(Sport("cycling+commute")) == GarminFitCode(2, 0)

    def test_coarsening_decode_unknown_sub_sport(self):
        # Case 6: (2, 99) is not in entries (would need a newer FIT SDK);
        # target_coarsening rewrites to (2, 0) which decodes to cycling.
        assert garmin_fit.decode(2, 99) == Sport("cycling")


# --------------------------------------------------------------------------
# Strava — flat string targets, no target_coarsening.
# --------------------------------------------------------------------------


class TestStravaRoundTrip:
    def test_preferred_round_trip(self):
        sport = Sport("cycling.road+virtual")
        assert strava.encode(sport) == "VirtualRide"
        assert strava.decode("VirtualRide") == sport

    def test_synonym_decode_to_canonical(self):
        # Strava doesn't have multiple targets for the same OST in the
        # current mapping. Verify the related case: a decode that walks
        # the parent in a more interesting way than the FIT case.
        # 'Ride' is canonical for plain cycling; 'GravelRide' is canonical
        # for cycling.gravel. Both are preferred (no synonyms in Strava).
        assert strava.decode("Ride") == Sport("cycling")
        assert strava.decode("GravelRide") == Sport("cycling.gravel")

    def test_null_sport_decodes_to_fallback(self):
        # Many Strava sport types (e.g. AlpineSki, Yoga) have no OST
        # equivalent today and decode to the fallback.
        assert strava.decode("AlpineSki") == Sport("generic")

    def test_parent_walk_encode(self):
        # cycling.cyclocross has no Strava entry; walks up to cycling -> Ride.
        assert strava.encode(Sport("cycling.cyclocross")) == "Ride"

    def test_modifier_drop_encode(self):
        # cycling.road+stationary has no Strava entry (Strava has no
        # indoor-but-not-virtual cycling type); drops +stationary -> Ride.
        assert strava.encode(Sport("cycling.road+stationary")) == "Ride"

    def test_unmapped_decode_falls_to_fallback(self):
        # Case 6 substitute: target absent from entries (would only happen
        # if the SDK adds new types after our snapshot) -> fallback.decode.
        # We can simulate by asking for a truly unknown string.
        assert strava.decode("NotARealStravaSportType") == Sport("generic")


# --------------------------------------------------------------------------
# Apple HealthKit — flat int targets, no target_coarsening.
# --------------------------------------------------------------------------


class TestAppleHealthkitRoundTrip:
    def test_preferred_round_trip(self):
        sport = Sport("cycling")
        assert apple_healthkit.encode(sport) == 13
        assert apple_healthkit.decode(13) == sport

    def test_synonym_decode_to_canonical(self):
        # HealthKit has no synonyms in the current mapping; verify
        # straightforward decode of two different preferred entries.
        assert apple_healthkit.decode(37) == Sport("running")
        assert apple_healthkit.decode(46) == Sport("swimming")

    def test_null_sport_decodes_to_fallback(self):
        # raw_value=2 (archery) and many others are sport: null.
        assert apple_healthkit.decode(2) == Sport("generic")

    def test_parent_walk_encode(self):
        # cycling.road has no HealthKit entry (HealthKit has only generic
        # cycling); walks up to cycling.
        assert apple_healthkit.encode(Sport("cycling.road")) == 13

    def test_modifier_drop_encode(self):
        # cycling+stationary has no HealthKit entry (HealthKit uses an
        # isIndoor flag at the workout level, not a separate type);
        # drops +stationary -> 13.
        assert apple_healthkit.encode(Sport("cycling+stationary")) == 13

    def test_unmapped_decode_falls_to_fallback(self):
        # A raw_value not in the bundled targets.yaml -> fallback.decode.
        assert apple_healthkit.decode(99999) == Sport("generic")


# --------------------------------------------------------------------------
# Garmin Training API — flat string targets, very small enum (9 types).
# --------------------------------------------------------------------------


class TestGarminTrainingApiRoundTrip:
    def test_preferred_round_trip(self):
        sport = Sport("cycling")
        assert garmin_training_api.encode(sport) == "CYCLING"
        assert garmin_training_api.decode("CYCLING") == sport

    def test_synonym_decode_to_canonical(self):
        # No synonyms in this small mapping; verify two distinct
        # preferred entries decode correctly.
        assert garmin_training_api.decode("RUNNING") == Sport("running")
        assert garmin_training_api.decode("LAP_SWIMMING") == Sport("swimming")

    def test_null_sport_decodes_to_fallback(self):
        # STRENGTH_TRAINING / CARDIO_TRAINING / YOGA etc. are sport: null
        # because OST does not model these.
        assert garmin_training_api.decode("YOGA") == Sport("generic")

    def test_parent_walk_encode(self):
        # cycling.gravel walks up to cycling -> CYCLING.
        assert garmin_training_api.encode(Sport("cycling.gravel")) == "CYCLING"

    def test_modifier_drop_encode(self):
        # cycling+stationary has no Training API entry today; drops
        # +stationary -> CYCLING.
        assert garmin_training_api.encode(Sport("cycling+stationary")) == "CYCLING"

    def test_unmapped_decode_falls_to_fallback(self):
        assert garmin_training_api.decode("NOT_A_REAL_TYPE") == Sport("generic")


# --------------------------------------------------------------------------
# Wahoo — flat int targets (workout_type_id), no target_coarsening.
# --------------------------------------------------------------------------


class TestWahooRoundTrip:
    def test_preferred_round_trip(self):
        sport = Sport("cycling.road")
        assert wahoo.encode(sport) == 15
        assert wahoo.decode(15) == sport

    def test_synonym_decode_to_canonical(self):
        # BIKING_INDOOR_CYCLING_CLASS (49) and BIKING_INDOOR_TRAINER (61)
        # both decode to cycling+stationary; only BIKING_INDOOR (12) is preferred.
        canonical = Sport("cycling+stationary")
        assert wahoo.decode(49) == canonical
        assert wahoo.decode(61) == canonical

    def test_null_sport_decodes_to_fallback(self):
        # SKIING (28) is sport: null — OST has no alpine skiing code.
        assert wahoo.decode(28) == Sport("generic")

    def test_parent_walk_encode(self):
        # cycling.gravel has no Wahoo type; walks up the OST tree to cycling -> 0.
        assert wahoo.encode(Sport("cycling.gravel")) == 0

    def test_modifier_drop_encode(self):
        # cycling.road+commute has no entry; drops +commute -> cycling.road (15).
        assert wahoo.encode(Sport("cycling.road+commute")) == 15

    def test_unmapped_decode_falls_to_fallback(self):
        # A workout_type_id not in the bundled targets.yaml -> fallback.decode.
        assert wahoo.decode(99999) == Sport("generic")
