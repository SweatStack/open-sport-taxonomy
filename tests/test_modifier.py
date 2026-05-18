import pytest

from open_sport_taxonomy import Modifier


class TestEnumBehavior:
    def test_lookup_by_value(self):
        assert Modifier("virtual") is Modifier.VIRTUAL

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            Modifier("unknown")

    def test_iteration(self):
        members = list(Modifier)
        assert len(members) > 0
        assert Modifier.VIRTUAL in members

    def test_identity(self):
        assert Modifier("race") is Modifier.RACE


class TestProperties:
    def test_code(self):
        assert Modifier.VIRTUAL.code == "virtual"

    def test_code_equals_value(self):
        for m in Modifier:
            assert m.code == m.value

    def test_label(self):
        assert Modifier.VIRTUAL.label == "virtual"

    def test_group_independent(self):
        assert Modifier.VIRTUAL.group is None
        assert Modifier.ASSISTED.group is None
        assert Modifier.STATIONARY.group is None

    def test_group_purpose(self):
        assert Modifier.RACE.group == "purpose"
        assert Modifier.COMMUTE.group == "purpose"
        assert Modifier.TRAINING.group == "purpose"


class TestStringInterop:
    def test_equals_string(self):
        assert Modifier.VIRTUAL == "virtual"

    def test_fstring(self):
        assert f"{Modifier.VIRTUAL}" == "virtual"


class TestInGroup:
    def test_purpose_group(self):
        purpose = Modifier.in_group("purpose")
        assert Modifier.RACE in purpose
        assert Modifier.COMMUTE in purpose
        assert Modifier.TRAINING in purpose
        assert Modifier.TEST in purpose
        assert Modifier.LEISURE in purpose
        assert len(purpose) == 5

    def test_unknown_group(self):
        assert Modifier.in_group("nonexistent") == []

    def test_independent_modifiers_have_no_group(self):
        no_group = [m for m in Modifier if m.group is None]
        assert Modifier.VIRTUAL in no_group
        assert Modifier.ASSISTED in no_group
        assert Modifier.STATIONARY in no_group


class TestCompleteness:
    def test_all_expected_modifiers_present(self):
        expected = {
            ("assisted", "assisted", None),
            ("commute", "commute", "purpose"),
            ("group", "group", "company"),
            ("leisure", "leisure", "purpose"),
            ("race", "race", "purpose"),
            ("solo", "solo", "company"),
            ("stationary", "stationary", None),
            ("test", "test", "purpose"),
            ("training", "training", "purpose"),
            ("virtual", "virtual", None),
        }
        actual = {(m.code, m.label, m.group) for m in Modifier}
        assert actual == expected
