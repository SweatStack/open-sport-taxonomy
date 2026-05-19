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
OUT_DIR = ROOT / "src" / "open_sport_taxonomy"

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
        "from open_sport_taxonomy._modifier import Modifier, validate_modifiers",
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

    # Hierarchy helper.
    lines.extend([
        "def _is_subsport_code(child: str, parent: str) -> bool:",
        '    """True if child == parent or child is below parent in the dot hierarchy."""',
        "    return child == parent or child.startswith(parent + '.')",
        "",
        "",
    ])

    # Sport class.
    lines.extend([
        "@dataclass(frozen=True, init=False, slots=True)",
        "class Sport:",
        '    """A sport with optional modifiers.',
        "",
        "    Two ways to create Sport instances:",
        "",
        "        Sport(raw)        — strict, enforces the standard vocabulary",
        "        Sport.parse(raw)  — permissive, for external input",
        "",
        "    Or use class constants for known sports::",
        "",
        "        Sport.CYCLING_ROAD",
        "        Sport.RUNNING_TRAIL",
        '    """',
        "",
        "    code: str",
        "    modifiers: frozenset[str]",
        "",
        "    # ------------------------------------------------------------------",
        "    # Constructor (strict — rejects unknown codes and modifiers)",
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
        '        object.__setattr__(self, "modifiers", frozenset(parsed_modifiers))',
        "",
        "    # ------------------------------------------------------------------",
        "    # Classmethods",
        "    # ------------------------------------------------------------------",
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
        "        # Convert known modifier strings to Modifier instances,",
        "        # keep unknown ones as plain strings.",
        "        mods: set[str] = set()",
        "        for m in raw_modifiers:",
        "            try:",
        "                mods.add(Modifier(m))",
        "            except ValueError:",
        "                mods.add(m)",
        "",
        "        sport = object.__new__(cls)",
        '        object.__setattr__(sport, "code", code)',
        '        object.__setattr__(sport, "modifiers", frozenset(mods))',
        "        return sport",
        "",
        "    # ------------------------------------------------------------------",
        "    # Instance methods",
        "    # ------------------------------------------------------------------",
        "",
        "    def resolve(self) -> Sport:",
        '        """Resolve to the nearest standard sport.',
        "",
        "        Walks up the hierarchy for unknown codes, drops unknown modifiers.",
        "        Returns self if already standard. Raises ValueError if known",
        "        modifiers conflict (e.g. race+training in the same group).",
        '        """',
        "        if self.is_standard:",
        "            return self",
        "",
        "        # Walk up the hierarchy until a known code is found.",
        "        code = self.code",
        "        while code and code not in _LABELS:",
        '            dot = code.rfind(".")',
        '            code = code[:dot] if dot != -1 else ""',
        "        if not code:",
        '            code = "generic"',
        "",
        "        # Keep only Modifier instances, drop plain strings.",
        "        known: set[Modifier] = set()",
        "        for m in self.modifiers:",
        "            if isinstance(m, Modifier):",
        "                known.add(m)",
        "",
        "        return Sport(code, modifiers=known)",
        "",
        "    def is_subsport_of(self, other: Sport) -> bool:",
        '        """True if this sport is a more specific version of other.',
        "",
        "        Checks two conditions:",
        "        1. self.code is equal to or below other.code in the dot hierarchy",
        "        2. self.modifiers is a superset of other.modifiers",
        '        """',
        "        if not _is_subsport_code(self.code, other.code):",
        "            return False",
        "        if not other.modifiers.issubset(self.modifiers):",
        "            return False",
        "        return True",
        "",
        "    # ------------------------------------------------------------------",
        "    # Properties",
        "    # ------------------------------------------------------------------",
        "",
        "    @property",
        "    def is_standard(self) -> bool:",
        '        """True if code and all modifiers are defined in the schema."""',
        "        if self.code not in _LABELS:",
        "            return False",
        "        known = []",
        "        for m in self.modifiers:",
        "            if not isinstance(m, Modifier):",
        "                return False",
        "            known.append(m)",
        "        try:",
        "            validate_modifiers(frozenset(known))",
        "        except ValueError:",
        "            return False",
        "        return True",
        "",
        "    @property",
        "    def label(self) -> str | None:",
        '        """Human-readable label, or None for non-standard sports."""',
        "        return _LABELS.get(self.code)",
        "",
        "    @property",
        "    def parent(self) -> Sport | None:",
        '        """Parent sport, preserving modifiers.',
        "",
        "        Derived from dot notation for non-standard codes.",
        '        """',
        "        if self.code in _PARENTS:",
        "            parent_code = _PARENTS[self.code]",
        "        else:",
        '            dot = self.code.rfind(".")',
        "            parent_code = self.code[:dot] if dot != -1 else None",
        "        if parent_code is None:",
        "            return None",
        "        if not self.modifiers:",
        "            return Sport.parse(parent_code)",
        "        # Reconstruct with the same modifiers.",
        "        mod_str = '+'.join(",
        "            sorted(m.value if isinstance(m, Modifier) else m for m in self.modifiers)",
        "        )",
        "        return Sport.parse(parent_code + '+' + mod_str)",
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
        "        return self.code == other.code and self.modifiers == other.modifiers",
        "",
        "    def __hash__(self) -> int:",
        "        return hash((self.code, self.modifiers))",
        "",
        "    def __str__(self) -> str:",
        "        all_mods = sorted(",
        "            m.value if isinstance(m, Modifier) else m for m in self.modifiers",
        "        )",
        "        if all_mods:",
        '            return self.code + "+" + "+".join(all_mods)',
        "        return self.code",
        "",
        "    def __repr__(self) -> str:",
        "        if self.is_standard:",
        '            return f"Sport({str(self)!r})"',
        '        return f"Sport.parse({str(self)!r})"',
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
        "from open_sport_taxonomy._platform import GarminFitCode",
        "",
        "",
    ]

    # Strava
    strava = load_mapping("strava")
    lines.append(f'STRAVA_FALLBACK: str = "{strava["fallback"]}"')
    lines.append("")
    lines.append("STRAVA_MAPPINGS: dict[tuple[str, frozenset[str]], str] = {")
    for entry in strava["mappings"]:
        key_code = entry["ost"]
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
        key_code = entry["ost"]
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
        key_code = entry["ost"]
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

def generate_init(schema: dict) -> str:
    version = schema["version"]
    return f'''{HEADER}
from open_sport_taxonomy._modifier import Modifier
from open_sport_taxonomy._platform import GarminFitCode
from open_sport_taxonomy._sport import Sport

version = "{version}"

__all__ = ["GarminFitCode", "Modifier", "Sport", "version"]
'''


def _check_version_consistency(schema: dict) -> list[str]:
    """Check that version is consistent across schema.yaml and pyproject.toml."""
    import re

    errors = []
    schema_version = schema["version"]

    pyproject_path = ROOT / "pyproject.toml"
    pyproject_text = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject_text, re.MULTILINE)
    if match:
        pyproject_version = match.group(1)
        if schema_version != pyproject_version:
            errors.append(
                f"Version mismatch: schema.yaml has {schema_version!r}, "
                f"pyproject.toml has {pyproject_version!r}"
            )
    else:
        errors.append("Could not find version in pyproject.toml")

    return errors


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
        OUT_DIR / "__init__.py": generate_init(schema),
    }

    if args.check:
        stale = []
        for path, expected in files.items():
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                stale.append(path)

        version_errors = _check_version_consistency(schema)

        if stale or version_errors:
            for p in stale:
                print(f"STALE: {p.relative_to(ROOT)}")
            for e in version_errors:
                print(f"ERROR: {e}")
            print("\nRun 'uv run scripts/generate.py' to update.")
            sys.exit(1)
        else:
            print("All generated files are up to date.")
            print("Version is consistent across schema.yaml and pyproject.toml.")
    else:
        for path, content in files.items():
            path.write_text(content, encoding="utf-8")
            print(f"Generated {path.relative_to(ROOT)}")

        version_errors = _check_version_consistency(schema)
        if version_errors:
            for e in version_errors:
                print(f"WARNING: {e}")
        else:
            print(f"Version {schema['version']} is consistent.")


if __name__ == "__main__":
    main()
