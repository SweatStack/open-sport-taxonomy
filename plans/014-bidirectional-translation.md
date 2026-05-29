# Bidirectional translation

## Problem

OST translates one way today: `Sport → platform code`. Consumers parsing platform data (FIT files, Strava webhooks, HealthKit exports) need the inverse: platform code → `Sport`. This plan adds bidirectional translation for all four platforms in a single change.

Doing all four together costs ~50% more than FIT alone and avoids transitional debt: the generator's bijection assertion fires platform-wide on first use, the README documents one consistent API, and the `translate` → `encode` rename touches every platform's tests regardless of scope.

## API: `encode` / `decode`

Rename `Platform.translate` → `Platform.encode`. Add `Platform.decode` as its inverse.

`translate` is directional but doesn't say which way. `encode`/`decode` is universally understood (json, codecs), inherently symmetric, and signals "lossy serialization" — matching the README's "translations are lossy by design."

```python
from open_sport_taxonomy.platforms import (
    garmin_fit, strava, apple_healthkit, garmin_training_api,
)

# Encode (existing behavior, renamed)
garmin_fit.encode(Sport.CYCLING_ROAD)              # → GarminFitCode(sport=2, sub_sport=7)
strava.encode(Sport("cycling.road+virtual"))       # → "VirtualRide"
apple_healthkit.encode(Sport.CYCLING_ROAD)         # → 13
garmin_training_api.encode(Sport.CYCLING_ROAD)     # → "CYCLING"

# Decode (new)
garmin_fit.decode(2, 7)                            # → Sport('cycling.road')
strava.decode("VirtualRide")                       # → Sport('cycling.road+virtual')
apple_healthkit.decode(13)                         # → Sport('cycling')
garmin_training_api.decode("CYCLING")              # → Sport('cycling')
```

## `decode` input surface, per platform

Each platform's `decode` accepts the platform's natural primitives — no `GarminFitCode` or other wrapper required at the call site.

| Platform | Signature | Notes |
|---|---|---|
| `garmin_fit` | `decode(sport, sub_sport=0)` | ints or strings, mix allowed |
| `strava` | `decode(sport_type)` | string |
| `apple_healthkit` | `decode(activity_type)` | int |
| `garmin_training_api` | `decode(sport_type)` | string |

For FIT specifically:

```python
garmin_fit.decode(2, 7)
garmin_fit.decode("cycling", "road")
garmin_fit.decode(2, "road")                       # mixed
garmin_fit.decode(sport=2, sub_sport=7)
garmin_fit.decode(2)                               # sub_sport defaults to 0
garmin_fit.decode(*garmin_fit.encode(sport))       # round-trip via NamedTuple unpacking
```

### Input validation policy

Asymmetric on purpose:

- **FIT names** validated against the enum tables in `reference/garmin-fit-sdk/`. Unknown name → `ValueError`. Almost always a typo; silent fallback would mask bugs.
- **FIT ints** accepted as-is. Opaque values may be future SDK enum additions; forward-compat matters more than typo detection here.
- **Strava / Training API strings** accepted as-is for now; unknown strings fall back to `Sport.GENERIC`. Typo validation requires shipping reference enum tables for those platforms (see "Future work" below).
- **HealthKit ints** accepted as-is.

## Schema: no change, only deletions

An earlier draft proposed a `canonical: true/false` YAML flag to break many-to-one ambiguity in reverse lookup. Rejected — bolt-on concept that exists only to patch a redundancy.

The redundancy itself is the real problem. With the parent-walk fix (next section), every entry whose target is reachable by walking up the OST hierarchy is forward-redundant and can be deleted. After deletion, every `target` in every mapping file is unique — a true 1:1 bijection — and the reverse map is `{v: k for k, v in mappings}`.

### The deletion rule

For each entry `(ost, modifiers) → target`:

> If walking up from `ost` (preserving `modifiers`, then dropping them) reaches an entry with the same `target`, delete this entry.

Applied mechanically. The bijection assertion in the generator (see below) catches any mistake.

### Deletions per platform

| Platform | Deletions | Behavioral encode change |
|---|---|---|
| Garmin FIT | 6 | `cycling.time_trial` encodes to `{2, 0}` (was `{2, 7}`); FIT has no `time_trial` sub_sport — mapping to "road" was a fiction |
| Strava | 14 | none — every deleted child reaches the same target via parent-walk |
| Apple HealthKit | 17 | none — same reason |
| Garmin Training API | 0 | already bijective |

Only the FIT `time_trial` case is a real behavioral change. All other deletions produce identical encode outputs via parent-walk; the change is structural (fewer rows in YAML) not observable.

