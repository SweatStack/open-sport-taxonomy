# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Allowed section headers: Added, Changed, Deprecated, Removed, Fixed, Security.


## [0.9.0] - 2026-06-11

### Added

- **`encode_for` — decode and encode may now have different cardinality.** Decode stays one-to-one (one platform code → one OST sport); encode becomes many-to-one (several OST sports may collapse onto one platform code). A `preferred` row may list `encode_for: [<broader sport>, …]` — ancestor sports that also encode to that target — so a code can decode to a precise discipline while remaining the encode home for the bare modality. Strict-ancestor constrained and round-trip validated; see [`docs/translation.md`](docs/translation.md).
- **Garmin FIT `virtual_activity` (sub_sport 58) now mapped.** `cycling/virtual_activity → cycling+stationary+virtual` and `running/virtual_activity → running+stationary+virtual` (previously coarsened to bare `cycling`/`running`, dropping the indoor + virtual facts). Aligns with the Strava/Wahoo `+stationary+virtual` convention.
- **`open_sport_taxonomy.taxonomy_version`** — the taxonomy/spec version (the vocabulary of sports + modifiers and the OST string format), exposed independently of the package release. Sourced from `schema.yaml`.

### Changed

- **Garmin FIT `generic` codes now decode to the dominant discipline (opinionated).** `running/generic → running.road`, `cycling/generic → cycling.road`, `cross_country_skiing/generic → xc_skiing.classic`. Modern Garmin devices have no road/classic profile, so road runs/rides and classic skis are written to the *generic* code while the specific disciplines (trail, gravel, mountain, skate, …) self-label — so on Garmin "generic" *is* the dominant discipline, which is what consumers expect. Via `encode_for`, both the bare modality and the discipline encode back to the generic code (`running`/`running.road → 1/0`, `cycling`/`cycling.road → 2/0`, `xc_skiing`/`xc_skiing.classic → 12/0`); the legacy `street` (1/2) and `road` (2/7) codes now decode to road and are the encode target of nothing.
- **Same generic→road default extended to Strava, Suunto, and Wahoo** (the platforms that offer the specific disciplines but no road type): Strava `Run → running.road`, `Ride → cycling.road`; Suunto `Running (1) → running.road`, `Cycling (2) → cycling.road`; Wahoo `RUNNING (1) → running.road`. Each carries `encode_for` so the bare modality still encodes home. **Wahoo cycling is deliberately *not* changed** — `BIKING_ROAD` (15) exists, so generic `BIKING` (0) remains bare `cycling` (a genuine "unspecified" signal). Polar, Apple HealthKit, and Garmin Training API are also unchanged: Polar models road explicitly (generic = unspecified), and the latter two have a single coarse running/cycling type that also covers trail/mountain (road would mislabel).
- **Two-version model (one spec version + one package version).** The mapping-file format is now versioned as part of the OST **spec version** (`schema.yaml`) together with the vocabulary, the OST string format, and the bundled mappings; the per-file `format_version` field is **removed**. The package version (`pyproject.toml`) is independent and reported by `open_sport_taxonomy.version` (from installed metadata); the spec version is `open_sport_taxonomy.taxonomy_version` (from `schema.yaml`). The schema/pyproject version-equality check is removed; git release tags track the spec version. See `plans/023` and `plans/024`.

### Fixed

- **Garmin FIT `rowing/indoor_rowing` (15/14) → `rowing+stationary`** (was coarsening to bare `rowing`, dropping the indoor signal). `fitness_equipment/indoor_rowing` (4/14) remains the canonical encode target for `rowing+stationary`.

### Removed

- Non-redistributable vendor source documents `reference/garmin-fit-sdk/Profile.xlsx` and `reference/suunto/Activities.pdf` are no longer committed (now gitignored); the derived `*.yaml` reference files remain the in-repo source of truth.


## [0.8.5] - 2026-06-09

### Changed

- Suunto `Ski touring` (31) and `Ski mountaineering` (116) now decode to `alpine_skiing` instead of `generic` — both are alpine-touring disciplines (skin up, ski down), consistent with `Backcountry skiing` (0.8.3). Plain mountaineering remains `null` across platforms (Suunto 83, Wahoo 10, FIT 16): it is rock/ice climbing, which OST does not model — not hiking.

## [0.8.4] - 2026-06-09

### Fixed

