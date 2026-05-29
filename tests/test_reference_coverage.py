"""Reference coverage: validation rules 5 and 6 from docs/translation.md.

- Every target in mappings/<platform>.yaml must appear in
  reference/<platform>/targets.yaml.
- Every value in reference/<platform>/targets.yaml must have exactly one
  row in mappings/<platform>.yaml.

This is the structural rule that makes coverage oversights impossible:
the 0.4.0 bug (FIT mapping missing indoor_cycling, treadmill, indoor_rowing)
cannot recur because the loader refuses to operate on a mapping file that
omits any reference value.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
MAPPINGS_DIR = ROOT / "mappings"
REFERENCE_DIR = ROOT / "reference"

PLATFORM_REF = {
    "garmin_fit": "garmin-fit-sdk",
    "strava": "strava",
    "apple_healthkit": "apple-healthkit",
    "garmin_training_api": "garmin-training-api",
}


def _target_key(t):
    if isinstance(t, dict):
        return tuple(sorted(t.items()))
    return t


def _load_targets(platform):
    return yaml.safe_load(
        (REFERENCE_DIR / PLATFORM_REF[platform] / "targets.yaml").read_text()
    )["targets"]


def _load_mapping_entries(platform):
    return yaml.safe_load((MAPPINGS_DIR / f"{platform}.yaml").read_text())["entries"]


@pytest.mark.parametrize("platform", sorted(PLATFORM_REF))
def test_every_reference_target_has_a_row(platform):
    reference_keys = {_target_key(t) for t in _load_targets(platform)}
    mapping_keys = {_target_key(e["target"]) for e in _load_mapping_entries(platform)}
    missing = reference_keys - mapping_keys
    assert not missing, (
        f"{platform}: {len(missing)} reference target(s) have no mapping row: "
        f"{sorted(missing)[:5]}{'...' if len(missing) > 5 else ''}"
    )


@pytest.mark.parametrize("platform", sorted(PLATFORM_REF))
def test_every_mapping_row_is_a_legal_target(platform):
    reference_keys = {_target_key(t) for t in _load_targets(platform)}
    mapping_keys = {_target_key(e["target"]) for e in _load_mapping_entries(platform)}
    extras = mapping_keys - reference_keys
    assert not extras, (
        f"{platform}: {len(extras)} mapping row(s) reference unknown targets: "
        f"{sorted(extras)[:5]}{'...' if len(extras) > 5 else ''}"
    )


@pytest.mark.parametrize("platform", sorted(PLATFORM_REF))
def test_targets_are_unique_within_mapping(platform):
    entries = _load_mapping_entries(platform)
    seen = {}
    duplicates = []
    for i, e in enumerate(entries):
        k = _target_key(e["target"])
        if k in seen:
            duplicates.append((e["target"], i, seen[k]))
        else:
            seen[k] = i
    assert not duplicates, (
        f"{platform}: duplicate target rows: {duplicates[:3]}"
    )
