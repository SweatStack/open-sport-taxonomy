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

Mapping files in `mappings/` translate platform-native sport identifiers to OST sport strings. The format (v3) is specified in [`docs/translation.md`](docs/translation.md). Briefly:

```yaml
format_version: 3
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
```

Files are **keyed by platform target** — every legal target in `reference/<platform>/targets.yaml` has exactly one row. Rows with no OST equivalent get `sport: null`. Exactly one row per non-null sport carries `preferred: true`; that row is used for encoding. Other rows decode to the same sport (synonyms).

The generator (`scripts/generate.py`) enforces 13 validation rules against every mapping file. The rule that mattered most for the 0.4.0 oversight: **every value in `reference/<platform>/targets.yaml` must have a row.** New SDK release → new rows or generation fails.

### Adding mappings to an existing file

Find the relevant row by its target. Change `sport: null` to the OST sport string. If multiple platform codes mean the same OST concept (e.g. FIT's `spin` and `indoor_cycling` both meaning `cycling+stationary`), mark exactly one as `preferred: true` and leave the others non-preferred.

**`null` vs `generic`** (see [`docs/taxonomy.md`](docs/taxonomy.md)): a target that names a **specific** activity OST doesn't model (yoga, elliptical, alpine skiing) is `null`; only the platform's own **catch-all** bucket ("Other"/"Workout"/"Unknown"/"Sports") is `generic`. Don't route a named fitness/cardio activity to `generic` just because it's a vague workout.

**Auditing tip.** Many platforms encode OST modifiers as distinct platform types (FIT's `indoor_*` sub_sports, Strava's `Virtual*` types, Garmin Training API's `INDOOR_*` / `VIRTUAL_*` activities). When working through a platform's targets, search for prefixes like `indoor_`, `virtual_`, `e_`, `treadmill` — these almost always belong as OST sport-with-modifier entries (e.g. `cycling+stationary`, `cycling.road+virtual`), not as new OST sport codes.

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
3. Register the platform in `PLATFORM_REF_DIR` and the defaults in `scripts/scaffold.py` and `scripts/generate.py`.
4. Run `uv run scripts/scaffold.py <platform>` to generate a skeleton mapping. Annotate where OST equivalents exist.
5. Add the platform's runtime instance under `src/open_sport_taxonomy/platforms/`.
6. Run `uv run scripts/lint.py` and the test suite.

## Test discipline

The test suite under `tests/` is organized into four directories:

- `tests/domain/` — Sport, Modifier, parsing, resolution, matching, pydantic integration
- `tests/algorithm/` — encode/decode code paths, the format-v3 loader/validator, GarminFitCode API
- `tests/integration/` — round-trip safety net, reference-coverage invariants, build_reference idempotency, performance regression bounds
- `tests/properties/` — property-based tests (Hypothesis) for the Sport class and platform encode/decode

The suite earns its keep, not its size. Plan 017 trimmed it from 643 tests to ~268 example-based tests plus 11 property-based tests by removing redundancies. Future test additions are evaluated against these principles:

1. **One test per claim.** Each test asserts a distinct logical property. If two tests fail together for the same root cause, one is redundant.
2. **Test the algorithm, not the data.** Mapping YAML files are the canonical specification. Tests that assert specific data values (`assert garmin_fit.encode(Sport.CYCLING_ROAD) == GarminFitCode(2, 7)`) are tautologies. Test the *algorithms* with representative inputs.
3. **Prefer build-time validation over runtime tests.** Properties enforceable in `scripts/generate.py` belong there. Runtime tests for the same property are defense-in-depth; ration them.
4. **Properties over examples for pure functions.** For Sport parsing, encode/decode, hierarchy walks: reach for `tests/properties/` first. Hypothesis covers more space than parametrized hand-written cases.
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
- **1 mutation of an unreachable error string** (`"Unknown coarsening rule kind"`). Format v3 defines only the `reset` rule kind, so this branch can't fire under any valid mapping. Tested for completeness via the loader's validation rules, but the runtime branch isn't reachable. Accepted.

Periodic mutation runs (recommended quarterly) should not chase 80% by adding brittle tests. The kill rate is a tool for finding genuinely-weak tests, not a target to optimize.

## Versioning

The `version` field in `schema.yaml` follows [Semantic Versioning](https://semver.org):

- **Patch** (0.1.x) — new sport codes or modifiers added
- **Minor** (0.x.0) — new fields, new metadata, structural additions
- **Major** (x.0.0) — breaking changes to the schema format

Sport codes are never removed. A deprecated code gets a `deprecated: true` field and a `replaced_by` pointer.

Each release is tagged in git (`v0.1.0`) and published as a GitHub Release.

## Reporting errors

If a sport is miscategorized or a modifier applies incorrectly, open an issue describing the problem and the expected correction.
