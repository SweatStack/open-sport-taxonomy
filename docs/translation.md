# Platform translation — format v3

This document is the normative specification for OpenSportTaxonomy mapping files. A conforming implementation in any language must produce identical behavior from the YAML data alone.

## Concepts

A **mapping file** translates between OST sport strings and a single platform's native sport identifiers. One file per platform, under `mappings/<platform>.yaml`.

- **OST sport string** — the canonical OST identifier, of the form `code` or `code+modifier[+modifier...]` (e.g. `cycling.road`, `cycling+stationary`). Modifiers are sorted alphabetically.
- **Target** — the platform's native sport identifier. Shape is platform-specific: FIT uses `{sport, sub_sport}` integer pairs; Strava uses strings; HealthKit uses integers; Garmin Training API uses strings; Wahoo uses integers; Polar uses strings; Suunto uses integers.
- **Entry** — one row in the mapping file: a `target` paired with the `sport` it decodes to (or `null` for "no OST equivalent").
- **Preferred entry** — the unique entry per non-null `sport` that is used for encoding.

The mapping file is keyed by the **finite** side (platform targets). OST sport strings, which have an unbounded combinatorial space, appear as annotations on platform values. This direction is intentional: it makes coverage structurally enforceable — every value in the platform's reference enum must appear as a row.

## Reference data contract

Each platform's `reference/<platform>/targets.yaml` is the authoritative enumeration of legal target values. It is consumed by the loader (validation rules 5–6), the linter, and the scaffolder.

How `targets.yaml` is produced is platform-specific: a per-platform build script under `scripts/build_reference/<platform>.py` derives it from the platform's upstream source data (FIT's `sports.yaml × sub_sports.yaml` filtered by `associated_sports`; Strava's `sport_types.yaml`; etc.). The runtime never invokes these scripts — they run at commit time. CI runs them and asserts `git diff --exit-code` to catch reference drift.

## File structure

```yaml
format_version: 3
platform: <platform_id>
platform_version: <version string of the bundled platform spec>

fallback:
  encode: <target value returned when no encode candidate matches>
  decode: <OST sport string returned when no decode candidate matches>

target_coarsening:                          # optional
  - <rule>
  - <rule>

entries:
  - target: <platform value>
    sport: <OST sport string> | null
    preferred: <bool>                       # optional, default false
```

Rows in `entries` are sorted lexicographically by `target` so the file scans side-by-side with `reference/<platform>/targets.yaml`.

### Field reference

| Field | Required | Meaning |
|---|---|---|
| `format_version` | yes | Integer. Must equal `3`. |
| `platform` | yes | Platform identifier; must match the directory name under `reference/`. |
| `platform_version` | yes | Version string of the bundled platform spec (informational; not parsed). |
| `fallback.encode` | yes | Platform value returned when no encode candidate matches. |
| `fallback.decode` | yes | OST sport string returned when no decode candidate matches. |
| `target_coarsening` | optional | List of rewrite rules used when decoding targets not present in `entries` (forward-compat with newer platform versions). |
| `entries` | yes | List of rows; one row per legal target in `reference/<platform>/targets.yaml`. |
| `entries[].target` | yes | Platform-specific value. Shape is fixed per platform. |
| `entries[].sport` | yes | OST sport string, or `null` if no OST equivalent exists. |
| `entries[].preferred` | optional | If `true`, this row is the encode target for its `sport`. Default `false`. Forbidden when `sport: null`. |

## Target coarsening

`target_coarsening` rules are consulted **only** when decoding a target that does not appear in `entries`. Because validation rule 6 requires every value in the bundled `targets.yaml` to have a row, coarsening only fires for forward-compat (a target value from a newer platform version than the bundled snapshot).

### Semantics

Each rule independently produces one candidate target by rewriting the original input. Rules apply in declaration order:

1. For each rule, compute `candidate = apply(rule, input_target)`.
2. If `candidate == input_target` (the rule was a no-op for this input), skip it.
3. Otherwise look up `candidate` in `entries`. If found, return its `sport` (or `fallback.decode` if `sport: null`).
4. If no rule produces a hit, return `fallback.decode`.

**Rules do not chain.** Rule N is applied to the original input target, not to rule N−1's output. This keeps each rule's effect locally inspectable.

### Rule kinds

The only rule kind defined in format v3 is `reset`:

```yaml
target_coarsening:
  - reset: { sub_sport: 0 }                    # set sub_sport to 0
  - reset: { sport: 0, sub_sport: 0 }          # set both fields
```

`reset` sets the listed fields to the values declared inline. Fields not named in the rule pass through unchanged. Every field named in a `reset` rule must exist in the platform's target shape (validation rule 13).

Future rule kinds require a `format_version` bump.

## Validation rules (load-time, strict)

A loader rejects a mapping file if any of these hold. Validation is fail-fast: the library refuses to operate on a partially valid file.

