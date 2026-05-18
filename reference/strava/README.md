# Strava — SportType

> Reference documentation for Strava's sport type enumeration.

**Source:** [Strava API v3 Reference — SportType](https://developers.strava.com/docs/reference/#api-models-SportType)

## Overview

Strava uses a string enum called `SportType` to classify activities. It replaced the older `ActivityType` enum which had fewer values.

- **56 values** (string enum, no numeric IDs)
- Flat list, no hierarchy
- Some types encode what OpenSportTaxonomy treats as modifiers: `VirtualRide`, `VirtualRun`, `VirtualRow`, `EBikeRide`, `EMountainBikeRide`

## Files

- [`sport_types.yaml`](sport_types.yaml) — Complete SportType enum values
