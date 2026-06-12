"""Generate Python source files from schema.yaml and mapping files.

Run: uv run scripts/generate.py
Check: uv run scripts/generate.py --check

Inputs:
  - schema.yaml — the OST taxonomy (sports, modifiers).
  - mappings/<platform>.yaml — platform-keyed mapping files.
  - reference/<platform>/targets.yaml — authoritative legal-target enumeration.

Outputs:
  - src/open_sport_taxonomy/_modifier.py
  - src/open_sport_taxonomy/_sport.py
  - src/open_sport_taxonomy/_platforms.py
  - src/open_sport_taxonomy/__init__.py

Validation:
  All 13 validation rules from docs/translation.md are enforced here at
  generation time. A YAML file that violates any rule aborts the build —
  the package will not be regenerated until the data is fixed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema.yaml"
MAPPINGS_DIR = ROOT / "mappings"
REFERENCE_DIR = ROOT / "reference"
OUT_DIR = ROOT / "src" / "open_sport_taxonomy"

HEADER = "# Auto-generated from schema.yaml — do not edit.\n# Run: uv run scripts/generate.py\n"

PLATFORM_REF_DIR = {
    "garmin_fit": "garmin-fit-sdk",
    "strava": "strava",
    "apple_healthkit": "apple-healthkit",
    "garmin_training_api": "garmin-training-api",
    "wahoo": "wahoo",
    "polar": "polar",
    "suunto": "suunto",
}


def load_schema() -> dict:
    return yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_mapping(name: str) -> dict:
    return yaml.safe_load((MAPPINGS_DIR / f"{name}.yaml").read_text(encoding="utf-8"))


def load_targets(platform: str) -> list[Any]:
    ref_dir = REFERENCE_DIR / PLATFORM_REF_DIR[platform]
    return yaml.safe_load((ref_dir / "targets.yaml").read_text(encoding="utf-8"))["targets"]


def load_reference(*parts: str) -> dict:
    return yaml.safe_load(REFERENCE_DIR.joinpath(*parts).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Validation — rules 1–13 from docs/translation.md.
# ---------------------------------------------------------------------------


class ValidationError(Exception):
    pass


ALLOWED_TOP_KEYS = {
    "platform",
    "platform_version",
    "fallback",
    "target_coarsening",
    "entries",
}
ALLOWED_ENTRY_KEYS = {"target", "sport", "preferred", "encode_for"}
ALLOWED_FALLBACK_KEYS = {"encode", "decode"}


def target_key(t: Any) -> Any:
    """Hashable form of a target."""
    if isinstance(t, dict):
        return tuple(sorted(t.items()))
    return t


def parse_sport(
    raw: str, sport_codes: set[str], modifier_codes: set[str]
) -> tuple[str, frozenset[str]]:
    """Parse a sport string into (code, modifiers); enforce rule 6."""
    if not raw or "+" in raw[:1] or raw.endswith("+") or "++" in raw:
        raise ValidationError(f"malformed sport string: {raw!r}")
    parts = raw.split("+")
    code = parts[0]
    mods = parts[1:]
    if code not in sport_codes:
        raise ValidationError(
            f"sport code {code!r} is not in schema.yaml "
            f"(non-standard codes are forbidden in mapping files)"
        )
    for m in mods:
        if m not in modifier_codes:
            raise ValidationError(f"unknown modifier {m!r} in {raw!r}")
    if mods != sorted(mods):
        raise ValidationError(
            f"modifiers in {raw!r} must be alphabetically sorted ({'+'.join(sorted(mods))!r})"
        )
    return code, frozenset(mods)


def validate_mapping(
    platform: str,
    mapping: dict,
    targets: list[Any],
    sport_codes: set[str],
    modifier_codes: set[str],
) -> dict:
    """Run validation rules 1–13. Returns the canonicalized mapping on success.

    The returned dict is the input with one derived structure attached:
      - `_parsed_entries`: list of
        `(target, (code, mods) | None, preferred, [encode_for_key, ...])`, where each
        `encode_for_key` is a parsed `(code, mods)` from the entry's `encode_for`.
    """
    file_label = f"mappings/{platform}.yaml"

    # Rule 1: platform field.
    if mapping.get("platform") != platform:
        raise ValidationError(
            f"{file_label}: platform field {mapping.get('platform')!r} does not match filename"
        )
    if platform not in PLATFORM_REF_DIR:
        raise ValidationError(f"{file_label}: platform {platform!r} has no reference/ directory")

    # Rule 2: no unknown top-level keys.
    unknown_top = set(mapping) - ALLOWED_TOP_KEYS
    if unknown_top:
        raise ValidationError(f"{file_label}: unknown top-level keys: {sorted(unknown_top)}")

    # fallback structure.
    fb = mapping.get("fallback", {})
    if not isinstance(fb, dict):
        raise ValidationError(f"{file_label}: fallback must be a mapping")
    unknown_fb = set(fb) - ALLOWED_FALLBACK_KEYS
    if unknown_fb:
        raise ValidationError(f"{file_label}: unknown fallback keys: {sorted(unknown_fb)}")
    if "encode" not in fb:
        raise ValidationError(f"{file_label}: fallback.encode is required")
    if "decode" not in fb:
        raise ValidationError(f"{file_label}: fallback.decode is required")

    # entries structure.
    entries = mapping.get("entries")
    if not isinstance(entries, list):
        raise ValidationError(f"{file_label}: entries must be a list")
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            raise ValidationError(f"{file_label}: entries[{i}] must be a mapping")
        unknown_entry = set(e) - ALLOWED_ENTRY_KEYS
        if unknown_entry:
            raise ValidationError(
                f"{file_label}: entries[{i}] has unknown keys: {sorted(unknown_entry)}"
            )
        if "target" not in e:
            raise ValidationError(f"{file_label}: entries[{i}] missing target")
        if "sport" not in e:
            raise ValidationError(f"{file_label}: entries[{i}] missing sport")

    # Rule 3: targets unique within entries.
    seen: dict[Any, int] = {}
    for i, e in enumerate(entries):
        k = target_key(e["target"])
        if k in seen:
            raise ValidationError(
                f"{file_label}: entries[{i}] target {e['target']!r} duplicates entries[{seen[k]}]"
            )
        seen[k] = i

    # Rule 4: every target is in targets.yaml.
    legal_keys = {target_key(t) for t in targets}
    for i, e in enumerate(entries):
        if target_key(e["target"]) not in legal_keys:
            raise ValidationError(
                f"{file_label}: entries[{i}] target {e['target']!r} not in reference targets.yaml"
            )

    # Rule 5: every targets.yaml value has a row.
    entry_keys = {target_key(e["target"]) for e in entries}
    missing = sorted(t for t in legal_keys if t not in entry_keys)
    if missing:
        sample = missing[:5]
        raise ValidationError(
            f"{file_label}: {len(missing)} target(s) in targets.yaml have no row. "
            f"First few: {sample}. Run scripts/scaffold.py {platform} --update to scaffold."
        )

    # Rule 6: parse each non-null sport string (and any encode_for ancestors).
    # Each parsed entry is (target, parsed_sport | None, preferred, encode_for_keys).
    SportKey = tuple[str, frozenset[str]]
    parsed_entries: list[tuple[Any, SportKey | None, bool, list[SportKey]]] = []
    for i, e in enumerate(entries):
        sport_raw = e["sport"]
        preferred = bool(e.get("preferred", False))
        encode_for_raw = e.get("encode_for", []) or []
        if not isinstance(encode_for_raw, list):
            raise ValidationError(
                f"{file_label}: entries[{i}] encode_for must be a list, "
                f"got {type(encode_for_raw).__name__}"
            )

        if sport_raw is None:
            # Rule 8: preferred and encode_for forbidden when sport is null.
            if encode_for_raw:
                raise ValidationError(
                    f"{file_label}: entries[{i}] has sport: null but non-empty encode_for"
                )
            parsed_entries.append((e["target"], None, preferred, []))
            continue
        if not isinstance(sport_raw, str):
            raise ValidationError(
                f"{file_label}: entries[{i}] sport must be a string or null, "
                f"got {type(sport_raw).__name__}"
            )
        try:
            parsed = parse_sport(sport_raw, sport_codes, modifier_codes)
        except ValidationError as ex:
            raise ValidationError(f"{file_label}: entries[{i}] {ex}") from None

        # encode_for attaches to the canonical (preferred) encode home only.
        if encode_for_raw and not preferred:
            raise ValidationError(
                f"{file_label}: entries[{i}] has encode_for but is not preferred; "
                f"encode_for may only attach to the canonical (preferred) entry for a target"
            )
        encode_for_keys: list[SportKey] = []
        for a in encode_for_raw:
            if not isinstance(a, str):
                raise ValidationError(
                    f"{file_label}: entries[{i}] encode_for must contain strings, "
                    f"got {type(a).__name__}"
                )
            try:
                ef_key = parse_sport(a, sport_codes, modifier_codes)
            except ValidationError as ex:
                raise ValidationError(f"{file_label}: entries[{i}] encode_for {ex}") from None
            # Constraint: each encode_for code must be a STRICT ANCESTOR of the row's
            # sport. You may declare a precise target as the encode home for a broader
            # sport — never for an unrelated or finer one. (See docs/translation.md.)
            row_code = parsed[0]
            ef_code = ef_key[0]
            if not row_code.startswith(ef_code + "."):
                raise ValidationError(
                    f"{file_label}: entries[{i}] encode_for {a!r} is not a strict ancestor "
                    f"of sport {sport_raw!r}"
                )
            encode_for_keys.append(ef_key)
        parsed_entries.append((e["target"], parsed, preferred, encode_for_keys))

    # Rule 8: preferred forbidden when sport is null.
    for i, (_target, parsed, preferred, _aliases) in enumerate(parsed_entries):
        if parsed is None and preferred:
            raise ValidationError(f"{file_label}: entries[{i}] has sport: null but preferred: true")

    # Rule 7: every non-null sport has exactly ONE encode home — either a preferred
    # entry whose sport it is, or an encode_for mention. Never both, never neither,
    # never twice. Encode is many-to-one (several sports → one target), but each sport
    # encodes to exactly one target.
    home_count: dict[SportKey, int] = {}
    for _target, parsed, preferred, encode_for_keys in parsed_entries:
        if parsed is not None and preferred:
            home_count[parsed] = home_count.get(parsed, 0) + 1
        for a in encode_for_keys:
            home_count[a] = home_count.get(a, 0) + 1
    # Sports needing a home: every sport that appears as a decode result, plus every
    # encode_for ancestor (which appears only on the encode side).
    needs_home = {p for _, p, _, _ in parsed_entries if p is not None}
    needs_home |= {a for _, _, _, ef in parsed_entries for a in ef}
    for s in needs_home:
        c = home_count.get(s, 0)
        if c != 1:
            sport_str = _format_sport(s)
            raise ValidationError(
                f"{file_label}: sport {sport_str!r} has {c} encode homes "
                f"(preferred entries + encode_for mentions), expected exactly 1"
            )

    # Rule 12: target_coarsening reset rules name valid fields.
    coarsening = mapping.get("target_coarsening", []) or []
    if not isinstance(coarsening, list):
        raise ValidationError(f"{file_label}: target_coarsening must be a list")
    target_fields = _target_fields(targets)
    for i, rule in enumerate(coarsening):
        if not isinstance(rule, dict) or set(rule) != {"reset"}:
            raise ValidationError(
                f"{file_label}: target_coarsening[{i}] must be a dict with exactly one key "
                f"`reset`; got {rule!r}"
            )
        reset = rule["reset"]
        if not isinstance(reset, dict) or not reset:
            raise ValidationError(
                f"{file_label}: target_coarsening[{i}].reset must be a non-empty mapping"
            )
        unknown_fields = set(reset) - target_fields
        if unknown_fields:
            raise ValidationError(
                f"{file_label}: target_coarsening[{i}].reset names unknown target field(s) "
                f"{sorted(unknown_fields)}; valid fields are {sorted(target_fields)}"
            )

    # Rule 11: fallback.decode parses; equals sport of some preferred entry.
    try:
        fallback_decode_parsed = parse_sport(fb["decode"], sport_codes, modifier_codes)
    except ValidationError as ex:
        raise ValidationError(f"{file_label}: fallback.decode {ex}") from None
    preferred_sports = {p for _, p, pref, _ in parsed_entries if pref and p is not None}
    if fallback_decode_parsed not in preferred_sports:
        raise ValidationError(
            f"{file_label}: fallback.decode {fb['decode']!r} is not the `sport` of any "
            f"preferred entry; encode of the fallback would not round-trip"
        )

    mapping["_parsed_entries"] = parsed_entries
    return mapping


def _target_fields(targets: list[Any]) -> set[str]:
    """The set of named fields in target shape (empty for non-dict targets)."""
    if not targets:
        return set()
    sample = targets[0]
    if isinstance(sample, dict):
        return set(sample)
    return set()


def _format_sport(s: tuple[str, frozenset[str]]) -> str:
    code, mods = s
    if not mods:
        return code
    return code + "+" + "+".join(sorted(mods))


def validate_round_trips(platform: str, mapping: dict, runtime_platform: Any) -> None:
    """Rules 9–10, 13: round-trip per preferred entry; decode per non-preferred row;
    encode_for ancestors encode to their target.

    Requires the runtime Platform object built from the same data. Runs after
    code generation against the freshly imported module.
    """
    from open_sport_taxonomy._sport import Sport

    parsed = mapping["_parsed_entries"]
    file_label = f"mappings/{platform}.yaml"

    def _sport_from_key(key: tuple[str, frozenset[str]]) -> Any:
        code, mods = key
        return Sport(code) if not mods else Sport(code + "+" + "+".join(sorted(mods)))

    for i, (target, p, preferred, encode_for_keys) in enumerate(parsed):
        # Build runtime target value matching what generated tables use.
        rt_target = _runtime_target(platform, target)
        if p is None:
            # Decode should hit fallback.decode (rule respected by algorithm).
            sport = runtime_platform.decode(rt_target)
            if sport != runtime_platform._fallback_decode:
                raise ValidationError(
                    f"{file_label}: entries[{i}] sport: null but decode returned {sport!r}"
                )
            continue
        sport = _sport_from_key(p)
        decoded = runtime_platform.decode(rt_target)
        if decoded != sport:
            raise ValidationError(
                f"{file_label}: entries[{i}] decode({rt_target!r}) returned {decoded!r}, "
                f"expected {sport!r}"
            )
        if preferred:
            encoded = runtime_platform.encode(sport)
            if encoded != rt_target:
                raise ValidationError(
                    f"{file_label}: entries[{i}] encode({sport!r}) returned {encoded!r}, "
                    f"expected {rt_target!r}"
                )
        # encode_for invariant: each broader ancestor encodes to THIS target, while
        # decode(target) stays the canonical (preferred) sport above. Round-trip then
        # moves along the hierarchy — decode(encode(ancestor)) sharpens to the canonical
        # sub-sport (the dual of coarsening).
        for ef_key in encode_for_keys:
            ef_sport = _sport_from_key(ef_key)
            encoded = runtime_platform.encode(ef_sport)
            if encoded != rt_target:
                raise ValidationError(
                    f"{file_label}: entries[{i}] encode_for {ef_sport!r} encodes to "
                    f"{encoded!r}, expected {rt_target!r}"
                )


def _runtime_target(platform: str, target: Any) -> Any:
    """Convert a YAML-loaded target into its runtime form."""
    if platform == "garmin_fit":
        from open_sport_taxonomy._platform import GarminFitCode

        return GarminFitCode(target["sport"], target["sub_sport"])
    return target


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

    for entry in modifiers:
        name = entry["code"].upper()
        lines.append(f'    {name} = "{entry["code"]}"')
    lines.append("")

    lines.extend(
        [
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
        ]
    )

    lines.append("_LABELS: dict[str, str] = {")
    for entry in modifiers:
        lines.append(f'    "{entry["code"]}": "{entry["label"]}",')
    lines.append("}")
    lines.append("")
    lines.append("_GROUPS: dict[str, str] = {")
    for entry in modifiers:
        if "group" in entry:
            lines.append(f'    "{entry["code"]}": "{entry["group"]}",')
    lines.append("}")
    lines.append("")

    # validate_modifiers helper.
    lines.extend(
        [
            "",
            "def validate_modifiers(modifiers: frozenset) -> None:",
            '    """Raise ValueError if modifiers from the same group are combined."""',
            "    groups_seen: dict[str, str] = {}",
            "    for m in modifiers:",
            "        code = m.value if isinstance(m, Modifier) else m",
            "        g = _GROUPS.get(code)",
            "        if g is None:",
            "            continue",
            "        if g in groups_seen:",
            "            conflict = groups_seen[g]",
            "            raise ValueError(",
            '                f"Modifiers {conflict!r} and {code!r} "',
            '                f"conflict (same group: {g!r})"',
            "            )",
            "        groups_seen[g] = code",
            "",
        ]
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# _sport.py
# ---------------------------------------------------------------------------


def generate_sport(schema: dict) -> str:
    """Regenerate _sport.py preserving existing structure."""
    sports = schema["sports"]
    codes = sorted({s["code"] for s in sports})

    labels = {s["code"]: s["label"] for s in sports}
    parents: dict[str, str | None] = {}
    children: dict[str, list[str]] = {c: [] for c in codes}
    for c in codes:
        if "." in c:
            parent = c.rsplit(".", 1)[0]
            parents[c] = parent
            children[parent].append(c)
        else:
            parents[c] = None

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
    for c in codes:
        lines.append(f'    "{c}": "{labels[c]}",')
    lines.append("}")
    lines.append("")
    lines.append("_PARENTS: dict[str, str | None] = {")
    for c in codes:
        parent = parents[c]
        lines.append(f'    "{c}": {("None" if parent is None else repr(parent))},')
    lines.append("}")
    lines.append("")
    lines.append("_CHILDREN: dict[str, tuple[str, ...]] = {")
    for c in codes:
        kids = children[c]
        if kids:
            kids_str = ", ".join(f'"{k}"' for k in sorted(kids))
            lines.append(f'    "{c}": ({kids_str},),')
        else:
            lines.append(f'    "{c}": (),')
    lines.append("}")
    lines.append("")
    lines.append("")
    lines.append("def _split_encoded(raw: str) -> tuple[str, list[str]]:")
    lines.append('    """Split an encoded sport string into code and modifier tokens.')
    lines.append("")
    lines.append("    Raises ValueError on structural errors (empty, trailing +, double +).")
    lines.append('    """')
    lines.append("    if not isinstance(raw, str):")
    lines.append('        raise TypeError(f"Expected str, got {type(raw).__name__}")')
    lines.append("    if not raw:")
    lines.append('        raise ValueError("Sport code cannot be empty")')
    lines.append('    parts = raw.split("+")')
    lines.append('    if "" in parts:')
    lines.append('        raise ValueError(f"Invalid encoded string: {raw!r}")')
    lines.append("    return parts[0], parts[1:]")
    lines.append("")
    lines.append("")
    lines.append("def _is_subsport_code(child: str, parent: str) -> bool:")
    lines.append('    """True if child == parent or child is below parent in the dot hierarchy."""')
    lines.append("    return child == parent or child.startswith(parent + '.')")
    lines.append("")
    lines.append("")
    lines.append("@dataclass(frozen=True, init=False, slots=True)")
    lines.append("class Sport:")
    lines.append('    """A sport with optional modifiers.')
    lines.append("")
    lines.append("    Two ways to create Sport instances:")
    lines.append("")
    lines.append("        Sport(raw)        — strict, enforces the standard vocabulary")
    lines.append("        Sport.parse(raw)  — permissive, for external input")
    lines.append("")
    lines.append("    Or use class constants for known sports::")
    lines.append("")
    lines.append("        Sport.CYCLING_ROAD")
    lines.append("        Sport.RUNNING_TRAIL")
    lines.append('    """')
    lines.append("")
    lines.append("    code: str")
    lines.append("    modifiers: frozenset[str]")
    lines.append("")
    # Constructor.
    lines.extend(
        [
            "    def __init__(self, code: str, *, modifiers: Iterable[Modifier] | None = None) -> None:",
            "        if not isinstance(code, str):",
            '            raise TypeError(f"Expected str, got {type(code).__name__}")',
            '        if modifiers is not None and "+" in code:',
            "            raise ValueError(",
            '                "Cannot pass both an encoded string and modifiers keyword. "',
            "                \"Use either Sport('cycling.road+virtual') or \"",
            "                \"Sport('cycling.road', modifiers={Modifier.VIRTUAL}).\"",
            "            )",
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
            "        if not parsed_code:",
            '            raise ValueError("Sport code cannot be empty")',
            "        if parsed_code not in _LABELS:",
            '            raise ValueError(f"Unknown sport code: {parsed_code!r}")',
            "        validate_modifiers(parsed_modifiers)",
            '        object.__setattr__(self, "code", parsed_code)',
            '        object.__setattr__(self, "modifiers", frozenset(parsed_modifiers))',
            "",
            "    @classmethod",
            "    def parse(cls, raw: str) -> Sport:",
            '        """Parse a sport string, preserving unknown codes and modifiers.',
            "",
            "        Returns a standard or non-standard sport. Only structural errors",
            "        raise ValueError. No schema validation, no modifier group checks.",
            '        """',
            "        code, raw_modifiers = _split_encoded(raw)",
            "        mods: set[str] = set()",
            "        for m in raw_modifiers:",
            "            try:",
            "                mods.add(Modifier(m))",
            "            except ValueError:",
            "                mods.add(m)",
            "        sport = object.__new__(cls)",
            '        object.__setattr__(sport, "code", code)',
            '        object.__setattr__(sport, "modifiers", frozenset(mods))',
            "        return sport",
            "",
            "    def resolve(self) -> Sport:",
            '        """Resolve to the nearest standard sport."""',
            "        if self.is_standard:",
            "            return self",
            "        code = self.code",
            "        while code and code not in _LABELS:",
            '            dot = code.rfind(".")',
            '            code = code[:dot] if dot != -1 else ""',
            "        if not code:",
            '            code = "generic"',
            "        known: set[Modifier] = set()",
            "        for m in self.modifiers:",
            "            if isinstance(m, Modifier):",
            "                known.add(m)",
            "        return Sport(code, modifiers=known)",
            "",
            "    def is_subsport_of(self, other: Sport) -> bool:",
            '        """True if this sport is a more specific version of other."""',
            "        if not _is_subsport_code(self.code, other.code):",
            "            return False",
            "        if not other.modifiers.issubset(self.modifiers):",
            "            return False",
            "        return True",
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
            "    def _with_code(self, code: str) -> Sport:",
            '        """Return a sport with a different code but the same modifiers."""',
            "        if not self.modifiers:",
            "            return Sport.parse(code)",
            "        mod_str = '+'.join(",
            "            sorted(m.value if isinstance(m, Modifier) else m for m in self.modifiers)",
            "        )",
            "        return Sport.parse(code + '+' + mod_str)",
            "",
            "    @property",
            "    def parent(self) -> Sport | None:",
            '        """Parent sport, preserving modifiers."""',
            "        if self.code in _PARENTS:",
            "            parent_code = _PARENTS[self.code]",
            "        else:",
            '            dot = self.code.rfind(".")',
            "            parent_code = self.code[:dot] if dot != -1 else None",
            "        if parent_code is None:",
            "            return None",
            "        return self._with_code(parent_code)",
            "",
            "    @property",
            "    def disciplines(self) -> tuple[Sport, ...]:",
            '        """Direct child sports, preserving modifiers."""',
            "        children = _CHILDREN.get(self.code, ())",
            "        return tuple(self._with_code(c) for c in children)",
            "",
            "    @classmethod",
            "    def all(cls) -> list[Sport]:",
            '        """All standard sports defined in the schema."""',
            "        return [Sport(code) for code in _LABELS]",
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
        ]
    )
    for c in codes:
        name = c.replace(".", "_").upper()
        lines.append(f'Sport.{name} = Sport("{c}")  # type: ignore[attr-defined]')
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# _platforms.py — generated platform tables.
# ---------------------------------------------------------------------------


