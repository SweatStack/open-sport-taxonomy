from __future__ import annotations

from typing import Any, NamedTuple

from open_sports_schema._sport import Sport


class GarminFitCode(NamedTuple):
    sport: int
    sub_sport: int


class Platform:
    def __init__(
        self,
        mappings: dict[tuple[str, frozenset[str]], Any],
        fallback: Any,
    ) -> None:
        self._mappings = mappings
        self._fallback = fallback

    def translate(self, sport: Sport) -> Any:
        mod_codes = frozenset(m.value for m in sport.modifiers)

        # 1. Exact match (code + modifiers).
        key = (sport.code, mod_codes)
        if key in self._mappings:
            return self._mappings[key]

        # 2. Drop modifiers.
        key = (sport.code, frozenset())
        if key in self._mappings:
            return self._mappings[key]

        # 3. Walk up to parent.
        parent = sport.parent
        while parent is not None:
            key = (parent.code, frozenset())
            if key in self._mappings:
                return self._mappings[key]
            parent = parent.parent

        # 4. Fallback.
        return self._fallback
