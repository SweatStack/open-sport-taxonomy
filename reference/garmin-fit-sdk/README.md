# Garmin FIT SDK — Sport & Sub Sport Enums

> Reference documentation for Garmin's FIT protocol sport classification system.

**Source:** Garmin FIT SDK `Profile.xlsx` (Types sheet)

## Overview

The FIT (Flexible and Interoperable Data Transfer) protocol uses a **two-level enum system** to classify activities:

- **`sport`** — top-level activity category (e.g. `cycling` = 2)
- **`sub_sport`** — discipline within a sport (e.g. `gravel_cycling` = 46)

An activity is identified by the combination of `(sport, sub_sport)`. A `sub_sport` of `generic` (0) means no further specialization.

## Key Characteristics

- **Two-level hierarchy only** — no nesting beyond sport + sub_sport
- **Integer enums** — both sport and sub_sport are numeric values
- **Sparse value ranges** — not all integers are assigned (gaps exist in both enums)
- **Sub_sports are shared** — some sub_sport values apply to multiple sports (e.g. `generic` = 0 is valid for any sport)
- **69 sport values**, **89 sub_sport values** (including `all` = 254 which is for goals only)

## Sub_sport to Sport Associations

Sub_sports have comments in the SDK indicating which sport(s) they belong to. For example:

| Sub Sport | Value | Associated Sport(s) |
|---|---|---|
| `treadmill` | 1 | Run, Fitness Equipment |
| `spin` | 5 | Cycling |
| `indoor_cycling` | 6 | Cycling, Fitness Equipment |
| `lap_swimming` | 17 | Swimming |
| `open_water` | 18 | Swimming |
| `gravel_cycling` | 46 | Cycling |
| `backcountry` | 37 | Alpine Skiing, Snowboarding |

These associations are documented in the comment field but not formally enforced — a device could technically send any sport/sub_sport combination.

## Files

- [`sports.yaml`](sports.yaml) — Complete sport enum reference
- [`sub_sports.yaml`](sub_sports.yaml) — Complete sub_sport enum reference with sport associations
- `Profile.xlsx` — Original Garmin FIT SDK profile (source of truth). **Not committed**
  — this is a Garmin FIT SDK file and is not redistributed here (gitignored). Download
  it from the [Garmin FIT SDK](https://developer.garmin.com/fit/download/) and place it
  in this directory to regenerate the YAML enums.