def _platform_var_prefix(platform: str) -> str:
    return platform.upper()


def _emit_target_literal(platform: str, target: Any) -> str:
    if platform == "garmin_fit":
        return f"GarminFitCode(sport={target['sport']}, sub_sport={target['sub_sport']})"
    if isinstance(target, str):
        return repr(target)
    return repr(target)


def _emit_sport_call(parsed: tuple[str, frozenset[str]]) -> str:
    code, mods = parsed
    if not mods:
        return f"Sport({code!r})"
    s = code + "+" + "+".join(sorted(mods))
    return f"Sport({s!r})"


def _emit_sport_key(parsed: tuple[str, frozenset[str]]) -> str:
    code, mods = parsed
    if not mods:
        return f"({code!r}, frozenset())"
    items = ", ".join(repr(m) for m in sorted(mods))
    return f"({code!r}, frozenset({{{items}}}))"


def _emit_target_field_value(v: Any) -> str:
    return repr(v) if not isinstance(v, int) or isinstance(v, bool) else str(v)


def _emit_coarsening(coarsening: list[dict]) -> str:
    if not coarsening:
        return "()"
    parts = []
    for rule in coarsening:
        reset = rule["reset"]
        items = ", ".join(f"{k!r}: {v!r}" for k, v in reset.items())
        parts.append(f'{{"reset": {{{items}}}}}')
    return "(" + ", ".join(parts) + ",)"


