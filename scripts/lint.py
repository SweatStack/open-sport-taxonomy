# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///

"""Lint schema.yaml and mappings/<platform>.yaml.

The mapping lint defers to scripts/generate.py — running generate.py
with --check validates the v3 mapping files against all 13 rules in
docs/translation.md and confirms the generated Python is up to date.
This script wraps that plus schema.yaml's own ordering/orphan checks.

Usage:
    uv run scripts/lint.py          # check only, exit 1 if issues found
    uv run scripts/lint.py --fix    # auto-fix what can be fixed (schema sort order)

Run in CI to catch:
  - schema.yaml ordering or orphan issues.
  - mapping files violating any format v3 rule.
  - generated Python out of sync with YAML inputs.
  - build_reference scripts out of sync with reference/*/targets.yaml.
"""

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema.yaml"


# --------------------------------------------------------------------------
# schema.yaml lint — unchanged from v1.
# --------------------------------------------------------------------------


def load_schema():
    return yaml.safe_load(SCHEMA_PATH.read_text())


def check_orphans(entries):
    codes = {e["code"] for e in entries}
    errors = []
    for code in sorted(codes):
        parts = code.split(".")
        for i in range(1, len(parts)):
            parent = ".".join(parts[:i])
            if parent not in codes:
                errors.append(f"orphan: {code!r} has no parent {parent!r}")
    return errors


def check_order(entries, section):
    codes = [e["code"] for e in entries]
    expected = sorted(codes)
    errors = []
    if codes != expected:
        errors.append(f"{section}: not sorted alphabetically")
    return errors


def sort_entries(entries):
    return sorted(entries, key=lambda e: e["code"])


def write_schema(schema):
    lines = [
        "# OpenSportTaxonomy — https://github.com/sweatstack/open-sport-taxonomy",
        "",
        f'version: "{schema["version"]}"',
        "",
        "sports:",
    ]
    for entry in schema["sports"]:
        lines.append("")
        lines.append(f"  - code: {entry['code']}")
        lines.append(f"    label: {entry['label']}")
    lines.append("")
    lines.append("modifiers:")
    for entry in schema["modifiers"]:
        lines.append("")
        lines.append(f"  - code: {entry['code']}")
        if "group" in entry:
            lines.append(f"    group: {entry['group']}")
        lines.append(f"    label: {entry['label']}")
    lines.append("")
    SCHEMA_PATH.write_text("\n".join(lines))


def lint_schema(fix: bool) -> int:
    schema = load_schema()
    sports = schema.get("sports", [])
    modifiers = schema.get("modifiers", [])

    errors = []
    errors.extend(check_orphans(sports))
    errors.extend(check_order(sports, "sports"))
    errors.extend(check_order(modifiers, "modifiers"))

    if not errors:
        print("schema.yaml: ok")
        return 0

    if fix:
        schema["sports"] = sort_entries(sports)
        schema["modifiers"] = sort_entries(modifiers)
        write_schema(schema)
        remaining = check_orphans(schema["sports"])
        if remaining:
            for e in remaining:
                print(f"schema.yaml error: {e}")
            print(f"schema.yaml: fixed sort order; {len(remaining)} error(s) remain")
            return 1
        print("schema.yaml: fixed")
        return 0

    for e in errors:
        print(f"schema.yaml error: {e}")
    return 1


# --------------------------------------------------------------------------
# Mapping + generated-code lint via scripts/generate.py --check.
# --------------------------------------------------------------------------


def lint_mappings() -> int:
    """Mapping validation is implemented in generate.py (validation rules 1–13).

    `generate.py --check` runs the same validator used during code generation
    and confirms the generated Python is in sync. Any v3 violation in a
    mapping file (unknown keys, missing rows, round-trip break, etc.) fails
    here.
    """
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"],
        capture_output=True,
        text=True,
    )
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return result.returncode


# --------------------------------------------------------------------------
# build_reference idempotency.
# --------------------------------------------------------------------------

BUILD_SCRIPTS = [
    ("scripts/build_reference/garmin_fit.py", "reference/garmin-fit-sdk/targets.yaml"),
    ("scripts/build_reference/strava.py", "reference/strava/targets.yaml"),
    ("scripts/build_reference/apple_healthkit.py", "reference/apple-healthkit/targets.yaml"),
    ("scripts/build_reference/garmin_training_api.py", "reference/garmin-training-api/targets.yaml"),
]


def lint_reference_drift() -> int:
    """Each build_reference script must reproduce its targets.yaml byte-for-byte."""
    errors = []
    for script, target in BUILD_SCRIPTS:
        target_path = ROOT / target
        before = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
        subprocess.run(
            [sys.executable, str(ROOT / script)],
            check=True,
            capture_output=True,
            cwd=str(ROOT),
        )
        after = target_path.read_text(encoding="utf-8")
        if before != after:
            errors.append(
                f"{target}: changed when running {script}. "
                f"Reference data is out of sync — commit the regenerated file."
            )
    if errors:
        for e in errors:
            print(f"reference drift error: {e}")
        return 1
    print("reference targets.yaml: ok")
    return 0


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main():
    fix = "--fix" in sys.argv

    rc = 0
    rc |= lint_schema(fix)
    rc |= lint_reference_drift()
    rc |= lint_mappings()
    return rc


if __name__ == "__main__":
    sys.exit(main())
