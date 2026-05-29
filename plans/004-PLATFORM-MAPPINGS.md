# Platform Mappings

> Outward translations from OpenSportTaxonomy to platform-specific sport identifiers.

**Status:** Proposed

---

## Goal

Provide language-agnostic mapping files to translate OST codes to platform identifiers. One YAML file per platform, all following the same structure.

Outward translation only (OST to platform) for now.

---

## Reference data

Raw platform sport definitions live in `reference/`, one directory per platform. Each directory has a README explaining what the files are and where they came from. The data files themselves can be in whatever format the platform provides or is most natural (xlsx, json, yaml, csv). No enforced schema. The only requirement is that a human or coding agent can read it.

What we have:
- `reference/apple-healthkit/` — HealthKit HKWorkoutActivityType enum (YAML, sourced from Apple docs)
- `reference/garmin-fit-sdk/` — FIT sport + sub_sport enums (YAML extracted from Profile.xlsx, plus original xlsx)

What we need:
- `reference/strava/` — SportType enum from https://developers.strava.com/docs/reference/#api-models-SportType

---

## Mapping files

```
mappings/
  apple_healthkit.yaml
  garmin_fit.yaml
  strava.yaml
```

### Format

Every mapping file has the same structure:

```yaml
platform: <platform_id>
platform_version: <version of the platform spec this was mapped against>
fallback: <platform's generic/catch-all value>

mappings:
  - ost: <sport_code>
    modifiers: [<modifier>, ...]     # optional, omit when no modifiers
    target: <platform_specific_value>
```

Each entry maps one (sport code + modifier combination) to one platform value. The `target` field type varies by platform but is consistent within a file. Entries are sorted by `ost`, then by `modifiers`.

Every OST sport code should have an entry in every mapping file, even when the mapping is lossy. Sports with no specific platform equivalent map to the platform's generic value. The `fallback` field documents this generic value and serves as a safety net for OST codes that haven't been added to the file yet.

For platforms with numeric identifiers, inline YAML comments document the human-readable name. These comments are not parsed and exist purely for readability. Maintainers should take care to keep them in sync.

### Apple HealthKit

Target is an integer (HKWorkoutActivityType raw value):

```yaml
platform: apple_healthkit
platform_version: "iOS 18"
fallback: 3000  # other

mappings:
  - ost: cycling
    target: 13  # cycling
  - ost: cycling.cyclocross
    target: 13  # cycling
  - ost: cycling.gravel
    target: 13  # cycling
  - ost: cycling.mountain
    target: 13  # cycling
  - ost: cycling.road
    target: 13  # cycling
  - ost: cycling.time_trial
    target: 13  # cycling
  - ost: cycling.track
    target: 13  # cycling
  - ost: generic
    target: 3000  # other
  - ost: rowing
    target: 35  # rowing
  - ost: running
    target: 37  # running
  - ost: running.road
    target: 37  # running
  - ost: running.track
    target: 37  # running
  - ost: running.trail
    target: 37  # running
  - ost: swimming
    target: 46  # swimming
  - ost: swimming.open_water
    target: 46  # swimming
  - ost: swimming.pool
    target: 46  # swimming
  - ost: walking
    target: 52  # walking
  - ost: walking.hiking
    target: 24  # hiking
  - ost: xc_skiing
    target: 60  # crossCountrySkiing
  - ost: xc_skiing.backcountry
    target: 60  # crossCountrySkiing
  - ost: xc_skiing.classic
    target: 60  # crossCountrySkiing
  - ost: xc_skiing.roller
    target: 30  # skatingSports
  - ost: xc_skiing.roller.classic
    target: 30  # skatingSports
  - ost: xc_skiing.roller.skate
    target: 30  # skatingSports
  - ost: xc_skiing.skate
    target: 60  # crossCountrySkiing
```

Many-to-one is expected: HealthKit doesn't distinguish cycling disciplines.

### Garmin FIT

Target is a sport + sub_sport pair:

```yaml
platform: garmin_fit
platform_version: "FIT SDK 21.133"
fallback: { sport: 0, sub_sport: 0 }  # generic

mappings:
  - ost: cycling
    target: { sport: 2, sub_sport: 0 }   # cycling / generic
  - ost: cycling.cyclocross
    target: { sport: 2, sub_sport: 11 }   # cycling / cyclocross
  - ost: cycling.gravel
    target: { sport: 2, sub_sport: 46 }   # cycling / gravel_cycling
  - ost: cycling.mountain
    target: { sport: 2, sub_sport: 8 }    # cycling / mountain
  - ost: cycling.road
    target: { sport: 2, sub_sport: 7 }    # cycling / road
  - ost: cycling.time_trial
    target: { sport: 2, sub_sport: 7 }    # cycling / road (no TT sub_sport)
  - ost: cycling.track
    target: { sport: 2, sub_sport: 13 }   # cycling / track_cycling
  - ost: generic
    target: { sport: 0, sub_sport: 0 }    # generic / generic
  - ost: rowing
    target: { sport: 15, sub_sport: 0 }   # rowing / generic
  - ost: running
    target: { sport: 1, sub_sport: 0 }    # running / generic
  - ost: running.road
    target: { sport: 1, sub_sport: 2 }    # running / street
  - ost: running.track
    target: { sport: 1, sub_sport: 4 }    # running / track
  - ost: running.trail
    target: { sport: 1, sub_sport: 3 }    # running / trail
  - ost: swimming
    target: { sport: 5, sub_sport: 0 }    # swimming / generic
  - ost: swimming.open_water
    target: { sport: 5, sub_sport: 18 }   # swimming / open_water
  - ost: swimming.pool
    target: { sport: 5, sub_sport: 17 }   # swimming / lap_swimming
  - ost: walking
    target: { sport: 11, sub_sport: 0 }   # walking / generic
  - ost: walking.hiking
    target: { sport: 17, sub_sport: 0 }   # hiking / generic
  - ost: xc_skiing
    target: { sport: 12, sub_sport: 0 }   # cross_country_skiing / generic
  - ost: xc_skiing.backcountry
    target: { sport: 12, sub_sport: 0 }   # cross_country_skiing / generic
  - ost: xc_skiing.classic
    target: { sport: 12, sub_sport: 0 }   # cross_country_skiing / generic (no classic sub_sport)
  - ost: xc_skiing.roller
    target: { sport: 30, sub_sport: 0 }   # inline_skating / generic
  - ost: xc_skiing.roller.classic
    target: { sport: 30, sub_sport: 0 }   # inline_skating / generic
  - ost: xc_skiing.roller.skate
    target: { sport: 30, sub_sport: 0 }   # inline_skating / generic
  - ost: xc_skiing.skate
    target: { sport: 12, sub_sport: 42 }  # cross_country_skiing / skate_skiing
```

