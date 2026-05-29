# 017 — Test suite refactor: tightening, properties, and quality enforcement

## Background

After the format-v3 redesign (plan 015) the test suite grew from 296 to 643 tests. Auditing each file reveals two distinct problems:

1. **Bloat.** Three locations multiply tests without adding signal:
   - `test_round_trip.py` parametrizes the same encode/decode invariant across **every entry in every mapping file** (292 invocations). The invariant is already enforced by `scripts/generate.py` validation rules 10–11 at generation time, and the algorithms it exercises have ~8 distinct code paths total. The remaining ~280 invocations test the same code paths against different data values.
   - Per-platform test files (`test_platform_strava.py`, `test_platform_healthkit.py`, `test_platform_garmin_training_api.py`, most of `test_platform_garmin.py`) consist of hardcoded `assert platform.encode(Sport.X) == Y` assertions. In v0.4.0 these had value as a hand-written sanity layer over a small hand-written mapping. In v0.5.0 the YAML *is* the canonical specification — these assertions now compare the YAML against itself via a different syntax.
   - `test_reference_coverage.py` re-asserts loader validation rules 4, 5, 6 at runtime.

2. **Missing infrastructure.** The suite has gaps that the bloat hides:
   - No property-based tests — the only generative coverage is the hand-written parametrization.
   - No coverage measurement — there is no falsifiable claim that the refactor preserves coverage.
   - No mutation testing — suite quality is judged by inspection, not measured.
   - No strict type checking in CI — the codebase uses type hints throughout but they are not enforced.
   - No directory structure — three distinct concerns (domain, algorithm, integration) sit in a flat layout.
   - No performance regression guard — algorithms are O(small) by inspection, not by test.

The principle this plan applies: **a test earns its place by catching a class of bug that no other test catches, and the suite as a whole must be measurably high-quality, not just nominally complete.** Tests that mirror the source-of-truth data, or that re-verify guarantees the build pipeline already enforces, are noise rather than signal. Suite quality must be backed by coverage and mutation metrics, not inspection alone.

This plan does both things in one coordinated PR series: tightens the existing suite *and* adds the quality infrastructure that makes the tightening verifiable.

## Design principles

These principles govern every per-file decision and every infrastructure addition. They should also govern future test additions to this codebase.

1. **One test per claim.** Each test asserts a distinct logical property of the system. If two tests fail together for the same root cause, one of them is redundant.
2. **Test the algorithm, not the data.** The YAML mapping files are the canonical specification. Tests that assert specific data values (`assert garmin_fit.encode(Sport.CYCLING_ROAD) == GarminFitCode(2, 7)`) are tautologies once the YAML is the source of truth. Test the *algorithms* with representative inputs that exercise each code path once.
3. **Prefer build-time validation over runtime tests.** When a property is enforceable in `scripts/generate.py`, enforce it there. Runtime tests for the same property are defense-in-depth; ration them deliberately.
4. **Properties over examples where possible.** For pure functions on structured data (parsing, encoding, hierarchy walks), property-based tests cover more space than parametrized hand-written cases, find smaller failing reproducers, and document the spec more honestly. Reach for Hypothesis as the primary tool, not a supplement.
5. **Suite quality is measured, not asserted.** Coverage (`pytest-cov`) and mutation score (`mutmut`) are the falsifiable evidence that the suite is as good as we think it is. Strict type checking (`mypy --strict`) catches a class of bugs no test does.
6. **Failure noise has a cost.** A 292-failure test pass communicates less than a 1-failure pass that points at the actual broken thing. Parametrization should multiply *coverage*, not *failure counts*.
7. **Test names are the spec.** Reading the suite's test names should produce a coherent description of what the system does. Test names like `test_cycling_road_virtual` are data assertions; names like `test_modifiers_dominate_discipline_in_encode_walk` are spec.

## Target architecture