- **Garmin FIT: sub-sports of mapped sports no longer decode to `generic`.** Eleven rows that were left `sport: null` now decode to the right OST modality: `cycling/recumbent`, `cycling/bmx`, `cycling/mixed_surface` → `cycling`; `cycling/downhill` → `cycling.mountain`; `walking/casual_walking`, `walking/speed_walking` → `walking`; `running/indoor_running` → `running`; `cycling/commuting` → `cycling+commute`; `cycling/e_bike_mountain` → `cycling.mountain+assisted`; and the previously-unmapped `e_biking` sport (`e_biking/generic`, `e_biking/e_bike_fitness`) → `cycling+assisted`. Consequently `cycling+assisted` now encodes to FIT `e_biking (21, 0)` instead of plain `cycling` (which dropped the assist), and `cycling+commute` / `cycling.mountain+assisted` gain FIT encode targets.

## [0.8.3] - 2026-06-09

### Changed

- Suunto `Backcountry skiing` (107) now decodes to `alpine_skiing` instead of `xc_skiing`. Backcountry skiing is alpine touring, not cross-country; with `alpine_skiing` now in the schema (0.8.2) this is the correct modality. (A `.backcountry` discipline for both alpine and XC may follow.)

## [0.8.2] - 2026-06-09

### Added

- **New modality codes `alpine_skiing`, `snowboarding`, `hand_cycling`.** Per [`docs/taxonomy.md`](docs/taxonomy.md), each is a distinct movement pattern — not a discipline or modifier of an existing sport (alpine skiing ≠ `xc_skiing`; hand cycling is arm-powered, not `cycling`). All six platforms that distinguish them now decode to the real modality instead of `generic`: e.g. `AlpineSki`, `downhillSkiing`, `SKIING_DOWNHILL`, `Downhill skiing`; `Snowboard`/`SNOWBOARDING`/`Splitboarding`; `Handcycle`/`handCycling`/`HANDCYCLING`/`hand_cycling`.

### Changed

- **Cycling/running/rowing modifier conventions (Strava).** A base e-bike/virtual ride no longer asserts a `.road` discipline: `EBikeRide → cycling+assisted` (was `cycling.road+assisted`). Virtual indoor-trainer activities now carry `+stationary`: `VirtualRide → cycling+stationary+virtual`, `VirtualRun → running+stationary+virtual`, `VirtualRow → rowing+stationary+virtual`. This aligns Strava with Wahoo's `*_INDOOR_VIRTUAL` mappings; the convention is recorded in `CONTRIBUTING.md`.

## [0.8.1] - 2026-06-09

### Fixed

- Cross-platform mapping corrections surfaced by the audit in `plans/021`, now that [`docs/taxonomy.md`](docs/taxonomy.md) defines relatedness (group by movement pattern) and the `null` vs `generic` rule:
  - `apple_healthkit` `mixedMetabolicCardioTraining` and `garmin_fit` `inline_skating` no longer decode to `xc_skiing+roller` — neither is roller skiing. Now `null` (→ `generic`).
  - **Hand cycling is a separate modality, not cycling** (it is arm-powered). `wahoo`, `polar`, and `suunto` hand-cycling targets now decode to `generic` instead of `cycling`.
  - `wahoo` named fitness machines/classes (`FE_ELLIPTICAL`, `FE_CLIMBER`, `CARDIO_CLASS`, `STAIR_CLIMBER`) now `null`, matching the other platforms. Genuinely-unspecified targets (`FE`, `FE_GENERAL`, `TICKR_OFFLINE`, `WORKOUT`, `OTHER`, `UNKNOWN`) stay `generic`.

## [0.8.0] - 2026-06-08

### Added

- **Suunto Activities mapping** (`mappings/suunto.yaml`, `reference/suunto/`). Translates Suunto's integer activity ID (0–121, with gaps) to and from OST. Indoor/treadmill/roller/e-bike activities map to OST sport-with-modifier entries — frequently finer than Suunto's own FIT export, which e.g. files E-mtb under a single `E_BIKING` sport (OST keeps `cycling.mountain+assisted`) and roller skiing under `CROSS_COUNTRY_SKIING` (OST keeps `xc_skiing+roller`). Suunto's broad taxonomy (ball sports, martial arts, named gym/fitness, alpine/touring snow sports, water sports) decodes via the `generic` fallback. The source `Activities.pdf` is stored at `reference/suunto/`; the enumeration is hand-curated in `reference/suunto/activities.yaml`. See [`reference/suunto/README.md`](reference/suunto/README.md).

## [0.7.0] - 2026-06-08

### Added

