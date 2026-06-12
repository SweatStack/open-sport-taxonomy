# Auto-generated from schema.yaml — do not edit.
# Run: uv run scripts/generate.py

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from open_sport_taxonomy._modifier import Modifier, validate_modifiers


# Taxonomy data — generated from schema.yaml.
# _LABELS is the standard-sports catalogue, keyed by canonical string
# (bare codes AND recommended combinations).
_LABELS: dict[str, str] = {
    "alpine_skiing": "alpine skiing",
    "cycling": "cycling",
    "cycling+assisted": "e-bike ride",
    "cycling+commute": "bike commute",
    "cycling+stationary": "indoor cycling",
    "cycling+stationary+virtual": "virtual indoor cycling",
    "cycling.cyclocross": "cyclocross",
    "cycling.gravel": "gravel cycling",
    "cycling.mountain": "mountain biking",
    "cycling.mountain+assisted": "e-mountain biking",
    "cycling.road": "road cycling",
    "cycling.time_trial": "time trial cycling",
    "cycling.track": "track cycling",
    "generic": "generic",
    "hand_cycling": "hand cycling",
    "rowing": "rowing",
    "rowing+stationary": "indoor rowing",
    "rowing+stationary+virtual": "virtual indoor rowing",
    "running": "running",
    "running+race": "running race",
    "running+stationary": "treadmill running",
    "running+stationary+virtual": "virtual treadmill running",
    "running.road": "road running",
    "running.track": "track running",
    "running.trail": "trail running",
    "snowboarding": "snowboarding",
    "swimming": "swimming",
    "swimming.open_water": "open water swimming",
    "swimming.pool": "pool swimming",
    "walking": "walking",
    "walking+stationary": "treadmill walking",
    "walking.hiking": "hiking",
    "xc_skiing": "XC skiing",
    "xc_skiing+roller": "roller skiing",
    "xc_skiing.classic": "classic XC skiing",
    "xc_skiing.classic+roller": "classic roller skiing",
    "xc_skiing.double_poling": "double poling XC skiing",
    "xc_skiing.skate": "skate XC skiing",
    "xc_skiing.skate+roller": "skate roller skiing",
}

# StandardSport — a Literal of every standard-sport canonical string,
# generated from the catalogue. Annotate your own variables/fields with it
# for autocomplete + mypy typo-checking. The Sport constructors take plain
# `str` (they ingest runtime data); use `is_standard` to test membership.
StandardSport = Literal[
    "alpine_skiing",
    "cycling",
    "cycling+assisted",
    "cycling+commute",
    "cycling+stationary",
    "cycling+stationary+virtual",
    "cycling.cyclocross",
    "cycling.gravel",
    "cycling.mountain",
    "cycling.mountain+assisted",
    "cycling.road",
    "cycling.time_trial",
    "cycling.track",
    "generic",
    "hand_cycling",
    "rowing",
    "rowing+stationary",
    "rowing+stationary+virtual",
    "running",
    "running+race",
    "running+stationary",
    "running+stationary+virtual",
    "running.road",
    "running.track",
    "running.trail",
    "snowboarding",
    "swimming",
    "swimming.open_water",
    "swimming.pool",
    "walking",
    "walking+stationary",
    "walking.hiking",
    "xc_skiing",
    "xc_skiing+roller",
    "xc_skiing.classic",
    "xc_skiing.classic+roller",
    "xc_skiing.double_poling",
    "xc_skiing.skate",
    "xc_skiing.skate+roller",
]

# _CODES — the bare (modifier-free) codes: the modality tree.
_CODES: frozenset[str] = frozenset({
    "alpine_skiing",
    "cycling",
    "cycling.cyclocross",
    "cycling.gravel",
    "cycling.mountain",
    "cycling.road",
    "cycling.time_trial",
    "cycling.track",
    "generic",
    "hand_cycling",
    "rowing",
    "running",
    "running.road",
    "running.track",
    "running.trail",
    "snowboarding",
    "swimming",
    "swimming.open_water",
    "swimming.pool",
    "walking",
    "walking.hiking",
    "xc_skiing",
    "xc_skiing.classic",
    "xc_skiing.double_poling",
    "xc_skiing.skate",
})

