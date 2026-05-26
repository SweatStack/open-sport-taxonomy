# Platform translation

OpenSportTaxonomy translates between OST sports and platform-native codes in both directions. This document specifies the algorithms so any language can produce identical behavior from the YAML mapping files alone.

## Data model

A **mapping** is a YAML file under `mappings/` with two sections:

- `fallback` — the platform code to return when no entry matches.
- `mappings` — a list of entries, each with:
  - `ost` — an OST sport code (e.g. `cycling.road`)
  - `modifiers` (optional) — a list of OST modifier codes (e.g. `[virtual]`)
  - `target` — the platform-native code

Every mapping is a **bijection**: each `target` value appears in at most one entry across all entries in the file. Implementations should assert this at load time. The reverse table is `{entry.target → (entry.ost, entry.modifiers)}`.

## Encode (`Sport → target`)

Inputs: a `Sport` with `code` (string) and `modifiers` (set of strings).

1. Look up `(sport.code, sport.modifiers)` in the forward table. Hit → return the target.
2. If `sport.modifiers` is non-empty, look up `(sport.code, ∅)`. Hit → return.
3. For each ancestor of `sport.code` in the dot-notation hierarchy, from nearest to furthest:
   a. If `sport.modifiers` is non-empty, look up `(ancestor, sport.modifiers)`. Hit → return.
   b. Look up `(ancestor, ∅)`. Hit → return.
4. Return the platform's `fallback`.

The ancestor sequence of `cycling.road` is `cycling`. The ancestor sequence of `generic` is empty.

## Decode (`target → Sport`)

Inputs: a platform code (the same shape as the `target` field).

1. Look up `target` in the reverse table. Hit → return `Sport(code, modifiers)`.
2. If the platform defines a **reducer**, iterate it. For each coarser candidate (other than `target` itself), look up the reverse table. Hit → return.
3. Return `Sport("generic")`.

A reducer is a function `target → iterator[target]` that yields progressively less-specific platform codes. It is platform-specific and optional.

## Reducers, per platform

Only Garmin FIT defines a reducer in this release:

> Given `(sport_id, sub_sport_id)`, yield `(sport_id, sub_sport_id)`, then — if `sub_sport_id != 0` — `(sport_id, 0)`.

Strava, Apple HealthKit, and Garmin Training API have no reducer. Their decode is exact-match-or-fallback.

## Round-trip invariant

For every entry `(ost, modifiers, target)` in a mapping:

```
encode(Sport(ost, modifiers)) == target
decode(target) == Sport(ost, modifiers)
```

This is the load-bearing test that justifies the bijection requirement. Implementations should test it exhaustively over the mapping data.

Note: not all `Sport` values round-trip — only those that appear as `(ost, modifiers)` in a mapping entry. For instance, `Sport("cycling.cyclocross")` encodes to Strava `"Ride"` via the parent-walk, but `decode("Ride")` returns `Sport("cycling")` (which is what's actually stored as Strava). This is correct lossy collapse, not a bug.

## Input validation for Garmin FIT

FIT exposes sport and sub_sport as both integer enum values and string names (the FIT SDK profile defines them; see `reference/garmin-fit-sdk/`). The Python reference implementation accepts either.

- **Names** are validated against the SDK enum tables. Unknown names raise an error — they are almost always typos.
- **Ints** are accepted as-is. Unknown ids may be future SDK additions; forward-compat matters more than typo detection in this case.

Other platforms accept their natural primitive (`str` or `int`) without name-table validation. Reference enum tables for those platforms may be added in the future and would enable the same typo guard.

## Why a bijection?

A many-to-one forward mapping (the same target reached by multiple `(ost, modifiers)` pairs) makes the reverse direction ambiguous: which OST should `decode(target)` return? Rather than annotate the YAML with a "canonical" flag, we delete forward-redundant entries — entries whose target the encode parent-walk would reach anyway. After deletion, the bijection is self-evident in the data and the reverse map is just `{v: k for k, v in mappings}`.

The deletion rule:

> If, after preserving its modifiers, walking up from `entry.ost` reaches an entry with the same `target`, delete `entry`.

Applied mechanically. The bijection assertion at construction time catches any mistake.