```
tests/
  domain/                  — pure-Python type behavior
    test_sport.py            Sport construction, properties, str/repr, equality, hash
    test_parse.py            Sport.parse permissive semantics
    test_resolve.py          Sport.resolve walk-up behavior
    test_matching.py         is_subsport_of logic
    test_modifier.py         Modifier enum domain logic
    test_cross_operation.py  Cross-method invariants (parse + resolve + str)
    test_pydantic.py         SportField pydantic integration

  algorithm/               — format v3 algorithms and loader
    test_loader.py           One test per validation rule (1–13)
    test_encode.py           One test per encode code path
    test_decode.py           One test per decode code path
    test_garmin_fit_code.py  GarminFitCode NamedTuple API + decode argument forms

  integration/             — cross-component invariants
    test_round_trip.py             Representative round-trip per platform
    test_reference_coverage.py     Loader-contract runtime safety net
    test_build_reference.py        build_reference idempotency
    test_performance.py            Algorithmic regression bounds

  properties/              — property-based tests (Hypothesis)
    test_sport_properties.py       Parse/str/equality/hash/parent invariants
    test_platform_properties.py    encode/decode invariants on generated inputs

Deleted entirely:
  tests/test_validate.py                          — fully subsumed by test_sport.py
  tests/test_platform_strava.py                   — data assertions; subsumed
  tests/test_platform_healthkit.py                — same
  tests/test_platform_garmin_training_api.py      — same
  tests/test_platform_garmin.py                   — split: TestGarminFitCode + decode-arg-forms moved;
                                                    remainder deleted
```

Target count: ~260 tests (~250 example-based + ~10 property-based; Hypothesis runs each property test against many generated inputs internally, so the test *count* understates coverage).

## Quality infrastructure

These are added alongside the test refactor, in dedicated phases:

### Coverage (`pytest-cov`)

- Add as a dev dependency.
- Configure via `pyproject.toml`: `--cov=open_sport_taxonomy --cov-report=term-missing --cov-branch`.
- CI gate: `--cov-fail-under=95` on statement coverage, `--cov-fail-under=90` on branch coverage. Thresholds chosen by running the trimmed suite once and rounding down from the observed numbers; adjust at phase end if reality differs.
- This is the load-bearing check that the refactor doesn't quietly drop coverage. Without it we are trusting our audit; with it we are verifying it.

### Property-based tests (`hypothesis`)

- Add as a dev dependency.
- Live under `tests/properties/`. Two files:
  - `test_sport_properties.py` — Sport class invariants (round-trip, hash stability, parent preservation, modifier sorting, etc.).
  - `test_platform_properties.py` — encode/decode invariants generated against random sports.
- Strategies built from `schema.yaml` data (sampled_from for codes and modifiers), filtered for group-conflict rules where relevant. Custom strategies live in a `tests/properties/conftest.py` so they are shareable.
- Each property test asserts one invariant; Hypothesis explores the input space. Failing examples are auto-shrunk to minimal reproducers and recorded in the Hypothesis database (gitignored) for replay.

### Mutation testing (`mutmut`)

- Add as a dev dependency.
- **Not in CI** — too slow (minutes per run for a library this size, but not seconds).
- Documented as a periodic health check: `uv run mutmut run --paths-to-mutate src/open_sport_taxonomy/`.
- Baseline mutation score captured at the end of the refactor and recorded in `CONTRIBUTING.md`. Target: ≥80% killed mutants. Surviving mutants reviewed; legitimate weak spots in the suite trigger follow-up tests.
- This is the empirical answer to "are the tests we kept actually any good?" — not an opinion, a measurement.

### Strict type checking (`mypy --strict`)

- Add as a dev dependency.
- Configure via `pyproject.toml`: `[tool.mypy]` block with `strict = true`, `files = ["src/open_sport_taxonomy"]`.
- Wire into `scripts/lint.py` so CI fails on type errors.
- May reveal a small number of `Any` usages or missing annotations to fix; do those fixes inline as part of the mypy phase.
- This catches bugs no test can — the codebase already uses type hints, so making them enforced is finishing the job, not starting new work.

### Linting and formatting (`ruff`)