## Required precondition: parent-walk preserves modifiers

`_platform.py:38-43` currently drops modifiers before walking up:

```python
parent = sport.parent
while parent is not None:
    key = (parent.code, frozenset())     # ← modifiers already gone
    ...
```

This means `xc_skiing.classic+roller` after deletion would walk to `xc_skiing` *without* `roller` and hit the regular xc_skiing entry instead of the `+roller` inline-skating entry. The redundancy claim only holds if the walk preserves modifiers one step:

```python
parent = sport.parent
while parent is not None:
    key = (parent.code, mod_codes)       # try with modifiers
    if key in self._mappings: return ...
    key = (parent.code, frozenset())     # then without
    if key in self._mappings: return ...
    parent = parent.parent
```

Strictly more permissive — every case that resolved before resolves identically (exact match and modifier-drop at the current level fire first); only adds new hits in cases that previously fell through. Applies to all platforms.

This is the load-bearing fix that makes the deletions safe. The FIT `xc_skiing.classic+roller` case needs it concretely; the other platforms get it as future-proofing.

## Symmetric lossy collapse

Each side walks its own native hierarchy on a miss:

| Direction | Coarsening | Mechanism | Scope |
|---|---|---|---|
| OST → platform (encode) | many OST codes share a platform target | walk up `Sport.parent`, modifiers preserved | all platforms |
| Platform → OST (decode) | unknown sub_sport under a known FIT sport | reduce `sub_sport` to `0` | FIT only |

`Platform.__init__` takes an optional `reducer` callable; default is identity. FIT supplies:

```python
# platforms/_garmin_fit.py
def _reduce(code: GarminFitCode):
    yield code                                   # exact lookup
    yield GarminFitCode(code.sport_id, 0)        # drop sub_sport
                                                 # → ultimate fallback Sport.GENERIC
```

`Platform.decode` iterates the reducer, returns the first match, falls back to `Sport.GENERIC` if everything misses. Strava, HealthKit, Training API don't supply a reducer — exact match or `Sport.GENERIC`.

This is the only platform-specific code in the runtime. Everything else is data-driven.

## `GarminFitCode`: dual-form value

`encode` for FIT returns a `GarminFitCode` carrying both representations:

```python
GarminFitCode(2, 7)
GarminFitCode("cycling", "road")
GarminFitCode(sport=2, sub_sport="road")           # mixed
code.sport_id == 2
code.sport_name == "cycling"
code.sub_sport_id == 7
code.sub_sport_name == "road"
```

A NamedTuple subclass storing `(sport_id, sub_sport_id)` (hashable, unpackable, equality works across forms), with name lookups as properties. Name↔id tables generated from `reference/garmin-fit-sdk/sports.yaml` and `sub_sports.yaml`. Names validated at construction; ints accepted as-is.

Strava, HealthKit, and Training API encode to flat primitives (`str`, `int`, `str`) — no wrapper type needed.

## Generator changes

`scripts/generate.py` emits, per platform:

- `*_MAPPINGS` (existing)
- `*_REVERSE: dict[target, tuple[code, frozenset[str]]]` — `{v: k for k, v in mappings}`. **Generator asserts the source is bijective** and fails build on duplicates. This is the mechanical replacement for the rejected canonical-flag concept.
- For FIT only: `FIT_SPORT_NAMES`, `FIT_SPORT_IDS`, `FIT_SUB_SPORT_NAMES`, `FIT_SUB_SPORT_IDS` from the reference YAMLs.

The bijection assertion is enforced by `uv run scripts/generate.py --check` in CI. Any YAML edit that introduces ambiguity fails the build.

## Round-trip invariant

For every entry `(ost, modifiers, target)` in every platform mapping:

```python
assert platform.decode(target) == Sport(ost, modifiers=modifiers)
assert platform.encode(Sport(ost, modifiers=modifiers)) == target
```

Enforced as a parameterized unit test iterating all platforms. The second load-bearing safety net alongside the generator-level bijection assertion. Wrong YAML edits can't reach main.

## Language-agnostic specification

OST is an open taxonomy with a Python reference implementation. Anyone implementing OST in another language (JS, Go, Rust, Swift) must produce identical encode/decode behavior from the YAML alone. That requires a spec, not just code.

Add `docs/translation.md` documenting:

**Encode algorithm** (`Sport → target`):

1. Lookup `(sport.code, sport.modifiers)` in the platform's mapping. Hit → return.
2. Lookup `(sport.code, ∅)`. Hit → return.
3. For each ancestor of `sport.code` in dot-notation hierarchy:
   a. Lookup `(ancestor, sport.modifiers)`. Hit → return.
   b. Lookup `(ancestor, ∅)`. Hit → return.
