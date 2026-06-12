"""Tests for Sport.label and Sport.uses_known_atoms — the three-level model.

`label` always returns a string: curated for a standard sport, composed from the
parts otherwise. `uses_known_atoms` is the level-2 predicate (code + every
modifier declared), strictly weaker than `is_standard` (level 3). See
docs/taxonomy.md and plans/027.
"""

from open_sport_taxonomy import Sport


class TestCuratedLabels:
    def test_bare_code(self):
        assert Sport("cycling").label == "cycling"

    def test_discipline(self):
        assert Sport("cycling.road").label == "road cycling"

    def test_standard_combination(self):
        assert Sport("cycling+stationary").label == "indoor cycling"

    def test_standard_multi_modifier_combination(self):
        assert Sport("cycling+stationary+virtual").label == "virtual indoor cycling"


class TestComposedLabels:
    def test_known_code_and_modifier(self):
        # Not catalogued → composed from the code's label + the modifier's label.
        assert Sport.parse("cycling.road+race").label == "road cycling (race)"

    def test_known_code_multiple_modifiers_sorted(self):
        assert (
            Sport.parse("cycling.road+stationary+virtual").label
            == "road cycling (stationary, virtual)"
        )

    def test_unknown_code_falls_back_to_token(self):
        assert Sport.parse("climbing.mountain+solo").label == "climbing mountain (solo)"

    def test_unknown_code_underscores_become_spaces(self):
        assert Sport.parse("some_activity.foo+bar").label == "some activity foo (bar)"

    def test_unknown_modifier_falls_back_to_raw_token(self):
        assert Sport.parse("cycling.road+wibble").label == "road cycling (wibble)"

    def test_unknown_code_no_modifiers(self):
        assert Sport.parse("parkour.freerunning").label == "parkour freerunning"


class TestUsesKnownAtoms:
    def test_standard_sport_uses_known_atoms(self):
        assert Sport("cycling+stationary").uses_known_atoms is True

    def test_known_atoms_but_not_catalogued(self):
        sport = Sport.parse("cycling.road+race")
        assert sport.uses_known_atoms is True
        assert sport.is_standard is False

    def test_unknown_code_is_not_known_atoms(self):
        assert Sport.parse("climbing.mountain").uses_known_atoms is False

    def test_unknown_modifier_is_not_known_atoms(self):
        assert Sport.parse("cycling+wibble").uses_known_atoms is False

    def test_group_conflict_is_not_known_atoms(self):
        # race and commute are both 'purpose'; the atoms are known but the
        # combination is group-invalid, so it is not known-atoms.
        assert Sport.parse("cycling+commute+race").uses_known_atoms is False