- Add as a dev dependency. Replaces multiple tools at once (black + isort + flake8 + many pylint rules) with a single fast Rust-based implementation.
- Configure via `pyproject.toml`: `[tool.ruff]` with a curated rule set including `E` (pycodestyle errors), `F` (pyflakes — undefined names, unused imports), `B` (bugbear — common pitfalls like mutable defaults), `I` (isort), `UP` (pyupgrade), `SIM` (flake8-simplify), `RUF` (ruff-native). Avoid the long-tail style rules that produce noise without value.
- Wire into `scripts/lint.py` alongside mypy. CI fails on lint errors.
- `ruff format` replaces black. Run once across the codebase to normalize; commit the diff as part of the ruff phase. From then on, CI catches drift.
- This is the same category of static-analysis tool as mypy. Both belong in the quality stack of a serious Python library; including one without the other is incoherent.

### Performance regression bounds (`pytest-benchmark`)

- Add as a dev dependency.
- Single integration test file `tests/integration/test_performance.py` with one benchmark per platform exercising encode + decode through a representative entry.
- Assert mean execution time is under a generous bound (e.g. 100 µs). The point is not to optimize — it is to fail CI if someone introduces an accidental O(n²) walk or import-time pathology.
- Bounds calibrated from a baseline measurement at the end of the phase; documented in the test docstrings so future contributors know where the numbers came from.

### Directory restructure

- New layout: `tests/{domain,algorithm,integration,properties}/`.
- Each directory gets an empty `__init__.py` (or none, depending on pytest discovery preference; verify during phase 1).
- Pytest config in `pyproject.toml` updated to `testpaths = ["tests"]` (recursive — already default behavior, but make explicit).
- A new `tests/conftest.py` at the root if shared fixtures emerge during the refactor; per-directory conftests for properties/ strategies.

## Per-file disposition

Every file in the existing `tests/` is addressed below with current count, action, target count, and concrete rationale. Counts are pytest-collected (includes parametrize expansion). Paths shown are post-restructure.

### Domain model files

#### `tests/domain/test_sport.py` — 45 → 40

Core Sport class testing. The TestRoundtrip loops are tight (one test, internal loop over `_LABELS`); keep as-is.

**Actions:**
- Audit for overlap with `test_validate.py` (which will be deleted): the construction-rejection tests in `test_validate.py::TestRejectsNonStandard` and `TestStructuralErrors` overlap with `TestConstruction`. Merge any uniquely-covered cases first, then delete `test_validate.py`.
- Drop ~5 tests that exist only to assert obvious-from-the-type-system facts.

**Keep**: all property tests (str/repr, equality, hash, parent, disciplines, label), all rejection tests for distinct failure modes.

#### `tests/domain/test_parse.py` — 34 → 28

Sport.parse permissive semantics. Mostly meaningful: tests cover standard input, unknown codes at different depths, unknown modifiers, mixed, round-trip.

**Actions:** Drop ~6 tests that exercise the same code path with cosmetic variation. Keep all tests exercising a distinct branch.

#### `tests/domain/test_resolve.py` — 29 → 24

Sport.resolve walk-up behavior.

**Actions:** Drop ~5 tests that exercise the same resolution branch against multiple data points. Keep tests for: known input unchanged, unknown code walks up, unknown modifier dropped, mixed unknown code + modifier, walk-to-generic, modifier conflict.

#### `tests/domain/test_matching.py` — 20 → 20

`is_subsport_of` logic. Each test exercises a distinct logical case. No bloat.

**Action**: Keep as-is.

#### `tests/domain/test_modifier.py` — 15 → 9

Some tests exercise Python's stdlib `enum` module rather than this library's behavior.

**Drop:**
- `TestEnumBehavior::test_lookup_by_value`, `test_invalid_value_raises`, `test_iteration`, `test_identity` — all test `enum.Enum`, a stdlib feature.
- `TestProperties::test_code_equals_value` — asserts `m.code == m.value` for every modifier; structurally guaranteed by the generated property definition.
- `TestStringInterop::test_equals_string` and `test_fstring` — test stdlib `str` subclass behavior.

**Keep:** `TestProperties::test_code`, `test_label`, `test_group_independent`, `test_group_purpose`, all of `TestInGroup`, `TestCompleteness::test_all_expected_modifiers_present`.

