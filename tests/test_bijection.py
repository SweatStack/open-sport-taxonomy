"""Round-trip and bijection invariants for every platform mapping.

For each entry ``(ost, modifiers, target)`` in every mapping YAML:

    encode(Sport(ost, modifiers)) == target
    decode(target) == Sport(ost, modifiers)

These are the load-bearing invariants that make encode/decode safe to
extend. A YAML edit that breaks either fails this test.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from open_sport_taxonomy import GarminFitCode, Modifier, Sport
from open_sport_taxonomy.platforms import (
    apple_healthkit,
    garmin_fit,
    garmin_training_api,
    strava,
)

MAPPINGS_DIR = Path(__file__).resolve().parent.parent / "mappings"


def _load(name: str) -> list[dict]:
    return yaml.safe_load((MAPPINGS_DIR / f"{name}.yaml").read_text())["mappings"]


def _sport_from(entry: dict) -> Sport:
    code = entry["ost"]
    mods = entry.get("modifiers", [])
    if mods:
        return Sport(code, modifiers={Modifier(m) for m in mods})
    return Sport(code)


def _target_id(target):
    # Readable test ids without dumping the full dict for FIT.
    if isinstance(target, dict):
        return f"sport={target['sport']},sub_sport={target['sub_sport']}"
    return str(target)


def _params(platform_name: str):
    return [
        pytest.param(entry, id=f"{entry['ost']}->{_target_id(entry['target'])}")
        for entry in _load(platform_name)
    ]


class TestStrava:
    @pytest.mark.parametrize("entry", _params("strava"))
    def test_round_trip(self, entry):
        sport = _sport_from(entry)
        target = entry["target"]
        assert strava.encode(sport) == target
        assert strava.decode(target) == sport


class TestAppleHealthkit:
    @pytest.mark.parametrize("entry", _params("apple_healthkit"))
    def test_round_trip(self, entry):
        sport = _sport_from(entry)
        target = entry["target"]
        assert apple_healthkit.encode(sport) == target
        assert apple_healthkit.decode(target) == sport


class TestGarminTrainingApi:
    @pytest.mark.parametrize("entry", _params("garmin_training_api"))
    def test_round_trip(self, entry):
        sport = _sport_from(entry)
        target = entry["target"]
        assert garmin_training_api.encode(sport) == target
        assert garmin_training_api.decode(target) == sport


class TestGarminFit:
    @pytest.mark.parametrize("entry", _params("garmin_fit"))
    def test_round_trip(self, entry):
        sport = _sport_from(entry)
        target = entry["target"]
        expected_code = GarminFitCode(target["sport"], target["sub_sport"])
        assert garmin_fit.encode(sport) == expected_code
        assert garmin_fit.decode(target["sport"], target["sub_sport"]) == sport


class TestBijectionInvariant:
    """Constructing a Platform with a non-bijective mapping must fail."""

    def test_duplicate_target_raises(self):
        from open_sport_taxonomy._platform import Platform

        with pytest.raises(ValueError, match="not bijective"):
            Platform(
                mappings={
                    ("cycling", frozenset()): "Ride",
                    ("running", frozenset()): "Ride",
                },
                fallback="Workout",
            )