1. `format_version == 3`.
2. `platform` matches a directory under `reference/`.
3. No unknown top-level or per-entry keys.
4. Every `target` in `entries` is unique.
5. Every `target` in `entries` is a member of `reference/<platform>/targets.yaml`.
6. Every member of `reference/<platform>/targets.yaml` has exactly one matching `target` row in `entries`. *(The rule that makes coverage oversights impossible.)*
7. Every non-null `sport` parses as a valid sport string per `schema.yaml`. The sport code must be standard (present in `schema.yaml`); non-standard codes are forbidden in mapping files. Modifiers must be alphabetically sorted in the canonical form.
8. For each non-null `sport` value appearing in `entries`, exactly one entry has `preferred: true`.
9. `preferred: true` is forbidden on rows where `sport: null`.
10. Round-trip on preferred entries: for every preferred entry, `decode(target) == sport` AND `encode(sport) == target`.
11. Decode of non-preferred synonym rows: for every entry with `preferred: false` (and non-null `sport`), `decode(target) == sport`.
12. `fallback.decode` parses as a valid sport string AND equals the `sport` of some preferred entry in `entries` (so the fallback round-trips through encode).
13. Every field named in a `reset` rule exists in the platform's target shape.

## Algorithms

### Decode `target → sport`

```
decode(target):
  entry = entries_by_target.get(target)
  if entry is not None:
    return entry.sport if entry.sport is not None else fallback.decode

  for rule in target_coarsening:
    candidate = apply(rule, target)
    if candidate == target:                         # no-op for this input
      continue
    entry = entries_by_target.get(candidate)
    if entry is not None:
      return entry.sport if entry.sport is not None else fallback.decode

  return fallback.decode
```

A direct lookup against the platform-keyed table, with `target_coarsening` providing forward-compatible fallback for values newer than the bundled snapshot. An entry with `sport: null` short-circuits to `fallback.decode` — the row's author asserted "no OST equivalent" and that assertion is respected.

### Encode `sport → target`

```
encode(sport):
  for candidate in ost_hierarchy_walk(sport):
    entry = preferred_index.get(candidate)
    if entry is not None:
      return entry.target
  return fallback.encode

ost_hierarchy_walk(sport):
  # Candidate enumeration. Modifiers dominate discipline depth.
  yield (sport.code, sport.modifiers)               # exact
  for ancestor in strict_ancestors(sport.code):     # nearest first
    yield (ancestor, sport.modifiers)
  if sport.modifiers:
    yield (sport.code, ∅)
    for ancestor in strict_ancestors(sport.code):
      yield (ancestor, ∅)
```

`preferred_index` is built at load time by selecting rows with `preferred == true` and inverting them: `(sport.code, frozenset(sport.modifiers)) → target`.

`strict_ancestors(code)` yields the dot-notation ancestors of `code`, nearest first: `strict_ancestors("cycling.road.crit") = ["cycling.road", "cycling"]`. The root code (e.g. `cycling`) has no strict ancestors.

#### Why modifiers dominate

Modifiers like `stationary`, `virtual`, `assisted` describe measurement circumstances that materially change activity interpretation (indoor vs outdoor, electric vs human-powered). Discipline depth is a finer-grained categorization *within* the same circumstances. The hierarchy walk preserves the more semantically important axis: dropping `+stationary` to keep `.road` would render an indoor trainer ride as a 40 km outdoor route — a worse error than dropping `.road` to keep `+stationary` (correctly indoor, less specific discipline).

This is a deliberate change from format v1, which let discipline depth dominate.

### Why the asymmetry is correct

Decode's domain is finite (the platform enum, capped by `targets.yaml`). A lookup is the natural shape. One indexed read; optional forward-compat coarsening.

Encode's domain is unbounded (any OST sport code × any subset of modifiers). A hierarchical search is the natural shape. Multiple candidates ordered by priority.

The two algorithms have different shapes because the data has different shapes. Earlier drafts pursued symmetric algorithms; this was a contortion that obscured the underlying structure.

## Worked examples

### Decode (FIT)

| Input target | Output sport | Path |
|---|---|---|
| `(2, 6)` indoor_cycling | `cycling+stationary` | Direct lookup; preferred row |
| `(2, 5)` spin | `cycling+stationary` | Direct lookup; non-preferred row |
| `(4, 6)` fitness_equipment/indoor_cycling | `cycling+stationary` | Direct lookup; non-preferred row |
| `(1, 1)` running/treadmill | `running+stationary` | Direct lookup; preferred row |
| `(4, 15)` elliptical | `generic` | Row exists with `sport: null` → `fallback.decode` |
| `(2, 99)` future SDK addition | `cycling` | Not in entries; `reset: {sub_sport: 0}` yields `(2, 0)`; that row's `sport: cycling` |
| `(99, 99)` future SDK addition | `generic` | First rule yields `(99, 0)` (miss); second rule yields `(0, 0)` → `generic` |

### Encode (FIT)

| Input sport | Output target | Path |
|---|---|---|
| `cycling+stationary` | `(2, 6)` | Exact match in `preferred_index` |
| `cycling.road+stationary` | `(2, 6)` | Exact miss; walk up tree keeping modifiers; `(cycling, {stationary})` hits |
| `cycling.road+race+stationary` | `(2, 6)` | Same; modifiers preserved while OST tree walks up |
| `cycling.cyclocross` | `(2, 11)` | Exact match |
| `cycling.unknown_discipline` | `(2, 0)` | Walk up to `cycling` (unknown codes have no recorded ancestors in `schema.yaml`, but dot-notation ancestors are computed mechanically) |
| `paragliding` (not in schema) | `(0, 0)` | No preferred entry at any walk step; `fallback.encode` |

