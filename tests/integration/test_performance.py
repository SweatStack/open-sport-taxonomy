"""Performance regression bounds.

These are not benchmarks for the sake of benchmarks. They exist to fail
CI if someone introduces an accidental algorithmic regression — for
example, an encode walk that becomes O(n²) in modifier count, or a
hidden import-time pathology in a hot path.

Baselines measured at the time of writing (Python 3.10, M2 Mac):

  - FIT       encode ~2 µs   decode <1 µs
  - Strava    encode ~4 µs   decode <1 µs
  - HealthKit encode ~4 µs   decode <1 µs
  - Training  encode ~4 µs   decode <1 µs

The 100 µs threshold gives ~25× headroom over the slowest observed
operation. The point is not to optimise — it is to detect order-of-
magnitude regressions. If a legitimate improvement reduces the
baseline, the threshold stays; if a legitimate change increases it,
the threshold rises with a comment in this file documenting why.

The benchmarks use ``pytest-benchmark`` for stable measurement
methodology (warm-up, multiple rounds, GC control).
"""

from __future__ import annotations

from open_sport_taxonomy import Sport
from open_sport_taxonomy.platforms import (
    apple_healthkit,
    garmin_fit,
    garmin_training_api,
    strava,
)

# Threshold in seconds. 100 microseconds = 1e-4 s.
THRESHOLD_S = 1e-4


# --------------------------------------------------------------------------
# Garmin FIT — struct target; exercises target_coarsening on decode misses.
# --------------------------------------------------------------------------


def test_garmin_fit_encode_under_threshold(benchmark) -> None:
    sport = Sport("cycling.road+stationary")
    result = benchmark(garmin_fit.encode, sport)
    assert benchmark.stats.stats.mean < THRESHOLD_S, (
        f"FIT encode mean {benchmark.stats.stats.mean * 1e6:.1f} us "
        f"exceeds threshold {THRESHOLD_S * 1e6:.0f} us"
    )
    assert result is not None  # sanity


def test_garmin_fit_decode_under_threshold(benchmark) -> None:
    result = benchmark(garmin_fit.decode, 2, 6)
    assert benchmark.stats.stats.mean < THRESHOLD_S
    assert result == Sport("cycling+stationary")


# --------------------------------------------------------------------------
# Strava — flat string target.
# --------------------------------------------------------------------------


def test_strava_encode_under_threshold(benchmark) -> None:
    sport = Sport("cycling+stationary+virtual")
    result = benchmark(strava.encode, sport)
    assert benchmark.stats.stats.mean < THRESHOLD_S
    assert result == "VirtualRide"


def test_strava_decode_under_threshold(benchmark) -> None:
    result = benchmark(strava.decode, "VirtualRide")
    assert benchmark.stats.stats.mean < THRESHOLD_S
    assert result == Sport("cycling+stationary+virtual")


# --------------------------------------------------------------------------
# Apple HealthKit — flat int target.
# --------------------------------------------------------------------------


def test_apple_healthkit_encode_under_threshold(benchmark) -> None:
    sport = Sport("cycling.road")
    result = benchmark(apple_healthkit.encode, sport)
    assert benchmark.stats.stats.mean < THRESHOLD_S
    assert result == 13


def test_apple_healthkit_decode_under_threshold(benchmark) -> None:
    result = benchmark(apple_healthkit.decode, 13)
    assert benchmark.stats.stats.mean < THRESHOLD_S
    assert result == Sport("cycling")


# --------------------------------------------------------------------------
# Garmin Training API — flat string target, small enum.
# --------------------------------------------------------------------------


def test_garmin_training_api_encode_under_threshold(benchmark) -> None:
    sport = Sport("cycling.road")
    result = benchmark(garmin_training_api.encode, sport)
    assert benchmark.stats.stats.mean < THRESHOLD_S
    assert result == "CYCLING"


def test_garmin_training_api_decode_under_threshold(benchmark) -> None:
    result = benchmark(garmin_training_api.decode, "CYCLING")
    assert benchmark.stats.stats.mean < THRESHOLD_S
    assert result == Sport("cycling")
