from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any, NamedTuple

from open_sport_taxonomy._modifier import Modifier
from open_sport_taxonomy._sport import Sport

# ---------------------------------------------------------------------------
# Garmin FIT — dual-form value carrying both name and id.
# ---------------------------------------------------------------------------


class _GarminFitCodeBase(NamedTuple):
    sport: int
    sub_sport: int


class GarminFitCode(_GarminFitCodeBase):
    """A Garmin FIT (sport, sub_sport) pair.

    Constructible from ints, names, or a mix:

        GarminFitCode(2, 7)
        GarminFitCode("cycling", "road")
        GarminFitCode(sport=2, sub_sport="road")

    Storage is always ``(sport, sub_sport)`` (integer ids) so equality,
    hashing, and unpacking are well-defined across construction forms.
    Field names match the YAML ``target: {sport, sub_sport}`` shape used
    in mapping files and ``target_coarsening`` rules.

    Names are validated at construction against the FIT enum tables
    shipped in ``reference/garmin-fit-sdk/``. Unknown names raise
    ``ValueError``. Unknown ints are accepted as-is, for forward
    compatibility with future SDK enum additions.
    """

    __slots__ = ()

    def __new__(
        cls,
        sport: int | str,
        sub_sport: int | str = 0,
    ) -> GarminFitCode:
        sport_id = _resolve_fit_value(sport, "sport")
        sub_sport_id = _resolve_fit_value(sub_sport, "sub_sport")
        return _GarminFitCodeBase.__new__(cls, sport_id, sub_sport_id)

    @property
    def sport_name(self) -> str | None:
        """The FIT sport enum name, or ``None`` if this id is not in the SDK tables."""
        from open_sport_taxonomy._platforms import FIT_SPORT_NAMES

        return FIT_SPORT_NAMES.get(self.sport)

    @property
    def sub_sport_name(self) -> str | None:
        """The FIT sub_sport enum name, or ``None`` if this id is not in the SDK tables."""
        from open_sport_taxonomy._platforms import FIT_SUB_SPORT_NAMES

        return FIT_SUB_SPORT_NAMES.get(self.sub_sport)

    def __repr__(self) -> str:
        return f"GarminFitCode(sport={self.sport}, sub_sport={self.sub_sport})"


def _resolve_fit_value(value: int | str, field: str) -> int:
    # bool is a subclass of int — exclude it explicitly to avoid surprises.
    if isinstance(value, bool):
        raise TypeError(f"FIT {field} must be int or str, got bool")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        # Lazy import: avoids a circular import during _platforms module init.
        from open_sport_taxonomy._platforms import FIT_SPORT_IDS, FIT_SUB_SPORT_IDS

        table = FIT_SPORT_IDS if field == "sport" else FIT_SUB_SPORT_IDS
        if value not in table:
            raise ValueError(f"Unknown FIT {field} name: {value!r}")
        return table[value]
    raise TypeError(f"FIT {field} must be int or str, got {type(value).__name__}")


# ---------------------------------------------------------------------------
# Platform — bidirectional translator between OST sports and platform codes.
# ---------------------------------------------------------------------------
#
# See docs/translation.md for the mapping-format specification and the
# normative algorithm definitions. The runtime here implements them
# directly from data assembled at generation time by scripts/generate.py.


SportKey = tuple[str, frozenset[str]]
CoarseningRule = Mapping[str, Any]


