"""Generate Python source files from schema.yaml and mapping files.

Run: uv run scripts/generate.py
Check: uv run scripts/generate.py --check
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema.yaml"
MAPPINGS_DIR = ROOT / "mappings"
OUT_DIR = ROOT / "src" / "open_sports_schema"

HEADER = '# Auto-generated from schema.yaml — do not edit.\n# Run: uv run scripts/generate.py\n'


def load_schema() -> dict:
    return yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_mapping(name: str) -> dict:
    path = MAPPINGS_DIR / f"{name}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# _modifier.py
# ---------------------------------------------------------------------------

def generate_modifier(schema: dict) -> str:
    modifiers = schema["modifiers"]

    lines = [
        HEADER,
        "from __future__ import annotations",
        "",
        "from enum import Enum",
        "",
        "",
        "class Modifier(str, Enum):",
        '    """A modifier that qualifies a sport (e.g. race, virtual, assisted)."""',
        "",
    ]

    # Enum members.
    for entry in modifiers:
        name = entry["code"].upper()
        lines.append(f'    {name} = "{entry["code"]}"')
    lines.append("")

    # Properties.
    lines.extend([
        "    @property",
        "    def code(self) -> str:",
        "        return self.value",
        "",
        "    @property",
        "    def label(self) -> str:",
        "        return _LABELS[self.value]",
        "",
        "    @property",
        "    def group(self) -> str | None:",
        "        return _GROUPS.get(self.value)",
        "",
        "    @classmethod",
        "    def in_group(cls, group: str) -> list[Modifier]:",
        "        return [m for m in cls if m.group == group]",
        "",
        "",
    ])

    # Label lookup.
    lines.append("_LABELS: dict[str, str] = {")
    for entry in modifiers:
        lines.append(f'    "{entry["code"]}": "{entry["label"]}",')
    lines.append("}")
    lines.append("")

    # Group lookup (only entries that have a group).
    lines.append("_GROUPS: dict[str, str] = {")
    for entry in modifiers:
        if "group" in entry:
            lines.append(f'    "{entry["code"]}": "{entry["group"]}",')
    lines.append("}")
    lines.append("")

    # validate_modifiers function.
    lines.extend([
        "",
        "def validate_modifiers(modifiers: frozenset[Modifier]) -> None:",
        '    """Raise ValueError if modifiers from the same group are combined."""',
        "    groups_seen: dict[str, Modifier] = {}",
        "    for mod in modifiers:",
        "        g = mod.group",
        "        if g is not None:",
        "            if g in groups_seen:",
        "                conflict = groups_seen[g]",
        "                raise ValueError(",
        '                    f"Modifiers {conflict.code!r} and {mod.code!r} "',
        '                    f"conflict (same group: {g!r})"',
        "                )",
        "            groups_seen[g] = mod",
        "",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# _sport.py
# ---------------------------------------------------------------------------

def generate_sport(schema: dict) -> str:
    sports = schema["sports"]

    # Build taxonomy data.
    codes = [entry["code"] for entry in sports]
    labels = {entry["code"]: entry["label"] for entry in sports}

    parents: dict[str, str | None] = {}
    children: dict[str, list[str]] = {code: [] for code in codes}
    for code in codes:
        dot = code.rfind(".")
        parents[code] = code[:dot] if dot != -1 else None
    for code, parent in parents.items():
        if parent is not None:
            children[parent].append(code)

    lines = [
        HEADER,
        "from __future__ import annotations",
        "",
        "from collections.abc import Iterable",
        "from dataclasses import dataclass",
        "",
        "from open_sports_schema._modifier import Modifier, validate_modifiers",
        "",
        "",
        "# Taxonomy data — generated from schema.yaml.",
        "_LABELS: dict[str, str] = {",
    ]
    for code in codes:
        lines.append(f'    "{code}": "{labels[code]}",')
    lines.append("}")
    lines.append("")

    lines.append("_PARENTS: dict[str, str | None] = {")
    for code in codes:
        parent = parents[code]
        val = f'"{parent}"' if parent else "None"
        lines.append(f'    "{code}": {val},')
    lines.append("}")
    lines.append("")

    lines.append("_CHILDREN: dict[str, tuple[str, ...]] = {")
    for code in codes:
        kids = children[code]
        if kids:
            kid_strs = ", ".join(f'"{k}"' for k in kids)
            lines.append(f'    "{code}": ({kid_strs},),')
        else:
            lines.append(f'    "{code}": (),')
    lines.append("}")
    lines.append("")

    # Helper for structural validation (shared by all entry points).
    lines.extend([
        "",
        "def _split_encoded(raw: str) -> tuple[str, list[str]]:",
        '    """Split an encoded sport string into code and modifier tokens.',
        "",
        "    Raises ValueError on structural errors (empty, trailing +, double +).",
        '    """',
        "    if not isinstance(raw, str):",
        '        raise TypeError(f"Expected str, got {type(raw).__name__}")',
        "    if not raw:",
        '        raise ValueError("Sport code cannot be empty")',
        '    parts = raw.split("+")',
        '    if "" in parts:',
        '        raise ValueError(f"Invalid encoded string: {raw!r}")',
        "    return parts[0], parts[1:]",
        "",
        "",
    ])

    # Sport class.
    lines.extend([
        "@dataclass(frozen=True, init=False, slots=True)",
        "class Sport:",
        '    """A sport with optional modifiers.',
        "",
        "    Use the three classmethods to create Sport instances:",
        "",
        "        Sport.resolve(raw)    — forward-compatible (recommended)",
        "        Sport.parse(raw)      — preserves non-standard codes and modifiers",
        "        Sport.validate(raw)   — strict, rejects non-standard input",
        "",
        "    Or use class constants for known sports::",
        "",
        "        Sport.CYCLING_ROAD",
        "        Sport.RUNNING_TRAIL",
        '    """',
        "",
        "    code: str",
        "    modifiers: frozenset[Modifier]",
        "    unknown_modifiers: frozenset[str]",
        "    raw: str",
        "",
        "    # ------------------------------------------------------------------",
        "    # Constructor (validates strictly — same as Sport.validate)",
        "    # ------------------------------------------------------------------",
        "",
        "    def __init__(",
        "        self,",
        "        code: str,",
        "        *,",
        "        modifiers: Iterable[Modifier] | None = None,",
        "    ) -> None:",
        "        if not isinstance(code, str):",
        '            raise TypeError(f"Expected str, got {type(code).__name__}")',
        "",
        '        if modifiers is not None and "+" in code:',
        "            raise ValueError(",
        '                "Cannot pass both an encoded string and modifiers keyword. "',
        "                \"Use either Sport('cycling.road+virtual') or \"",
        "                \"Sport('cycling.road', modifiers={Modifier.VIRTUAL}).\"",
        "            )",
        "",
        '        if "+" in code:',
        '            parts = code.split("+")',
        '            if "" in parts:',
        '                raise ValueError(f"Invalid encoded string: {code!r}")',
        "            parsed_code = parts[0]",
        "            parsed_modifiers = frozenset(Modifier(m) for m in parts[1:])",
        "        else:",
        "            parsed_code = code",
        "            parsed_modifiers = (",
        "                frozenset(modifiers) if modifiers is not None else frozenset()",
        "            )",
        "",
        "        if not parsed_code:",
        '            raise ValueError("Sport code cannot be empty")',
        "",
        "        if parsed_code not in _LABELS:",
        '            raise ValueError(f"Unknown sport code: {parsed_code!r}")',
        "",
        "        validate_modifiers(parsed_modifiers)",
        "",
        '        object.__setattr__(self, "code", parsed_code)',
        '        object.__setattr__(self, "modifiers", parsed_modifiers)',
        '        object.__setattr__(self, "unknown_modifiers", frozenset())',
        "        # raw is the canonical standard form for validated sports.",
        "        _raw = parsed_code",
        "        if parsed_modifiers:",
        '            _raw += "+" + "+".join(sorted(m.value for m in parsed_modifiers))',
        '        object.__setattr__(self, "raw", _raw)',
        "",
        "    # ------------------------------------------------------------------",
        "    # Classmethods: resolve, parse, validate",
        "    # ------------------------------------------------------------------",
        "",
        "    @classmethod",
        "    def resolve(cls, raw: str) -> Sport:",
        '        """Resolve a sport string to the nearest standard sport.',
        "",
        "        Walks up the hierarchy for unknown codes, drops unknown modifiers.",
        "        Always returns a standard sport. Preserves the original in .raw.",
        '        """',
        "        raw_code, raw_modifiers = _split_encoded(raw)",
        "",
        "        # Walk up the hierarchy until a known code is found.",
        "        code = raw_code",
        "        while code and code not in _LABELS:",
        '            dot = code.rfind(".")',
        '            code = code[:dot] if dot != -1 else ""',
        "        if not code:",
        '            code = "generic"',
        "",
        "        # Keep only known modifiers, drop the rest.",
        "        known: set[Modifier] = set()",
        "        for m in raw_modifiers:",
        "            try:",
        "                known.add(Modifier(m))",
        "            except ValueError:",
        "                continue",
        "",
        "        sport = cls(code, modifiers=known)",
        "        # Override raw with the original input.",
        '        object.__setattr__(sport, "raw", raw)',
        "        return sport",
        "",
        "    @classmethod",
        "    def parse(cls, raw: str) -> Sport:",
        '        """Parse a sport string, preserving unknown codes and modifiers.',
        "",
        "        Returns a standard or non-standard sport. Only structural errors",
        "        raise ValueError. No schema validation, no modifier group checks.",
        '        """',
        "        code, raw_modifiers = _split_encoded(raw)",
        "",
        "        # Separate known from unknown modifiers.",
        "        known: set[Modifier] = set()",
        "        unknown: set[str] = set()",
        "        for m in raw_modifiers:",
        "            try:",
        "                known.add(Modifier(m))",
        "            except ValueError:",
        "                unknown.add(m)",
        "",
        "        sport = object.__new__(cls)",
        '        object.__setattr__(sport, "code", code)',
        '        object.__setattr__(sport, "modifiers", frozenset(known))',
        '        object.__setattr__(sport, "unknown_modifiers", frozenset(unknown))',
        '        object.__setattr__(sport, "raw", raw)',
        "        return sport",
        "",
        "    @classmethod",
        "    def validate(cls, raw: str) -> Sport:",
        '        """Validate a sport string strictly.',
        "",
        "        Rejects unknown codes and modifiers. Same behavior as the constructor.",
        '        """',
        "        return cls(raw)",
        "",
        "    # ------------------------------------------------------------------",
        "    # Properties",
        "    # ------------------------------------------------------------------",
        "",
        "    @property",
        "    def is_standard(self) -> bool:",
        '        """True if code and all modifiers are defined in the schema."""',
        "        return self.code in _LABELS and not self.unknown_modifiers",
        "",
        "    @property",
        "    def label(self) -> str | None:",
        '        """Human-readable label, or None for non-standard sports."""',
        "        return _LABELS.get(self.code)",
        "",
        "    @property",
        "    def parent(self) -> Sport | None:",
        '        """Parent sport. Derived from dot notation for non-standard codes."""',
        "        if self.code in _PARENTS:",
        "            parent_code = _PARENTS[self.code]",
        "        else:",
        '            dot = self.code.rfind(".")',
        "            parent_code = self.code[:dot] if dot != -1 else None",
        "        if parent_code is None:",
        "            return None",
        "        return Sport.parse(parent_code)",
        "",
        "    @property",
        "    def disciplines(self) -> tuple[Sport, ...]:",
        '        """Direct child sports. Empty for non-standard or leaf sports."""',
        "        children = _CHILDREN.get(self.code, ())",
        "        return tuple(Sport(c) for c in children)",
        "",
        "    @classmethod",
        "    def all(cls) -> list[Sport]:",
        '        """All standard sports defined in the schema."""',
        "        return [Sport(code) for code in _LABELS]",
        "",
        "    # ------------------------------------------------------------------",
        "    # Dunder methods",
        "    # ------------------------------------------------------------------",
        "",
        "    def __eq__(self, other: object) -> bool:",
        "        if not isinstance(other, Sport):",
        "            return NotImplemented",
        "        return (",
        "            self.code == other.code",
        "            and self.modifiers == other.modifiers",
        "            and self.unknown_modifiers == other.unknown_modifiers",
        "        )",
        "",
        "    def __hash__(self) -> int:",
        "        return hash((self.code, self.modifiers, self.unknown_modifiers))",
        "",
        "    def __str__(self) -> str:",
        "        all_mods = sorted(",
        "            [m.value for m in self.modifiers] + list(self.unknown_modifiers)",
        "        )",
        "        if all_mods:",
        '            return self.code + "+" + "+".join(all_mods)',
        "        return self.code",
        "",
        "    def __repr__(self) -> str:",
        '        return f"Sport({str(self)!r})"',
        "",
        "",
        "# Class constants.",
    ])

    for code in codes:
        name = code.replace(".", "_").upper()
        lines.append(f'Sport.{name} = Sport("{code}")  # type: ignore[attr-defined]')

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# _platforms.py
# ---------------------------------------------------------------------------

