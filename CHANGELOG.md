# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-18

Initial release.

### Taxonomy

- 7 sport families, 25 sport codes: cycling (6 disciplines), running (3), swimming (2), walking (1), xc_skiing (5 including roller variants), rowing, generic
- 10 modifiers in 2 groups + 3 independent flags:
  - **purpose** (mutually exclusive): race, training, test, leisure, commute
  - **company** (mutually exclusive): solo, group
  - **independent**: assisted, stationary, virtual

### String encoding

- Canonical sport string format using `+` separator: `cycling.road+race+virtual`
- Grammar, parsing rules, canonicalization, and invalid input handling

### Platform mappings

- Apple HealthKit — HKWorkoutActivityType integer values (iOS 18)
- Garmin FIT — sport + sub_sport integer pairs (FIT SDK 21.133)
- Strava — SportType string values (v3 API, 2024)
- Mapping fallback chain: exact match, drop modifiers, walk up hierarchy, platform fallback

### Python library (`open-sport-taxonomy`)

- `Sport` frozen dataclass with class constants (`Sport.CYCLING_ROAD`)
- Three entry points: `Sport.resolve()` (recommended), `Sport.parse()`, `Sport.validate()`
- `Modifier` str enum with group support and `in_group()` filtering
- Standard/non-standard sport distinction with `is_standard` property
- Forward-compatible: `resolve()` handles unknown codes from newer taxonomy versions
- Lossless round-tripping via `parse()` and `.raw` preservation
- Platform translation via `strava.translate()`, `apple_healthkit.translate()`, `garmin_fit.translate()`
- `GarminFitCode` NamedTuple for typed Garmin FIT results
- Build-time code generation from schema.yaml — zero runtime dependencies
- 189 tests