class Platform:
    """Bidirectional translator between OST sports and a platform's codes.

    Built from two data views over the same mapping table:

    - ``entries_by_target`` maps every legal platform target to a
      ``(Sport | None, preferred)`` tuple. Used by ``decode``.
    - ``preferred_index`` maps every preferred entry's ``(sport_code,
      modifiers)`` pair to its target. Used by ``encode``.

    Both views are derived from ``mappings/<platform>.yaml`` by
    ``scripts/generate.py``; the runtime does not parse YAML.
    """

    def __init__(
        self,
        *,
        entries_by_target: Mapping[Any, tuple[Sport | None, bool]],
        preferred_index: Mapping[SportKey, Any],
        fallback_encode: Any,
        fallback_decode: Sport,
        target_coarsening: tuple[CoarseningRule, ...] = (),
    ) -> None:
        self._entries_by_target = entries_by_target
        self._preferred_index = preferred_index
        self._fallback_encode = fallback_encode
        self._fallback_decode = fallback_decode
        self._target_coarsening = target_coarsening

    # ------------------------------------------------------------------
    # Forward: Sport → target
    # ------------------------------------------------------------------

    def encode(self, sport: Sport) -> Any:
        """Encode an OST sport to the platform's native target.

        Walks the OST hierarchy with **modifiers dominating discipline
        depth**: tries the exact ``(code, modifiers)`` pair first, then
        each ancestor with modifiers preserved, then drops modifiers
        and walks again. Returns ``fallback_encode`` if no candidate
        matches a preferred entry. See docs/translation.md §"Encode".
        """
        if not isinstance(sport, Sport):
            raise TypeError(
                f"encode() requires a Sport, got {type(sport).__name__}. "
                f"Construct one with Sport(...) for known sports or "
                f"Sport.parse(...) for external input."
            )
        for candidate in _ost_hierarchy_walk(sport):
            target = self._preferred_index.get(candidate)
            if target is not None:
                return target
        return self._fallback_encode

    # ------------------------------------------------------------------
    # Reverse: target → Sport
    # ------------------------------------------------------------------

    def decode(self, target: Any) -> Sport:
        """Decode a platform target into the corresponding OST sport.

        A direct lookup in ``entries_by_target``. Targets absent from
        the table (a value newer than the bundled reference snapshot)
        are routed through ``target_coarsening`` for forward-compat.
        ``sport: null`` entries short-circuit to ``fallback_decode``.
        See docs/translation.md §"Decode".
        """
        entry = self._entries_by_target.get(target)
        if entry is not None:
            sport, _preferred = entry
            return sport if sport is not None else self._fallback_decode

        for rule in self._target_coarsening:
            candidate = _apply_coarsening_rule(rule, target)
            if candidate == target:
                continue  # rule was a no-op for this input
            entry = self._entries_by_target.get(candidate)
            if entry is not None:
                sport, _preferred = entry
                return sport if sport is not None else self._fallback_decode

        return self._fallback_decode


# ---------------------------------------------------------------------------
# Algorithm helpers — pure functions, data-driven per docs/translation.md.
# ---------------------------------------------------------------------------


def _ost_hierarchy_walk(sport: Sport) -> Iterator[SportKey]:
    """Enumerate encode candidates per the modifiers-dominate ordering.

    The walk yields:

    1. ``(sport.code, sport.modifiers)`` — exact.
    2. Each strict ancestor of ``sport.code`` with the original modifiers.
    3. If modifiers are non-empty, repeat steps 1–2 with the empty
       modifier set.
    """
    mods = frozenset(m.value if isinstance(m, Modifier) else m for m in sport.modifiers)

    # Step 1–2: exact and ancestors-with-modifiers.
    yield (sport.code, mods)
    ancestor = sport.parent
    while ancestor is not None:
        yield (ancestor.code, mods)
        ancestor = ancestor.parent

    # Step 3: drop modifiers and walk again (only if modifiers existed).
    if mods:
        yield (sport.code, frozenset())
        ancestor = sport.parent
        while ancestor is not None:
            yield (ancestor.code, frozenset())
            ancestor = ancestor.parent


def _apply_coarsening_rule(rule: CoarseningRule, target: Any) -> Any:
    """Apply one coarsening rule to a target, returning the new target.

    Only the `reset` rule kind is defined. A rule whose
    output equals the input is a no-op for that input; the caller
    skips no-ops.
    """
    if "reset" in rule:
        values = rule["reset"]
        # NamedTuple targets support _replace; other shapes don't carry
        # named fields and thus can't be coarsened by `reset`.
        if hasattr(target, "_replace"):
            return target._replace(**values)
        raise TypeError(
            f"`reset` coarsening rule requires a NamedTuple target, got {type(target).__name__}"
        )
    raise ValueError(f"Unknown coarsening rule kind: {rule!r}")