## Round-trip properties

For each preferred entry `(sport, target)`:

```
encode(sport) == target
decode(target) == sport
```

For each non-preferred entry `(sport, target_synonym)`:

```
decode(target_synonym) == sport     # one-way: synonyms decode to their canonical sport
encode(sport) != target_synonym     # encode prefers the canonical row's target
```

For `fallback.decode`:

```
fallback.decode parses to a valid Sport
encode(fallback.decode) is the target of some preferred entry
```

These properties are enforced by validation rules 10–12 at load time.

## Notes for implementers

- The loader builds two indexes from `entries`: `entries_by_target` (all rows, used by decode) and `preferred_index` (only `preferred: true` rows, inverted, used by encode).
- `sport.modifiers` is a `frozenset`; index keys must use frozenset to be hashable.
- Sport string canonicalization (sorting modifiers) happens at parse time. Index keys are built from canonical forms.
- `apply(rule, target)` is a small dispatch table on rule kind. Only `reset` exists in v3; adding a kind requires a `format_version` bump.
- `entries_by_target` is keyed by the target value's canonical form; for FIT this is the tuple `(sport_id, sub_sport_id)`. The YAML's `{ sport: 2, sub_sport: 6 }` deserializes to that tuple.

## Future extension (not implemented): `encode_for` — asymmetric granularity

**Status: documented, not implemented.** Recorded here so the design is settled before it is needed. Adopting it requires a `format_version` bump. The trigger to implement is a *second* real instance — today there is exactly one (below).

### The problem it solves

format v3 ties a target's **decode meaning** and its **encode preference** to a single `sport` field on one row. That coupling is fine until a platform's *only* target for a family is named more specifically than the family it must serve — then the two directions pull apart.

Motivating case — **Garmin Training API**. Its sole swimming target is `LAP_SWIMMING`; there is no generic `SWIMMING` target. The faithful behavior is:

- `decode(LAP_SWIMMING) = swimming.pool` — lap swimming *is* pool swimming (the precise truth), **and**
- `encode(swimming) = LAP_SWIMMING` — a generic swim plan must still push as a swim (the only swim bucket exists), not fall through to `fallback.encode = GENERIC`.

In v3 one row cannot express both. `sport: swimming` gives correct encode but coarse decode; `sport: swimming.pool` gives precise decode but sends generic and open-water swims to `GENERIC`. You cannot add a separate `SWIMMING` row, because the platform has no such target. So the file must choose one direction to favor (it currently favors encode: `LAP_SWIMMING → swimming`).

### The field

A row keeps `sport` as its **true decode meaning** and optionally lists the ancestor sports it is also the encode target for:

```yaml
- target: LAP_SWIMMING
  sport: swimming.pool        # decode(LAP_SWIMMING) = swimming.pool  (the truth)
  encode_for: [swimming]      # encode(swimming) = LAP_SWIMMING; descendants reach it via the walk
```

Semantics:

- **Decode** is unchanged: `decode(target) = sport`.
- **Encode**: `preferred_index` is populated from both `preferred: true` (key = the row's own `sport`) and every code in `encode_for` (key = that ancestor sport). `encode(swimming.pool)` still resolves to this row via its own `preferred`; `encode(swimming)` resolves via `encode_for`; `encode(swimming.open_water)` walks up to `swimming` and resolves via `encode_for`.
- **Constraint** (keeps it principled): every code in `encode_for` must be a **strict ancestor** of `sport`. You may declare a precise target as the encode home for a *broader* sport — never for an unrelated or finer one. The "one encode target per sport" rule (validation rule 8) still holds across both mechanisms.

### Effect on round-trip

The strict `decode(encode(s)) == s` (validation rule 10) relaxes for sports encoded via `encode_for`: `encode(swimming) = LAP_SWIMMING`, then `decode(LAP_SWIMMING) = swimming.pool`, so `decode(encode(s))` is a **sub-sport** of `s` — encoding a vague sport and reading it back *sharpens* it to the platform's actual granularity. This is the dual of the existing **coarsening** (encoding a fine sport with no exact target and reading it back yields an *ancestor*). The generalized invariant: a round trip moves only **along the hierarchy** (up or down), never sideways — `decode(encode(s))` is always comparable to `s` in the sub-sport order.

### Why not now

Across the seven bundled mappings, `LAP_SWIMMING` is the **only** row that wants this. A format field + validator + generator change + a relaxed round-trip rule + spec, all for one row, is over-engineering — and Garmin Training API is a push (encode-first) API, so decode precision there is low value. `LAP_SWIMMING → swimming` is correct for the direction that matters. Adopt `encode_for` when a second instance appears; `LAP_SWIMMING` becomes its first user that day. The change is purely additive — existing rows are unaffected.
