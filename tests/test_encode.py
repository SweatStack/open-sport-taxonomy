"""Encode-side algorithm tests.

Covers:
  - Exact-match in preferred_index.
  - Modifiers-dominate ordering (the v3 behavior change vs v1).
  - OST hierarchy walk for unknown disciplines.
  - Fallback when nothing matches.
"""

from __future__ import annotations

import pytest

from open_sport_taxonomy import GarminFitCode, Sport
from open_sport_taxonomy.platforms import garmin_fit, strava


class TestExactMatch:
    def test_cycling_stationary(self):
        assert garmin_fit.encode(Sport("cycling+stationary")) == GarminFitCode(2, 6)

    def test_running_stationary(self):
        assert garmin_fit.encode(Sport("running+stationary")) == GarminFitCode(1, 1)

    def test_rowing_stationary(self):
        assert garmin_fit.encode(Sport("rowing+stationary")) == GarminFitCode(4, 14)


class TestModifiersDominateDisciplineDepth:
    """The v3 ordering: when both axes can be coarsened, drop discipline first."""

    def test_road_stationary_keeps_stationary(self):
        # cycling.road+stationary has no exact match.
        # v1 would have returned (2, 7) — keep .road, drop +stationary.
        # v3 keeps +stationary, drops .road → (2, 6) indoor_cycling.
        assert garmin_fit.encode(Sport("cycling.road+stationary")) == GarminFitCode(2, 6)

    def test_extra_modifier_falls_through_to_discipline(self):
        # cycling.road+race+stationary: modifier-set is {race, stationary},
        # which matches no preferred row exactly. The algorithm matches the
        # whole modifier set; modifier-subset matching is intentionally out
        # of scope. After exhausting the with-modifiers walk, the empty-
        # modifier walk yields (cycling.road, ∅) which is preferred → (2, 7).
        # The +stationary information is lost, but .road is preserved —
        # the closest available row wins.
        assert garmin_fit.encode(Sport("cycling.road+race+stationary")) == GarminFitCode(2, 7)

    def test_road_stationary_alone_works(self):
        # Single-modifier case: cycling.road+stationary → walks to cycling+stationary.
        assert garmin_fit.encode(Sport("cycling.road+stationary")) == GarminFitCode(2, 6)


class TestOSTHierarchyWalk:
    def test_unknown_discipline_walks_up_to_root(self):
        # cycling.cyclocross has a preferred row; this hits exact.
        assert garmin_fit.encode(Sport("cycling.cyclocross")) == GarminFitCode(2, 11)


class TestModifierFallback:
    def test_unknown_modifier_combo_falls_back_to_plain_sport(self):
        # cycling+commute has no preferred row; drop modifier → cycling.
        assert garmin_fit.encode(Sport("cycling+commute")) == GarminFitCode(2, 0)


class TestEncodeFallback:
    def test_unmappable_sport_returns_fallback_encode(self):
        # parsing a non-standard sport via Sport.parse.
        assert garmin_fit.encode(Sport.parse("paragliding")) == GarminFitCode(0, 0)


class TestStravaModifierWins:
    def test_road_virtual_uses_virtual_ride(self):
        # cycling.road+virtual is a preferred entry on Strava.
        assert strava.encode(Sport("cycling.road+virtual")) == "VirtualRide"


class TestTypeContract:
    """encode requires a Sport instance — strings and other types are rejected
    with a clear TypeError that points the caller at Sport(...) or Sport.parse(...).

    Application code should construct Sport instances at the boundary so typos
    fail at construction (Sport raises on unknown codes/modifiers). Accepting
    strings here would silently absorb typos via the hierarchy walk — see the
    discussion in commit history.
    """

    def test_string_rejected_with_helpful_message(self):
        with pytest.raises(TypeError, match=r"Sport\(\.\.\.\)"):
            garmin_fit.encode("cycling.road")

    def test_none_rejected(self):
        with pytest.raises(TypeError, match="encode\\(\\) requires a Sport"):
            garmin_fit.encode(None)

    def test_dict_rejected(self):
        with pytest.raises(TypeError, match="encode\\(\\) requires a Sport"):
            garmin_fit.encode({"code": "cycling"})
