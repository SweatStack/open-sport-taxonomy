# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///

"""Lint and format schema.yaml.

Usage:
    uv run scripts/lint.py          # check only, exit 1 if issues found
    uv run scripts/lint.py --fix    # fix ordering in place
"""

import sys
from pathlib import Path

import yaml

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema.yaml"


def load_schema():
    return yaml.safe_load(SCHEMA_PATH.read_text())


def check_orphans(entries):
    """Check that every child code has a parent entry."""
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
    """Check that entries are sorted alphabetically by code."""
    codes = [e["code"] for e in entries]
    expected = sorted(codes)
    errors = []
    for i, (actual, exp) in enumerate(zip(codes, expected)):
        if actual != exp:
            errors.append(f"{section}: {actual!r} should come after {exp!r}")
            break
    if codes != expected:
        errors.append(f"{section}: not sorted alphabetically")
    return errors


def sort_entries(entries):
    """Return entries sorted alphabetically by code, preserving all fields."""
    return sorted(entries, key=lambda e: e["code"])


def write_schema(schema):
    """Write schema.yaml preserving the structure."""
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


def main():
    fix = "--fix" in sys.argv
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
        # Re-check for orphans (sorting doesn't fix those)
        remaining = check_orphans(schema["sports"])
        if remaining:
            for e in remaining:
                print(f"error: {e}")
            print("fixed: sort order")
            print(f"{len(remaining)} error(s) remaining (fix manually)")
            return 1
        print("fixed: schema.yaml")
        return 0

    for e in errors:
        print(f"error: {e}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
