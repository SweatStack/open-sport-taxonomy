# Auto-generated from schema.yaml — do not edit.
# Run: uv run scripts/generate.py

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from open_sport_taxonomy._modifier import Modifier, validate_modifiers


# Taxonomy data — generated from schema.yaml.
_LABELS: dict[str, str] = {
    "cycling": "cycling",
    "cycling.cyclocross": "cyclocross",
    "cycling.gravel": "gravel cycling",
    "cycling.mountain": "mountain biking",
    "cycling.road": "road cycling",
    "cycling.time_trial": "time trial cycling",
    "cycling.track": "track cycling",
    "generic": "generic",
    "rowing": "rowing",
    "running": "running",
    "running.road": "road running",
    "running.track": "track running",
    "running.trail": "trail running",
    "swimming": "swimming",
    "swimming.open_water": "open water swimming",
    "swimming.pool": "pool swimming",
    "walking": "walking",
    "walking.hiking": "hiking",
    "xc_skiing": "XC skiing",
    "xc_skiing.classic": "classic XC skiing",
    "xc_skiing.double_poling": "double poling XC skiing",
    "xc_skiing.skate": "skate XC skiing",
}

_PARENTS: dict[str, str | None] = {
    "cycling": None,
    "cycling.cyclocross": "cycling",
    "cycling.gravel": "cycling",
    "cycling.mountain": "cycling",
    "cycling.road": "cycling",
    "cycling.time_trial": "cycling",
    "cycling.track": "cycling",
    "generic": None,
    "rowing": None,
    "running": None,
    "running.road": "running",
    "running.track": "running",
    "running.trail": "running",
    "swimming": None,
    "swimming.open_water": "swimming",
    "swimming.pool": "swimming",
    "walking": None,
    "walking.hiking": "walking",
    "xc_skiing": None,
    "xc_skiing.classic": "xc_skiing",
    "xc_skiing.double_poling": "xc_skiing",
    "xc_skiing.skate": "xc_skiing",
}

_CHILDREN: dict[str, tuple[str, ...]] = {
    "cycling": ("cycling.cyclocross", "cycling.gravel", "cycling.mountain", "cycling.road", "cycling.time_trial", "cycling.track",),
    "cycling.cyclocross": (),
    "cycling.gravel": (),
    "cycling.mountain": (),
    "cycling.road": (),
    "cycling.time_trial": (),
    "cycling.track": (),
    "generic": (),
    "rowing": (),
    "running": ("running.road", "running.track", "running.trail",),
    "running.road": (),
    "running.track": (),
    "running.trail": (),
    "swimming": ("swimming.open_water", "swimming.pool",),
    "swimming.open_water": (),
    "swimming.pool": (),
    "walking": ("walking.hiking",),
    "walking.hiking": (),
    "xc_skiing": ("xc_skiing.classic", "xc_skiing.double_poling", "xc_skiing.skate",),
    "xc_skiing.classic": (),
    "xc_skiing.double_poling": (),
    "xc_skiing.skate": (),
}


def _split_encoded(raw: str) -> tuple[str, list[str]]:
    """Split an encoded sport string into code and modifier tokens.

    Raises ValueError on structural errors (empty, trailing +, double +).
    """
    if not isinstance(raw, str):
        raise TypeError(f"Expected str, got {type(raw).__name__}")
    if not raw:
        raise ValueError("Sport code cannot be empty")
    parts = raw.split("+")
    if "" in parts:
        raise ValueError(f"Invalid encoded string: {raw!r}")
    return parts[0], parts[1:]


