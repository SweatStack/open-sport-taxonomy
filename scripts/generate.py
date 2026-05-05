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

    # Sport class.
    lines.extend([
        "",
        "@dataclass(frozen=True, init=False, slots=True)",
        "class Sport:",
        '    """A sport code with optional modifiers.',
        "",
        "    Construct from an encoded string or a bare code with explicit modifiers::",
        "",
        "        Sport(\"cycling.road\")",
        "        Sport(\"cycling.road+race+virtual\")",
        "        Sport(\"cycling.road\", modifiers={Modifier.RACE, Modifier.VIRTUAL})",
        '    """',
        "",
        "    code: str",
        "    modifiers: frozenset[Modifier]",
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
        "",
        "    @property",
        "    def label(self) -> str:",
        "        return _LABELS[self.code]",
        "",
        "    @property",
        "    def parent(self) -> Sport | None:",
        "        parent_code = _PARENTS[self.code]",
        "        if parent_code is None:",
        "            return None",
        "        return Sport(parent_code)",
        "",
        "    @property",
        "    def disciplines(self) -> tuple[Sport, ...]:",
        "        return tuple(Sport(c) for c in _CHILDREN[self.code])",
        "",
        "    @classmethod",
        "    def all(cls) -> list[Sport]:",
        "        return [Sport(code) for code in _LABELS]",
        "",
        "    def __str__(self) -> str:",
        "        if self.modifiers:",
        '            mods = "+".join(sorted(m.value for m in self.modifiers))',
        '            return f"{self.code}+{mods}"',
        "        return self.code",
        "",
        "    def __repr__(self) -> str:",
        '        return f"Sport({str(self)!r})"',
        "",
        "    @classmethod",
        "    def resolve(cls, raw: str) -> Sport:",
        '        """Resolve an encoded string to the nearest known Sport.',
        "",
        "        Walks up the sport code hierarchy for unknown codes and drops",
        "        unknown modifiers. Always returns a schema-valid Sport.",
        "",
        "        Structural errors (empty string, trailing +) still raise ValueError.",
        '        """',
        "        if not isinstance(raw, str):",
        '            raise TypeError(f"Expected str, got {type(raw).__name__}")',
        "",
        "        if not raw:",
        '            raise ValueError("Sport code cannot be empty")',
        "",
        '        parts = raw.split("+")',
        '        if "" in parts:',
        '            raise ValueError(f"Invalid encoded string: {raw!r}")',
        "",
        "        raw_code = parts[0]",
        "        raw_modifiers = parts[1:]",
        "",
        "        # Walk up the hierarchy until a known code is found.",
        "        code = raw_code",
        "        while code and code not in _LABELS:",
        '            dot = code.rfind(".")',
        '            code = code[:dot] if dot != -1 else ""',
        "",
        "        if not code:",
        '            code = "generic"',
        "",
        "        # Keep only known modifiers, drop the rest.",
        "        known_modifiers: set[Modifier] = set()",
        "        for m in raw_modifiers:",
        "            try:",
        "                known_modifiers.add(Modifier(m))",
        "            except ValueError:",
        "                continue",
        "",
        "        return cls(code, modifiers=known_modifiers)",
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