4. Return the platform's fallback.

**Decode algorithm** (`target → Sport`):

1. Lookup `target` in the platform's reverse mapping. Hit → return `Sport(code, modifiers)`.
2. If the platform defines a reducer, iterate it. For each reduced target, lookup. Hit → return.
3. Return `Sport.GENERIC`.

**Bijection invariant.** For every platform, the forward mapping is one-to-one on `target`. Implementations should assert this at load time.

**Round-trip property.** For every entry `(ost, modifiers, target)`: `decode(target) == Sport(ost, modifiers)` and `encode(Sport(ost, modifiers)) == target`. Test exhaustively.

**Garmin FIT reducer.** Given `(sport_id, sub_sport_id)`, yield `(sport_id, sub_sport_id)`, then `(sport_id, 0)`. No other platform defines a reducer in this release.

**Garmin FIT input validation.** Names validated against `reference/garmin-fit-sdk/`; unknown names raise. Ints accepted as-is.

The Python implementation is a reference, not the source of truth — the YAML + this document are.

## Footprint

| File | Change |
|---|---|
| `mappings/garmin_fit.yaml` | delete 6 forward-redundant entries |
| `mappings/strava.yaml` | delete 14 forward-redundant entries |
| `mappings/apple_healthkit.yaml` | delete 17 forward-redundant entries |
| `mappings/garmin_training_api.yaml` | no data change |
| `mappings/*.yaml` headers | reference `docs/translation.md` and the bijection invariant |
| `src/open_sport_taxonomy/_platform.py` | rename `translate` → `encode`; add `decode`; add optional `reducer` parameter; parent-walk preserves modifiers; extend `GarminFitCode` to dual-form |
| `src/open_sport_taxonomy/_platforms.py` (generated) | emit `*_REVERSE` dicts for all platforms; FIT name↔id tables |
| `src/open_sport_taxonomy/platforms/_garmin_fit.py` | wire up `_reduce` callable |
| `src/open_sport_taxonomy/platforms/_strava.py`, `_apple_healthkit.py`, `_garmin_training_api.py` | no change (Platform constructor signature unchanged for these) |
| `scripts/generate.py` | emit reverse dicts + FIT name tables; assert bijection per platform |
| `tests/test_platform_*.py` | rename `translate` → `encode`; parameterized round-trip + decode coverage tests across all platforms |
| `docs/translation.md` | **new** — language-agnostic spec |
| `README.md` § "Platform translation" | rewrite for `encode`/`decode`; show all four platforms in both directions; cross-link `docs/translation.md` |
| `CHANGELOG.md` | document breaking changes (below) |

No new dependencies. No new YAML keys. No new lint rules. No transitional flags.

## Breaking changes (hard rename, no deprecation shim — single known consumer is the maintainer)

- `Platform.translate(sport)` → `Platform.encode(sport)`. All platform instances affected.
- `encode(Sport.CYCLING_TIME_TRIAL)` returns `GarminFitCode(2, 0)` instead of `GarminFitCode(2, 7)`. Only behavioral output change across all four platforms.

Minor-version bump under SemVer; sport codes themselves are unchanged.

## Future work (additive, non-blocking)

- Ship `reference/strava/sport_types.yaml` and `reference/garmin-training-api/sport_types.yaml` enumerating documented platform sport types, so `decode("VirtualRid")` raises on typo instead of silently falling back to `Sport.GENERIC`. Mirrors the FIT input-validation policy. Purely additive.
- HealthKit name input (`decode("HKWorkoutActivityTypeCycling")`) could be supported similarly if a use case emerges. Today HK consumers work with ints.

## What I'm staking on this design

- **Algorithm is platform-agnostic.** One `_platform.py`, one spec, four data files. The only platform-specific runtime code is the ~3-line FIT reducer.
- **Bijection assertion in the generator** replaces the canonical-flag concept. Enforced mechanically, not by convention.
- **Round-trip unit test** is the second independent safety net.
- **Parent-walk-with-modifiers fix** makes the deletion claim true; it's also independently correct (strictly more permissive).
- **Positional primitives on `decode`** keeps wrapper types off every input surface. Users decoding from a FIT parser, a Strava webhook, or an HK export pass exactly the primitives they have in hand.
- **`docs/translation.md`** makes OST a real open taxonomy that's implementable in any language without reading Python.
- **No transitional flags, no shims.** The shape after the change is the shape the project should have forever.

If something changes about a platform in the future, the points of edit are obvious and local: the YAML, optionally the reducer, optionally the reference enum file. No hidden coupling, no platform-aware code in the core.
