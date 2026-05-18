# Auto-generated from schema.yaml — do not edit.
# Run: uv run scripts/generate.py

from __future__ import annotations

from typing import Any

from open_sport_taxonomy._platform import GarminFitCode


STRAVA_FALLBACK: str = "Workout"

STRAVA_MAPPINGS: dict[tuple[str, frozenset[str]], str] = {
    ("cycling", frozenset()): "Ride",
    ("cycling.cyclocross", frozenset()): "Ride",
    ("cycling.gravel", frozenset()): "GravelRide",
    ("cycling.mountain", frozenset()): "MountainBikeRide",
    ("cycling.mountain", frozenset({"assisted"})): "EMountainBikeRide",
    ("cycling.road", frozenset()): "Ride",
    ("cycling.road", frozenset({"assisted"})): "EBikeRide",
    ("cycling.road", frozenset({"virtual"})): "VirtualRide",
    ("cycling.time_trial", frozenset()): "Ride",
    ("cycling.track", frozenset()): "Ride",
    ("generic", frozenset()): "Workout",
    ("rowing", frozenset()): "Rowing",
    ("rowing", frozenset({"virtual"})): "VirtualRow",
    ("running", frozenset()): "Run",
    ("running.road", frozenset()): "Run",
    ("running.road", frozenset({"virtual"})): "VirtualRun",
    ("running.track", frozenset()): "Run",
    ("running.trail", frozenset()): "TrailRun",
    ("swimming", frozenset()): "Swim",
    ("swimming.open_water", frozenset()): "Swim",
    ("swimming.pool", frozenset()): "Swim",
    ("walking", frozenset()): "Walk",
    ("walking.hiking", frozenset()): "Hike",
    ("xc_skiing", frozenset()): "NordicSki",
    ("xc_skiing.backcountry", frozenset()): "BackcountrySki",
    ("xc_skiing.classic", frozenset()): "NordicSki",
    ("xc_skiing.roller", frozenset()): "RollerSki",
    ("xc_skiing.roller.classic", frozenset()): "RollerSki",
    ("xc_skiing.roller.skate", frozenset()): "RollerSki",
    ("xc_skiing.skate", frozenset()): "NordicSki",
}

APPLE_HEALTHKIT_FALLBACK: int = 3000

APPLE_HEALTHKIT_MAPPINGS: dict[tuple[str, frozenset[str]], int] = {
    ("cycling", frozenset()): 13,
    ("cycling.cyclocross", frozenset()): 13,
    ("cycling.gravel", frozenset()): 13,
    ("cycling.mountain", frozenset()): 13,
    ("cycling.road", frozenset()): 13,
    ("cycling.time_trial", frozenset()): 13,
    ("cycling.track", frozenset()): 13,
    ("generic", frozenset()): 3000,
    ("rowing", frozenset()): 35,
    ("running", frozenset()): 37,
    ("running.road", frozenset()): 37,
    ("running.track", frozenset()): 37,
    ("running.trail", frozenset()): 37,
    ("swimming", frozenset()): 46,
    ("swimming.open_water", frozenset()): 46,
    ("swimming.pool", frozenset()): 46,
    ("walking", frozenset()): 52,
    ("walking.hiking", frozenset()): 24,
    ("xc_skiing", frozenset()): 60,
    ("xc_skiing.backcountry", frozenset()): 60,
    ("xc_skiing.classic", frozenset()): 60,
    ("xc_skiing.roller", frozenset()): 30,
    ("xc_skiing.roller.classic", frozenset()): 30,
    ("xc_skiing.roller.skate", frozenset()): 30,
    ("xc_skiing.skate", frozenset()): 60,
}

GARMIN_FIT_FALLBACK: GarminFitCode = GarminFitCode(sport=0, sub_sport=0)

GARMIN_FIT_MAPPINGS: dict[tuple[str, frozenset[str]], GarminFitCode] = {
    ("cycling", frozenset()): GarminFitCode(sport=2, sub_sport=0),
    ("cycling.cyclocross", frozenset()): GarminFitCode(sport=2, sub_sport=11),
    ("cycling.gravel", frozenset()): GarminFitCode(sport=2, sub_sport=46),
    ("cycling.mountain", frozenset()): GarminFitCode(sport=2, sub_sport=8),
    ("cycling.road", frozenset()): GarminFitCode(sport=2, sub_sport=7),
    ("cycling.time_trial", frozenset()): GarminFitCode(sport=2, sub_sport=7),
    ("cycling.track", frozenset()): GarminFitCode(sport=2, sub_sport=13),
    ("generic", frozenset()): GarminFitCode(sport=0, sub_sport=0),
    ("rowing", frozenset()): GarminFitCode(sport=15, sub_sport=0),
    ("running", frozenset()): GarminFitCode(sport=1, sub_sport=0),
    ("running.road", frozenset()): GarminFitCode(sport=1, sub_sport=2),
    ("running.track", frozenset()): GarminFitCode(sport=1, sub_sport=4),
    ("running.trail", frozenset()): GarminFitCode(sport=1, sub_sport=3),
    ("swimming", frozenset()): GarminFitCode(sport=5, sub_sport=0),
    ("swimming.open_water", frozenset()): GarminFitCode(sport=5, sub_sport=18),
    ("swimming.pool", frozenset()): GarminFitCode(sport=5, sub_sport=17),
    ("walking", frozenset()): GarminFitCode(sport=11, sub_sport=0),
    ("walking.hiking", frozenset()): GarminFitCode(sport=17, sub_sport=0),
    ("xc_skiing", frozenset()): GarminFitCode(sport=12, sub_sport=0),
    ("xc_skiing.backcountry", frozenset()): GarminFitCode(sport=12, sub_sport=0),
    ("xc_skiing.classic", frozenset()): GarminFitCode(sport=12, sub_sport=0),
    ("xc_skiing.roller", frozenset()): GarminFitCode(sport=30, sub_sport=0),
    ("xc_skiing.roller.classic", frozenset()): GarminFitCode(sport=30, sub_sport=0),
    ("xc_skiing.roller.skate", frozenset()): GarminFitCode(sport=30, sub_sport=0),
    ("xc_skiing.skate", frozenset()): GarminFitCode(sport=12, sub_sport=42),
}
