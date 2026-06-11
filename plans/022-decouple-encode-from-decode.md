# Plan 022: Decouple encode from decode (format v4 — `encode_for`)

> **As-built note.** This was *not* a fresh invention. `docs/translation.md` already
> carried a fully-specified-but-unimplemented design for exactly this, named **`encode_for`**,
> with a **strict-ancestor constraint** and a "round-trip moves along the hierarchy /
> *sharpening*" framing, marked "adopt when a second real instance appears." The garmin_fit
> generic→discipline work is that second instance, so we adopted that design verbatim
> (name, constraint, framing) rather than the working name `encode_aliases` used while
> drafting this plan. Below, read every "alias" as an `encode_for` ancestor; round-trip
> "promotion" is the doc's "sharpening." Implemented and green in format v4.

## Problem

We decided three opinionated decodes for `garmin_fit` (plan to follow plan 021):

- `1/0 running/generic   → running.road`
- `2/0 cycling/generic   → cycling.road`
- `12/0 xc/generic       → xc_skiing.classic`

Rationale: Garmin has **no** road/classic profile, so road runs/rides and classic skis
are written to the *generic* code; the specific disciplines (trail, gravel, mountain,
skate, …) self-label. So on Garmin, "generic" *is* the dominant discipline. (See
[021](021-cross-platform-mapping-audit.md) for the cross-platform candidate list: Strava
`Run`/`Ride`, Suunto running/cycling, Wahoo running — same logic; Polar / Garmin TA /
Apple HealthKit explicitly excluded.)

That decode decision is fine on its own. The trouble is **encode**. Every platform still
produces bare `running` / `cycling` / `xc_skiing` (Strava `Run`, Polar, Suunto, Apple,
Garmin TA, …), so those bare modalities must still encode to a *sensible* Garmin code —
not to `generic/generic (0/0)`, which would drop the sport entirely.

The natural answer is: **both `cycling` and `cycling.road` should encode to
`cycling/generic` (2/0)** — because that is the code a real Garmin device writes for
either. Likewise `running` and `running.road` → `1/0`, and `xc_skiing` and
`xc_skiing.classic` → `12/0`. The dead `street`/`road` codes (`1/2`, `2/7`) should be the
encode target of **nothing**.

**This is not expressible in format v3.**

## The principle

Decode and encode have **different cardinality**, and must be decoupled:

- **Decode is one-to-one.** Each platform code maps to exactly one OST sport.
  `2/0 → cycling.road`.
- **Encode is many-to-one.** Several OST sports legitimately collapse onto one platform
  code. `cycling`, `cycling.road`, `cycling+leisure`, … all → `2/0`.

v3 forces them to be mutual inverses (a bijection on `preferred` rows). That coupling is
the root cause of every workaround we hit — parking bare `cycling` on `mixed_surface`,
then on the dead `road` code; bare `xc_skiing` having *no* home at all.

## Why v3 can't do it (grounded in the code)

From `src/open_sport_taxonomy/_platform.py`:

- `decode(target)` = `entries_by_target[target]` — **one entry per target**
  (validation rule 6). One code → one sport.
- `encode(sport)` = first hit in `preferred_index` while walking
  `_ost_hierarchy_walk(sport)`. `preferred_index` is built by **inverting the preferred
  entries** — so each target is the encode home of **exactly one** sport. Two sports
  cannot both name `2/0` as their encode target.
- `_ost_hierarchy_walk` only walks **child → ancestor** (`sport.parent` chain). The only
  way several sports share an encode target is coarsening *downhill* to a common
  **ancestor**.

The trap: we want `cycling` (general) **and** `cycling.road` (specific) to both land on a
code that decodes to `cycling.road` (the *specific* one). The walk never goes uphill, and
even if it did, decode is single-valued. Formally:

> `decode(2/0)=cycling.road` **and** `encode(cycling)=2/0` cannot coexist in v3. The first
> forces `2/0`'s entry to be `cycling.road`; the second needs `2/0` to be bare `cycling`'s
> encode home — and one entry can't be both.

## Design: encode aliases (format v4)

Add an optional `encode_for` list to a decode entry: **extra OST sports (beyond the
canonical `preferred` sport) whose encode target is this code.**