@dataclass(frozen=True, init=False, slots=True)
class Sport:
    """A sport with optional modifiers.

    Two ways to create Sport instances:

        Sport(raw)        — strict, enforces the standard vocabulary
        Sport.parse(raw)  — permissive, for external input

    Or use class constants for known sports::

        Sport.CYCLING_ROAD
        Sport.RUNNING_TRAIL
    """

    code: str
    modifiers: frozenset[str]

    # ------------------------------------------------------------------
    # Constructor (strict — rejects unknown codes and modifiers)
    # ------------------------------------------------------------------

    def __init__(
        self,
        code: str,
        *,
        modifiers: Iterable[Modifier] | None = None,
    ) -> None:
        if not isinstance(code, str):
            raise TypeError(f"Expected str, got {type(code).__name__}")

        if modifiers is not None and "+" in code:
            raise ValueError(
                "Cannot pass both an encoded string and modifiers keyword. "
                "Use either Sport('cycling.road+virtual') or "
                "Sport('cycling.road', modifiers={Modifier.VIRTUAL})."
            )

        if "+" in code:
            parts = code.split("+")
            if "" in parts:
                raise ValueError(f"Invalid encoded string: {code!r}")
            parsed_code = parts[0]
            parsed_modifiers = frozenset(Modifier(m) for m in parts[1:])
        else:
            parsed_code = code
            parsed_modifiers = (
                frozenset(modifiers) if modifiers is not None else frozenset()
            )

        if not parsed_code:
            raise ValueError("Sport code cannot be empty")

        if parsed_code not in _LABELS:
            raise ValueError(f"Unknown sport code: {parsed_code!r}")

        validate_modifiers(parsed_modifiers)

        object.__setattr__(self, "code", parsed_code)
        object.__setattr__(self, "modifiers", frozenset(parsed_modifiers))

    # ------------------------------------------------------------------
    # Classmethods
    # ------------------------------------------------------------------

    @classmethod
    def parse(cls, raw: str) -> Sport:
        """Parse a sport string, preserving unknown codes and modifiers.

        Returns a standard or non-standard sport. Only structural errors
        raise ValueError. No schema validation, no modifier group checks.
        """
        code, raw_modifiers = _split_encoded(raw)

        # Convert known modifier strings to Modifier instances,
        # keep unknown ones as plain strings.
        mods: set[str] = set()
        for m in raw_modifiers:
            try:
                mods.add(Modifier(m))
            except ValueError:
                mods.add(m)

        sport = object.__new__(cls)
        object.__setattr__(sport, "code", code)
        object.__setattr__(sport, "modifiers", frozenset(mods))
        return sport

    # ------------------------------------------------------------------
    # Instance methods
    # ------------------------------------------------------------------

    def resolve(self) -> Sport:
        """Resolve to the nearest standard sport.

        Walks up the hierarchy for unknown codes, drops unknown modifiers.
        Returns self if already standard. Raises ValueError if known
        modifiers conflict (e.g. race+training in the same group).
        """
        if self.is_standard:
            return self

        # Walk up the hierarchy until a known code is found.
        code = self.code
        while code and code not in _LABELS:
            dot = code.rfind(".")
            code = code[:dot] if dot != -1 else ""
        if not code:
            code = "generic"

        # Keep only Modifier instances, drop plain strings.
        known: set[Modifier] = set()
        for m in self.modifiers:
            if isinstance(m, Modifier):
                known.add(m)

        return Sport(code, modifiers=known)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_standard(self) -> bool:
        """True if code and all modifiers are defined in the schema."""
        if self.code not in _LABELS:
            return False
        known = []
        for m in self.modifiers:
            if not isinstance(m, Modifier):
                return False
            known.append(m)
        try:
            validate_modifiers(frozenset(known))
        except ValueError:
            return False
        return True

    @property
    def label(self) -> str | None:
        """Human-readable label, or None for non-standard sports."""
        return _LABELS.get(self.code)

    @property
    def parent(self) -> Sport | None:
        """Parent sport. Derived from dot notation for non-standard codes."""
        if self.code in _PARENTS:
            parent_code = _PARENTS[self.code]
        else:
            dot = self.code.rfind(".")
            parent_code = self.code[:dot] if dot != -1 else None
        if parent_code is None:
            return None
        return Sport.parse(parent_code)

    @property
    def disciplines(self) -> tuple[Sport, ...]:
        """Direct child sports. Empty for non-standard or leaf sports."""
        children = _CHILDREN.get(self.code, ())
        return tuple(Sport(c) for c in children)

    @classmethod
    def all(cls) -> list[Sport]:
        """All standard sports defined in the schema."""
        return [Sport(code) for code in _LABELS]

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Sport):
            return NotImplemented
        return self.code == other.code and self.modifiers == other.modifiers

    def __hash__(self) -> int:
        return hash((self.code, self.modifiers))

    def __str__(self) -> str:
        all_mods = sorted(
            m.value if isinstance(m, Modifier) else m for m in self.modifiers
        )
        if all_mods:
            return self.code + "+" + "+".join(all_mods)
        return self.code

    def __repr__(self) -> str:
        if self.is_standard:
            return f"Sport({str(self)!r})"
        return f"Sport.parse({str(self)!r})"


# Class constants.
Sport.CYCLING = Sport("cycling")  # type: ignore[attr-defined]
Sport.CYCLING_CYCLOCROSS = Sport("cycling.cyclocross")  # type: ignore[attr-defined]
Sport.CYCLING_GRAVEL = Sport("cycling.gravel")  # type: ignore[attr-defined]
Sport.CYCLING_MOUNTAIN = Sport("cycling.mountain")  # type: ignore[attr-defined]
Sport.CYCLING_ROAD = Sport("cycling.road")  # type: ignore[attr-defined]
Sport.CYCLING_TIME_TRIAL = Sport("cycling.time_trial")  # type: ignore[attr-defined]
Sport.CYCLING_TRACK = Sport("cycling.track")  # type: ignore[attr-defined]
Sport.GENERIC = Sport("generic")  # type: ignore[attr-defined]
Sport.ROWING = Sport("rowing")  # type: ignore[attr-defined]
Sport.RUNNING = Sport("running")  # type: ignore[attr-defined]
Sport.RUNNING_ROAD = Sport("running.road")  # type: ignore[attr-defined]
Sport.RUNNING_TRACK = Sport("running.track")  # type: ignore[attr-defined]
Sport.RUNNING_TRAIL = Sport("running.trail")  # type: ignore[attr-defined]
Sport.SWIMMING = Sport("swimming")  # type: ignore[attr-defined]
Sport.SWIMMING_OPEN_WATER = Sport("swimming.open_water")  # type: ignore[attr-defined]
Sport.SWIMMING_POOL = Sport("swimming.pool")  # type: ignore[attr-defined]
Sport.WALKING = Sport("walking")  # type: ignore[attr-defined]
Sport.WALKING_HIKING = Sport("walking.hiking")  # type: ignore[attr-defined]
Sport.XC_SKIING = Sport("xc_skiing")  # type: ignore[attr-defined]
Sport.XC_SKIING_CLASSIC = Sport("xc_skiing.classic")  # type: ignore[attr-defined]
Sport.XC_SKIING_DOUBLE_POLING = Sport("xc_skiing.double_poling")  # type: ignore[attr-defined]
Sport.XC_SKIING_SKATE = Sport("xc_skiing.skate")  # type: ignore[attr-defined]
