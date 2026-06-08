# Plan: Add Wahoo Cloud API Mapping

## Context

Wahoo's Cloud API (https://cloud-api.wahooligan.com/#data-types) classifies every
workout with a numeric `workout_type_id`. OST already maps four platforms; Wahoo is a
natural fifth, and structurally it is the **simplest platform added to date**: the
target is a single flat integer enum, exactly like Apple HealthKit.

This plan follows the "Adding a new platform" workflow in `CONTRIBUTING.md` and the
format v3 specification in `docs/translation.md`.

## Target shape

`target` = `workout_type_id` (a single `int`). This is the only field needed.

`workout_type_family_id` and `workout_type_location_id` are **fixed, derived
attributes of the type, not independent workout fields** — see
[Workout type families and locations](#workout-type-families-and-locations) below for
why they do not enter the runtime mapping. They are used only as annotation comments
and as an audit cross-check during mapping.

The target shape (flat `int`, `int` encode-fallback, `generic` decode-fallback, **no
`target_coarsening`**) is identical to `apple_healthkit`, which serves as the
line-for-line template for every mechanical step.

**`generate.py` needs no codegen changes.** `generate_platforms()` is fully
data-driven (`for platform in sorted(validated)`); the only platform-specific branches
in the generator are for `garmin_fit`'s struct target. An int-target platform is
emitted generically once it is registered in `PLATFORM_REF_DIR`. This is verified
against the current `scripts/generate.py`, not assumed.

## Wahoo workout type enumeration

From the Cloud API docs (`workout_type_id`, with derived family/location):

| ID | Name | Loc | Family |
|---:|------|-----|--------|
| 0 | BIKING | OUT | BIKING |
| 1 | RUNNING | OUT | RUNNING |
| 2 | FE | IN | N/A |
| 3 | RUNNING_TRACK | OUT | RUNNING |
| 4 | RUNNING_TRAIL | OUT | RUNNING |
| 5 | RUNNING_TREADMILL | IN | RUNNING |
| 6 | WALKING | OUT | WALKING |
| 7 | WALKING_SPEED | OUT | WALKING |
| 8 | WALKING_NORDIC | OUT | WALKING |
| 9 | HIKING | OUT | WALKING |
| 10 | MOUNTAINEERING | OUT | WALKING |
| 11 | BIKING_CYCLECROSS | OUT | BIKING |
| 12 | BIKING_INDOOR | IN | BIKING |
| 13 | BIKING_MOUNTAIN | OUT | BIKING |
| 14 | BIKING_RECUMBENT | OUT | BIKING |
| 15 | BIKING_ROAD | OUT | BIKING |
| 16 | BIKING_TRACK | OUT | BIKING |
| 17 | BIKING_MOTOCYCLING | OUT | BIKING |
| 18 | FE_GENERAL | IN | N/A |
| 19 | FE_TREADMILL | IN | RUNNING |
| 20 | FE_ELLIPTICAL | IN | N/A |
| 21 | FE_BIKE | IN | BIKING |
| 22 | FE_ROWER | IN | N/A |
| 23 | FE_CLIMBER | IN | N/A |
| 25 | SWIMMING_LAP | IN | SWIMMING |
| 26 | SWIMMING_OPEN_WATER | OUT | SWIMMING |
| 27 | SNOWBOARDING | OUT | SNOW |
| 28 | SKIING | OUT | SNOW |
| 29 | SKIING_DOWNHILL | OUT | SNOW |
| 30 | SKIINGCROSS_COUNTRY | OUT | SNOW |
| 31 | SKATING | OUT | SKATING |
| 32 | SKATING_ICE | OUT | SKATING |
| 33 | SKATING_INLINE | OUT | SKATING |
| 34 | LONG_BOARDING | OUT | SKATING |
| 35 | SAILING | OUT | WATER |
| 36 | WINDSURFING | OUT | WATER |
| 37 | CANOEING | OUT | WATER |
| 38 | KAYAKING | OUT | WATER |
| 39 | ROWING | OUT | WATER |
| 40 | KITEBOARDING | OUT | WATER |
| 41 | STAND_UP_PADDLE_BOARD | OUT | WATER |
| 42 | WORKOUT | IN | GYM |
| 43 | CARDIO_CLASS | IN | GYM |
| 44 | STAIR_CLIMBER | IN | GYM |
| 45 | WHEELCHAIR | OUT | OTHER |
| 46 | GOLFING | OUT | OTHER |
| 47 | OTHER | OUT | OTHER |
| 49 | BIKING_INDOOR_CYCLING_CLASS | IN | BIKING |
| 56 | WALKING_TREADMILL | IN | WALKING |
| 61 | BIKING_INDOOR_TRAINER | IN | BIKING |
| 62 | MULTISPORT | OUT | N/A |
| 63 | TRANSITION | OUT | N/A |
| 64 | EBIKING | OUT | BIKING |
| 65 | TICKR_OFFLINE | IN | OTHER |
| 66 | YOGA | IN | GYM |
| 67 | RUNNING_RACE | OUT | RUNNING |
| 68 | BIKING_INDOOR_VIRTUAL | IN | BIKING |
| 69 | MENTAL_STRENGTH | IN | OTHER |
| 70 | HANDCYCLING | OUT | BIKING |
| 71 | RUNNING_INDOOR_VIRTUAL | IN | RUNNING |
| 255 | UNKNOWN | UNK | UNKNOWN |

(IDs 24 and 48 and 50–55, 57–60 are unassigned in the published enum and are simply
absent from `targets.yaml`.)

## Proposed mapping

Wahoo's sport coverage is broader than OST's, so the mapping is heavy on `null`
(the designed escape hatch — cf. Strava's `AlpineSki`). Wahoo also encodes the
`stationary` / `virtual` / `assisted` / `race` concepts as distinct workout types,
which is exactly the "auditing tip" pattern from `CONTRIBUTING.md` — those become
OST sport-with-modifier entries, not new sport codes.

`preferred: true` marks the single encode target for each OST sport.

| ID | Name | → OST sport | preferred |
|---:|------|-------------|-----------|
| 0 | BIKING | `cycling` | ✅ |
| 1 | RUNNING | `running` | ✅ |
| 2 | FE | `generic` | |
| 3 | RUNNING_TRACK | `running.track` | ✅ |
| 4 | RUNNING_TRAIL | `running.trail` | ✅ |
| 5 | RUNNING_TREADMILL | `running+stationary` | ✅ |
| 6 | WALKING | `walking` | ✅ |
| 7 | WALKING_SPEED | `walking` | |
| 8 | WALKING_NORDIC | `walking` | |
| 9 | HIKING | `walking.hiking` | ✅ |
| 10 | MOUNTAINEERING | `null` | |
| 11 | BIKING_CYCLECROSS | `cycling.cyclocross` | ✅ |
| 12 | BIKING_INDOOR | `cycling+stationary` | ✅ |
| 13 | BIKING_MOUNTAIN | `cycling.mountain` | ✅ |
| 14 | BIKING_RECUMBENT | `cycling` | |
| 15 | BIKING_ROAD | `cycling.road` | ✅ |
| 16 | BIKING_TRACK | `cycling.track` | ✅ |
| 17 | BIKING_MOTOCYCLING | `null` | |
| 18 | FE_GENERAL | `generic` | |
| 19 | FE_TREADMILL | `running+stationary` | |
| 20 | FE_ELLIPTICAL | `generic` | |
| 21 | FE_BIKE | `cycling+stationary` | |
| 22 | FE_ROWER | `rowing+stationary` | ✅ |
| 23 | FE_CLIMBER | `generic` | |
| 25 | SWIMMING_LAP | `swimming.pool` | ✅ |
| 26 | SWIMMING_OPEN_WATER | `swimming.open_water` | ✅ |
| 27 | SNOWBOARDING | `null` | |
| 28 | SKIING | `null` | |
| 29 | SKIING_DOWNHILL | `null` | |
| 30 | SKIINGCROSS_COUNTRY | `xc_skiing` | ✅ |
| 31 | SKATING | `null` | |
| 32 | SKATING_ICE | `null` | |
| 33 | SKATING_INLINE | `null` | |
| 34 | LONG_BOARDING | `null` | |
| 35 | SAILING | `null` | |
| 36 | WINDSURFING | `null` | |
| 37 | CANOEING | `null` | |
| 38 | KAYAKING | `null` | |
| 39 | ROWING | `rowing` | ✅ |
| 40 | KITEBOARDING | `null` | |
| 41 | STAND_UP_PADDLE_BOARD | `null` | |
| 42 | WORKOUT | `generic` | |
| 43 | CARDIO_CLASS | `generic` | |
| 44 | STAIR_CLIMBER | `generic` | |
| 45 | WHEELCHAIR | `null` | |
| 46 | GOLFING | `null` | |
| 47 | OTHER | `generic` | ✅ |
| 49 | BIKING_INDOOR_CYCLING_CLASS | `cycling+stationary` | |
| 56 | WALKING_TREADMILL | `walking+stationary` | ✅ |
| 61 | BIKING_INDOOR_TRAINER | `cycling+stationary` | |
| 62 | MULTISPORT | `null` | |
| 63 | TRANSITION | `null` | |
| 64 | EBIKING | `cycling+assisted` | ✅ |
| 65 | TICKR_OFFLINE | `generic` | |
| 66 | YOGA | `null` | |
| 67 | RUNNING_RACE | `running+race` | ✅ |
| 68 | BIKING_INDOOR_VIRTUAL | `cycling+stationary+virtual` | ✅ |
| 69 | MENTAL_STRENGTH | `null` | |
| 70 | HANDCYCLING | `cycling` | |
| 71 | RUNNING_INDOOR_VIRTUAL | `running+stationary+virtual` | ✅ |
| 255 | UNKNOWN | `generic` | |

### Encoding notes

- **`cycling+stationary` has 4 Wahoo synonyms** (12, 21, 49, 61). `12 BIKING_INDOOR`
  is preferred; the other three decode to the same sport.
- **`running+stationary` has 2 synonyms** (5, 19); `5 RUNNING_TREADMILL` is preferred.
- **`generic` collects the gym/other catch-alls** (2, 18, 20, 23, 42, 43, 44, 65, 255);
  `47 OTHER` is preferred.
- **Bare `swimming` has no preferred target** — Wahoo has no generic swimming type,
  only lap (25) and open-water (26). `Sport("swimming")` therefore encodes to the
  fallback. This is lossy but accurate: Wahoo forces a pool/open-water choice.
- **`cycling.gravel`, `cycling.time_trial`, `running.road`, `xc_skiing.*`** have no
  Wahoo equivalent and encode via the hierarchy walk to their parent
  (`cycling` → 0, `running` → 1, `xc_skiing` → 30).

### Judgment calls (maintainer review)

These are the rows where reasonable people could differ — flagged for review:

- **7 WALKING_SPEED / 8 WALKING_NORDIC → `walking`** (in-family but lossy; the
  alternative is `null`). Kept as `walking` since the family is unambiguous.
- **10 MOUNTAINEERING → `null`** rather than `walking.hiking` — mountaineering is
  technical (rope/ice), not hiking.
- **14 BIKING_RECUMBENT → `cycling`** (decode-only; recumbent is still cycling).
- **20 FE_ELLIPTICAL / 23 FE_CLIMBER / 44 STAIR_CLIMBER → `generic`** rather than
  `null` — they are cardio activities OST has no code for; `generic` is the closest.
  Defensible either way.
- **70 HANDCYCLING → `cycling`** (decode-only; non-preferred). OST has no `cycling.hand`
  code today, so hand cycling decodes to the nearest standard sport, `cycling`, rather
  than `null`. A dedicated `cycling.hand` code (which Garmin FIT would also use) remains
  a possible future schema addition; until then `cycling` is the closest fit.

## Workout type families and locations

**Conclusion: ignore for the runtime mapping; use only as annotation + audit.**

The API confirms two facts that decide this:

1. **A workout always carries `workout_type_id`** (required on create).
2. **`workout_type_family_id` and `workout_type_location_id` are fixed attributes of
   the type, not independent workout fields.** Every `workout_type_id` always has the
   same family and location (e.g. `12 BIKING_INDOOR` is *always* INDOOR/BIKING).

So family and location carry **zero information beyond `workout_type_id`** — they are a
coarser projection of the same field. Three consequences:

- **Not a target.** Adding them to `target` would break the format-v3 bijection
  invariant (one row per unique target) for no gain. `target = workout_type_id` stays.
- **Not usable as decode coarsening either.** One might imagine "unknown future id →
  fall back by family" (analogous to FIT's `sub_sport → 0` coarsening). But at decode
  time the caller passes only the id; if we don't recognise the id, we don't have its
  family (it too is derived from the id we don't know). Family-based coarsening is
  therefore not reliably computable from the decode input. The plain `fallback.decode:
  generic` is the correct and only behaviour. **No `target_coarsening` for Wahoo.**
- **Where they *are* useful:** as the annotation comment on each scaffolded row
  (`# BIKING_INDOOR (BIKING/INDOOR)`), and as a **manual audit heuristic** while
  mapping — e.g. "every `location=INDOOR` type should map to a sport carrying
  `stationary`, or to `null`/`generic`". This catches mapping mistakes during review
  but is not a runtime rule.

This mirrors how OST already treats Garmin FIT: we map on the `(sport, sub_sport)`
pair, and the FIT SDK's separate `category`/grouping metadata is used only for
human-readable comments, not for translation.

## Prerequisite: the baseline is currently red

**Before any Wahoo work, fix a pre-existing failure unrelated to this change.**
`make lint` fails on the current `main`:

```
ERROR: Version mismatch: schema.yaml has '0.4.0', pyproject.toml has '0.5.0'
```

`schema.yaml` was not bumped to `0.5.0` at the 0.5.0 release, and
`generate.py --check` (which `make lint` runs) aborts on the mismatch. Fix first:

1. Set `schema.yaml` `version: "0.5.0"` (match `pyproject.toml`).
2. `make generate` (rewrites `__init__.py`'s `version`).
3. Confirm `make lint` is green.

Do this as a separate commit so the Wahoo change starts from a green baseline. Without
it, every "run `make lint`/`make test`" step below is meaningless.

## Changes

Following `CONTRIBUTING.md` → "Adding a new platform". `apple_healthkit` is the
template throughout (flat `int` target).

### 1. Reference data

`reference/wahoo/` containing:

- `README.md` — **already written** (this change). Documents the source link
  (https://cloud-api.wahooligan.com/#data-types) and the versioning policy: Wahoo has
  no SDK version, so `platform_version` tracks the **changelog date at the bottom of
  the docs page** (currently `2025-10-06`), formatted `"Cloud API (changelog
  YYYY-MM-DD)"`. Matches the convention of the other `reference/<platform>/README.md`
  files.
- `workout_types.yaml` — hand-curated `cases:` list, one entry per id with
  `value`, `name`, `family`, `location` (the table above). **Unlike the FIT SDK
  (`.xlsx`) or HealthKit, Wahoo publishes no machine-readable enum** — only HTML — so
  this transcription is the source of truth and the one piece of genuinely new manual
  work.
- `targets.yaml` — generated; the flat list of legal `workout_type_id` ints.

### 2. `scripts/build_reference/wahoo.py`

Near-copy of `build_reference/apple_healthkit.py`: read `workout_types.yaml`, emit
`targets.yaml` as a sorted flat int list with `# NAME (FAMILY/LOCATION)` comments.

### 3. Register the platform (3 copies of the platform→refdir map)

The `platform → reference-dir` map is **duplicated in three files**; all three need a
`"wahoo": "wahoo"` entry (the reference dir is `reference/wahoo/`, so the value equals
the key):

- `scripts/generate.py` — `PLATFORM_REF_DIR` (top of file). **This is the only
  `generate.py` change.** No codegen section is added — the generator emits
  `WAHOO_ENTRIES_BY_TARGET` / `WAHOO_PREFERRED_INDEX` / `WAHOO_FALLBACK_ENCODE` /
  `WAHOO_FALLBACK_DECODE` / `WAHOO_TARGET_COARSENING` automatically for any registered
  platform with a scalar target.
- `scripts/scaffold.py` — `PLATFORM_REF_DIR`, plus a `defaults_by_platform["wahoo"]`
  block:
  ```python
  "wahoo": {
      "platform_version": "Cloud API (changelog 2025-10-06)",
      "fallback_encode": 47,          # OTHER
      "fallback_decode": "generic",   # must be a preferred sport — see rule 12
      "target_coarsening": [],
  },
  ```
  Add a `_wahoo_comments()` helper (annotate rows with `NAME (FAMILY/LOCATION)`),
  wired in alongside the existing `_fit_comments` / `_healthkit_comments` dispatch.
- `tests/integration/test_reference_coverage.py` — the module-level `PLATFORMS` dict
  (see step 6).

**Rule-12 dependency:** `fallback.decode` must equal the `sport` of some `preferred`
entry (`generate.py` enforces this). `generic` qualifies because `47 OTHER` is
`generic`'s preferred row. Do not change `fallback.decode` to a sport that lacks a
preferred entry, or `make generate` aborts.

### 4. Scaffold + annotate the mapping

```bash
uv run scripts/scaffold.py wahoo
```

Then annotate `mappings/wahoo.yaml` per the [proposed mapping](#proposed-mapping).

### 5. Runtime instance

`src/open_sport_taxonomy/platforms/_wahoo.py` — copy of `_apple_healthkit.py` with
`WAHOO_*` constants:

```python
from open_sport_taxonomy._platform import Platform
from open_sport_taxonomy._platforms import (
    WAHOO_ENTRIES_BY_TARGET,
    WAHOO_FALLBACK_DECODE,
    WAHOO_FALLBACK_ENCODE,
    WAHOO_PREFERRED_INDEX,
    WAHOO_TARGET_COARSENING,
)

wahoo = Platform(
    entries_by_target=WAHOO_ENTRIES_BY_TARGET,
    preferred_index=WAHOO_PREFERRED_INDEX,
    fallback_encode=WAHOO_FALLBACK_ENCODE,
    fallback_decode=WAHOO_FALLBACK_DECODE,
    target_coarsening=WAHOO_TARGET_COARSENING,
)
```

Register in `src/open_sport_taxonomy/platforms/__init__.py`.

### 6. Update the three test files with hardcoded platform lists

**The runtime test suite does *not* auto-discover platforms.** Three files enumerate
platforms explicitly; Wahoo must be added to each to match the established pattern.
(The mapping *invariants* — coverage, uniqueness, round-trip — are independently
enforced at generation time by `generate.py` rules 4–6 and 10–11, so correctness holds
even before these edits. But the project's convention is one runtime row per platform,
and skipping it would leave Wahoo as the only untested platform at runtime.)

- `tests/integration/test_reference_coverage.py` — add `"wahoo": "wahoo"` to the
  module-level `PLATFORMS` dict. (One line; the three invariant tests iterate it.)
- `tests/integration/test_round_trip.py` — add `wahoo` to the platform import and add a
  `TestWahooRoundTrip` class with the six representative cases (mirroring
  `TestAppleHealthkitRoundTrip`, the closest analogue — flat int, no coarsening):
  1. preferred round-trip — `encode(Sport("cycling.road")) == 15`; `decode(15) == Sport("cycling.road")`
  2. synonym decode — `decode(61) == decode(49) == Sport("cycling+stationary")` (preferred is `12`)
  3. null-sport decode — `decode(28) == Sport("generic")` (SKIING → null → fallback)
  4. parent-walk encode — `encode(Sport("cycling.gravel")) == 0` (no gravel target → walks to `cycling`)
  5. modifier-drop encode — `encode(Sport("cycling.road+commute")) == 15` (drops `+commute`)
  6. unmapped decode → fallback — `decode(99999) == Sport("generic")`
- `tests/properties/test_platform_properties.py` — add `wahoo` to `ALL_PLATFORMS`,
  bump the Hypothesis bound `platform_index=st.integers(min_value=0, max_value=3)` to
  `max_value=4`, and extend the int-type assertion in
  `test_encode_returns_correct_target_type` from `platform is apple_healthkit` to
  `platform in (apple_healthkit, wahoo)`. (`_decode` needs no change — Wahoo's scalar
  target uses the default `platform.decode(target)` branch.)

`tests/algorithm/*` are genuinely data-agnostic and need no change.

### 7. Generate, lint, test

```bash
make generate    # data-driven; emits WAHOO_* tables + runs round-trip rules 10–11
make lint        # rules 1–9, 12–13: coverage, one-preferred-per-sport, fallback round-trip
make test
```

### 8. Docs, docstrings, and release hygiene

Easy to forget, and the difference between "works" and "maintainable." Five spots:

- **`README.md`** — add a `wahoo.yaml` bullet to the "One file per platform" list
  (~line 70) and one encode/decode line to the example block (~line 187). Match the
  existing entries' phrasing.
- **`docs/translation.md`** — the target-shape sentence (~line 10) enumerates every
  platform: "FIT uses `{sport, sub_sport}` pairs; Strava uses strings; HealthKit uses
  integers; Garmin Training API uses strings." Append "; Wahoo uses integers."
- **Stale "four platforms" docstrings** — these module docstrings count platforms and
  will lie after adding Wahoo:
  - `tests/integration/test_round_trip.py` — "Six cases per platform × four platforms
    = 24 tests" → "× five platforms = 30 tests".
  - `tests/integration/test_reference_coverage.py` — "all four platforms" → "all five".
  - `tests/properties/test_platform_properties.py` — "across all four platforms" →
    "five".
- **`CHANGELOG.md`** — add an `### Added` entry under a new version section:
  "Wahoo Cloud API mapping (`mappings/wahoo.yaml`, `reference/wahoo/`) — workout type
  integer enumeration." Adding a platform is a structural addition → **minor bump**
  per `CONTRIBUTING.md` versioning. Bump **both** `schema.yaml` and `pyproject.toml`
  to the new version (e.g. `0.6.0`); the generator's consistency check (see
  Prerequisite) enforces that they stay in lockstep.

## Verification

```bash
make generate
make lint
make test
```

Round-trip spot checks:
```python
from open_sport_taxonomy import Sport
from open_sport_taxonomy.platforms import wahoo

wahoo.encode(Sport("cycling.road"))                    # 15
wahoo.encode(Sport("cycling.road+stationary"))         # 12 (modifier dominates discipline)
wahoo.encode(Sport("cycling.road+virtual"))            # 15 (no outdoor-virtual type; +virtual dropped)
wahoo.encode(Sport("running+race"))                    # 67
wahoo.decode(68)                                        # cycling+stationary+virtual
wahoo.decode(64)                                        # cycling+assisted
wahoo.decode(61)                                        # cycling+stationary (synonym)
wahoo.decode(28)                                        # generic (null → fallback)
```

## Validation dry-run

The proposed mapping was checked against the generator's rules before writing this plan
(`scripts/generate.py`):

- **Rule 8 (one preferred per sport):** each of the 23 mapped sports has exactly one
  `preferred` row; the multi-synonym sports (`cycling+stationary` ×4,
  `running+stationary` ×2, `generic` ×9) each name a single preferred target.
- **Rules 10–11 (round-trip):** every preferred entry round-trips
  (`encode(decode(target)) == target`), and every `sport: null` row decodes to
  `generic` via fallback. Verified by tracing each preferred target.
- **Rule 12 (fallback round-trip):** `fallback.decode: generic` is the sport of the
  preferred row `47 OTHER`, so it round-trips.

No rule violations found, so `make generate` / `make lint` should pass for the Wahoo
data **once the version-mismatch prerequisite is fixed** (see above). This is a
hand-trace against the rules, not an executed run — the first implementation step
should still run `make generate && make lint && make test` to confirm.

## Complexity

**Low–Moderate.** Mechanically the easiest platform yet — flat `int` target, no
coarsening, **zero `generate.py` codegen** (the generator is data-driven),
`apple_healthkit` as the template for the runtime instance. The non-trivial work:

1. Hand-curating `reference/wahoo/workout_types.yaml` — the one piece of new manual
   data, since Wahoo publishes no machine-readable enum (HTML docs only).
2. The mapping judgment calls — mostly settled by existing modifier conventions.
3. Threading Wahoo through the mechanical touch-points it shares with every platform —
   3 registration sites (`generate.py`, `scaffold.py`, `test_reference_coverage.py`),
   the runtime instance, `platforms/__init__.py`, 2 more test files
   (`test_round_trip.py`, `test_platform_properties.py`), and the docs/release hygiene
   (README, `translation.md`, 3 stale docstrings, CHANGELOG, version bump). None hard,
   but easy to miss one — hence the explicit per-step checklist.
4. The **prerequisite baseline fix** (version mismatch) — trivial but blocking, and
   independent of Wahoo.

No architectural changes; fits format v3 as-is. Realistically a focused half-day
including tests, docs, and a clean release commit — provided the baseline is fixed
first.

## Decisions

1. **`HANDCYCLING` (70) → `cycling`** (decode-only). Resolved: map to the nearest
   standard sport rather than `null`. A future `cycling.hand` code remains optional.
2. **`platform_version` → `"Cloud API (changelog 2025-10-06)"`.** Resolved: Wahoo has
   no SDK version, so we pin the latest changelog date from the bottom of the docs page.
   Versioning policy recorded in `reference/wahoo/README.md`.
3. **Elliptical (20) / stair-climber (44) / climber (23) → `generic`.** Resolved:
   decode to `generic` (closest cardio bucket), consistent with FE / WORKOUT /
   CARDIO_CLASS.

## Open questions

None. All design decisions resolved.
