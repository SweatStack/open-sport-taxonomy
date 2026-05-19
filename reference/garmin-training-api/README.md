# Garmin Training API V2 — Sport Types

> Reference documentation for Garmin's Training API V2 structured workout sport classification.

**Source:** Garmin Connect Developer Program, Training API V2 specification (Version 1.0, 2025-05-26)

## Overview

The Training API V2 allows third-party partners to push structured workouts and workout schedules to Garmin Connect. Workouts sync to Garmin devices for execution.

Unlike the FIT SDK (integer pairs), the Training API uses **string sport types** at the workout and segment level.

## Sport Types

| Value | Description |
|---|---|
| `CYCLING` | Cycling |
| `RUNNING` | Running |
| `LAP_SWIMMING` | Pool swimming |
| `STRENGTH_TRAINING` | Strength training |
| `CARDIO_TRAINING` | Cardio training |
| `GENERIC` | Generic (limited device support) |
| `YOGA` | Yoga |
| `PILATES` | Pilates |
| `MULTI_SPORT` | Multi-sport container (workout level only) |

## Key Characteristics

- **Flat list** — no hierarchy, no sub-types
- **String values** — uppercase, underscore-separated
- **Very coarse** — all cycling disciplines map to a single `CYCLING` value, all running to `RUNNING`
- **Limited coverage** — only 8 sport types (plus `MULTI_SPORT`), no rowing, walking, or XC skiing

## Files

The source documents are confidential under the Garmin Connect Developer Program agreement and cannot be committed to this repository.

- `Training_API_V2.pdf` — Official Garmin Training API V2 specification
- `Appendix A and B.xlsx` — Exercise categories and names for strength/cardio/yoga/pilates