# _CODE_MODSETS — per code, its catalogue modifier-sets, largest first
# (ties by canonical string). Drives resolve()'s phase 2.
_CODE_MODSETS: dict[str, tuple[frozenset[str], ...]] = {
    "alpine_skiing": (frozenset(),),
    "cycling": (frozenset({"stationary", "virtual"}), frozenset({"assisted"}), frozenset({"commute"}), frozenset({"stationary"}), frozenset(),),
    "cycling.cyclocross": (frozenset(),),
    "cycling.gravel": (frozenset(),),
    "cycling.mountain": (frozenset({"assisted"}), frozenset(),),
    "cycling.road": (frozenset(),),
    "cycling.time_trial": (frozenset(),),
    "cycling.track": (frozenset(),),
    "generic": (frozenset(),),
    "hand_cycling": (frozenset(),),
    "rowing": (frozenset({"stationary", "virtual"}), frozenset({"stationary"}), frozenset(),),
    "running": (frozenset({"stationary", "virtual"}), frozenset({"race"}), frozenset({"stationary"}), frozenset(),),
    "running.road": (frozenset(),),
    "running.track": (frozenset(),),
    "running.trail": (frozenset(),),
    "snowboarding": (frozenset(),),
    "swimming": (frozenset(),),
    "swimming.open_water": (frozenset(),),
    "swimming.pool": (frozenset(),),
    "walking": (frozenset({"stationary"}), frozenset(),),
    "walking.hiking": (frozenset(),),
    "xc_skiing": (frozenset({"roller"}), frozenset(),),
    "xc_skiing.classic": (frozenset({"roller"}), frozenset(),),
    "xc_skiing.double_poling": (frozenset(),),
    "xc_skiing.skate": (frozenset({"roller"}), frozenset(),),
}

_PARENTS: dict[str, str | None] = {
    "alpine_skiing": None,
    "cycling": None,
    "cycling.cyclocross": 'cycling',
    "cycling.gravel": 'cycling',
    "cycling.mountain": 'cycling',
    "cycling.road": 'cycling',
    "cycling.time_trial": 'cycling',
    "cycling.track": 'cycling',
    "generic": None,
    "hand_cycling": None,
    "rowing": None,
    "running": None,
    "running.road": 'running',
    "running.track": 'running',
    "running.trail": 'running',
    "snowboarding": None,
    "swimming": None,
    "swimming.open_water": 'swimming',
    "swimming.pool": 'swimming',
    "walking": None,
    "walking.hiking": 'walking',
    "xc_skiing": None,
    "xc_skiing.classic": 'xc_skiing',
    "xc_skiing.double_poling": 'xc_skiing',
    "xc_skiing.skate": 'xc_skiing',
}