#### `tests/domain/test_cross_operation.py` — 22 → 20

Cross-method invariants. Mostly high-value integration tests.

**Actions:** Drop ~2 tests exercising the same invariant against multiple data variations.

#### `tests/domain/test_pydantic.py` — 21 → 18

Third-party integration; necessary because the integration is non-trivial.

**Actions:** Drop ~3 tests duplicating same field behavior with multiple sport values.

#### `tests/test_validate.py` — 9 → 0 (DELETE)

Leftover from the v0.2.0 constructor redesign (plan 012). Every test is now covered by `test_sport.py`.

**Action:** Delete after auditing each of the 9 tests has equivalent coverage. Port any uniquely-covered case to `test_sport.py` first.

### Algorithm files

#### `tests/algorithm/test_loader.py` — 16 → 18

**Add:**
- Test for rule 2 (platform field mismatch) — currently absent.
- Smoke test: a minimal valid mapping passes all validators.

#### `tests/algorithm/test_encode.py` — 13 → 12

**Actions:**
- Consolidate `TestExactMatch` from 3 tests to 1 representative + 1 for the cross-sport-encoding edge case (rowing+stationary → fitness_equipment).
- Add 1 test for the modifier-walk fallback case currently implicit.
- Keep `TestTypeContract` intact — it pins a design decision.

#### `tests/algorithm/test_decode.py` — 10 → 10

One test per decode code path. Keep as-is.

#### `tests/algorithm/test_garmin_fit_code.py` — 0 → 19 (NEW FILE)

Extracted from `test_platform_garmin.py`:
- `TestGarminFitCode` (8 tests) — NamedTuple construction API.
- `TestDecodeArgumentForms` (10 tests, new class) — `decode("cycling", "road")`, `decode(2, None)`, `decode(None, None)`, etc. These test the `_GarminFitPlatform.decode` override (platform-specific input handling) — not covered elsewhere.
- `TestDecodeExhaustiveSmoke` (1 test) — "every FIT sport id produces a Sport" smoke test.

### Integration files

#### `tests/integration/test_round_trip.py` — 292 → 24

The 292 figure comes from parametrizing three test functions across all mapping entries. The encode/decode algorithms have ~8 distinct code paths total.

**Rewrite** as 24 hardcoded tests structured by code path × platform shape:

```
6 tests per platform × 4 platforms = 24 tests.
Each platform's set exercises:
  1. preferred-entry exact round-trip
  2. non-preferred synonym decode (synonym → canonical)
  3. null-sport decode (→ fallback.decode)
  4. encode of a sport whose closest match is via parent walk
  5. encode of a sport+modifier combo whose closest match drops the modifier
  6. decode of a target that requires target_coarsening (FIT-only;
     other platforms substitute "decode of unmapped target → fallback.decode")
```

The exhaustive guarantee on preferred entries is provided by `scripts/generate.py`'s rules 10–11; this file is the algorithm-regression safety net.

#### `tests/integration/test_reference_coverage.py` — 12 → 3

Three runtime invariants × 4 platforms = 12. Consolidate to 3 tests, each iterating over all four platforms internally and surfacing the platform name in failure messages.

#### `tests/integration/test_build_reference.py` — 4 → 4

Idempotency check per platform. Each test exercises a distinct script. Keep as-is.

#### `tests/integration/test_performance.py` — 0 → 4 (NEW FILE)

One benchmark per platform exercising encode + decode through a representative entry. Assert mean < 100 µs. Catches accidental algorithmic regressions and import-time pathologies.

### Properties files (new)

#### `tests/properties/test_sport_properties.py` — 0 → ~6

Properties of the Sport class:
- For any standard sport `s`: `Sport(str(s)) == s`.
- For any standard sport `s`: `Sport.parse(str(s)) == s`.
- For any standard sport with modifiers: `str(s)` lists modifiers alphabetically.
- For any standard sport `s`: `hash(s)` depends only on `(code, modifiers)`.
- For any standard sport `s`: `s.parent` (if non-None) preserves modifiers exactly.
- For any standard sport: `is_subsport_of` is reflexive.

