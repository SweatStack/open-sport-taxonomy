# Contributing

OpenSportTaxonomy is maintained by SweatStack. Contributions are welcome.

## Developer quick reference

The `Makefile` is the canonical entry point. Run `make` to see all targets.

```bash
make test     # lint then test — what CI runs
make lint     # static checks only (ruff + mypy + schema + reference drift + generator)
make fix      # auto-fix ruff lint + format issues
make generate # regenerate auto-generated Python after schema/mapping edits
```

See [Test discipline](#test-discipline) below for the full workflow and rationale.

## Schema format

The canonical schema is [`schema.yaml`](schema.yaml). It contains two flat lists:

**Sports** are sorted alphabetically by code. Each entry has a `code` and a `label`. Hierarchy is encoded in the dot notation: `cycling.mountain.xco` is a child of `cycling.mountain`, which is a child of `cycling`. Every parent must have its own entry.

**Modifiers** are sorted alphabetically by code. Each entry has a `code` and `label`. Modifiers with a `group` field are mutually exclusive within that group. Modifiers without a group are independent flags.

## Adding a sport code

Open an issue or pull request with:

- **Code** — lowercase, dot-separated. Must nest under an existing parent or introduce a new top-level sport.
- **Label** — English display name.
- **Rationale** — why this is a distinct discipline, not a variant of an existing code.

**Read [`docs/taxonomy.md`](docs/taxonomy.md) first** — it is the canonical rule for whether something is a discipline, a modifier, or a separate modality. In short: OST groups by *movement pattern* (the muscular, kinematic, biomechanical-load, and substitution lenses), ignoring intensity, metabolic load, and circumstance. Same movement → discipline; same movement with only the circumstance changed → modifier; different movement → separate modality (a shared name or shared equipment is not evidence of sameness — hand cycling is not cycling).

Examples of sport codes: `cycling.track` (different bike, different technique, specialized venue). `xc_skiing.double_poling` (distinct technique, own racing category).

Examples of things that are NOT sport codes: indoor cycling (it's `cycling.road` + `stationary`), e-bike gravel (it's `cycling.gravel` + `assisted`), roller skiing (it's `xc_skiing.classic` + `roller` — same technique, different surface), a cycling race (it's any cycling code + `race`).

## Adding a modifier

Modifiers should be rare. A modifier is a **circumstance of execution that does not change the movement** (see [`docs/taxonomy.md`](docs/taxonomy.md)) — if it changes which muscles do the work, it is a separate modality, not a modifier. A new modifier must apply to multiple modalities and cut across the tree. Open an issue with:

- **Code** — lowercase, single word.
- **Group** — if mutually exclusive with existing modifiers, which group? If independent, leave blank.
- **Rationale** — why this can't be a sport code.

## Conventions

- Codes are lowercase, using underscores for multi-word segments: `hand_cycling`, not `handCycling`.
- Codes use full words, not abbreviations: `cycling.time_trial`, not `cycling.tt`. Abbreviations are acceptable only when the full form is rarely used (e.g. `xc_skiing`).
- Labels are lowercase, with capitals only for acronyms: "road cycling", "classic XC skiing", "BMX".
- Both sports and modifiers are sorted alphabetically by code.
- Keep entries minimal. Descriptions, emoji, mappings, and translations live in separate files, not in the core schema.

Before submitting a pull request, run the linter:

```bash
uv run scripts/lint.py          # check for ordering and orphan issues
uv run scripts/lint.py --fix    # auto-fix ordering
```

## Platform mappings

Mapping files in `mappings/` translate platform-native sport identifiers to OST sport strings. The format is specified in [`docs/translation.md`](docs/translation.md) and is part of the OST spec version (see [Versioning](#versioning)). Briefly:

```yaml
platform: <platform_id>
platform_version: <version of the bundled platform spec>

fallback:
  encode: <platform value returned when encoding has no match>
  decode: <OST sport string returned when decoding has no match>

target_coarsening:                  # optional, only for hierarchical targets
  - reset: { <field>: <root_value> }

entries:
  - target: <platform value>
    sport: <OST sport string> | null
    preferred: <bool>               # optional, default false
    encode_for: [<broader sport>]   # optional; only on a preferred row
```

Files are **keyed by platform target** — every legal target in `reference/<platform>/targets.yaml` has exactly one row. Rows with no OST equivalent get `sport: null`. Exactly one row per non-null sport carries `preferred: true`; that row is used for encoding. Other rows decode to the same sport (synonyms). A preferred row may also list `encode_for` — broader (ancestor) sports that *also* encode to its target, letting several sports collapse onto one code on encode while decode stays one-to-one.

The generator (`python/scripts/generate.py`) enforces 13 validation rules against every mapping file. The rule that mattered most for the 0.4.0 oversight: **every value in `reference/<platform>/targets.yaml` must have a row.** New SDK release → new rows or generation fails.

### Adding mappings to an existing file

Find the relevant row by its target. Change `sport: null` to the OST sport string. If multiple platform codes mean the same OST concept (e.g. FIT's `spin` and `indoor_cycling` both meaning `cycling+stationary`), mark exactly one as `preferred: true` and leave the others non-preferred.

**`null` vs `generic`** (see [`docs/taxonomy.md`](docs/taxonomy.md)): a target that names a **specific** activity OST doesn't model (yoga, elliptical, alpine skiing) is `null`; only the platform's own **catch-all** bucket ("Other"/"Workout"/"Unknown"/"Sports") is `generic`. Don't route a named fitness/cardio activity to `generic` just because it's a vague workout.

**Auditing tip.** Many platforms encode OST modifiers as distinct platform types (FIT's `indoor_*` sub_sports, Strava's `Virtual*` types, Garmin Training API's `INDOOR_*` / `VIRTUAL_*` activities). When working through a platform's targets, search for prefixes like `indoor_`, `virtual_`, `e_`, `treadmill` — these almost always belong as OST sport-with-modifier entries (e.g. `cycling+stationary`, `running+stationary+virtual`), not as new OST sport codes.

**Modifier conventions.** Apply modifiers for the circumstance the target *actually* denotes, and don't invent a discipline:
- **Virtual indoor-trainer activities** (Zwift-style `Virtual*`, `*_INDOOR_VIRTUAL`) are *both* stationary and virtual → `cycling+stationary+virtual` (likewise `running+stationary+virtual`, `rowing+stationary+virtual`).
- **A base e-bike or virtual ride takes no `.road`** (or any discipline) unless the platform names one: `EBikeRide → cycling+assisted`, but `EMountainBikeRide → cycling.mountain+assisted`.

**Hierarchical targets (e.g. Garmin FIT).** When a platform has a sport/sub-sport hierarchy, a sub-sport under a parent that maps to a real OST modality must decode to that modality (or finer) — never `null`. A recumbent or BMX ride is still `cycling`; `walking/casual_walking` is still `walking`. `target_coarsening` only rescues *future-SDK* sub-sports that are absent from the file; it does **not** override an explicit `null` row, so annotate every known sub-sport down to its parent.

### Bumping a platform version

When the upstream SDK adds new values:

1. Update the upstream source files in `reference/<platform>/`.
2. Run `uv run scripts/build_reference/<platform>.py` to regenerate `targets.yaml`.
3. Run `uv run scripts/scaffold.py <platform> --update` to add rows for the new targets (annotated with `sport: null`).
4. Annotate the new rows where they correspond to existing OST sports/modifiers.
5. Run `uv run scripts/lint.py`. If lint complains about missing OST codes, file a schema PR first.

### Adding a new platform

1. Create `reference/<platform>/` and document the upstream source in a `README.md`.
2. Write `scripts/build_reference/<platform>.py` that produces `reference/<platform>/targets.yaml` (a flat list of every legal target).
3. Register the platform in `PLATFORM_REF_DIR` and the defaults in `scripts/scaffold.py` and `python/scripts/generate.py`.
4. Run `uv run scripts/scaffold.py <platform>` to generate a skeleton mapping. Annotate where OST equivalents exist.
5. Add the platform's runtime instance under `python/src/open_sport_taxonomy/platforms/`.
6. Run `uv run scripts/lint.py` and the test suite.

## Test discipline

The library test suite under `python/tests/` is organized into four directories (it tests the **Python package**; spec-data invariants like reference coverage and `build_reference` idempotency are enforced separately by `make lint`, not duplicated here):

- `python/tests/domain/` — Sport, Modifier, parsing, resolution, matching, pydantic integration
- `python/tests/algorithm/` — encode/decode code paths, the loader/validator, GarminFitCode API
- `python/tests/integration/` — round-trip safety net, performance regression bounds
- `python/tests/properties/` — property-based tests (Hypothesis) for the Sport class and platform encode/decode

The suite earns its keep, not its size. Plan 017 trimmed it from 643 tests to ~268 example-based tests plus 11 property-based tests by removing redundancies. Future test additions are evaluated against these principles:

1. **One test per claim.** Each test asserts a distinct logical property. If two tests fail together for the same root cause, one is redundant.
2. **Test the algorithm, not the data.** Mapping YAML files are the canonical specification. Tests that assert specific data values (`assert garmin_fit.encode(Sport.CYCLING_ROAD) == GarminFitCode(2, 0)`) are tautologies. Test the *algorithms* with representative inputs.
3. **Prefer build-time validation over runtime tests.** Properties enforceable in `python/scripts/generate.py` belong there. Runtime tests for the same property are defense-in-depth; ration them.
4. **Properties over examples for pure functions.** For Sport parsing, encode/decode, hierarchy walks: reach for `python/tests/properties/` first. Hypothesis covers more space than parametrized hand-written cases.
5. **Suite quality is measured, not asserted.** Coverage (`pytest-cov`), mutation score (`mutmut`), and strict typing (`mypy --strict`) are the falsifiable evidence. Use them.
6. **Failure noise has a cost.** A 100-failure test pass communicates less than a 1-failure pass. Parametrization multiplies *coverage*, not *failure counts*.
7. **Test names are spec.** `test_modifiers_dominate_discipline_in_encode_walk` reads like a contract clause. `test_cycling_road_virtual` reads like a YAML entry.

### Running the suite

The `Makefile` is the canonical entry point for every developer workflow. Run `make` (or `make help`) to see the full list of targets with descriptions.

```bash
make lint        # static checks: ruff, mypy, schema, reference drift, generator (~3s)
make test-only   # pytest with coverage and benchmarks; skips lint (~8s)
make test        # lint then test-only — the safe default for CI (~11s)
make check       # alias for `test`; preferred CI entry point
make format      # apply ruff formatter
make fix         # auto-fix what ruff can (lint + format)
make mutmut      # mutation testing baseline (~1m; periodic health check, not in CI)
make generate    # regenerate auto-generated Python from schema + mappings
make clean       # remove caches and build artifacts
```

**`make test` runs lint first by design.** The lint step is fast (~3s — ruff, mypy, schema, reference drift, and the generator's --check pass) and catches an entire class of issues that the test suite cannot. Defaulting to safety is the right call for CI and for pre-push checks.

**Use `make test-only` for tight iteration loops.** When you're debugging a single failing test and don't want lint feedback on every cycle, `test-only` is the escape hatch.

**Override pytest flags inline** with `PYTEST_FLAGS`:

```bash
make test-only PYTEST_FLAGS=-v                                    # verbose
make test-only PYTEST_FLAGS="tests/algorithm/test_encode.py -v"   # one file
make test-only PYTEST_FLAGS="-k test_modifiers_dominate -v"       # one test by name
```

Direct `uv run` invocations still work and are equivalent — the Makefile is a convenience layer, not a wrapper that changes behavior.

### Quality baseline (as of this refactor)

- Statement + branch coverage: ≥ 95% (enforced by `pytest-cov --cov-fail-under=95`)
- `mypy --strict`: clean
- `ruff check` and `ruff format --check`: clean
- Mutation kill rate: 77.8% (42/54 mutants killed)

The 12 surviving mutants are categorized:

- **8 mutations of error-message string content.** Asserting exact error-message wording would make tests brittle without catching real bugs; we assert that the right exception type fires with a useful regex match, not that every character is identical. Accepted.
- **2 mutations of type aliases** (`SportKey`, `CoarseningRule`). These are runtime no-ops; the `mypy --strict` check is the right tool, not pytest. Accepted.
- **1 mutation in `decode`'s coarsening loop** (`continue` → `break`). Functionally equivalent given the current FIT mapping data: both code paths reach `fallback.decode = generic`. Would become a real gap if any platform adds non-generic fallbacks or a third coarsening rule; revisit at that time. Accepted with caveat.
- **1 mutation of an unreachable error string** (`"Unknown coarsening rule kind"`). The mapping format defines only the `reset` rule kind, so this branch can't fire under any valid mapping. Tested for completeness via the loader's validation rules, but the runtime branch isn't reachable. Accepted.

Periodic mutation runs (recommended quarterly) should not chase 80% by adding brittle tests. The kill rate is a tool for finding genuinely-weak tests, not a target to optimize.

## Versioning

OST carries **two** version numbers (see [`plans/024`](plans/024-two-version-model.md) for the rationale):

- **Spec version** (`schema.yaml`, `version:`) — the version of the *standard*: the sport + modifier vocabulary, the OST string format, the mapping-file format, and the bundled platform mappings, all under one SemVer line. This is the number other implementations of OST (the web tool, future ports) refer to.
- **Package version** (`pyproject.toml`) — the version of *this Python library*, on its own SemVer line. What you `pip install`.

They are related but not equal: **`open-sport-taxonomy` implements OST spec X.** The package version advances on any library release; the spec version advances only when the standard's content or format changes. The library exposes both — `open_sport_taxonomy.version` (package, from installed metadata) and `open_sport_taxonomy.taxonomy_version` (spec, from `schema.yaml`).

**Compatibility is by spec major version.** Data and mappings are interoperable within a major: an implementation of spec `M.x` reads anything tagged `M.*` — older minors fully, newer minors best-effort (unknown codes decode to `generic`). A major bump signals a breaking change.

When to bump the **spec** version:

- **patch** — editorial only (a label reworded); no code/format/decode change.
- **minor** — additive & backward-compatible: a new sport/modifier code, a new mapping-file feature, a new platform mapping, a brand-new row for a previously-unmapped target.
- **major** — breaking: a code removed/renamed, the string grammar changed, the mapping format changed beyond what older loaders can read, **or an existing input re-interpreted** (a target that used to decode to A now decodes to B).

Sport codes are never removed silently. A deprecated code gets a `deprecated: true` field and a `replaced_by` pointer (removal/rename is a major bump).

> **Pre-1.0:** while OST is `0.x`, the major axis is pinned at 0 and breaking changes ride the **minor** number. The major-compatibility rule becomes binding at `1.0`.

### Releasing

1. Bump the spec version in `schema.yaml` if the standard changed; bump the package version in `pyproject.toml`.
2. Move the CHANGELOG `[Unreleased]` block under a dated version heading.
3. `make generate && make lint && make test` — all green.
4. `make build` to produce the wheel/sdist (carries the package version from `pyproject.toml`).
5. **Tag the release with the spec version** (`git tag v<spec>`, e.g. `v0.9.0`) and push; cut a GitHub Release. A code-only release where the spec is unchanged is tagged with the **package** version instead, so every release has a unique tag. Git tags do not affect what PyPI publishes — `uv_build` reads the static `version` from `pyproject.toml`.
6. `make publish` to upload to PyPI.

## Reporting errors

If a sport is miscategorized or a modifier applies incorrectly, open an issue describing the problem and the expected correction.
