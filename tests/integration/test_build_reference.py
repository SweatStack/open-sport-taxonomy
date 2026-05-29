"""Idempotency of build_reference scripts.

Running each platform's build_reference script must reproduce the committed
reference/<platform>/targets.yaml byte-for-byte. CI runs this to catch drift
between the upstream source data and the committed snapshot.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

PLATFORM_BUILD = {
    "garmin_fit": (
        "scripts/build_reference/garmin_fit.py",
        "reference/garmin-fit-sdk/targets.yaml",
    ),
    "strava": ("scripts/build_reference/strava.py", "reference/strava/targets.yaml"),
    "apple_healthkit": (
        "scripts/build_reference/apple_healthkit.py",
        "reference/apple-healthkit/targets.yaml",
    ),
    "garmin_training_api": (
        "scripts/build_reference/garmin_training_api.py",
        "reference/garmin-training-api/targets.yaml",
    ),
}


@pytest.mark.parametrize("platform", sorted(PLATFORM_BUILD))
def test_build_reference_is_idempotent(platform, tmp_path):
    script_rel, target_rel = PLATFORM_BUILD[platform]
    target_path = ROOT / target_rel
    expected = target_path.read_text(encoding="utf-8")

    subprocess.run(
        [sys.executable, str(ROOT / script_rel)],
        check=True,
        cwd=str(ROOT),
    )
    actual = target_path.read_text(encoding="utf-8")
    assert actual == expected, (
        f"Running {script_rel} changed {target_rel}. "
        f"Reference data may be out of sync — re-run the build script and commit."
    )