Strategies built from `_LABELS` (sport codes) and `Modifier` enum values, filtered for group-conflict rules.

#### `tests/properties/test_platform_properties.py` — 0 → ~5

Properties of encode/decode across all four platforms:
- For any standard sport: `encode(sport)` returns a value of the correct platform-native type.
- For any sport reachable via the preferred index: `decode(encode(sport)) == sport`.
- For any platform: `decode` is deterministic (called twice on the same input yields the same Sport).
- For any platform: `encode` is deterministic.
- For any reference target in `targets.yaml`: `decode(target)` returns a standard Sport.

#### `tests/properties/conftest.py` — 0 → ~50 LOC

Shared Hypothesis strategies. Custom strategies for sport codes, modifier sets (filtered for conflicts), Sport instances, and platform targets.

### Summary

| Path | Before | After | Δ | Note |
|---|---:|---:|---:|---|
| `test_sport.py` | 45 | 40 | -5 | drop tautologies; absorb `test_validate.py` |
| `test_parse.py` | 34 | 28 | -6 | drop same-branch repetition |
| `test_platform_garmin.py` | 44 | 0 | -44 | extract platform-API tests |
| `test_resolve.py` | 29 | 24 | -5 | drop same-branch repetition |
| `test_cross_operation.py` | 22 | 20 | -2 | drop minor repetition |
| `test_pydantic.py` | 21 | 18 | -3 | drop same-field repetition |
| `test_platform_strava.py` | 20 | 0 | -20 | data-mirror assertions |
| `test_platform_healthkit.py` | 20 | 0 | -20 | same |
| `test_matching.py` | 20 | 20 | 0 | keep |
| `test_platform_garmin_training_api.py` | 17 | 0 | -17 | same |
| `test_loader.py` | 16 | 18 | +2 | add rule-2 + smoke |
| `test_modifier.py` | 15 | 9 | -6 | drop stdlib-enum tests |
| `test_encode.py` | 13 | 12 | -1 | refactor TestExactMatch |
| `test_reference_coverage.py` | 12 | 3 | -9 | consolidate |
| `test_decode.py` | 10 | 10 | 0 | keep |
| `test_validate.py` | 9 | 0 | -9 | DELETE |
| `test_build_reference.py` | 4 | 4 | 0 | keep |
| `test_garmin_fit_code.py` (new) | — | 19 | +19 | extracted |
| `test_round_trip.py` | 292 | 24 | -268 | representative |
| `test_performance.py` (new) | — | 4 | +4 | regression bounds |
| `test_sport_properties.py` (new) | — | 6 | +6 | Hypothesis |
| `test_platform_properties.py` (new) | — | 5 | +5 | Hypothesis |
| **Total** | **643** | **264** | **−379** | |

Example-based tests: ~253. Property tests: ~11 (each generating many inputs internally). Total visible: ~264.

## Implementation phases

Each phase is independently mergeable. Run the full test suite + `scripts/lint.py` after each phase to confirm green.

### Phase 1 — Directory restructure

Create `tests/{domain,algorithm,integration,properties}/`. Move existing test files to their new locations. No content changes — pure `git mv`. Add per-directory `__init__.py` if pytest discovery needs them (verify in this phase). Update `pyproject.toml` `[tool.pytest.ini_options]` if needed.

Verify: full suite still passes, all 643 tests still collected.

### Phase 2 — Extract from `test_platform_garmin.py`

Create `tests/algorithm/test_garmin_fit_code.py`. Move `TestGarminFitCode` verbatim. Move decode argument-form tests into a new `TestDecodeArgumentForms` class. Move `TestExhaustive::test_every_known_fit_sport_decodes` into a `TestDecodeExhaustiveSmoke` class. Delete `tests/test_platform_garmin.py` (now at its new location).

Verify: 19 tests in new file pass; previously hardcoded platform encode tests now absent (covered elsewhere already).

### Phase 3 — Delete subsumed platform-specific files

Audit by inspection that every test in `test_platform_strava.py`, `test_platform_healthkit.py`, `test_platform_garmin_training_api.py` is covered by some combination of `test_round_trip.py`, `test_encode.py`, `test_decode.py`, `test_loader.py`, or generator validation. Document the mapping in the PR description. Delete the three files.

