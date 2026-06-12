"""Loader/validator tests for format v4 (rules 1–13 in docs/translation.md).

The validator lives in scripts/generate.py — these tests construct
synthetic mappings and assert the validator rejects each kind of
violation. Run via:

    uv run python -m pytest tests/test_loader.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_generate_module():
    """Import scripts/generate.py as a module (it has no __init__.py)."""
    spec = importlib.util.spec_from_file_location("generate", ROOT / "scripts" / "generate.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate"] = module
    spec.loader.exec_module(module)
    return module


generate = _load_generate_module()
SPORT_CODES = {
    "cycling",
    "cycling.road",
    "cycling.cyclocross",
    "generic",
    "running",
    "running.road",
    "rowing",
    "swimming",
    "walking",
}
MODIFIER_CODES = {"stationary", "virtual", "race", "assisted", "commute"}


def _minimal_valid_mapping(extras=None):
    """The smallest valid mapping for testing."""
    base = {
        "platform": "garmin_fit",
        "platform_version": "test",
        "fallback": {
            "encode": {"sport": 0, "sub_sport": 0},
            "decode": "generic",
        },
        "target_coarsening": [{"reset": {"sub_sport": 0}}],
        "entries": [
            {
                "target": {"sport": 0, "sub_sport": 0},
                "sport": "generic",
                "preferred": True,
            },
            {
                "target": {"sport": 2, "sub_sport": 0},
                "sport": "cycling",
                "preferred": True,
            },
        ],
    }
    if extras:
        base.update(extras)
    return base


def _minimal_targets():
    return [
        {"sport": 0, "sub_sport": 0},
        {"sport": 2, "sub_sport": 0},
    ]


def _validate(mapping, targets=None, platform="garmin_fit"):
    return generate.validate_mapping(
        platform,
        mapping,
        targets or _minimal_targets(),
        SPORT_CODES,
        MODIFIER_CODES,
    )


class TestSmoke:
    """A minimal valid mapping passes all 13 validation rules."""

    def test_minimal_valid_mapping_passes(self):
        # Defense-in-depth against a regression where one rule's "pass"
        # condition is implemented incorrectly — if any rule's positive
        # branch is broken, the minimal mapping will fail to validate.
        _validate(_minimal_valid_mapping())


class TestRule1PlatformField:
    def test_platform_mismatch_rejected(self):
        # Filename says "garmin_fit" but the field says "strava".
        m = _minimal_valid_mapping({"platform": "strava"})
        with pytest.raises(generate.ValidationError, match="platform"):
            _validate(m, platform="garmin_fit")


class TestRule2UnknownKeys:
    def test_top_level_unknown_rejected(self):
        m = _minimal_valid_mapping({"unknown_key": "x"})
        with pytest.raises(generate.ValidationError, match="unknown_key"):
            _validate(m)

    def test_entry_unknown_rejected(self):
        m = _minimal_valid_mapping()
        m["entries"][0]["unknown"] = "x"
        with pytest.raises(generate.ValidationError, match="unknown"):
            _validate(m)


class TestRule3UniqueTargets:
    def test_duplicate_target_rejected(self):
        m = _minimal_valid_mapping()
        m["entries"].append(
            {
                "target": {"sport": 0, "sub_sport": 0},  # duplicates entry[0]
                "sport": "cycling",
                "preferred": False,
            }
        )
        with pytest.raises(generate.ValidationError, match="duplicate"):
            _validate(m)


class TestRule4LegalTargets:
    def test_unknown_target_rejected(self):
        m = _minimal_valid_mapping()
        m["entries"].append(
            {
                "target": {"sport": 99, "sub_sport": 99},
                "sport": None,
            }
        )
        with pytest.raises(generate.ValidationError, match="not in reference"):
            _validate(m)


class TestRule5Coverage:
    def test_missing_target_rejected(self):
        m = _minimal_valid_mapping()
        # Drop entry[1] so target (2, 0) becomes uncovered.
        m["entries"].pop()
        with pytest.raises(generate.ValidationError, match=r"target.*no row"):
            _validate(m)


class TestRule6SportString:
    def test_non_standard_code_rejected(self):
        m = _minimal_valid_mapping()
        m["entries"][0]["sport"] = "paragliding"
        with pytest.raises(generate.ValidationError, match="not in schema"):
            _validate(m)

    def test_unknown_modifier_rejected(self):
        m = _minimal_valid_mapping()
        m["entries"][1]["sport"] = "cycling+xyz"
        with pytest.raises(generate.ValidationError, match="unknown modifier"):
            _validate(m)

    def test_unsorted_modifiers_rejected(self):
        m = _minimal_valid_mapping()
        m["entries"][1]["sport"] = "cycling+virtual+race"  # should be race+virtual
        with pytest.raises(generate.ValidationError, match="alphabetically sorted"):
            _validate(m)


class TestRule7OneEncodeHomePerSport:
    def test_two_preferred_same_sport_rejected(self):
        m = _minimal_valid_mapping()
        m["entries"].append(
            {
                "target": {"sport": 0, "sub_sport": 0},
                "sport": "cycling",
                "preferred": True,  # second preferred for cycling
            }
        )
        # First trigger: duplicate target. Skip — adjust to a new target.
        targets = [*_minimal_targets(), {"sport": 2, "sub_sport": 7}]
        m["entries"][-1]["target"] = {"sport": 2, "sub_sport": 7}
        with pytest.raises(generate.ValidationError, match="preferred entries"):
            _validate(m, targets=targets)

    def test_zero_preferred_for_annotated_sport_rejected(self):
        m = _minimal_valid_mapping()
        m["entries"][1]["preferred"] = False  # cycling now has no preferred row
        with pytest.raises(generate.ValidationError, match="preferred entries"):
            _validate(m)


class TestRule8NullCannotBePreferred:
    def test_null_sport_with_preferred_rejected(self):
        m = _minimal_valid_mapping()
        targets = [*_minimal_targets(), {"sport": 2, "sub_sport": 7}]
        m["entries"].append(
            {
                "target": {"sport": 2, "sub_sport": 7},
                "sport": None,
                "preferred": True,
            }
        )
        with pytest.raises(generate.ValidationError, match=r"null.*preferred"):
            _validate(m, targets=targets)


class TestRule11FallbackDecodeRoundTrips:
    def test_fallback_not_in_preferred_rejected(self):
        m = _minimal_valid_mapping()
        m["fallback"]["decode"] = "running"  # no preferred entry for running
        with pytest.raises(generate.ValidationError, match="not the `sport`"):
            _validate(m)


class TestRule12CoarseningFields:
    def test_unknown_reset_field_rejected(self):
        m = _minimal_valid_mapping()
        m["target_coarsening"] = [{"reset": {"unknown_field": 0}}]
        with pytest.raises(generate.ValidationError, match="unknown target field"):
            _validate(m)

    def test_non_reset_rule_kind_rejected(self):
        m = _minimal_valid_mapping()
        m["target_coarsening"] = [{"unknown_rule": {}}]
        with pytest.raises(generate.ValidationError, match="reset"):
            _validate(m)


class TestRule13EncodeFor:
    """encode_for: decode-precise, encode many-to-one (rules 8, 9, 14)."""

    def _road_with_encode_for(self, **overrides):
        # entry[1] is 2/0 → cycling (preferred). Recast it as the canonical
        # road row with bare `cycling` collapsing onto it via encode_for.
        m = _minimal_valid_mapping()
        m["entries"][1]["sport"] = "cycling.road"
        m["entries"][1]["encode_for"] = ["cycling"]
        m["entries"][1].update(overrides)
        return m

    def test_valid_encode_for_passes(self):
        # cycling.road decodes at 2/0; bare cycling encodes there too. Both have
        # exactly one encode home, cycling is a strict ancestor of cycling.road.
        _validate(self._road_with_encode_for())

    def test_encode_for_non_ancestor_rejected(self):
        m = self._road_with_encode_for(encode_for=["running"])
        with pytest.raises(generate.ValidationError, match="strict ancestor"):
            _validate(m)

    def test_encode_for_on_non_preferred_rejected(self):
        m = self._road_with_encode_for(preferred=False)
        with pytest.raises(generate.ValidationError, match="not preferred"):
            _validate(m)

    def test_encode_for_on_null_sport_rejected(self):
        m = _minimal_valid_mapping()
        targets = [*_minimal_targets(), {"sport": 2, "sub_sport": 7}]
        m["entries"].append(
            {
                "target": {"sport": 2, "sub_sport": 7},
                "sport": None,
                "encode_for": ["cycling"],
            }
        )
        with pytest.raises(generate.ValidationError, match="encode_for"):
            _validate(m, targets=targets)

    def test_sport_with_two_encode_homes_rejected(self):
        # bare cycling is both an encode_for target (2/0) AND a preferred row (2/7).
        m = self._road_with_encode_for()
        targets = [*_minimal_targets(), {"sport": 2, "sub_sport": 7}]
        m["entries"].append(
            {
                "target": {"sport": 2, "sub_sport": 7},
                "sport": "cycling",
                "preferred": True,
            }
        )
        with pytest.raises(generate.ValidationError, match="encode homes"):
            _validate(m, targets=targets)
