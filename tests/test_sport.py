import pytest

from open_sports_schema import Modifier, Sport
from open_sports_schema._sport import _LABELS as TAXONOMY


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

    def test_from_encoded_string_single_modifier(self):
        sport = Sport("cycling.road+race")
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

    def test_modifier_conflict_explicit(self):
        with pytest.raises(ValueError, match="conflict"):
            Sport("cycling.road", modifiers={Modifier.RACE, Modifier.COMMUTE})

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

    def test_repr(self):
        assert repr(Sport("cycling.road")) == "Sport('cycling.road')"
        assert (
            repr(Sport("cycling.road+race"))
            == "Sport('cycling.road+race')"
        )

    def test_roundtrip(self):
        for code in TAXONOMY:
            sport = Sport(code)
            assert Sport(str(sport)) == sport

    def test_roundtrip_with_modifiers(self):
        for code in TAXONOMY:
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

    def test_equal_to_class_constant(self):
        assert Sport("cycling.road") == Sport.CYCLING_ROAD

    def test_hash_equal(self):
        a = Sport("cycling.road+race")
        b = Sport("cycling.road", modifiers={Modifier.RACE})
        assert hash(a) == hash(b)

    def test_usable_as_dict_key(self):
        d = {Sport.CYCLING_ROAD: "road"}
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
        assert Sport.CYCLING_ROAD.label == "road cycling"

    def test_parent(self):
        assert Sport.CYCLING_ROAD.parent == Sport.CYCLING

    def test_parent_top_level_is_none(self):
        assert Sport.CYCLING.parent is None

    def test_disciplines(self):
        disciplines = Sport.CYCLING.disciplines
        assert Sport.CYCLING_ROAD in disciplines
        assert Sport.CYCLING_GRAVEL in disciplines
        assert Sport.CYCLING_TRACK in disciplines

    def test_disciplines_leaf_is_empty(self):
        assert Sport.CYCLING_ROAD.disciplines == ()

    def test_parent_has_no_modifiers(self):
        sport = Sport("cycling.road+race")
        assert sport.parent.modifiers == frozenset()

    def test_disciplines_have_no_modifiers(self):
        for d in Sport.CYCLING.disciplines:
            assert d.modifiers == frozenset()


class TestAll:
    def test_all_returns_all_taxonomy_entries(self):
        all_sports = Sport.all()
        assert len(all_sports) == len(TAXONOMY)

    def test_all_entries_have_no_modifiers(self):
        for sport in Sport.all():
            assert sport.modifiers == frozenset()

    def test_all_codes_match_taxonomy(self):
        codes = {s.code for s in Sport.all()}
        assert codes == set(TAXONOMY.keys())


class TestClassConstants:
    def test_all_taxonomy_entries_have_constants(self):
        for code in TAXONOMY:
            name = code.replace(".", "_").upper()
            constant = getattr(Sport, name)
            assert constant.code == code
            assert constant.modifiers == frozenset()

    def test_constant_equals_constructed(self):
        assert Sport.CYCLING_ROAD == Sport("cycling.road")
        assert Sport.RUNNING_TRAIL == Sport("running.trail")
        assert Sport.XC_SKIING_ROLLER_CLASSIC == Sport("xc_skiing.roller.classic")