Verify: full suite passes; total test count drops by 57.

### Phase 4 — Delete `test_validate.py`

Audit every test against `test_sport.py`. Port any uniquely-covered case first. Delete.

Verify: full suite passes.

### Phase 5 — Trim domain-model files

- `test_modifier.py`: delete the 6 stdlib-enum tests and `test_code_equals_value`.
- `test_sport.py`: drop ~5 tautological tests.
- `test_parse.py`: drop ~6 same-branch tests.
- `test_resolve.py`: drop ~5.
- `test_cross_operation.py`: drop ~2.
- `test_pydantic.py`: drop ~3.

Verify after each file: tests pass; coverage of the affected module remains complete (will be verified empirically once `pytest-cov` lands in phase 11).

### Phase 6 — Rewrite `test_round_trip.py`

Rewrite from scratch as 24 hardcoded tests, each annotated with the code path it covers. Delete the parametrize-over-YAML logic.

Verify: 24 tests pass; pytest output for this file fits on a single screen.

### Phase 7 — Consolidate `test_reference_coverage.py`

Rewrite three tests to iterate over all four platforms internally.

Verify: 3 tests cover all four platforms; failure messages remain informative.

### Phase 8 — Refine `test_encode.py` and `test_loader.py`

Refactor `TestExactMatch`. Add the missing modifier-walk fallback test. Add `test_loader.py` rule-2 test and smoke test.

Verify: full suite passes.

### Phase 9 — Property-based tests (Hypothesis)

Add `hypothesis` to dev dependencies. Create `tests/properties/conftest.py` with shared strategies. Implement `test_sport_properties.py` (~6 properties) and `test_platform_properties.py` (~5 properties). Add `.hypothesis/` to `.gitignore`.

Verify: property tests pass with default `max_examples`. Run with `--hypothesis-show-statistics` once to confirm reasonable coverage of the input space.

### Phase 10 — Performance regression bounds

Add `pytest-benchmark` to dev dependencies. Create `tests/integration/test_performance.py` with 4 benchmarks (one per platform). Measure baseline, set thresholds at ~10× baseline (generous bound), document the numbers in the test docstrings.

Verify: benchmarks pass; intentionally slow down a function locally to confirm thresholds fire.

### Phase 11 — Coverage measurement

Add `pytest-cov` to dev dependencies. Configure in `pyproject.toml` with `--cov=open_sport_taxonomy --cov-report=term-missing --cov-branch --cov-fail-under=95`. Run the suite; if coverage is below 95%, audit the uncovered lines and either add a targeted test or adjust the threshold downward to the highest achievable round number with rationale.

Verify: CI fails if coverage drops; baseline coverage recorded in PR.

### Phase 12 — Linting and formatting (ruff)

Add `ruff` to dev dependencies. Add `[tool.ruff]` config block with the curated rule set above. Run `ruff format src/ tests/ scripts/` to normalize formatting in one shot; commit the diff. Run `ruff check src/ tests/ scripts/` and fix any reported issues — most are auto-fixable with `--fix`. Wire `ruff format --check` and `ruff check` into `scripts/lint.py`.

Order matters: ruff runs *before* mypy. Style and import-hygiene fixes can change which lines mypy analyzes; doing them first means mypy works against the final form.

Verify: `uv run scripts/lint.py` includes the ruff step and exits 0. The codebase is formatted consistently.

### Phase 13 — Strict type checking

Add `mypy` to dev dependencies. Add `[tool.mypy]` config block with `strict = true`, `files = ["src/open_sport_taxonomy"]`. Wire into `scripts/lint.py`. Fix any type errors that surface — likely a small number of `Any` usages or missing annotations.

Verify: `uv run scripts/lint.py` includes the mypy step and exits 0.

### Phase 14 — Mutation testing baseline

Add `mutmut` to dev dependencies. Run `uv run mutmut run --paths-to-mutate src/open_sport_taxonomy/`. Review survivors. For each surviving mutant: either (a) write a targeted test that kills it, (b) judge the mutant equivalent to the original and document, or (c) accept as a known weak spot. Record the resulting kill rate in `CONTRIBUTING.md`. Target ≥80%.

