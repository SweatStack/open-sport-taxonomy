# Plan 024: Two-version model (spec version + package version)

> **Supersedes the versioning design in [`plans/023`](023-decouple-spec-version-from-package-version.md).**
> 023 decoupled the package version from the schema version but left a *third* axis —
> the per-file `format_version`. This plan collapses format into the spec version, so the
> project has exactly **two** version numbers. Status: implemented in spec `0.9.0` /
> package `0.9.0`.

## Decision

OST is a **standard** with potentially several implementations (the Python package, the
JS web tool, future ports). It carries **two** version numbers, and only two:

1. **Spec version** — the version of the standard itself: the sport + modifier
   **vocabulary**, the **OST string format**, the **mapping-file format**, and the
   **bundled platform mappings**, versioned together under one SemVer line. Lives in
   `schema.yaml` (`version:`). This is the FIT **Profile-version** analog.
2. **Package version** — the version of this Python library. Lives in `pyproject.toml`,
   on its own SemVer line. The FIT **SDK-version** analog.

This matches how mature data standards version: Garmin FIT couples its enum vocabulary and
its message/field structure into one **Profile version**, kept separate from the **SDK
version** that implements it. We do the same — one "what the data/format is" number, one
"what the code is" number.

### Why not three

The earlier model had a standalone integer `format_version` on every mapping file (the
mapping-file *grammar* version). That is conceptually part of "the format," which is part
of the spec — so it is folded into the spec version. The `format_version` field is
**removed** from all mapping files and the loader. Adding a mapping-format feature (e.g.
`encode_for`, added this release) is now just a spec version bump, not a separate number.

### Why not one

Collapsing spec into the package version (or vice versa) would force the spec version to
move on every code-only release (a bug fix would inflate "the standard's version"), and
would tie non-Python consumers of the standard to the Python package's release cadence.
The two genuinely move at different rates.

## The relationship

- **`open-sport-taxonomy` {package} implements OST spec {spec}.** Today: package `0.9.0`
  implements spec `0.9.0`. They coincide now and will diverge the first time a code-only
  release ships (package `0.9.1`, spec stays `0.9.0`).
- **Compatibility is by spec major version.** Data and mappings are interoperable within a
  major: an implementation of spec `M.x` reads anything tagged `M.*` — older minors fully,
  newer minors best-effort (codes it doesn't recognise decode to `generic`, via
  `fallback.decode` + `target_coarsening`). A **major** bump signals a breaking change and
  carries no backward-compatibility guarantee.

The library exposes both numbers:

- `open_sport_taxonomy.version` — the installed **package** version (from
  `importlib.metadata`; single source: `pyproject.toml`).
- `open_sport_taxonomy.taxonomy_version` — the **spec** version (single source:
  `schema.yaml`).

## Bump rules

**Spec version** (`schema.yaml`) — bump when *the standard* changes:

- **patch** — editorial only (a label reworded). No code/format/decode change.
- **minor** — additive & backward-compatible: a new sport/modifier code; a new
  mapping-file feature (e.g. `encode_for`); a new platform mapping; a brand-new row for a
  target that had none.
- **major** — breaking: a code removed/renamed; the OST string grammar changed; the
  mapping format changed so older loaders can't parse it; **or an existing input
  re-interpreted** (a target that used to decode to A now decodes to B).

**Package version** (`pyproject.toml`) — ordinary library SemVer (patch = fix, minor = new
API, major = breaking API), and at least a minor when it carries a new spec version.

**The rule people get wrong:** changing what an existing input decodes to is a
*re-interpretation* → a **major** spec change, not a minor. Adding a new code/mapping is
minor; changing the meaning of an existing one is major.

> **Pre-1.0 caveat.** While OST is `0.x`, the major axis is pinned at 0 and breaking
> changes ride the **minor** number (standard SemVer 0.x behaviour). The major-compat rule
> above becomes binding at `1.0`. That is why this release — which re-interprets generic
> codes as road/classic — ships as `0.9.0`, not `1.0.0`.

## Git tags — one namespace per version line

The two version lines diverge (the package releases more often than the spec), and a single
`v*` namespace can't represent both unambiguously. So each line has its own **prefixed tag
namespace** (the standard monorepo convention — cf. Go modules' `subdir/vX`, Lerna's
`pkg@X`):

- **`spec/vX.Y.Z`** — cut **only when `schema.yaml` changes**. Marks a release of the
  standard. Current: `spec/v0.9.0`.
- **`python/vX.Y.Z`** — cut for **every** Python package release (each PyPI publish).
  Current: `python/v0.9.1`.
- Future implementations get their own: `js/vX.Y.Z`, etc.

Both use the same `vSemVer` format — only the prefix differs (namespaced, not mixed
formats). "Latest spec" = highest `spec/*`; "latest package" = highest `python/*`.

- **Schema pins reference a spec tag:** `…/raw/spec/v0.9.0/schema.yaml` (slashed refs work
  in raw URLs).
- **PyPI is unaffected.** `uv_build` reads a **static** `version` from `pyproject.toml`; the
  build never inspects git, so the tag name has no bearing on what is published. (If the
  project ever adopts a VCS-derived version backend like `hatch-vcs`/`setuptools-scm`, this
  must be revisited.)
- **Tooling note:** some tooling assumes a bare `vX` at the repo root (`git describe`,
  release automation); filter with `--match 'python/v*'` / `--match 'spec/v*'` as needed.
- The pre-split `v0.9.0` tag is retained as a historical alias (it predates the namespaces);
  it is not deleted in case anything pinned it.

## Migration performed this release

- `format_version` removed from all 7 mapping files, the loader (`generate.py`), the
  scaffolder, and the docs. Validation rules renumbered 1–13 (the old rule 1 was the
  `format_version` check).
- `schema.yaml` bumped to the spec version `0.9.0`; `pyproject.toml` to package `0.9.0`.
- `docs/translation.md` reframed: the mapping format has no version field of its own; it is
  governed by the spec version.

## Future

If externally-authored mapping files ever need to travel independently of the package
(third-party mappings), reintroduce a per-file `requires_spec: ">=X.Y.Z"` marker — the
FIT-header pattern (a data file stamps the Profile version it needs). Not needed while all
mappings are bundled with, and validated against, the package's own spec.
