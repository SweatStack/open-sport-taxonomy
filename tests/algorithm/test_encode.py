"""Encode-side algorithm tests.

One test per distinct code path the encode algorithm exercises. The
exhaustive guarantee on preferred entries is provided by
``scripts/generate.py`` validation rules 10–11; this file documents the
algorithm's spec via worked examples.

Covers:
  - Exact-match in the preferred index (canonical happy path).
  - Cross-sport-encoding via the preferred index (FIT's rowing+stationary
    → fitness_equipment is a non-obvious case worth pinning).
  - The v3 modifiers-dominate-discipline-depth ordering on parent walk.
  - OST hierarchy walk with discipline-only candidates.
  - Modifier-drop fallback when no modifier-bearing entry matches.
  - The encode fallback when nothing matches.
  - The type contract: encode requires a Sport, not a string.
"""

from __future__ import annotations

import pytest

from open_sport_taxonomy import GarminFitCode, Sport
from open_sport_taxonomy.platforms import garmin_fit, strava


class TestExactMatch:
    def test_exact_preferred_entry(self):
        # Canonical: an exact (code, modifiers) match in the preferred index.
        assert garmin_fit.encode(Sport("cycling+stationary")) == GarminFitCode(2, 6)

    def test_cross_sport_encoding(self):
        # rowing+stationary maps to (4, 14) — sport=4 is fitness_equipment,
        # not rowing (15). The OST sport string and the platform's sport id
        # differ. Worth pinning because it exercises the inversion through
        # preferred_index without any OST-tree assistance.
        assert garmin_fit.encode(Sport("rowing+stationary")) == GarminFitCode(4, 14)


class TestModifiersDominateDisciplineDepth:
    """The v3 ordering: when both axes can be coarsened, drop discipline first."""

    def test_road_stationary_keeps_stationary(self):
        # cycling.road+stationary has no exact match.
        # v1 would have kept .road and dropped +stationary → (2, 7).
        # v3 keeps +stationary and drops .road → (2, 6) indoor_cycling.
        assert garmin_fit.encode(Sport("cycling.road+stationary")) == GarminFitCode(2, 6)

    def test_extra_modifier_falls_through_to_discipline(self):
        # cycling.road+race+stationary: modifier set is {race, stationary},
        # matching no preferred row exactly. The algorithm matches whole
        # modifier sets (subset matching is intentionally out of scope).
        # After exhausting the with-modifiers walk, the empty-modifier walk
        # yields (cycling.road, ∅) → (2, 7). +stationary is lost, .road kept.
        assert garmin_fit.encode(Sport("cycling.road+race+stationary")) == GarminFitCode(2, 7)


class TestOSTHierarchyWalk:
    def test_exact_hit_short_circuits_walk(self):
        # cycling.cyclocross is itself preferred; the walk hits step 1.
        assert garmin_fit.encode(Sport("cycling.cyclocross")) == GarminFitCode(2, 11)

    def test_modifier_walk_finds_ancestor_with_modifiers(self):
        # cycling.gravel+race: no preferred (cycling.gravel, {race}).
        # Walk preserves modifiers up the OST tree: tries (cycling, {race}),
        # no hit. Then drops modifiers: (cycling.gravel, ∅) hits → (2, 46).
        assert garmin_fit.encode(Sport("cycling.gravel+race")) == GarminFitCode(2, 46)


class TestModifierFallback:
    def test_unknown_modifier_combo_drops_modifier(self):
        # cycling+leisure has no FIT target; drop the modifier → cycling.
        assert garmin_fit.encode(Sport("cycling+leisure")) == GarminFitCode(2, 0)


class TestEncodeFallback:
    def test_unmappable_sport_returns_fallback_encode(self):
        # Non-standard sport via Sport.parse — no preferred entry at any
        # walk step, falls through to fallback.encode.
        assert garmin_fit.encode(Sport.parse("paragliding")) == GarminFitCode(0, 0)


class TestStravaModifierWins:
    def test_assisted_dominates_discipline(self):
        # +assisted (modifier) dominates .gravel (discipline) in the walk:
        # (cycling.gravel, {assisted}) misses, then (cycling, {assisted}) hits
        # EBikeRide — rather than dropping +assisted to reach GravelRide.
        # Smoke test that modifier-dominance holds against a non-FIT platform.
        assert strava.encode(Sport("cycling.gravel+assisted")) == "EBikeRide"


class TestTypeContract:
    """encode requires a Sport — strings and other types are rejected
    with a clear TypeError pointing the caller at Sport(...) or Sport.parse(...).

    Application code should construct Sport instances at the boundary so typos
    fail at construction (Sport raises on unknown codes/modifiers). Accepting
    strings here would silently absorb typos via the hierarchy walk — see
    the design rationale captured in CONTRIBUTING.md and plan 017.
    """

    def test_string_rejected_with_helpful_message(self):
        with pytest.raises(TypeError, match=r"Sport\(\.\.\.\)"):
            garmin_fit.encode("cycling.road")

    def test_none_rejected(self):
        with pytest.raises(TypeError, match=r"encode\(\) requires a Sport"):
            garmin_fit.encode(None)

    def test_dict_rejected(self):
        with pytest.raises(TypeError, match=r"encode\(\) requires a Sport"):
            garmin_fit.encode({"code": "cycling"})
