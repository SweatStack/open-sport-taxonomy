"""Modifier enum domain-logic tests.

Tests cover this library's data and API:
  - Per-modifier properties (code, label, group) carry the right values.
  - The :meth:`Modifier.in_group` classmethod returns the correct members.
  - Schema-vs-code completeness: every modifier defined in schema.yaml
    surfaces with the expected (code, label, group) triple.

Stdlib :class:`enum.Enum` behavior (`Modifier("virtual") is Modifier.VIRTUAL`,
iteration, value lookup) is not retested — those are Python language
guarantees, not this library's contract.
"""

from open_sport_taxonomy import Modifier


class TestProperties:
    def test_code(self):
        assert Modifier.VIRTUAL.code == "virtual"

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
        """Schema-vs-code invariant: every documented modifier exists."""
        expected = {
            ("assisted", "assisted", None),
            ("commute", "commute", "purpose"),
            ("group", "group", "company"),
            ("leisure", "leisure", "purpose"),
            ("race", "race", "purpose"),
            ("roller", "roller", None),
            ("solo", "solo", "company"),
            ("stationary", "stationary", None),
            ("test", "test", "purpose"),
            ("training", "training", "purpose"),
            ("virtual", "virtual", None),
        }
        actual = {(m.code, m.label, m.group) for m in Modifier}
        assert actual == expected
