"""Round-trip invariants for every v3 mapping file.

For every preferred entry in mappings/<platform>.yaml:

    encode(sport) == target
    decode(target) == sport

For every non-preferred entry (with non-null sport):

    decode(target) == sport          # one-way: synonyms decode to canonical

For every null-sport entry:

    decode(target) == fallback.decode

These properties are also enforced at generation time by scripts/generate.py
(validation rules 10–11 in docs/translation.md), but exercising them here
catches drift if the generated tables are edited or the algorithms change.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from open_sport_taxonomy import GarminFitCode, Sport
from open_sport_taxonomy.platforms import (
    apple_healthkit,
    garmin_fit,
    garmin_training_api,
    strava,
)

MAPPINGS_DIR = Path(__file__).resolve().parent.parent / "mappings"

PLATFORMS = {
    "garmin_fit": garmin_fit,
    "strava": strava,
    "apple_healthkit": apple_healthkit,
    "garmin_training_api": garmin_training_api,
}


def _load(platform: str) -> dict:
    return yaml.safe_load((MAPPINGS_DIR / f"{platform}.yaml").read_text())


def _runtime_target(platform: str, target):
    if platform == "garmin_fit":
        return GarminFitCode(target["sport"], target["sub_sport"])
    return target


def _decode(platform: str, target):
    runtime = PLATFORMS[platform]
    if platform == "garmin_fit":
        return runtime.decode(target["sport"], target["sub_sport"])
    return runtime.decode(target)


def _entry_id(platform: str, entry: dict) -> str:
    t = entry["target"]
    sport = entry.get("sport")
    if isinstance(t, dict):
        t_str = f"({t['sport']},{t['sub_sport']})"
    else:
        t_str = str(t)
    return f"{t_str}->{sport}"


def _params(platform: str, predicate):
    mapping = _load(platform)
    return [
        pytest.param(platform, entry, id=_entry_id(platform, entry))
        for entry in mapping["entries"]
        if predicate(entry)
    ]


def _is_preferred(entry):
    return entry.get("preferred", False)


def _is_non_preferred_annotated(entry):
    return entry.get("sport") is not None and not entry.get("preferred", False)


def _is_null(entry):
    return entry.get("sport") is None


@pytest.mark.parametrize(
    "platform, entry",
    [p for plat in PLATFORMS for p in _params(plat, _is_preferred)],
)
def test_preferred_round_trip(platform, entry):
    sport = Sport(entry["sport"])
    expected = _runtime_target(platform, entry["target"])
    assert PLATFORMS[platform].encode(sport) == expected
    assert _decode(platform, entry["target"]) == sport


@pytest.mark.parametrize(
    "platform, entry",
    [p for plat in PLATFORMS for p in _params(plat, _is_non_preferred_annotated)],
)
def test_non_preferred_decodes_to_canonical(platform, entry):
    """Synonyms decode to the canonical sport (one-way; encode is not asserted)."""
    sport = Sport(entry["sport"])
    assert _decode(platform, entry["target"]) == sport


@pytest.mark.parametrize(
    "platform, entry",
    [p for plat in PLATFORMS for p in _params(plat, _is_null)],
)
def test_null_decodes_to_fallback(platform, entry):
    expected = Sport(_load(platform)["fallback"]["decode"])
    assert _decode(platform, entry["target"]) == expected
