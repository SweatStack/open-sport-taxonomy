"""Tests for Sport.resolve() — the two-phase, drop-only resolution.

resolve() maps any well-formed sport to the nearest *standard* (catalogue)
sport: (1) climb the code tree to the nearest ancestor whose bare form is
standard (else `generic`); (2) keep the largest subset of the original
modifiers that forms a catalogue entry. It only ever drops — it never adds a
modifier or specificity. See docs/taxonomy.md and plans/027 §7.1.
"""

import pytest

from open_sport_taxonomy import Sport


class TestStandardReturnsSelf:
    def test_bare_code(self):
        s = Sport("cycling.road")
        assert s.resolve() is s

    def test_standard_combination(self):
        s = Sport("cycling+stationary")
        assert s.resolve() is s


class TestClimbCodeTree:
    """Phase 1: climb to the nearest ancestor whose bare form is standard."""

    def test_unknown_child_of_known_code(self):
        assert Sport.parse("cycling.road.criterium").resolve() == Sport("cycling.road")

    def test_unknown_child_of_known_parent(self):
        assert Sport.parse("running.fell").resolve() == Sport("running")

    def test_unknown_top_level_resolves_to_generic(self):
        assert Sport.parse("parkour").resolve() == Sport("generic")

    def test_unknown_nested_under_unknown_top_level(self):
        assert Sport.parse("parkour.freerunning").resolve() == Sport("generic")


class TestDropModifiers:
    """Phase 2: keep the largest modifier subset that forms a catalogue entry."""

    def test_modifier_kept_when_combination_is_standard(self):
        # running+race is standard, so race survives once the unknown is gone.
        assert Sport.parse("running+race+relay").resolve() == Sport("running+race")

    def test_modifier_dropped_when_combination_not_standard(self):
        # cycling.road+race is not catalogued → race is dropped to bare cycling.road.
        assert Sport.parse("cycling.road+race").resolve() == Sport("cycling.road")

    def test_largest_standard_subset_kept(self):
        # cycling+stationary is standard; cycling+leisure is not, so leisure goes.
        assert Sport.parse("cycling+leisure+stationary").resolve() == Sport("cycling+stationary")

    def test_unknown_modifier_dropped_known_combination_kept(self):
        assert Sport.parse("cycling+stationary+relay").resolve() == Sport("cycling+stationary")

    def test_all_modifiers_dropped_when_no_combination(self):
        assert Sport.parse("cycling.road+race+relay").resolve() == Sport("cycling.road")


class TestNeverAddsModifiers:
    """resolve() never invents a modifier to manufacture a richer match."""

    def test_bare_code_does_not_gain_modifiers(self):
        # running has standard combinations (running+race, …) but plain running
        # must resolve to bare running, never running+race.
        assert Sport.parse("running.fell").resolve() == Sport("running")

    def test_unknown_code_resolves_up_not_to_a_sibling_combination(self):
        # xc_skiing+roller is standard, but xc_skiing.unknown climbs to bare
        # xc_skiing — it does not borrow the +roller modifier it never had.
        assert Sport.parse("xc_skiing.unknown").resolve() == Sport("xc_skiing")


class TestResolveIsStandard:
    def test_resolved_is_always_standard(self):
        assert Sport.parse("cycling.road.criterium+race+rainy").resolve().is_standard is True

    def test_resolved_all_unknown(self):
        assert Sport.parse("parkour.freerunning+foo").resolve().is_standard is True


class TestConflictingModifiersDropped:
    """Group conflicts never raise in resolve(); the subset search just skips them."""

    def test_conflicting_known_modifiers_resolve_without_error(self):
        # commute and race are both 'purpose'; cycling.road has no combination, so
        # both are dropped — resolve is total and never raises on a conflict.
        assert Sport.parse("cycling.road+commute+race").resolve() == Sport("cycling.road")

    def test_conflict_resolved_to_the_standard_subset(self):
        # Of {leisure, race} only running+race is catalogued, so race wins.
        assert Sport.parse("running+leisure+race").resolve() == Sport("running+race")


class TestStructuralErrors:
    def test_empty_string(self):
        with pytest.raises(ValueError):
            Sport.parse("").resolve()

    def test_trailing_plus(self):
        with pytest.raises(ValueError, match="Invalid encoded string"):
            Sport.parse("cycling.road+").resolve()

    def test_leading_plus(self):
        with pytest.raises(ValueError, match="Invalid encoded string"):
            Sport.parse("+cycling.road").resolve()

    def test_double_plus(self):
        with pytest.raises(ValueError, match="Invalid encoded string"):
            Sport.parse("cycling.road++virtual").resolve()

    def test_non_string(self):
        with pytest.raises(TypeError):
            Sport.parse(123).resolve()  # type: ignore[arg-type]