- **Polar AccessLink API mapping** (`mappings/polar.yaml`, `reference/polar/`). Translates Polar's `detailed_sport_info` string enumeration (175 legal targets) to and from OST. Indoor/treadmill/roller/e-bike values map to OST sport-with-modifier entries (e.g. `INDOOR_CYCLING`/`SPINNING` ↔ `cycling+stationary`, `ROLLER_SKIING_FREESTYLE` ↔ `xc_skiing.skate+roller`, `E_BIKE` ↔ `cycling+assisted`) — frequently finer than Polar's own FIT export, which sends several of these to FIT `GENERIC`. Polar's broad taxonomy (ball sports, martial arts, dance, motorsports, water sports, etc.) decodes via the `generic` fallback. The full AccessLink OpenAPI spec is stored at `reference/polar/swagger.yaml` for provenance; the sport enumeration is hand-curated in `reference/polar/detailed_sport_info.yaml` (the swagger does not enumerate it). See [`reference/polar/README.md`](reference/polar/README.md).

## [0.6.0] - 2026-06-08

### Added

- **Wahoo Cloud API mapping** (`mappings/wahoo.yaml`, `reference/wahoo/`). Translates the Wahoo `workout_type_id` integer enumeration (61 legal targets) to and from OST. Indoor/virtual/e-assist/race workout types map to OST sport-with-modifier entries (e.g. `BIKING_INDOOR_VIRTUAL` ↔ `cycling+stationary+virtual`, `EBIKING` ↔ `cycling+assisted`, `RUNNING_RACE` ↔ `running+race`); sports OST does not model (snow, water, skating, golf, etc.) decode via the `generic` fallback. The source enum is hand-curated in `reference/wahoo/workout_types.yaml` (Wahoo publishes no machine-readable enum), and `platform_version` tracks the docs changelog date. See [`reference/wahoo/README.md`](reference/wahoo/README.md).

### Fixed

- `schema.yaml` version was left at `0.4.0` when 0.5.0 was released, causing `generate.py`'s version-consistency check to fail `make lint`. Aligned `schema.yaml` with `pyproject.toml`.


## [0.5.0] - 2026-05-29

### Added

- **Format v3 mapping files.** Mappings are now keyed by platform target rather than OST sport string. Every legal target in `reference/<platform>/targets.yaml` has exactly one row; coverage oversights are structurally impossible. See [`docs/translation.md`](docs/translation.md).
- `reference/<platform>/targets.yaml` files for all four platforms, generated by `scripts/build_reference/<platform>.py`. CI enforces idempotency.
- `scripts/scaffold.py <platform>` generates skeleton mappings from `targets.yaml`. Supports `--update` for SDK bumps.
- **FIT indoor/stationary mappings.** New entries for `cycling+stationary` (canonical: indoor_cycling; synonyms: spin, fitness_equipment/indoor_cycling), `running+stationary` (canonical: running/treadmill; synonym: fitness_equipment/treadmill), `rowing+stationary` (fitness_equipment/indoor_rowing), and `walking+stationary` (canonical: walking/indoor_walking; synonym: fitness_equipment/indoor_walking). Fixes the 0.4.0 oversight that motivated this redesign.
- 13 normative validation rules enforced at generation time (`scripts/generate.py`). Rules 1–9, 12, 13 are static; rules 10–11 exercise the generated runtime for round-trip correctness.
- `scripts/lint.py` rewritten to drive `generate.py --check` for mapping validation plus a reference-drift check (each `build_reference/<platform>.py` must reproduce its `targets.yaml` byte-for-byte). The schema sort/orphan checks are preserved.
- `Platform.encode` rejects non-`Sport` inputs with a `TypeError` that points the caller at `Sport(...)` (strict) or `Sport.parse(...)` (permissive). The accept-a-string convenience was deliberately not added — it would silently absorb typos via the hierarchy walk; see the decision in `tests/test_encode.py::TestTypeContract`.
- New test files: `test_loader.py`, `test_decode.py`, `test_encode.py`, `test_round_trip.py`, `test_reference_coverage.py`, `test_build_reference.py`.

### Changed

