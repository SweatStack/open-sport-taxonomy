# Plan 023: Decouple the taxonomy (spec) version from the package version

> **Superseded in part by [`plans/024`](024-two-version-model.md)**, which folds the
> per-file `format_version` into the spec version (two versions total, not three). The
> decouple below stands; only the third axis changed.
>
> **Status: implemented.** `open_sport_taxonomy.version` now reads the installed
> package release via `importlib.metadata`; `taxonomy_version` (from `schema.yaml`) is
> exposed alongside it; the equality lint check is removed; `docs/reference.md` shows the
> taxonomy version and is drift-checked in lint. Also folded in: `generate_reference.py`
> is now part of `make generate` and the lint pipeline (closing the staleness gap that
> let it drift to `0.1.0`).

## Decision

OST is a **standard** with potentially multiple implementations (the JS `tool/` already
reads `schema.yaml`/`mappings/` directly; other languages may follow). The **taxonomy
spec** must therefore be versioned **independently** of the Python library that happens to
implement it. (Decision recorded; chosen over collapsing to a single version.)

## Three independent version axes

| version | lives in | versions | bumps when |
|---|---|---|---|
| `format_version` | each `mappings/*.yaml` | the **mapping-file grammar** | a mapping rule/key changes (e.g. v3→v4, plan 022) |
| **taxonomy / spec version** | `schema.yaml: version` | the **vocabulary** (sports + modifiers) **and the OST string format** | a sport/modifier is added/removed/renamed, or the string grammar changes |
| **package version** | `pyproject.toml` | the **Python library release** | any release — bugfix, perf, new API — *even with no vocabulary change* |

These are genuinely different things and will diverge: the package version races ahead on
code-only releases; the spec version moves only when the taxonomy itself changes. A
non-Python consumer cares about the **spec** version and should never have to track the
Python package's release number.

## Current state (the cruft to remove)

- `schema.yaml: version` is the source of truth; `generate.py` bakes it into the library
  as `open_sport_taxonomy.version`.
- `pyproject.toml` carries a **hand-maintained duplicate**, and
  `_check_version_consistency` (in `generate.py`) **asserts the two are equal**.
- The spec version is **not load-bearing** — nothing branches on it; it's identity/display
  only.

So today there are two version fields locked equal by a lint check: the ceremony of two
versions with none of the benefit of independence, and the "taxonomy version" already lies
(it inflates on every code-only release).

## Target

- `schema.yaml: version` → **taxonomy/spec version**. Bump only on a vocabulary or
  OST-string-format change. This is the canonical spec version.
- `pyproject.toml` version → **package version**, independent and self-owned. The library
  reads it from installed metadata (`importlib.metadata.version("open-sport-taxonomy")`)
  rather than a generated hardcode.
- Library surface exposes **both**, unambiguously:
  - `open_sport_taxonomy.version` → package version (library convention).
  - `open_sport_taxonomy.taxonomy_version` → spec version (from `schema.yaml`).
- **Remove** `_check_version_consistency` (the equality assertion). No cross-check
  replaces it — the two are independent by design. (Optionally a soft doc note that the
  package's bundled spec version is whatever `taxonomy_version` reports.)
- `docs/reference.md` header shows the **taxonomy version** (it documents the spec), not
  the package version.

## Mechanics

1. `generate.py`: emit `taxonomy_version = "<schema.version>"` into the generated module;
   stop emitting a hardcoded package `version`.
2. Library `__init__`: `version = importlib.metadata.version("open-sport-taxonomy")`;
   `taxonomy_version` from the generated module. Export both in `__all__`.
3. Delete `_check_version_consistency` and its lint wiring.
4. `pyproject.toml`: keep a normal static `version` (the package release), maintained on
   its own cadence.
5. `generate_reference.py` / template: header uses `taxonomy_version`.

## Migration

Both are `0.8.5` today; they simply stop being forced equal. First package-only release
bumps `pyproject` (e.g. `0.8.6`) while `schema.yaml` stays `0.8.5`. First vocabulary change
bumps `schema.yaml`. No data migration; this is a metadata/policy change.

## Note

Independent of plan 022 (format v4). Can land before, after, or alongside it.