This phase is not in CI; document as a periodic health check (e.g. quarterly).

### Phase 15 — Documentation and acceptance audit

- Add a "Test discipline" section to `CONTRIBUTING.md` codifying the 7 design principles above. Future test additions are evaluated against this bar.
- Update the `## [Unreleased]` section of `CHANGELOG.md` under `Changed`: "Test suite refactored from 643 to ~264 tests with property-based coverage, mutation-tested quality baseline, strict type checking, and a coverage gate. See plan 017."
- Run the full check: `uv run scripts/lint.py && uv run python -m pytest tests/ -q && uv run mutmut results`.

## Acceptance criteria

After all phases:

1. Full test suite passes: `uv run python -m pytest tests/ -q` exits 0.
2. Total visible test count is ~264 (±10 acceptable).
3. `scripts/lint.py` exits 0 — includes schema lint, generator check, reference drift, **ruff lint, ruff format check**, and mypy.
4. **Statement coverage ≥ 95%, branch coverage ≥ 90%** (or the highest round numbers actually achieved, documented).
5. **Mutation kill rate ≥ 80%** (or the actual baseline with surviving mutants documented).
6. `mypy --strict` exits 0 on `src/open_sport_taxonomy/`.
7. **`ruff check` and `ruff format --check` exit 0 across `src/`, `tests/`, and `scripts/`.**
8. Performance benchmarks pass (each platform's encode + decode under 100 µs).
9. Every retained test, when its name is read aloud, describes a distinct property of the system.
10. No test asserts that the YAML mapping data equals itself.
11. No test re-verifies a generator-enforced guarantee except for the consolidated defense-in-depth checks.
12. Directory structure (`tests/{domain,algorithm,integration,properties}/`) is in place and used.
13. `CONTRIBUTING.md` documents the test discipline so this work survives accretion.

## Risk analysis

**Risk:** removing a test removes coverage for a bug class the remaining suite doesn't catch.

**Mitigation:** the per-file disposition explicitly names what catches each removed test's property. Phase 11 (`pytest-cov`) provides empirical verification — if coverage drops below 95% after the trims, the lost coverage is named and re-added before the phase is declared complete. Phase 14 (`mutmut`) is the second line: any class of bug the suite no longer catches surfaces as surviving mutants.

**Risk:** future contributors restore deleted tests because "more tests = safer."

**Mitigation:** Phase 15 adds a `CONTRIBUTING.md` section codifying the principles. The plan is committed under `plans/017-test-suite-refactor.md` and referenced from the CHANGELOG.

**Risk:** the `test_round_trip.py` rewrite picks unrepresentative cases that miss a regression the parametrized version would have caught.

**Mitigation:** the 24 cases are chosen to exercise distinct documented code paths. The generator validation rules 10–11 *do* exercise every preferred entry exhaustively at build time. Phase 9 adds property-based round-trip coverage across generated sports, which is more thorough than the parametrized version was — it explores inputs we'd never write by hand.

**Risk:** Hypothesis tests are flaky or non-deterministic.

**Mitigation:** strategies are deterministic (no `st.randoms()`). The Hypothesis database (`.hypothesis/`) caches failing examples; in CI, set `HYPOTHESIS_PROFILE=ci` with a fixed seed and larger example count for repeatability. Document in `tests/properties/conftest.py`.

**Risk:** mutation testing reveals so many surviving mutants that the phase becomes unbounded.

**Mitigation:** Phase 14 explicitly allows three responses per mutant: add a test, mark equivalent, or accept with documented rationale. The phase succeeds when the surviving set is categorized, not when it is empty.

**Risk:** mypy --strict on a previously-loose codebase surfaces a long tail of issues that bloats the phase.

**Mitigation:** Phase 13 fixes type errors inline; if the count exceeds ~20, the phase splits — fix the easy ones, document the rest as a follow-up. The codebase already uses type hints throughout, so the count is expected to be small.

**Risk:** ruff's default rule set is too aggressive and produces noise.

**Mitigation:** Phase 12 enables a *curated* rule set (`E`, `F`, `B`, `I`, `UP`, `SIM`, `RUF`), not all rules. Each enabled rule family has been chosen for value. Per-line `# noqa` is allowed for legitimate exceptions but must include the rule code and a justification comment.

**Risk:** coverage threshold of 95% is unachievable without adding tests for edge cases that don't matter.

**Mitigation:** Phase 11 explicitly allows lowering the threshold to "the highest round number actually achieved" with rationale. The point is to lock in *current* coverage as the floor, not to chase coverage for its own sake.

**Risk:** intermediate states have inconsistent or duplicate coverage during the phased rollout.

**Mitigation:** each phase is self-contained and runs the full suite before declaring complete. The order ensures no test is deleted before its replacement (if any) exists. Phase 11 (coverage gate) and phase 14 (mutation baseline) come *after* the trim phases — they verify the result, not gate the intermediates.

## Out of scope

- **Doctest of README/CHANGELOG code blocks.** The README's code blocks are illustrative, not executable in isolation (they assume imports, omit context). Converting them to doctests would distort the docs more than it would protect them. The property-based tests cover the same examples more rigorously.
- **Adjacent infrastructure (separate plans).** Three items are deliberately not in this plan because they are workflow/operational concerns rather than test-suite quality, and pulling them in would distract from the focus. Each is worth a dedicated follow-up:
  - **`pre-commit` framework** — runs ruff/mypy/lint locally before push. Cheap to adopt once Phase 12+13 land. Reduces CI friction; doesn't add new quality guarantees beyond what CI already enforces.
  - **`pip-audit` / dependency security scanning in CI** — distinct concern from test suite quality. Worth a separate plan.
  - **GitHub Actions CI configuration** — the plan repeatedly says "CI fails on X." If the project lacks a CI workflow file, adding one is a separate concern from defining what CI runs.

Everything in this plan's scope is what makes the *test suite itself* world-class: tests that earn their place, properties that cover the input space, measurements that verify quality, and static analysis that catches what tests can't.

## Files touched

### Deleted
- `tests/test_platform_garmin.py`
- `tests/test_platform_strava.py`
- `tests/test_platform_healthkit.py`
- `tests/test_platform_garmin_training_api.py`
- `tests/test_validate.py`

### Moved (no content change in phase 1)
- All remaining `tests/test_*.py` → `tests/{domain,algorithm,integration}/test_*.py`

### Rewritten
- `tests/integration/test_round_trip.py`
- `tests/integration/test_reference_coverage.py`
- `tests/algorithm/test_encode.py` (consolidate TestExactMatch)

### Trimmed
- `tests/domain/test_sport.py`
- `tests/domain/test_parse.py`
- `tests/domain/test_resolve.py`
- `tests/domain/test_modifier.py`
- `tests/domain/test_cross_operation.py`
- `tests/domain/test_pydantic.py`

### New files
- `tests/algorithm/test_garmin_fit_code.py`
- `tests/integration/test_performance.py`
- `tests/properties/conftest.py`
- `tests/properties/test_sport_properties.py`
- `tests/properties/test_platform_properties.py`
- `tests/__init__.py` and per-directory `__init__.py` (if needed for pytest discovery)
- `tests/conftest.py` (if shared fixtures emerge)

### Configuration
- `pyproject.toml` — add `pytest-cov`, `hypothesis`, `pytest-benchmark`, `mypy`, `mutmut`, `ruff` to dev deps; add `[tool.pytest.ini_options]` with coverage flags; add `[tool.mypy]` block; add `[tool.ruff]` and `[tool.ruff.lint]` blocks; add `testpaths`.
- `.gitignore` — add `.hypothesis/`, `.mutmut-cache`, `htmlcov/`, `.coverage`, `.ruff_cache/`.
- `scripts/lint.py` — wire in ruff (lint + format check) and mypy steps.

### Documentation
- `CONTRIBUTING.md` — new "Test discipline" section.
- `CHANGELOG.md` — `## [Unreleased]` entry under `Changed`.
