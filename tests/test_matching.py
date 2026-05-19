import pytest

from open_sport_taxonomy import Modifier, Sport


class TestIsSubsportOf:
    def test_identity(self):
        sport = Sport("cycling.road")
        assert sport.is_subsport_of(sport)

    def test_identity_with_modifiers(self):
        sport = Sport("cycling.road+race")
        assert sport.is_subsport_of(sport)

    def test_child_of_parent(self):
        assert Sport("cycling.road").is_subsport_of(Sport("cycling"))

    def test_grandchild_of_grandparent(self):
        sport = Sport.parse("cycling.road.criterium")
        assert sport.is_subsport_of(Sport("cycling"))

    def test_child_with_matching_modifiers(self):
        assert Sport("cycling.road+stationary").is_subsport_of(Sport("cycling+stationary"))

    def test_extra_modifiers_on_self(self):
        assert Sport("cycling.road+stationary+race").is_subsport_of(Sport("cycling+stationary"))

    def test_missing_required_modifier(self):
        assert not Sport("cycling.road").is_subsport_of(Sport("cycling+stationary"))

    def test_wrong_hierarchy(self):
        assert not Sport("running+stationary").is_subsport_of(Sport("cycling+stationary"))

    def test_parent_is_not_subsport_of_child(self):
        assert not Sport("cycling").is_subsport_of(Sport("cycling.road"))

    def test_unrelated_codes(self):
        assert not Sport("running").is_subsport_of(Sport("cycling"))

    def test_non_standard_sports(self):
        a = Sport.parse("cycling.road.criterium+race")
        b = Sport.parse("cycling+race")
        assert a.is_subsport_of(b)

    def test_non_standard_with_unknown_modifiers(self):
        a = Sport.parse("cycling.road+race+rainy")
        b = Sport.parse("cycling+race")
        assert a.is_subsport_of(b)

    def test_unknown_modifier_required(self):
        a = Sport.parse("cycling.road+race")
        b = Sport.parse("cycling+race+rainy")
        assert not a.is_subsport_of(b)


class TestParentPreservesModifiers:
    def test_parent_with_modifiers(self):
        sport = Sport("cycling.road+stationary")
        parent = sport.parent
        assert parent.code == "cycling"
        assert Modifier.STATIONARY in parent.modifiers

    def test_parent_with_multiple_modifiers(self):
        sport = Sport("cycling.road+race+virtual")
        parent = sport.parent
        assert parent.code == "cycling"
        assert Modifier.RACE in parent.modifiers
        assert Modifier.VIRTUAL in parent.modifiers

    def test_parent_without_modifiers(self):
        sport = Sport("cycling.road")
        parent = sport.parent
        assert parent == Sport("cycling")
        assert parent.modifiers == frozenset()

    def test_parent_of_root_is_none(self):
        assert Sport("cycling+race").parent is None

    def test_bare_tree_navigation(self):
        sport = Sport("cycling.road+stationary")
        bare_parent = Sport(sport.code).parent
        assert bare_parent == Sport("cycling")
        assert bare_parent.modifiers == frozenset()

    def test_non_standard_parent_preserves_modifiers(self):
        sport = Sport.parse("cycling.road.criterium+race")
        parent = sport.parent
        assert parent.code == "cycling.road"
        assert Modifier.RACE in parent.modifiers

    def test_parent_chain_preserves_modifiers(self):
        sport = Sport.parse("cycling.road.criterium+race")
        parent = sport.parent       # cycling.road+race
        grandparent = parent.parent  # cycling+race
        assert grandparent.code == "cycling"
        assert Modifier.RACE in grandparent.modifiers