```yaml
format_version: 4

  - target: { sport: 2, sub_sport: 0 }    # cycling / generic
    sport: cycling.road                   # decode: 2/0 → cycling.road  (opinionated default)
    preferred: true                       # encode: cycling.road → 2/0  (canonical, round-trips)
    encode_for: [cycling]             # encode: cycling → 2/0  too   (alias, encode-only)

  - target: { sport: 2, sub_sport: 7 }    # cycling / road (legacy FR735-era)
    sport: cycling.road                   # decode-only synonym → road (correct!); encode target of nothing
```

Loader change: when building `preferred_index`, also insert `(alias.code, ∅) → target`
for each `encode_for` sport. Aliases integrate naturally into the existing hierarchy
walk, so modifier-bearing variants coarsen onto them for free
(`cycling+leisure → cycling → 2/0`).

### Resulting behaviour (the whole point)

| | decode | encode |
|---|---|---|
| `running` | (from `1/2`, `1/45`) | → `1/0` |
| `running.road` | `1/0`, `1/2` → road | → `1/0` |
| `cycling` | (from `2/7`, `2/10`, …) | → `2/0` |
| `cycling.road` | `2/0`, `2/7` → road | → `2/0` |
| `xc_skiing` | (synonym, if any) | → `12/0` |
| `xc_skiing.classic` | `12/0` → classic | → `12/0` |

No homeless bare modality, no `mixed_surface`, no parking on dead codes. The
`street`/`road` codes correctly **decode** to road and are the encode target of nothing.

**v4 also fixes XC** — the one case that had *no* spare code in v3. `12/0` decodes to
`xc_skiing.classic` and carries `encode_for: [xc_skiing]`, so bare `xc_skiing` (from
Strava/Polar/Suunto/etc.) encodes to `12/0` instead of falling back to generic.

## Validation rule changes

- **Rule 8** (was: "exactly one `preferred` per sport") → "**each non-null sport has
  exactly one encode home**: either a `preferred` entry *or* an `encode_for` mention,
  never both, never neither-when-it-needs-one." For v3 files without aliases this is
  identical to the old rule.
- **Rule 10** (preferred round-trips both ways) → keep for the **canonical** sport only:
  for a preferred entry, `decode(target)==sport` AND `encode(sport)==target`.
- **New rule (alias round-trip invariant).** For every `encode_for` sport `A` on
  target `T` whose canonical (preferred) sport is `P`:
  - `encode(A) == T`  (the alias encodes here),
  - `decode(T) == P`  (decode goes to the canonical, not the alias),
  - and `encode(P) == T`  (so `encode∘decode` is stable on `T`).
  This makes round-trip well-defined: `decode(encode(A)) == P` — an alias sport is
  **promoted** to the platform's canonical discipline on round-trip
  (`cycling → 2/0 → cycling.road`). That promotion is intentional and is exactly the
  "generic = road" semantics; it is documented, not accidental.
- **New rule.** Every `encode_for` target value exists in `targets.yaml`; an alias
  sport is not also a `preferred` sport elsewhere; aliases forbidden when `sport: null`.

## Versioning & scope

- **Decision: bump _all_ mapping files to `format_version: 4`; drop v3 entirely** (no
  legacy/dead format). The loader's `!= 3` gate becomes `!= 4` — a single accepted
  version, one validation code path. Files that don't use `encode_for` are unchanged
  except the version line (v4-without-aliases is behaviourally identical to v3).
- **Phase 1 — `garmin_fit`:** apply the three opinionated decodes + `encode_for` for
  bare `running`/`cycling`/`xc_skiing`; revert the v3 stopgaps (`1/2→running`,
  `2/7→cycling`, `2/49` preferred) to clean decode-only synonyms. Update the ~11 stale
  tests; add alias-mechanism tests.
- **Phase 2 — cross-platform candidates** (from 021): Strava `Run`/`Ride`, Suunto
  running/cycling, Wahoo running — same pattern.
- Touch points: `_platform.py` (index build + encode), the loader/validator,
  `scripts/generate.py`, `docs/translation.md` (§Encode, validation rules, new field),
  `mappings/*.yaml` (version bump where used).

## Decisions

1. **Field name `encode_for`** — adopted from the pre-existing design in
   `docs/translation.md` (not the draft name `encode_aliases`). Reads as "this row is the
   encode target *for* these broader sports." Local to the target's entry → a target's
   full decode+encode story is in one place. DRY: only the exceptions are listed; the
   bijective common case stays implicit in `preferred`.
   - **Strict-ancestor constraint** (from that design): every `encode_for` code must be a
     strict ancestor of the row's `sport` (`cycling` ⊐ `cycling.road`). You may declare a
     precise target as the encode home for a *broader* sport, never an unrelated/finer one.
