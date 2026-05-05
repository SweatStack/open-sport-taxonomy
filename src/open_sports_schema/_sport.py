# Auto-generated from schema.yaml — do not edit.
# Run: uv run scripts/generate.py

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from open_sports_schema._modifier import Modifier, validate_modifiers


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
    "xc_skiing.backcountry": "backcountry XC skiing",
    "xc_skiing.classic": "classic XC skiing",
    "xc_skiing.roller": "roller skiing",
    "xc_skiing.roller.classic": "classic roller skiing",
    "xc_skiing.roller.skate": "skate roller skiing",
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
    "xc_skiing.backcountry": "xc_skiing",
    "xc_skiing.classic": "xc_skiing",
    "xc_skiing.roller": "xc_skiing",
    "xc_skiing.roller.classic": "xc_skiing.roller",
    "xc_skiing.roller.skate": "xc_skiing.roller",
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
    "xc_skiing": ("xc_skiing.backcountry", "xc_skiing.classic", "xc_skiing.roller", "xc_skiing.skate",),
    "xc_skiing.backcountry": (),
    "xc_skiing.classic": (),
    "xc_skiing.roller": ("xc_skiing.roller.classic", "xc_skiing.roller.skate",),
    "xc_skiing.roller.classic": (),
    "xc_skiing.roller.skate": (),
    "xc_skiing.skate": (),
}


@dataclass(frozen=True, init=False, slots=True)
class Sport:
    """A sport code with optional modifiers.

    Construct from an encoded string or a bare code with explicit modifiers::

        Sport("cycling.road")
        Sport("cycling.road+race+virtual")
        Sport("cycling.road", modifiers={Modifier.RACE, Modifier.VIRTUAL})
    """

    code: str
    modifiers: frozenset[Modifier]

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
        object.__setattr__(self, "modifiers", parsed_modifiers)

    @property
    def label(self) -> str:
        return _LABELS[self.code]

    @property
    def parent(self) -> Sport | None:
        parent_code = _PARENTS[self.code]
        if parent_code is None:
            return None
        return Sport(parent_code)

    @property
    def disciplines(self) -> tuple[Sport, ...]:
        return tuple(Sport(c) for c in _CHILDREN[self.code])

    @classmethod
    def all(cls) -> list[Sport]:
        return [Sport(code) for code in _LABELS]

    def __str__(self) -> str:
        if self.modifiers:
            mods = "+".join(sorted(m.value for m in self.modifiers))
            return f"{self.code}+{mods}"
        return self.code

    def __repr__(self) -> str:
        return f"Sport({str(self)!r})"

    @classmethod
    def resolve(cls, raw: str) -> Sport:
        """Resolve an encoded string to the nearest known Sport.

        Walks up the sport code hierarchy for unknown codes and drops
        unknown modifiers. Always returns a schema-valid Sport.

        Structural errors (empty string, trailing +) still raise ValueError.
        """
        if not isinstance(raw, str):
            raise TypeError(f"Expected str, got {type(raw).__name__}")

        if not raw:
            raise ValueError("Sport code cannot be empty")

        parts = raw.split("+")
        if "" in parts:
            raise ValueError(f"Invalid encoded string: {raw!r}")

        raw_code = parts[0]
        raw_modifiers = parts[1:]

        # Walk up the hierarchy until a known code is found.
        code = raw_code
        while code and code not in _LABELS:
            dot = code.rfind(".")
            code = code[:dot] if dot != -1 else ""

        if not code:
            code = "generic"

        # Keep only known modifiers, drop the rest.
        known_modifiers: set[Modifier] = set()
        for m in raw_modifiers:
            try:
                known_modifiers.add(Modifier(m))
            except ValueError:
                continue

        return cls(code, modifiers=known_modifiers)


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
Sport.XC_SKIING_BACKCOUNTRY = Sport("xc_skiing.backcountry")  # type: ignore[attr-defined]
Sport.XC_SKIING_CLASSIC = Sport("xc_skiing.classic")  # type: ignore[attr-defined]
Sport.XC_SKIING_ROLLER = Sport("xc_skiing.roller")  # type: ignore[attr-defined]
Sport.XC_SKIING_ROLLER_CLASSIC = Sport("xc_skiing.roller.classic")  # type: ignore[attr-defined]
Sport.XC_SKIING_ROLLER_SKATE = Sport("xc_skiing.roller.skate")  # type: ignore[attr-defined]
Sport.XC_SKIING_SKATE = Sport("xc_skiing.skate")  # type: ignore[attr-defined]