- **Breaking format change.** Mapping YAML moves from v1 (`ost`-keyed, `modifiers:` field, single `fallback`) to v3 (`target`-keyed, sport string with `+modifiers` inline, `fallback: { encode, decode }`, optional `target_coarsening`). The Python public API (`Sport`, `encode`, `decode`) is unchanged.
- **Breaking:** `GarminFitCode` fields renamed from `sport_id`/`sub_sport_id` back to `sport`/`sub_sport` to match the YAML target shape used in `target_coarsening` rules. `sport_name`/`sub_sport_name` properties unchanged.
- **Algorithm change (encode):** modifiers now dominate discipline depth in the hierarchy walk. `cycling.road+stationary` encodes to FIT `(2, 6)` indoor_cycling rather than `(2, 7)` road, since dropping `+stationary` to keep `.road` would render an indoor trainer ride as outdoor — a worse error than dropping `.road` to keep `+stationary`. See [`docs/translation.md`](docs/translation.md) for the full priority ordering.
- **Algorithm change (decode):** direct lookup against the platform-keyed table. Forward-compat is handled by data-driven `target_coarsening` rules (FIT's hand-coded `_reduce` is replaced by `reset: { sub_sport: 0 }`).
- `validate_modifiers` (internal) now accepts both `Modifier` enum members and plain modifier-code strings, so generate-time validation of YAML data can run without instantiating enums.
- **Test suite refactor (plan 017).** Trimmed from 643 to ~268 example-based tests plus 11 property-based tests. New `tests/{domain,algorithm,integration,properties}/` directory structure. Quality infrastructure added: `pytest-cov` (≥95% coverage gate, currently 97.6%), `hypothesis` property-based tests, `pytest-benchmark` performance bounds, `ruff` lint + format, `mypy --strict`, and a `mutmut` baseline (77.8% kill rate, all surviving mutants categorized in CONTRIBUTING.md). `scripts/lint.py` now drives schema + ruff + mypy + reference drift + generator check from one entry point.

### Removed

- The v1 bijection-on-target invariant — replaced by a constructive constraint (`preferred: true` flags one row per sport) plus 13 explicit validation rules.
- Per-platform Python code in encode/decode paths. All algorithmic decisions are now data in YAML.
- `tests/test_bijection.py` — read the v1 YAML shape; superseded by `test_round_trip.py`, `test_reference_coverage.py`, and the round-trip pass inside `generate.py`.

## [0.4.0] - 2026-05-26

### Added

- `Platform.decode(target) -> Sport` on every platform. Strava, Apple HealthKit, Garmin Training API, and Garmin FIT all support reverse translation.
- Garmin FIT `decode(sport, sub_sport=None)` accepts ints, FIT enum names, or `None` (= generic) in either position. Drop-in for values from FIT parsers.
- `GarminFitCode` carries both `sport_id`/`sport_name` and `sub_sport_id`/`sub_sport_name`; constructible from ints, names, or a mix.
- [`docs/translation.md`](docs/translation.md): language-agnostic spec of the encode/decode algorithms.

### Changed

- **Breaking:** `Platform.translate` renamed to `Platform.encode`.
- **Breaking:** `GarminFitCode` fields renamed from `sport`/`sub_sport` to `sport_id`/`sub_sport_id`. Kwargs still accepted as `sport=`/`sub_sport=`.
- **Breaking:** `encode(Sport.CYCLING_TIME_TRIAL)` now returns `GarminFitCode(2, 0)` instead of `GarminFitCode(2, 7)` — FIT has no `time_trial` sub_sport.

## [0.3.1] - 2026-05-19

### Fixed

- Garmin Training API fallback changed from `CYCLING` to `GENERIC`. Unmapped sports should not falsely report as cycling.

## [0.3.0] - 2026-05-19

### Added

- Garmin Training API V2 platform mapping (`garmin_training_api`). Maps to string sport types: `CYCLING`, `RUNNING`, `LAP_SWIMMING`, `GENERIC`.

## [0.2.0] - 2026-05-19

### Added

- `Sport.is_subsport_of(other)` method: check if a sport is a more specific version of another (code hierarchy + modifier superset).
- `SportField` and `StrictSportField` Pydantic v2 field types in `open_sport_taxonomy.pydantic`. Install with `open-sport-taxonomy[pydantic]`.

### Changed

- `Sport(raw)` constructor is now strict by default: rejects unknown codes and modifiers with `ValueError`.
- `Sport.resolve()` is now an instance method. Use `Sport.parse(raw).resolve()` instead of `Sport.resolve(raw)`.
- `modifiers` type changed from `frozenset[Modifier]` to `frozenset[str]`. Known modifiers are `Modifier` instances (which are `str` subclasses), unknown modifiers from `Sport.parse()` are plain strings.
- `str(sport)` now always reconstructs faithfully from `.code` and all modifiers. Previously lossy for resolved sports.
- `repr(sport)` now shows `Sport.parse('...')` for non-standard sports.
- `is_standard` now also checks for modifier group conflicts.
- `.parent` now preserves modifiers. `Sport("cycling.road+race").parent` returns `Sport("cycling+race")` instead of `Sport("cycling")`.
- `.disciplines` now preserves modifiers. `Sport("cycling+commute").disciplines` returns disciplines with `+commute`.

### Removed

- `Sport.validate()` classmethod. Use `Sport(raw)` instead (same behavior).
- `Sport.resolve()` classmethod. Use `Sport.parse(raw).resolve()` instead.
- `raw` field. Use `str(sport)` instead, which is now always faithful.
- `unknown_modifiers` field. Unknown modifiers are now part of the unified `modifiers` frozenset. Use `sport.modifiers - sport.resolve().modifiers` to find unknowns.

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