_CHILDREN: dict[str, tuple[str, ...]] = {
    "alpine_skiing": (),
    "cycling": ("cycling.cyclocross", "cycling.gravel", "cycling.mountain", "cycling.road", "cycling.time_trial", "cycling.track",),
    "cycling.cyclocross": (),
    "cycling.gravel": (),
    "cycling.mountain": (),
    "cycling.road": (),
    "cycling.time_trial": (),
    "cycling.track": (),
    "generic": (),
    "hand_cycling": (),
    "rowing": (),
    "running": ("running.road", "running.track", "running.trail",),
    "running.road": (),
    "running.track": (),
    "running.trail": (),
    "snowboarding": (),
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

def _atom_words(token: str) -> str:
    """Best-effort words from a raw code/modifier token (label fallback only)."""
    return token.replace(".", " ").replace("_", " ")


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


def _is_subsport_code(child: str, parent: str) -> bool:
    """True if child == parent or child is below parent in the dot hierarchy."""
    return child == parent or child.startswith(parent + ".")


@dataclass(frozen=True, init=False, slots=True)
class Sport:
    """A sport with optional modifiers.

    Two ways to create Sport instances:

        Sport(raw)        — strict, enforces known atoms (known code + modifiers)
        Sport.parse(raw)  — permissive, for external input

    The module exports ``StandardSport`` — a ``Literal`` of every catalogue
    string. Annotate your own variables/fields with it for autocomplete and
    static typo-checking; the constructors take plain ``str`` because they ingest
    runtime data (API/DB values) and validate at runtime.

    Three nested levels describe any sport (see docs/taxonomy.md):
      - well-formed   — `Sport.parse(...)` succeeded;
      - known-atoms   — `uses_known_atoms`: code and every modifier are declared;
      - standard sport — `is_standard`: the exact canonical string is catalogued.
    """

    code: str
    modifiers: frozenset[str]

    def __init__(self, code: str, *, modifiers: Iterable[Modifier] | None = None) -> None:
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
        if parsed_code not in _CODES:
            raise ValueError(f"Unknown sport code: {parsed_code!r}")
        validate_modifiers(parsed_modifiers)
        object.__setattr__(self, "code", parsed_code)
        object.__setattr__(self, "modifiers", frozenset(parsed_modifiers))

    @classmethod
    def parse(cls, raw: str) -> Sport:
        """Parse a sport string, preserving unknown codes and modifiers.

        Returns a standard or non-standard sport. Only structural errors
        raise ValueError. No schema validation, no modifier group checks.
        """
        code, raw_modifiers = _split_encoded(raw)
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

    def resolve(self) -> Sport:
        """Resolve to the nearest standard sport.

        Two ordered phases, **drop-only** — never adds a modifier or specificity:
          1. climb the code tree to the nearest ancestor whose bare form is
             standard (else ``generic``);
          2. keep the largest subset of the original modifiers that forms a
             catalogue entry (bare code if none does).
        """
        if self.is_standard:
            return self
        code = self.code
        while code and code not in _CODES:
            dot = code.rfind(".")
            code = code[:dot] if dot != -1 else ""
        if not code:
            code = "generic"
        mod_values = {m.value for m in self.modifiers if isinstance(m, Modifier)}
        # _CODE_MODSETS[code] is largest-first and always contains the empty set
        # (the bare code), so a subset match is guaranteed.
        chosen = next(c for c in _CODE_MODSETS[code] if c <= mod_values)
        return Sport(code, modifiers={Modifier(m) for m in chosen})

    def is_subsport_of(self, other: Sport) -> bool:
        """True if this sport is a more specific version of other."""
        if not _is_subsport_code(self.code, other.code):
            return False
        if not other.modifiers.issubset(self.modifiers):
            return False
        return True

    @property
    def is_standard(self) -> bool:
        """True if this exact sport is in the standard-sports catalogue."""
        return str(self) in _LABELS

    @property
    def uses_known_atoms(self) -> bool:
        """True if the code and every modifier are declared atoms.

        Weaker than `is_standard`: the combination need not be catalogued, but
        every part must be known (and the modifiers group-valid). `is_standard`
        implies `uses_known_atoms`.
        """
        if self.code not in _CODES:
            return False
        known: list[Modifier] = []
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
    def label(self) -> str:
        """Human-readable label — always a string.

        Hand-crafted for a standard sport; otherwise composed from the parts as
        ``code-label (modifier, modifier)``. Unknown atoms fall back to their
        token with ``.``/``_`` turned to spaces. `is_standard` tells you whether
        the label is curated or composed.
        """
        curated = _LABELS.get(str(self))
        if curated is not None:
            return curated
        code_label = _LABELS.get(self.code)
        if code_label is None:
            code_label = _atom_words(self.code)
        mods = sorted(m.value if isinstance(m, Modifier) else m for m in self.modifiers)
        if not mods:
            return code_label
        rendered: list[str] = []
        for m in mods:
            try:
                rendered.append(Modifier(m).label)
            except ValueError:
                rendered.append(_atom_words(m))
        return f"{code_label} ({', '.join(rendered)})"

    def _with_code(self, code: str) -> Sport:
        """Return a sport with a different code but the same modifiers."""
        if not self.modifiers:
            return Sport.parse(code)
        mod_str = "+".join(
            sorted(m.value if isinstance(m, Modifier) else m for m in self.modifiers)
        )
        return Sport.parse(code + "+" + mod_str)

    @property
    def parent(self) -> Sport | None:
        """Parent sport, preserving modifiers."""
        if self.code in _PARENTS:
            parent_code = _PARENTS[self.code]
        else:
            dot = self.code.rfind(".")
            parent_code = self.code[:dot] if dot != -1 else None
        if parent_code is None:
            return None
        return self._with_code(parent_code)

    @property
    def disciplines(self) -> tuple[Sport, ...]:
        """Direct child sports, preserving modifiers."""
        children = _CHILDREN.get(self.code, ())
        return tuple(self._with_code(c) for c in children)

    @classmethod
    def all(cls) -> list[Sport]:
        """All standard sports in the catalogue (codes and combinations)."""
        return [Sport(s) for s in _LABELS]

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
