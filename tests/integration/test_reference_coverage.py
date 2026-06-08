"""Reference-coverage invariants — runtime defense-in-depth.

The same invariants are enforced at *generation* time by
``scripts/generate.py`` validation rules 4, 5, and 6. These runtime
tests are a defense-in-depth check that catches the case where the
generated ``_platforms.py`` is somehow stale or hand-edited (someone
bypassed the generator).

Each test iterates over all seven platforms internally and surfaces the
offending platform name in its failure message — one test per invariant,
not per platform.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MAPPINGS_DIR = ROOT / "mappings"
REFERENCE_DIR = ROOT / "reference"

PLATFORMS = {
    "garmin_fit": "garmin-fit-sdk",
    "strava": "strava",
    "apple_healthkit": "apple-healthkit",
    "garmin_training_api": "garmin-training-api",
    "wahoo": "wahoo",
    "polar": "polar",
    "suunto": "suunto",
}


def _target_key(t):
    """Hashable form of a target value (dicts become sorted-item tuples)."""
    if isinstance(t, dict):
        return tuple(sorted(t.items()))
    return t


def _load_reference_targets(platform: str) -> set:
    path = REFERENCE_DIR / PLATFORMS[platform] / "targets.yaml"
    return {_target_key(t) for t in yaml.safe_load(path.read_text())["targets"]}


def _load_mapping_target_keys(platform: str) -> list:
    """Return all target keys from mappings/<platform>.yaml, preserving duplicates."""
    path = MAPPINGS_DIR / f"{platform}.yaml"
    return [_target_key(e["target"]) for e in yaml.safe_load(path.read_text())["entries"]]


def test_every_reference_target_has_a_row():
    """Validation rule 6: every legal target in targets.yaml has a mapping row."""
    failures = []
    for platform in sorted(PLATFORMS):
        ref = _load_reference_targets(platform)
        mapped = set(_load_mapping_target_keys(platform))
        missing = ref - mapped
        if missing:
            sample = sorted(missing)[:3]
            failures.append(f"  {platform}: {len(missing)} missing, e.g. {sample}")
    assert not failures, "Reference targets without mapping rows:\n" + "\n".join(failures)


def test_every_mapping_row_is_a_legal_target():
    """Validation rule 5: every mapping row refers to a target in targets.yaml."""
    failures = []
    for platform in sorted(PLATFORMS):
        ref = _load_reference_targets(platform)
        mapped = set(_load_mapping_target_keys(platform))
        extras = mapped - ref
        if extras:
            sample = sorted(extras)[:3]
            failures.append(f"  {platform}: {len(extras)} extras, e.g. {sample}")
    assert not failures, "Mapping rows referencing unknown targets:\n" + "\n".join(failures)


def test_targets_are_unique_within_each_mapping():
    """Validation rule 4: every mapping target appears in at most one row."""
    failures = []
    for platform in sorted(PLATFORMS):
        keys = _load_mapping_target_keys(platform)
        seen = set()
        duplicates = []
        for k in keys:
            if k in seen:
                duplicates.append(k)
            seen.add(k)
        if duplicates:
            failures.append(f"  {platform}: duplicate targets {sorted(duplicates)[:3]}")
    assert not failures, "Duplicate targets in mapping files:\n" + "\n".join(failures)
