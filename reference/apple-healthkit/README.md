# Apple HealthKit — HKWorkoutActivityType

> Reference documentation for Apple's workout activity type enumeration.

**Source:** [Apple Developer Documentation](https://developer.apple.com/documentation/healthkit/hkworkoutactivitytype)

## Overview

`HKWorkoutActivityType` is a Swift/Objective-C enum (`UInt`) used by Apple HealthKit to classify workouts. It is a **flat enumeration** with no hierarchy — all activity types live at a single level.

- **84 total cases** (81 active, 3 deprecated)
- Raw integer values run 1–80, skip 81, then 82–84, with `other` at 3000
- No sub-type mechanism — e.g. all cycling variants (road, mountain, indoor) map to a single `cycling` (13)
- No built-in i18n — display names are managed by Apple's UI frameworks, not exposed via API

## Deprecations

| Deprecated Case | Raw Value | Replaced By |
|---|---|---|
| `dance` | 14 | `cardioDance` (77), `socialDance` (78) |
| `danceInspiredTraining` | 15 | `barre` (58), `pilates` (66) |
| `mixedMetabolicCardioTraining` | 30 | `mixedCardio` (73) |

## Key Limitations for Mapping

- **No cycling sub-types**: road, gravel, mountain, indoor all collapse to `cycling` (13). Only `handCycling` (74) is separate.
- **No running sub-types**: road, trail, track all collapse to `running` (37).
- **No swimming sub-types**: pool and open water both map to `swimming` (46).
- **Composite categories**: `snowSports` (40) bundles skiing, sledding, and snowmobiling. `surfingSports` (45) bundles surfing, kite surfing, and wind surfing.

## Files

- [`workout_activity_types.yaml`](workout_activity_types.yaml) — Complete enum reference with all cases, raw values, descriptions, and deprecation status.