def generate_platforms(schema: dict, validated: dict[str, dict]) -> str:
    """Emit _platforms.py with v3 tables.

    `validated[platform]` is the canonicalized mapping (with `_parsed_entries`)
    returned by `validate_mapping`.
    """
    lines = [
        HEADER,
        "from __future__ import annotations",
        "",
        "from open_sport_taxonomy._platform import GarminFitCode",
        "from open_sport_taxonomy._sport import Sport",
        "",
    ]

    for platform in sorted(validated):
        mapping = validated[platform]
        prefix = _platform_var_prefix(platform)
        entries = mapping["_parsed_entries"]
        fb = mapping["fallback"]
        coarsening = mapping.get("target_coarsening", []) or []

        lines.append("")
        lines.append(f"# ---- {platform} ".ljust(76, "-"))
        lines.append("")
        lines.append(f"{prefix}_FALLBACK_ENCODE = {_emit_target_literal(platform, fb['encode'])}")
        lines.append(f"{prefix}_FALLBACK_DECODE: Sport = Sport({fb['decode']!r})")
        lines.append("")

        # entries_by_target (decode table — one sport per target)
        lines.append(f"{prefix}_ENTRIES_BY_TARGET: dict = {{")
        for target, parsed, preferred, _ef in entries:
            target_repr = _emit_target_literal(platform, target)
            sport_repr = "None" if parsed is None else _emit_sport_call(parsed)
            lines.append(f"    {target_repr}: ({sport_repr}, {preferred}),")
        lines.append("}")
        lines.append("")

        # preferred_index (encode table — many sports may map to one target via
        # encode_for; the canonical preferred sport plus each broader ancestor).
        lines.append(f"{prefix}_PREFERRED_INDEX: dict = {{")
        for target, parsed, preferred, encode_for_keys in entries:
            target_repr = _emit_target_literal(platform, target)
            if preferred and parsed is not None:
                lines.append(f"    {_emit_sport_key(parsed)}: {target_repr},")
            for ef_key in encode_for_keys:
                lines.append(f"    {_emit_sport_key(ef_key)}: {target_repr},")
        lines.append("}")
        lines.append("")

        # target_coarsening
        lines.append(f"{prefix}_TARGET_COARSENING: tuple = {_emit_coarsening(coarsening)}")

    # FIT enum reference tables (unchanged behavior, used by GarminFitCode).
    fit_sports = load_reference("garmin-fit-sdk", "sports.yaml")["cases"]
    fit_sub_sports = load_reference("garmin-fit-sdk", "sub_sports.yaml")["cases"]

    lines.append("")
    lines.append("# ---- FIT enum reference tables ".ljust(76, "-"))
    lines.append("")
    lines.append("FIT_SPORT_IDS: dict[str, int] = {")
    for case in fit_sports:
        lines.append(f'    "{case["name"]}": {case["value"]},')
    lines.append("}")
    lines.append("")
    lines.append("FIT_SPORT_NAMES: dict[int, str] = {v: k for k, v in FIT_SPORT_IDS.items()}")
    lines.append("")
    lines.append("FIT_SUB_SPORT_IDS: dict[str, int] = {")
    for case in fit_sub_sports:
        lines.append(f'    "{case["name"]}": {case["value"]},')
    lines.append("}")
    lines.append("")
    lines.append(
        "FIT_SUB_SPORT_NAMES: dict[int, str] = {v: k for k, v in FIT_SUB_SPORT_IDS.items()}"
    )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# __init__.py
