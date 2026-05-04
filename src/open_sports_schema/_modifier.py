# Auto-generated from schema.yaml — do not edit.
# Run: uv run scripts/generate.py

from __future__ import annotations

from enum import Enum


class Modifier(str, Enum):
    """A modifier that qualifies a sport (e.g. race, virtual, assisted)."""

    ASSISTED = "assisted"
    COMMUTE = "commute"
    RACE = "race"
    STATIONARY = "stationary"
    TRAINING = "training"
    VIRTUAL = "virtual"

    @property
    def code(self) -> str:
        return self.value

    @property
    def label(self) -> str:
        return _LABELS[self.value]

    @property
    def group(self) -> str | None:
        return _GROUPS.get(self.value)

    @classmethod
    def in_group(cls, group: str) -> list[Modifier]:
        return [m for m in cls if m.group == group]


_LABELS: dict[str, str] = {
    "assisted": "assisted",
    "commute": "commute",
    "race": "race",
    "stationary": "stationary",
    "training": "training",
    "virtual": "virtual",
}

_GROUPS: dict[str, str] = {
    "commute": "purpose",
    "race": "purpose",
    "training": "purpose",
}


def validate_modifiers(modifiers: frozenset[Modifier]) -> None:
    """Raise ValueError if modifiers from the same group are combined."""
    groups_seen: dict[str, Modifier] = {}
    for mod in modifiers:
        g = mod.group
        if g is not None:
            if g in groups_seen:
                conflict = groups_seen[g]
                raise ValueError(
                    f"Modifiers {conflict.code!r} and {mod.code!r} "
                    f"conflict (same group: {g!r})"
                )
            groups_seen[g] = mod