def generate_platforms(schema: dict) -> str:
    lines = [
        HEADER,
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
        "from open_sports_schema._platform import GarminFitCode",
        "",
        "",
    ]

    # Strava
    strava = load_mapping("strava")
    lines.append(f'STRAVA_FALLBACK: str = "{strava["fallback"]}"')
    lines.append("")
    lines.append("STRAVA_MAPPINGS: dict[tuple[str, frozenset[str]], str] = {")
    for entry in strava["mappings"]:
        key_code = entry["oss"]
        key_mods = frozenset(entry.get("modifiers", []))
        mods_repr = _frozenset_repr(key_mods)
        lines.append(f'    ("{key_code}", {mods_repr}): "{entry["target"]}",')
    lines.append("}")
    lines.append("")

    # Apple HealthKit
    hk = load_mapping("apple_healthkit")
    lines.append(f"APPLE_HEALTHKIT_FALLBACK: int = {hk['fallback']}")
    lines.append("")
    lines.append("APPLE_HEALTHKIT_MAPPINGS: dict[tuple[str, frozenset[str]], int] = {")
    for entry in hk["mappings"]:
        key_code = entry["oss"]
        key_mods = frozenset(entry.get("modifiers", []))
        mods_repr = _frozenset_repr(key_mods)
        lines.append(f'    ("{key_code}", {mods_repr}): {entry["target"]},')
    lines.append("}")
    lines.append("")

    # Garmin FIT
    gf = load_mapping("garmin_fit")
    fb = gf["fallback"]
    lines.append(
        f"GARMIN_FIT_FALLBACK: GarminFitCode = "
        f"GarminFitCode(sport={fb['sport']}, sub_sport={fb['sub_sport']})"
    )
    lines.append("")
    lines.append(
        "GARMIN_FIT_MAPPINGS: dict[tuple[str, frozenset[str]], GarminFitCode] = {"
    )
    for entry in gf["mappings"]:
        key_code = entry["oss"]
        key_mods = frozenset(entry.get("modifiers", []))
        mods_repr = _frozenset_repr(key_mods)
        t = entry["target"]
        lines.append(
            f'    ("{key_code}", {mods_repr}): '
            f"GarminFitCode(sport={t['sport']}, sub_sport={t['sub_sport']}),"
        )
    lines.append("}")
    lines.append("")

    return "\n".join(lines)


def _frozenset_repr(s: frozenset) -> str:
    if not s:
        return "frozenset()"
    items = ", ".join(f'"{x}"' for x in sorted(s))
    return f"frozenset({{{items}}})"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Python source from schema.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check that generated files are up to date (exit 1 if stale).",
    )
    args = parser.parse_args()

    schema = load_schema()

    files = {
        OUT_DIR / "_modifier.py": generate_modifier(schema),
        OUT_DIR / "_sport.py": generate_sport(schema),
        OUT_DIR / "_platforms.py": generate_platforms(schema),
    }

    if args.check:
        stale = []
        for path, expected in files.items():
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                stale.append(path)
        if stale:
            for p in stale:
                print(f"STALE: {p.relative_to(ROOT)}")
            print("\nRun 'uv run scripts/generate.py' to update.")
            sys.exit(1)
        else:
            print("All generated files are up to date.")
    else:
        for path, content in files.items():
            path.write_text(content, encoding="utf-8")
            print(f"Generated {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