# ---------------------------------------------------------------------------


def generate_init(schema: dict) -> str:
    # Two independent versions (see plans/023):
    #   - `version`: the installed PACKAGE release, read from distribution
    #     metadata at runtime (single source: pyproject.toml).
    #   - `taxonomy_version`: the SPEC version — the vocabulary of sports +
    #     modifiers and the OST string format (single source: schema.yaml).
    taxonomy_version = schema["version"]
    return f'''{HEADER}
from importlib.metadata import PackageNotFoundError, version as _dist_version

from open_sport_taxonomy._modifier import Modifier
from open_sport_taxonomy._platform import GarminFitCode
from open_sport_taxonomy._sport import Sport

try:
    version = _dist_version("open-sport-taxonomy")
except PackageNotFoundError:  # running from a source tree without an install
    version = "0+unknown"

taxonomy_version = "{taxonomy_version}"

__all__ = ["GarminFitCode", "Modifier", "Sport", "taxonomy_version", "version"]
'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Python source from schema and mappings.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check that generated files are up to date (exit 1 if stale).",
    )
    args = parser.parse_args()

    schema = load_schema()
    sport_codes = {s["code"] for s in schema["sports"]}
    modifier_codes = {m["code"] for m in schema["modifiers"]}

    # Validate every mapping file (rules 1–8, 11–12).
    validated: dict[str, dict] = {}
    for platform in PLATFORM_REF_DIR:
        mapping = load_mapping(platform)
        targets = load_targets(platform)
        try:
            validate_mapping(platform, mapping, targets, sport_codes, modifier_codes)
        except ValidationError as ex:
            print(f"ERROR: {ex}")
            return 1
        validated[platform] = mapping

    files = {
        OUT_DIR / "_modifier.py": generate_modifier(schema),
        OUT_DIR / "_sport.py": generate_sport(schema),
        OUT_DIR / "_platforms.py": generate_platforms(schema, validated),
        OUT_DIR / "__init__.py": generate_init(schema),
    }

    if args.check:
        stale = [
            p for p, e in files.items() if not p.exists() or p.read_text(encoding="utf-8") != e
        ]
        if stale:
            for p in stale:
                print(f"STALE: {p.relative_to(ROOT)}")
            print("\nRun 'uv run scripts/generate.py' to update.")
            return 1
        print("All generated files are up to date.")
        return 0

    for path, content in files.items():
        path.write_text(content, encoding="utf-8")
        print(f"Generated {path.relative_to(ROOT)}")

    # Rules 9–10, 13: round-trip validation against the freshly generated runtime.
    # Re-import the module to pick up the new file.
    import importlib

    import open_sport_taxonomy._platforms

    importlib.reload(open_sport_taxonomy._platforms)

    from open_sport_taxonomy._platform import Platform

    pkg = importlib.import_module("open_sport_taxonomy._platforms")
    for platform in PLATFORM_REF_DIR:
        prefix = _platform_var_prefix(platform)
        rt = Platform(
            entries_by_target=getattr(pkg, f"{prefix}_ENTRIES_BY_TARGET"),
            preferred_index=getattr(pkg, f"{prefix}_PREFERRED_INDEX"),
            fallback_encode=getattr(pkg, f"{prefix}_FALLBACK_ENCODE"),
            fallback_decode=getattr(pkg, f"{prefix}_FALLBACK_DECODE"),
            target_coarsening=getattr(pkg, f"{prefix}_TARGET_COARSENING"),
        )
        try:
            validate_round_trips(platform, validated[platform], rt)
        except ValidationError as ex:
            print(f"ERROR: {ex}")
            return 1
        print(f"  {platform}: round-trip ok")

    print(f"Taxonomy (spec) version: {schema['version']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