### Strava

Target is a string (SportType value). Strava uses SportType (56 values), not the legacy ActivityType (37 values).

Strava encodes some OST modifiers as distinct sport types:

```yaml
platform: strava
platform_version: "v3 API, 2024"
fallback: Workout

mappings:
  - ost: cycling
    target: Ride
  - ost: cycling.cyclocross
    target: Ride
  - ost: cycling.gravel
    target: GravelRide
  - ost: cycling.mountain
    target: MountainBikeRide
  - ost: cycling.mountain
    modifiers: [assisted]
    target: EMountainBikeRide
  - ost: cycling.road
    target: Ride
  - ost: cycling.road
    modifiers: [assisted]
    target: EBikeRide
  - ost: cycling.road
    modifiers: [virtual]
    target: VirtualRide
  - ost: cycling.time_trial
    target: Ride
  - ost: cycling.track
    target: Ride
  - ost: generic
    target: Workout
  - ost: rowing
    target: Rowing
  - ost: rowing
    modifiers: [virtual]
    target: VirtualRow
  - ost: running
    target: Run
  - ost: running.road
    target: Run
  - ost: running.road
    modifiers: [virtual]
    target: VirtualRun
  - ost: running.track
    target: Run
  - ost: running.trail
    target: TrailRun
  - ost: swimming
    target: Swim
  - ost: swimming.open_water
    target: Swim
  - ost: swimming.pool
    target: Swim
  - ost: walking
    target: Walk
  - ost: walking.hiking
    target: Hike
  - ost: xc_skiing
    target: NordicSki
  - ost: xc_skiing.backcountry
    target: BackcountrySki
  - ost: xc_skiing.classic
    target: NordicSki
  - ost: xc_skiing.roller
    target: RollerSki
  - ost: xc_skiing.roller.classic
    target: RollerSki
  - ost: xc_skiing.roller.skate
    target: RollerSki
  - ost: xc_skiing.skate
    target: NordicSki
```

---

## Matching rules (recommended)

When translating an OST activity (sport + modifiers) to a platform value:

1. Look for an exact match on both `ost` and `modifiers`.
2. If no exact match, fall back to the entry matching `ost` without modifiers.
3. If no match, try the parent code (e.g. `cycling.road` falls back to `cycling`).

This is a recommendation for consuming libraries, not enforced by the data.

---

## Documentation

### README

Add a "Platform mappings" section for consumers:

- What mappings are: translation files from OST codes to platform-specific identifiers (HealthKit, Garmin FIT, Strava)
- That translations are lossy by design. Platforms with less granularity collapse multiple OST codes into one value. This is expected, not an error.
- A quick example showing the same OST code mapped to different platforms

### CONTRIBUTING

Add guidance for contributors working on mapping files:

- The mapping file format (uniform structure, flexible target type)
- How to add a new platform mapping
- How to handle modifier combinations (entries with and without modifiers)
- The recommended fallback behavior (exact match, then without modifiers, then parent code)

### Mapping files

Each mapping file should have a header comment pointing back to the README, same pattern as `schema.yaml`.

---

## Design decisions

**Uniform structure, flexible target.** Every file uses the same `ost` / `modifiers` / `target` shape. The `target` type varies by platform (integer, string, object) but is consistent within a file.

**One file per platform.** Adding a new platform doesn't touch existing files.

**Mappings live in this repo.** Same release, same tag. Can be split later if needed.

**Reference and mappings are separate.** Reference data documents what a platform provides. Mappings translate between OST and platform values. They live in separate directories and can be updated independently.

**Platform version tracking.** Each mapping file records which version of the platform's spec it was mapped against (e.g. "iOS 18", "FIT SDK 21.133"). This tells consumers when the mapping was last verified.

**Inline comments for readability.** Numeric targets include a YAML comment with the human-readable name (e.g. `target: 13  # cycling`). These are not parsed and can technically drift, but the readability benefit outweighs the risk for human-edited files.

**Strava uses SportType, not ActivityType.** SportType is newer and more granular.

**Complete coverage.** Every OST sport code should have an entry in every mapping file, even when the mapping is lossy. Sports with no specific platform equivalent map to the platform's generic value. This means consumers can do a simple lookup and trust they'll get a result.

**Fallback as safety net.** The `fallback` field documents the platform's generic/catch-all value. It covers the edge case where a new OST code hasn't been added to all mapping files yet. It does not replace explicit entries.
