# Plan 025: Spec-first repo layout (`python/` subdir, split changelog, tooling boundaries)

> **Status: implemented** (after `0.9.0`). The package now lives in `python/`; the root is
> the spec. As-built refinements beyond the original plan:
> - **Tests separated by deletion, not relocation.** The two pure spec-data tests
>   (`test_build_reference`, `test_reference_coverage`) were *removed* rather than moved to
>   a root suite — their invariants are already enforced by the root spec-lint
>   (`lint_reference_drift`) and the generator's validation rules (3–5 via `generate
>   --check`). `python/tests/` is now library + conformance only; spec validation lives
>   solely in `make lint`. (A language-agnostic conformance-vector suite remains the future
>   step when a second implementation lands.)
> - **lint.py is a PEP 723 root orchestrator** (deps `pyyaml`, `jinja2`): it runs the spec
>   checks itself and delegates package checks to `uv run --directory python …`.
> - **One ruff config, repo-wide:** ruff runs from `python/` with `--config pyproject.toml`
>   applied to both the package and the root `../scripts`, so there's a single lint-rule
>   source.
> - **`pythonpath = ["."]`** added to the package's pytest config so `from tests.…` helper
>   imports work regardless of invocation.
> - **Acceptance gate met:** the rebuilt wheel's `.py` payload is byte-identical to the
>   pre-move `0.9.0` build (METADATA differs only by the intended README swap).
>
> Builds on the two-version model in [`plans/024`](024-two-version-model.md).

## Motivation

The repository is **two artifacts in one git repo**: the **OST standard** (`schema.yaml`,
`mappings/`, `reference/`, `docs/`, the web `tool/`) and a **Python reference
implementation** (`src/`, `tests/`, `pyproject.toml`). Plan 024 split the *versions*; this
plan makes the *structure* reflect that split, so the repo reads as **a standard with
implementations**, not "a Python project that ships some YAML."

The Stripe lens: Stripe keeps the API spec (`stripe/openapi`, its own versioning/changelog)
separate from the SDKs (`stripe-python`, …, each its own version/changelog). At Stripe's
scale that's separate repos; at ours it's **spec-first root + implementation subdirs** —
same principle, scale-appropriate (one repo, clear internal boundary). Signals we are
already a standard: the JS `tool/`, the normative `docs/translation.md`, multi-platform
mappings, and now two version lines.

## Decisions

### D1 — Spec-first root, implementation(s) in subdirs

Root = the standard. The Python package moves to `python/`. Future implementations are
siblings (`js/`, …) sharing the root spec.

### D2 — Two CHANGELOGs

- **`CHANGELOG.md`** (root) — the *spec*: vocabulary, mappings, mapping-format, spec
  version bumps.
- **`python/CHANGELOG.md`** — the *package*: API, bug fixes, "now implements spec X",
  dependency bumps.

Dual-touch changes (e.g. `encode_for`) record the **spec-facing** effect at root and the
**impl-facing** effect in `python/`, cross-referencing. The package log will be lean —
correct, because most churn is the standard.

### D3 — pyproject boundaries: **one** package pyproject; spec tooling as PEP 723 scripts; **no** separate tooling pyproject

This is the crux of "should the generation stuff have its own pyproject." Classify the
tooling by what it *is*, not where it sits:

| Tooling | What it does | Home | Deps via |
|---|---|---|---|
| `build_reference/*.py` | derive `reference/*/targets.yaml` from vendor data (spec data) | root `scripts/` | **PEP 723 inline** (`uv run`, isolated) |
| `generate_reference.py` | render `docs/reference.md` from `schema.yaml` (spec doc) | root `scripts/` | **PEP 723 inline** (`pyyaml`, `jinja2`) |
| spec lint (schema order, reference drift) | validate the *standard's* files | root `scripts/` | PEP 723 inline |
| `generate.py` | validate mappings + generate the **Python** tables (`src/_platforms.py`); imports the runtime to round-trip-check | `python/scripts/` | the package's **dev group** (`pyyaml`) |
| ruff / mypy / pytest | lint + test the **package** | `python/` | the package's **dev group** |

**Verdict: do *not* introduce a third "tooling" `pyproject.toml`.** It would be a redundant
environment to manage. The spec/data/doc tooling is already best expressed as **PEP 723
self-contained scripts** — they declare their own deps inline and run in an isolated env
via `uv run`, needing no project at all. The only tooling that needs a project environment
is `generate.py` (it imports the runtime for round-trip validation), and that belongs *with*
the package it generates, using the package's existing dev group. So:

- **One** `pyproject.toml` — the Python package, in `python/`. Its `dependencies` stay `[]`
  (the shipped wheel is pure); `pyyaml` lives in its **dev** group (a build-time dep for
  regenerating the package from the spec, never shipped).
- **Spec tooling** at root needs **no** pyproject — PEP 723 scripts + `uv run`.

Reconsider only if the spec tooling ever becomes a *distributed product* (e.g. an
`ost-tools` package third parties install to author mappings). Until then, a tooling
pyproject is ceremony without benefit.

### D4 — README split

- **`README.md`** (root) — the standard's front door: what OST is, the taxonomy, links to
  `docs/`, the `tool/`, and "Python package → `python/`".
- **`python/README.md`** — the PyPI long description (install + Python API usage, lifted
  from the current root README's API sections). `pyproject.readme = "README.md"` resolves
  to it.

### D5 — Decompose lint orchestration

`scripts/lint.py` currently mixes spec checks (schema order, reference drift, reference-doc
drift) with package checks (ruff, mypy, `generate.py --check`). Split it:

- **root spec-lint** — schema ordering/orphans, `build_reference` drift, `reference.md`
  drift. (PEP 723 or a tiny root script.)
- **package checks** — ruff/mypy/pytest/`generate --check`, run inside `python/`.
- The **root `Makefile`** is the top orchestrator: `make lint` = spec-lint + `make -C
  python lint`; likewise `test`, `generate`, `build`.

## Target tree

```
/                         ← THE STANDARD
  schema.yaml  mappings/  reference/  docs/  tool/  plans/
  CHANGELOG.md            ← spec changelog
  README.md  LICENSE  CONTRIBUTING.md  AGENTS.md  Makefile
  scripts/
    build_reference/*.py  ← PEP 723 (spec data)
    generate_reference.py ← PEP 723 (spec doc)
    spec_lint.py          ← PEP 723 (schema/reference/doc drift)
  python/                 ← the Python reference implementation
    pyproject.toml  uv.lock  .python-version
    README.md             ← PyPI long description
    CHANGELOG.md          ← package changelog
    src/open_sport_taxonomy/
    tests/
    scripts/generate.py   ← validate mappings + codegen (reads ../../schema.yaml …)
    Makefile (optional)   ← or targets driven from the root Makefile
```

## File-by-file

**Move into `python/`:** `pyproject.toml`, `uv.lock`, `.python-version`,
`src/open_sport_taxonomy/`, `tests/`, `scripts/generate.py`, a package `README.md`, the
package `CHANGELOG.md`.

**Stay at root:** `schema.yaml`, `mappings/`, `reference/`, `docs/`, `tool/`, `plans/`,
`CHANGELOG.md` (spec), `LICENSE`, `CONTRIBUTING.md`, `AGENTS.md`, `Makefile`,
`scripts/build_reference/`, `scripts/generate_reference.py`.

**Split:** `README.md` (→ root standard + `python/` package); `scripts/lint.py` (→ root
spec-lint + package checks).

## The hard parts (where the risk is)

1. **`generate.py` paths.** Today `ROOT = Path(__file__).resolve().parent.parent`. After
   the move it sits at `python/scripts/generate.py`: introduce `REPO_ROOT =
   parents[2]` (reads `REPO_ROOT/schema.yaml`, `REPO_ROOT/mappings/`,
   `REPO_ROOT/reference/`) and `PKG_ROOT = parents[1]` (writes `PKG_ROOT/src/...`). It
   still imports the freshly-generated runtime for round-trip validation — runs fine from
   inside `python/` (editable install on path). `build_reference`/`generate_reference`
   keep their root-relative paths unchanged.
2. **`pyproject [tool.*]` paths** become relative to `python/`: `testpaths = ["tests"]`,
   `coverage.source = ["src/open_sport_taxonomy"]`, ruff `extend-exclude`, mypy `files`.
   These resolve correctly as long as ruff/mypy/pytest run with `python/` as cwd (root
   Makefile uses `make -C python` / `uv run --project python`).
3. **Packaging.** `uv_build` with the src layout in `python/src/` builds correctly when
   invoked from `python/`; wheel name unchanged. **Acceptance gate: the built
   `open_sport_taxonomy-0.9.x` wheel is byte-for-byte equivalent in contents to a
   pre-migration build** (the package is self-contained — the YAML is baked into generated
   Python, never shipped — so the move relocates a clean unit).
4. **Makefile.** Root `Makefile` orchestrates; package targets delegate to `python/`.
5. **CI / `.github`.** None today; when added, jobs `cd python` for package steps and run
   spec-lint at root.

## Verification (migration acceptance)

- `make generate && make lint && make test` green from root.
- `cd python && uv build` → identical wheel contents to pre-migration.
- Fresh `pip install dist/*.whl` in a clean env → `import open_sport_taxonomy`,
  `o.version` / `o.taxonomy_version` resolve.
- `tool/` still loads `../mappings/*.yaml` unchanged (it's root-relative; untouched).
- `git log --follow` works on moved files (use `git mv` so history is preserved).

## Sequencing

1. Ship **`0.9.0`** with the current flat layout (it's release-ready; structure is fine for
   one more release).
2. **Migration PR** (this plan): `git mv` the package into `python/`, fix paths/configs,
   split README + CHANGELOG + lint, verify the acceptance gate. One focused, reviewable PR.
3. Bump the **package** version (e.g. `0.9.1`) for the migration — it's a packaging/layout
   change with no spec change, so **spec version stays `0.9.0`** (the two-version model's
   first real divergence, and a nice demonstration). Tag `v0.9.1` (package tag, per 024's
   divergence rule).

## Risks & mitigations

- **Path breakage** in codegen/configs → covered by `make generate/lint/test` + the wheel
  equivalence gate; do it in one PR so CI validates the whole.
- **Lost git history** on moved files → use `git mv`; verify `--follow`.
- **Editable-install confusion** (running tooling from the wrong cwd) → the root Makefile
  is the single entry point; document `make -C python …` for direct use.
- **Over-engineering** → explicitly *not* doing: separate repos, a tooling pyproject, or
  extracting a language-agnostic validator (see below). Those are deferred until a real
  second implementation or product need exists.

## Future (deliberately deferred)

- **`js/` (and beyond).** When the web tool becomes a real package, it lands beside
  `python/`, sharing the root spec. The layout already accommodates it.
- **Language-agnostic spec validator.** The mapping validator currently lives inside the
  Python `generate.py`. If a second implementation needs to validate mappings
  independently, extract the rules into a spec-level checker (or codify them as a
  schema/JSON-Schema the spec ships). Until then, Python is the reference enforcer and CI
  is the gate — do not extract prematurely.
- **Separate repos.** Only if implementations grow large enough to warrant independent
  release cadences and issue trackers. Not at this size.
