import pytest

from open_sport_taxonomy import Modifier, Sport
from open_sport_taxonomy._sport import _CODES
from open_sport_taxonomy._sport import _LABELS as TAXONOMY


class TestConstruction:
    def test_from_bare_code(self):
        sport = Sport("cycling.road")
        assert sport.code == "cycling.road"
        assert sport.modifiers == frozenset()

    def test_from_encoded_string(self):
        sport = Sport("cycling.road+race+virtual")
        assert sport.code == "cycling.road"
        assert sport.modifiers == frozenset({Modifier.RACE, Modifier.VIRTUAL})

    def test_from_code_with_explicit_modifiers(self):
        sport = Sport("cycling.road", modifiers={Modifier.RACE})
        assert sport.code == "cycling.road"
        assert sport.modifiers == frozenset({Modifier.RACE})

    def test_unknown_sport_code(self):
        with pytest.raises(ValueError, match="Unknown sport code"):
            Sport("cycling.fake")

    def test_unknown_modifier_in_encoded_string(self):
        with pytest.raises(ValueError):
            Sport("cycling.road+unknown")

    def test_empty_string(self):
        with pytest.raises(ValueError):
            Sport("")

    def test_trailing_plus(self):
        with pytest.raises(ValueError, match="Invalid encoded string"):
            Sport("cycling.road+")

    def test_leading_plus(self):
        with pytest.raises(ValueError, match="Invalid encoded string"):
            Sport("+cycling.road")

    def test_double_plus(self):
        with pytest.raises(ValueError, match="Invalid encoded string"):
            Sport("cycling.road++virtual")

    def test_encoded_string_with_modifiers_kwarg_raises(self):
        with pytest.raises(ValueError, match="Cannot pass both"):
            Sport("cycling.road+virtual", modifiers={Modifier.RACE})

    def test_modifier_conflict(self):
        with pytest.raises(ValueError, match="conflict"):
            Sport("cycling.road+commute+race")

    def test_non_string_raises_type_error(self):
        with pytest.raises(TypeError, match="Expected str"):
            Sport(123)  # type: ignore[arg-type]


class TestStringRepresentation:
    def test_str_bare(self):
        assert str(Sport("cycling.road")) == "cycling.road"

    def test_str_with_modifiers(self):
        assert str(Sport("cycling.road+race+virtual")) == "cycling.road+race+virtual"

    def test_str_modifiers_sorted(self):
        sport = Sport("cycling.road", modifiers={Modifier.VIRTUAL, Modifier.RACE})
        assert str(sport) == "cycling.road+race+virtual"

    def test_repr_standard(self):
        assert repr(Sport("cycling.road")) == "Sport('cycling.road')"
        assert repr(Sport("cycling+stationary")) == "Sport('cycling+stationary')"

    def test_repr_non_standard(self):
        sport = Sport.parse("cycling.road.criterium")
        assert repr(sport) == "Sport.parse('cycling.road.criterium')"

    def test_roundtrip(self):
        for code in TAXONOMY:
            sport = Sport(code)
            assert Sport(str(sport)) == sport

    def test_roundtrip_with_modifiers(self):
        for code in _CODES:
            sport = Sport(code, modifiers={Modifier.RACE, Modifier.VIRTUAL})
            assert Sport(str(sport)) == sport


class TestEquality:
    def test_equal_bare(self):
        assert Sport("cycling.road") == Sport("cycling.road")

    def test_equal_with_modifiers(self):
        a = Sport("cycling.road+race+virtual")
        b = Sport("cycling.road", modifiers={Modifier.VIRTUAL, Modifier.RACE})
        assert a == b

    def test_not_equal_different_code(self):
        assert Sport("cycling.road") != Sport("cycling.gravel")

    def test_not_equal_different_modifiers(self):
        assert Sport("cycling.road") != Sport("cycling.road+race")

    def test_not_equal_to_non_sport(self):
        assert Sport("cycling.road") != "cycling.road"
        assert (Sport("cycling.road") == 42) is False

    def test_hash_equal(self):
        a = Sport("cycling.road+race")
        b = Sport("cycling.road", modifiers={Modifier.RACE})
        assert hash(a) == hash(b)

    def test_usable_as_dict_key(self):
        d = {Sport("cycling.road"): "road"}
        assert d[Sport("cycling.road")] == "road"

    def test_usable_in_set(self):
        s = {Sport("cycling.road"), Sport("cycling.road"), Sport("cycling.gravel")}
        assert len(s) == 2


class TestImmutability:
    def test_cannot_set_code(self):
        sport = Sport("cycling.road")
        with pytest.raises(AttributeError):
            sport.code = "running"  # type: ignore[misc]

    def test_cannot_set_modifiers(self):
        sport = Sport("cycling.road")
        with pytest.raises(AttributeError):
            sport.modifiers = frozenset()  # type: ignore[misc]

    def test_cannot_add_attribute(self):
        sport = Sport("cycling.road")
        with pytest.raises((AttributeError, TypeError)):
            sport.extra = "nope"  # type: ignore[attr-defined]


class TestTaxonomy:
    def test_label(self):
        assert Sport("cycling.road").label == "road cycling"

    def test_parent(self):
        assert Sport("cycling.road").parent == Sport("cycling")

    def test_parent_top_level_is_none(self):
        assert Sport("cycling").parent is None

    def test_disciplines(self):
        disciplines = Sport("cycling").disciplines
        assert Sport("cycling.road") in disciplines
        assert Sport("cycling.gravel") in disciplines
        assert Sport("cycling.track") in disciplines

    def test_disciplines_leaf_is_empty(self):
        assert Sport("cycling.road").disciplines == ()

    def test_parent_preserves_modifiers(self):
        sport = Sport("cycling.road+race")
        assert sport.parent.modifiers == frozenset({Modifier.RACE})

    def test_disciplines_without_modifiers(self):
        for d in Sport("cycling").disciplines:
            assert d.modifiers == frozenset()

    def test_disciplines_preserve_modifiers(self):
        sport = Sport("cycling+commute")
        for d in sport.disciplines:
            assert Modifier.COMMUTE in d.modifiers


class TestAll:
    def test_all_returns_the_catalogue(self):
        """Sport.all() returns one entry per catalogue sport (codes and combinations)."""
        all_sports = Sport.all()
        assert {str(s) for s in all_sports} == set(TAXONOMY.keys())
        assert all(s.is_standard for s in all_sports)


class TestStandardSportType:
    def test_literal_matches_catalogue(self):
        """StandardSport enumerates exactly the catalogue (codes and combinations)."""
        import typing

        from open_sport_taxonomy import StandardSport

        assert set(typing.get_args(StandardSport)) == set(TAXONOMY)

    def test_no_class_constants(self):
        """Per-code class constants were dropped in favour of StandardSport."""
        assert not hasattr(Sport, "CYCLING_ROAD")
