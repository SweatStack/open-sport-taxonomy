# Repo Structure Plan

> Focus: scaffold the repository with reference documentation for platform sport enums before building the canonical schema.

**Status:** Proposed

---

## Structure

```
open-sport-taxonomy/
│
├── plans/                            # Project plans
│
├── README.md
├── LICENSE
│
├── reference/                        # Platform reference docs (starting point)
│   ├── garmin-fit/
│   │   ├── README.md                 # Overview of FIT sport/sub_sport enum system
│   │   ├── sports.yaml               # All FIT sport enum values (0=generic, 1=running, 2=cycling, ...)
│   │   └── sub_sports.yaml           # All FIT sub_sport enum values, keyed by parent sport
│   │
│   ├── apple-healthkit/
│   │   ├── README.md                 # Overview of HKWorkoutActivityType
│   │   └── workout_activity_types.yaml  # All HKWorkoutActivityType cases with raw values
│   │
│   ├── strava/
│   │   └── sport_types.yaml          # Strava SportType enum (for later)
│   │
│   └── garmin-connect/
│       └── activity_types.yaml       # Garmin Connect activity type keys (for later)
│
├── schema/                           # Canonical taxonomy (future)
│   └── sports.yaml
│
├── i18n/                             # Translations (future)
│
├── mappings/                         # Cross-platform mapping tables (future)
│
├── dist/                             # Generated artifacts (future)
│
├── packages/                         # Language packages (future)
│   ├── python/
│   └── typescript/
│
└── scripts/                          # Build/validate tooling (future)
```

---

## Key Decisions

### `reference/` is separate from `schema/` and `mappings/`

Raw documentation of what each platform provides, not the normalized taxonomy. Keeps "what exists" cleanly separated from "what we define."

### YAML for reference data

Consistent with the rest of the project and easy to transform later. Each file documents one platform's enum/type system with original values, names, and notes.

### Per-platform subdirectories

Garmin FIT needs two files (sport + sub_sport are separate enums that combine), HealthKit is a single flat enum, so the structure adapts per platform.

---

## Phasing

1. **Now** — Populate `reference/garmin-fit/` and `reference/apple-healthkit/` with complete enum documentation
2. **Next** — Add `reference/strava/` and `reference/garmin-connect/`
3. **Then** — Use reference data to inform the canonical `schema/sports.yaml` and `mappings/`