2. **Encode stays a single home per sport** (one alias mention OR one preferred). No
   sport has two encode targets — keeps `encode` a pure function and the invariant simple.
3. **Promotion on round-trip is a feature, not a bug** — and is pinned by the alias
   round-trip invariant above.

## Rejected alternatives

- **No format change, accept loss:** `decode(2/0)=road`, `encode(road)=2/0`, bare
  `cycling → fallback 0/0`. Violates the principle (bare modality not encodable to a
  cycling code) and silently degrades every cross-platform generic→Garmin translation.
- **Encode-side OST coarsening** ("treat `cycling.road` as `cycling` for encode"): doesn't
  escape the coupling — it still resolves through a `preferred` entry whose decode would
  have to be the ancestor, reintroducing the contradiction.
- **Separate top-level `encode:` table:** fully decouples but duplicates the bijective
  common case for no benefit; `encode_for` expresses only the deltas.
- **`sports: [list]` + `preferred: <string>` per entry** (encode-fan-in-centric):
  functionally equivalent (verified — represents all entry kinds, no new capability), and
  cleaner for the ~15 many-to-one entries, but loses the **66 decode-only synonyms** (a
  decode-only concept doesn't fit an encode fan-in list — needs `sports: []` + a separate
  decode field) and rewrites all ~210 non-null entries across 7 files. `encode_for` is
  additive (touches zero existing rows), keeps decode as the spine, and is
  direction-explicit. Entry mix that drove this: **144 canonical / 66 synonym / ~15
  many-to-one.** The good part of the idea — explicit canonical + shared target — is what
  `encode_for` already provides; `sport:` already names the canonical decode sport, so
  a `preferred` string would only duplicate it.

## Fresh-look review — verified, and honest caveats

Traced against `_platform.py` to confirm no surprises:

- **Modifier routing is unaffected.** The alias key is `(code, ∅)` only, so
  `cycling+stationary` still resolves to its own preferred `(cycling, {stationary}) → 2/6`
  *before* the bare-`cycling` alias is ever consulted. `cycling+leisure` correctly
  coarsens past `(cycling, {leisure})` to `(cycling, ∅)` → `2/0`. No modifier leaks onto
  the alias.
- **No key collision.** `(cycling, ∅)` is no longer produced by a `preferred` row (that
  slot now belongs to `cycling.road`); it is produced solely by the alias. The validation
  rule "an alias sport is not also `preferred` elsewhere" keeps `encode` a pure function.
- **Deeper descendants ride along.** `xc_skiing.double_poling` (no FIT code) coarsens to
  `xc_skiing` → alias → `12/0` → decodes to `classic`. Defensible promotion; flagged, not
  accidental.

Two honest caveats — neither is a blocker, both should be stated up front:

1. **The format *enables* correctness; it cannot *enforce* it.** The `mixed_surface`
   mistake passed v3 lint because it was structurally valid. Under v4 the equivalent
   mis-placement (`encode_for: [cycling]` on the wrong code) would also pass lint.
   What v4 fixes is the *forcing*: v3 made the correct target unreachable; v4 makes it the
   natural choice. Semantic correctness of alias placement remains a review concern — no
   format can decide that `2/0` is the right home and `2/49` is wrong.
2. **Discoverability.** "Where does bare `cycling` encode?" is no longer answerable from a
   `cycling` row (there isn't one); you must find the `encode_for` mention. Mitigation:
   have `generate_reference.py` emit a derived **encode map** (sport → target, aliases
   marked) into `docs/reference.md`, so the many-to-one picture is visible without reading
   the loader.

Not needed now, noted for symmetry: an **encode-only target** (a code we'd write but whose
decode we route elsewhere) has no current use case; `encode_for` reuses existing decode
entries' targets. Add only if a real case appears.

**Verdict.** For the chosen decode policy this is the best available design: minimal
(one optional field), general (real platforms genuinely collapse disciplines on encode —
not a one-off), DRY (only deltas listed), and it resolves all three modalities including
the XC case that had no home in v3. The machinery exists *because* of the opinionated
decode; it pays for itself by being a reusable, correctly-modelled primitive rather than a
patch.
