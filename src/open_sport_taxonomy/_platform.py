from __future__ import annotations

from typing import Any, Callable, Iterable, NamedTuple

from open_sport_taxonomy._modifier import Modifier
from open_sport_taxonomy._sport import Sport


# ---------------------------------------------------------------------------
# Garmin FIT — dual-form value carrying both name and id.
# ---------------------------------------------------------------------------


class _GarminFitCodeBase(NamedTuple):
    sport_id: int
    sub_sport_id: int


class GarminFitCode(_GarminFitCodeBase):
    """A Garmin FIT (sport, sub_sport) pair.

    Constructible from ints, names, or a mix:

        GarminFitCode(2, 7)
        GarminFitCode("cycling", "road")
        GarminFitCode(sport=2, sub_sport="road")

    Storage is always ``(sport_id, sub_sport_id)`` so equality, hashing,
    and unpacking are well-defined across construction forms.

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
    ) -> "GarminFitCode":
        sport_id = _resolve_fit_value(sport, "sport")
        sub_sport_id = _resolve_fit_value(sub_sport, "sub_sport")
        return _GarminFitCodeBase.__new__(cls, sport_id, sub_sport_id)

    @property
    def sport_name(self) -> str | None:
        """The FIT sport enum name, or ``None`` if this id is not in the SDK tables."""
        from open_sport_taxonomy._platforms import FIT_SPORT_NAMES
        return FIT_SPORT_NAMES.get(self.sport_id)

    @property
    def sub_sport_name(self) -> str | None:
        """The FIT sub_sport enum name, or ``None`` if this id is not in the SDK tables."""
        from open_sport_taxonomy._platforms import FIT_SUB_SPORT_NAMES
        return FIT_SUB_SPORT_NAMES.get(self.sub_sport_id)

    def __repr__(self) -> str:
        return f"GarminFitCode(sport={self.sport_id}, sub_sport={self.sub_sport_id})"


def _resolve_fit_value(value: int | str, field: str) -> int:
    # bool is a subclass of int — exclude it explicitly to avoid surprises.
    if isinstance(value, bool):
        raise TypeError(f"FIT {field} must be int or str, got bool")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        # Lazy import: avoids a circular import during _platforms module init
        # (where GarminFitCode is constructed with int args to define
        # GARMIN_FIT_FALLBACK and the forward mappings).
        from open_sport_taxonomy._platforms import FIT_SPORT_IDS, FIT_SUB_SPORT_IDS
        table = FIT_SPORT_IDS if field == "sport" else FIT_SUB_SPORT_IDS
        if value not in table:
            raise ValueError(f"Unknown FIT {field} name: {value!r}")
        return table[value]
    raise TypeError(
        f"FIT {field} must be int or str, got {type(value).__name__}"
    )


# ---------------------------------------------------------------------------
# Platform — bidirectional translator between OST sports and platform codes.
# ---------------------------------------------------------------------------


class Platform:
    """Bidirectional translator between OST sports and a platform's codes.

    Built from a forward mapping ``(code, modifiers) -> target``. The
    reverse mapping is derived at construction time and the source is
    asserted to be one-to-one on ``target`` — i.e. a true bijection.

    See ``docs/translation.md`` for the algorithm specification.
    """

    def __init__(
        self,
        mappings: dict[tuple[str, frozenset[str]], Any],
        fallback: Any,
        *,
        reducer: Callable[[Any], Iterable[Any]] | None = None,
    ) -> None:
        self._mappings = mappings
        self._fallback = fallback
        self._reducer = reducer

        # Build reverse table and assert bijection. Any duplicate target
        # is a YAML bug that must be fixed at the source; we do not pick
        # a winner silently.
        reverse: dict[Any, tuple[str, frozenset[str]]] = {}
        for (code, mods), target in mappings.items():
            if target in reverse:
                existing_code, existing_mods = reverse[target]
                raise ValueError(
                    f"Mapping is not bijective: target {target!r} appears for "
                    f"both ({existing_code!r}, {set(existing_mods) or '∅'}) and "
                    f"({code!r}, {set(mods) or '∅'}). "
                    f"Every target must map back to exactly one (code, modifiers) pair."
                )
            reverse[target] = (code, mods)
        self._reverse = reverse

    # ------------------------------------------------------------------
    # Forward: Sport → target
    # ------------------------------------------------------------------

    def encode(self, sport: Sport) -> Any:
        """Encode an OST sport to the platform's native code.

        Walks ``sport`` and its ancestors in the OST hierarchy, preferring
        an exact ``(code, modifiers)`` match before falling back to
        ``(code, ∅)``. Modifiers are preserved one ancestor at a time.
        Returns the platform fallback if nothing matches.
        """
        mod_codes = frozenset(
            m.value if hasattr(m, "value") else m for m in sport.modifiers
        )

        # 1. Exact match at the current level.
        key = (sport.code, mod_codes)
        if key in self._mappings:
            return self._mappings[key]

        # 2. Same code, drop modifiers.
        if mod_codes:
            key = (sport.code, frozenset())
            if key in self._mappings:
                return self._mappings[key]

        # 3. Walk up the hierarchy, trying with-modifiers then without
        #    at each level.
        parent = sport.parent
        while parent is not None:
            if mod_codes:
                key = (parent.code, mod_codes)
                if key in self._mappings:
                    return self._mappings[key]
            key = (parent.code, frozenset())
            if key in self._mappings:
                return self._mappings[key]
            parent = parent.parent

        # 4. Fallback.
        return self._fallback

    # ------------------------------------------------------------------
    # Reverse: target → Sport
    # ------------------------------------------------------------------

    def decode(self, target: Any) -> Sport:
        """Decode a platform code into the nearest OST sport.

        Looks ``target`` up in the reverse table. On a miss, iterates the
        platform's reducer (if any) and tries each coarser key in turn.
        Returns ``Sport.GENERIC`` if nothing matches.
        """
        hit = self._reverse.get(target)
        if hit is not None:
            return _sport_from_reverse(hit)

        if self._reducer is not None:
            for candidate in self._reducer(target):
                if candidate == target:
                    continue  # already tried above
                hit = self._reverse.get(candidate)
                if hit is not None:
                    return _sport_from_reverse(hit)

        return Sport.GENERIC


def _sport_from_reverse(entry: tuple[str, frozenset[str]]) -> Sport:
    code, mods = entry
    return Sport(code, modifiers={Modifier(m) for m in mods})
