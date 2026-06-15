# Plan 027: Standard sports, atoms, and labels (a recommended profile over an open grammar)

> **Status: proposed (design).** Establishes the conceptual model for what OST *is* — an
> open canonical-string format, a curated catalogue of **standard sports** (each with a
> hand-crafted label), and platform mappings over them. Supersedes the scattered
> label discussion (it was never a plan); informs, but doesn't change, the format/versioning
> work in 022/024.

## 1. Purpose

OST serves two audiences at once, and the model must serve both cleanly:
- **Translation** — map platform sport identifiers to/from OST (Garmin, Strava, …).
- **Standalone adoption** — use OST directly as your own sport vocabulary, with no platform
  in the picture. Here OST's **labels** are the only human-facing layer, so they are
  first-class, not an afterthought.

The unifying frame: **a recommended profile over an open format.** The canonical string is
the open identity space; the standard-sports catalogue is the curated, named subset OST
recommends implementing; mappings live over the catalogue.

## 2. Definitions (the spine — read these first)

Three distinct levels, strictly nested. Conflating them (especially under the word
"standard") is the main hazard, so they are named separately:

| Level | Term | Meaning | Example check |
|---|---|---|---|
| 1 | **well-formed** | The string parses per the canonical grammar `code(+modifier)*`, modifiers sorted. The open identity space — unbounded. | `Sport.parse(s)` succeeds |
| 2 | **known-atoms** | Well-formed **and** its code and every modifier are declared atoms. Interpretable; composable. | code ∈ codes ∧ mods ⊆ modifiers |
| 3 | **standard sport** | The exact canonical string is in the curated **standard-sports catalogue**. Recommended; carries a hand-crafted label. | string ∈ catalogue |

Strict nesting: **standard ⊆ known-atoms ⊆ well-formed.** `cycling.road+race` can be
well-formed ✓ and known-atoms ✓ yet *not* a standard sport ✗ (valid, interpretable, but not
in the recommended catalogue).

**API predicates** (decided — see §7): `Sport.is_standard` → level 3 (in the catalogue);
`Sport.uses_known_atoms` → level 2 (code + every modifier are declared atoms); level 1 is
simply "`Sport.parse(...)` succeeded."

Supporting terms:
- **canonical string** — the normative serialization and identity of a sport: `code`,
  optionally `+modifier…` (modifiers alphabetically sorted). Identity is the *string*, not
  catalogue membership. This is what consumers store, match, and translate on.
- **code** — a dotted modality identifier (`cycling`, `cycling.road`); forms a tree.
- **modifier** — an orthogonal circumstance flag (`stationary`, `virtual`, …), per
  `docs/taxonomy.md`.
- **atoms** — the codes and modifiers; the building blocks.
- **standard sport** — an entry in the catalogue: a canonical string + a label.
- **label** — the human display name of a sport. **Always available**: hand-crafted for a
  standard sport (and for each modifier), composed for a non-standard one (§6). Presentation
  only; never affects identity; `is_standard` tells you whether it's curated or composed.

## 3. Dependencies (what rests on what)

```
canonical-string grammar            (open identity space; the foundation)
        │
        ├─ modifiers (declared: code, label, group)        ← atoms that aren't sports
        │
        └─ standard-sports catalogue  (PRIMARY artifact)
               │  each entry: canonical string + hand-crafted label
               │  includes bare codes AND recommended modifier combinations
               │
               ├─ codes + the modality tree  ← the modifier-free catalogue entries
               │      (atoms, SECONDARY: see §5)
               │
               └─ platform mappings  ── reference standard sports
                      every OST sport used in a mapping MUST be a standard sport
                      (catalogue ⊇ all sports used across mappings — the floor)
```

Key invariants:
- **catalogue ⊇ mapping-used sports.** The catalogue's lower bound is the union of every
  OST sport appearing in any `mappings/*.yaml`. The catalogue may hold **more** (recommended
  sports not yet mapped).
- **tree closure.** Every code that appears (as the code-part of any standard sport) has its
  own bare standard-sport entry (so the modality tree has no orphans, and every code has a
  label).
- **atoms declared.** Every modifier used is declared in `modifiers:`; every code used is a
  bare standard sport.

## 4. How standard sports are defined

The **catalogue is the primary artifact** — a hand-maintained list, each entry a canonical
string plus a hand-crafted label:

```yaml
sports:                              # the standard-sports catalogue
  - sport: cycling
    label: cycling
  - sport: cycling.road
    label: road cycling
  - sport: cycling.mountain
    label: mountain biking
  - sport: cycling+stationary        # a recommended COMBINATION, first-class
    label: indoor cycling
  - sport: cycling+stationary+virtual
    label: virtual indoor cycling
  - sport: cycling+assisted
    label: e-bike ride
  # … etc.
```

- Entries are **bare codes** *and* **recommended combinations**, uniformly — a combination
  is just a standard sport whose canonical string carries modifiers. No special section, no
  overlay.
- **Membership is curated, not generative.** Being a standard sport is *exact-string
  catalogue membership*, deliberately partial. This is safe — unlike enumerating identity —
  because identity stays the open grammar (level 1): a non-catalogue sport is still
  well-formed and usable, just "outside the recommended profile."
- **Floor:** every OST sport used in any mapping must appear here. Migration seeds the
  catalogue with the union of all currently-mapped sports.
- **Governance bar** (kept deliberately light): stay close to **what the mappings
  distinguish** — that's the bulk and its own justification. Add sports beyond the mapping
  floor only with a **solid, legitimate use case**, and apply the **highest bar to new
  disciplines** — a discipline is a new *code* (a real expansion of the modality tree,
  governed by the movement-pattern rule in [`docs/taxonomy.md`](../docs/taxonomy.md)), not
  just a combination of existing atoms. Don't invent finer codes speculatively. (A one-liner
  in CONTRIBUTING, not a rubric.)
- **Stability (binding from 1.0).** Catalogue membership is **append-only within a major
  version**: once a canonical string is a standard sport it stays one — entries are
  **deprecated, never removed** (mirroring the code-stability rule in plan 024). This keeps
  `is_standard` **monotone** — a string's standardness may go absent→present (additive ⇒
  minor) but never present→absent within a major (that's a re-interpretation ⇒ major). While
  OST is `0.x`, breaking changes are still permitted (024's pre-1.0 caveat); the guarantee
  binds at `1.0`.

## 5. Atoms: declared, secondary — not "derived"

Atoms are **secondary to the catalogue in emphasis**, but they are *declared*, not computed
away — because they carry metadata the catalogue can't supply:

- **Modifiers** are declared in their own section (`code`, `label`, `group`). This is
  irreducible: modifier **group** (mutual exclusion) and a modifier's own **label** cannot
  be deduced from the sports list. This is the one place an atom must be declared in full.
- **Codes** are the **modifier-free entries of the catalogue.** A bare standard sport
  *is* the code's declaration — it supplies the code's identity, its label, and (via dot
  notation) its place in the modality tree. So codes aren't a separate redundant list, and
  they aren't a magic derivation either: they're explicit catalogue rows, viewed as the
  code axis. **Every code is an explicit entry — always, no implied single-segment codes** —
  because the code string is *not* a usable human label: it may be abbreviated or terse
  (`xc_skiing`, `cycling.tt`), so its hand-crafted label is mandatory, not optional. The
  unknown-code fallback in §6.1 exists only for codes *outside* the catalogue.

So the "atom view" — the set of codes and the set of modifiers — is a **secondary
projection** for the extension/composition layer (§6), grounded in explicit declarations
(bare sports + the modifiers section), never a free-floating derivation. The headline of
the spec is the catalogue; the atoms are how you reason about sports *outside* it.

## 6. Labels

**One accessor — `Sport.label` — always returns a human-readable string.** "Label" already
means "for humans," so there is no separate `display_label`; the single `label` is curated
when we have a curated name and composed otherwise. `is_standard` (§7) tells a consumer which
of the two it got.

- **Every standard sport has a hand-crafted label. No exceptions, none generated.** The
  label is authored per catalogue entry — including combinations (`cycling+stationary` →
  "indoor cycling"), so idiomatic names are first-class, not composed approximations. For a
  standard sport, `label` returns this curated string verbatim.
- **Every modifier has a hand-crafted label** (in `modifiers:`) — used for composing labels
  in the extension space, since a modifier is never a standalone standard sport.
- Labels are **presentation, unique within the catalogue**, never serialized, never
  branched on. (Full label semantics carry over from the earlier discussion.)
- **Composed labels are derived, so curated-label edits propagate.** Because §6.1 composes
  from a code's and modifiers' labels, re-wording a curated label re-renders every composed
  label that uses it — re-wording `cycling.road` ("road cycling" → "road biking") changes the
  composed label of `cycling.road+race` to "road biking (race)". This is intended and harmless
  (labels are presentation, never identity or serialized) and stays an **editorial / patch**
  change per plan 024; it's noted only so the propagation isn't a surprise.

### 6.1 Composed labels for non-standard sports (core)

For **any** well-formed sport not in the catalogue — *including* one whose code or modifiers
aren't even declared atoms — `label` **composes** one from the parts by a fixed, dumb rule.
Composition is offered universally (level 1), never gated: `label` is presentation, never a
standardness signal — `is_standard` / `uses_known_atoms` are. So there is no reason to withhold
a best-effort name, and no part can fail to render (each axis has a fallback).

> **code-part**, then, if there are modifiers, a space and the **modifier labels** joined by
> `", "` between **parentheses**.

- **code-part** = the **code's catalogue label** when the code is itself a standard sport
  (the common case — usually only the *combination* is non-standard); otherwise the code
  string with **dots and underscores replaced by spaces** (fallback for a code outside the
  catalogue). The fallback is deliberately crude — it only ever fires for an *unknown* code,
  because every known code is an explicit catalogue entry with a hand-crafted label (§5).
- **modifier-part** = `" (" + ", ".join(modifier labels) + ")"`, in canonical (alphabetical)
  order, omitted entirely when there are no modifiers. Each modifier label = its **declared
  label** if the modifier is known, else the **raw token with underscores→spaces** (fallback
  for an undeclared modifier).

Both fallbacks share one transform — `code/token → spaces for "." and "_"` — so the rule is a
single, dumb, total function.

Examples:

| Canonical string | `label` | fallbacks exercised |
|---|---|---|
| `cycling+stationary` (standard) | `indoor cycling` | none — curated catalogue label |
| `cycling.road+race` | `road cycling (race)` | none — code label + declared modifier |
| `cycling.road+stationary+virtual` | `road cycling (stationary, virtual)` | none |
| `climbing.mountain+solo` (code not catalogued) | `climbing mountain (solo)` | code → `.`/`_`→spaces |
| `some_activity.foo+bar` (code not catalogued) | `some activity foo (bar)` | code → `.`/`_`→spaces |
| `cycling.road+wibble` (modifier undeclared) | `road cycling (wibble)` | modifier → raw token |

A composed label is explicitly approximate and is exactly as good as its inputs; `is_standard`
is how a consumer knows it's composed rather than curated. (No `resolve()`-to-nearest fallback
in the label itself — that's a separate operation a caller can choose.)

## 7. The `is_standard` disambiguation — **decided: option A**

Today `Sport.is_standard` means **level 2** (code + modifiers all declared — compositional).
The new model makes "standard sport" mean **level 3** (in the catalogue). One word can't mean
both, so **`is_standard` is realigned to level 3** (catalogue membership — matching the
model's vocabulary), and **level 2 gets its own named predicate**.

Consequences (accepted; single hard cutover):
- `cycling.road+race` flips `is_standard` True→False (it's level-2 but not in the catalogue).
- `resolve()` now targets the nearest *catalogue* sport — precise algorithm in §7.1.
- Breaking, but OST has **no external consumers yet** (only this package and the web tool,
  released together), so this ships as **one hard cutover** — no staged rollout, no compat
  shim. Rides a spec + package version bump per plan 024; called out in both changelogs. (The
  §4 catalogue-stability guarantee binds only from 1.0; pre-1.0 we may still break.)

**Level-2 predicate: `uses_known_atoms` (decided).** It reads as "uses only atoms OST knows,"
it's exact, and *atom* is a defined first-class term in this model (§2/§5). Level 1 stays
"`Sport.parse(...)` succeeded." All three levels — `Sport.parse` success (1),
`uses_known_atoms` (2), `is_standard` (3) — get named explicitly in the API and
`docs/taxonomy.md`.

### 7.1 `resolve()` — precise semantics

`resolve()` maps any well-formed sport to the nearest **standard** sport in two ordered
phases. The governing rule: **resolve only ever drops — it never adds a modifier and never
adds specificity.**

1. **Climb the code tree (first match wins).** From `self.code`, walk *up* the dotted
   hierarchy (`cycling.road.foo` → `cycling.road` → `cycling` → root) and stop at the
   **nearest ancestor whose bare form is a standard sport**; call it `C`. If none is, `C =
   generic` (the universal fallback, always catalogued). Phase 1 fixes `C` and does **not**
   look ahead to modifiers.
2. **Drop modifiers to the closest catalogue entry.** Among all subsets `M' ⊆ M` of the
   *original* modifiers for which `C + M'` is a standard sport, take the **largest** (drop the
   fewest); ties break to the smallest canonical string. Bare `C` (`M' = ∅`) is always such an
   entry (phase 1 guaranteed it), so phase 2 always succeeds.

Result `Sport(C, M')`. **Invariant:** `resolve(s)` is always standard; its code is an
ancestor-or-equal of `s`'s code; its modifiers are a subset of `s`'s. Resolution moves only
*up or out*, never *down or in* — the same "along the hierarchy, never sideways" discipline as
encode/decode coarsening (`docs/translation.md`).

Worked examples — catalogue `{cycling, cycling.road, cycling.road+stationary}`:

| Input | `C` (phase 1) | `M'` (phase 2) | `resolve()` |
|---|---|---|---|
| `cycling.road+stationary` | *(already standard — returns self)* | — | `cycling.road+stationary` |
| `cycling.road+stationary+virtual` | `cycling.road` | `{stationary}` | `cycling.road+stationary` |
| `cycling.road+race` | `cycling.road` | `∅` | `cycling.road` |
| `cycling.gravel+race` | `cycling` | `∅` | `cycling` |
| `farting.silent` (no `farting*` standard) | `generic` | `∅` | `generic` |

The last row is **"never add modifiers"** in force: even if `farting+stinky` were the only
catalogued farting sport, `farting.silent` resolves to `generic`, **not** `farting+stinky` —
resolve will not invent `stinky` to manufacture a match. (Tree-closure aside: if
`farting+stinky` is standard then bare `farting` is too, so the realistic result is `farting`
— still never `farting+stinky`.) This requires `generic` to be a permanent catalogue entry —
asserted as an invariant.

## 8. Schema shape (concrete)

```yaml
version: "X.Y.Z"

modifiers:                 # atom declarations: irreducible (group + label)
  - code: stationary
    label: stationary
  - code: assisted
    label: assisted
  - code: race
    group: purpose
    label: race
  # …

sports:                    # the standard-sports catalogue (PRIMARY)
  - sport: cycling
    label: cycling
  - sport: cycling.road
    label: road cycling
  - sport: cycling+stationary
    label: indoor cycling
  # bare codes (= the code atoms + tree) and recommended combinations, all labelled
```

(Two sections. `sports:` reuses the existing key but its contents broaden from
bare-codes-only to the full catalogue. `modifiers:` is unchanged in spirit.)

**Canonical ordering of `sports:`** — a two-key sort on **(1) code, then (2) modifier list**,
*not* on the raw canonical string (raw-string order puts `+` (0x2B) before `.` (0x2E), which
scatters combinations among codes). Within a code, the **bare entry comes first**, then its
combinations in ascending modifier-list order; modifiers within any string stay alphabetically
sorted (the canonical-form rule). This groups every combination directly under its bare code
and keeps file diffs legible. The generator enforces this order.

## 9. Migration (outline; sized later)

1. **Seed the catalogue.** Rename the per-entry field `code:` → `sport:` across `sports:`
   (its value is now a canonical sport string, not a code). Then scan all `mappings/*.yaml`
   for distinct OST sport strings and add every one not already an entry, each with a
   hand-crafted label (the combinations: `cycling+stationary+virtual`, `running+stationary`,
   `cycling.mountain+assisted`, …). This makes the catalogue ⊇ mapping-used sports.
2. **Validation.** New loader rule: every mapping sport string is in the catalogue
   (exact canonical match) — replacing today's "code is known + modifiers valid." Keep the
   tree/orphan + modifier-declared checks. Add: every catalogue entry has a unique,
   non-empty label; every code-part has a bare entry; every modifier used is declared.
3. **Predicate rename (§7)** + update `resolve()`/matching.
4. **Generation.** `_LABELS` reshaped `{code: label}` → `{canonical_string: label}` (see the
   consumer-by-consumer table in §9.2); the single `Sport.label` returns the catalogue label
   for a standard sport and the composed label (§6.1) otherwise — always a string. No
   `display_label`. **Per-code class constants (`Sport.CYCLING_ROAD`) are dropped** — a
   bare-code-only projection can't represent the catalogue's combinations and would need an
   ugly `+`/`.` naming scheme to complete. Replaced by **`StandardSport`**, a generated
   `Literal` of every catalogue string (codes *and* combinations), **exported for users to
   annotate their own variables/fields** (`x: StandardSport = "cycling+stationary"` →
   autocomplete + mypy typo-checking). The `Sport(...)` / `parse(...)` constructors keep an
   honest `str` signature — they ingest runtime data and validate at runtime, so the catalogue
   is never smuggled into the public type (a `Literal[...] | str` union just collapses to
   `str`, and `LiteralString` would reject the runtime strings we must accept). Discoverability
   without a parallel name vocabulary; no new runtime interface.
5. **Definitions & documentation** (§9.1) — a first-class step, not cleanup.
6. **Versioning.** Catalogue + semantics change ⇒ a **spec** version bump (vocabulary grows /
   "standard" redefined) and a **package** release (API change). Per plan 024.

### 9.1 Definitions & documentation to update (first-class)

Every surface that *defines* or *describes* the model. The vocabulary is part of the spec, so
these change in lockstep with the code — they are deliverables, not follow-ups:

- **`docs/taxonomy.md`** — the canonical glossary. Add **`label`** (undefined here today) and
  the **three-level model** (well-formed / `uses_known_atoms` / standard sport) + the
  **standard-sports catalogue** concept. Everything else points here.
- **`docs/translation.md`** — **validation rule 6 currently reads "the sport code must be
  standard (present in `schema.yaml`)"** — the *old* level-2 definition. Rewrite to: every
  mapping `sport` (and `encode_for` member) is a **standard sport** = an exact canonical match
  in the catalogue. Re-check neighbouring rules/wording that lean on "code is standard."
- **`docs/reference.md`** (generated) — regenerate via `generate_reference.py` so it renders
  the **catalogue** (codes *and* combinations) with labels and the renamed `sport:` field;
  confirm the generator handles combination entries.
- **`README.md`** (root, "Schema format") — describe `sports:` as the standard-sports
  catalogue (codes + combinations), field `sport:`; sanity-check the examples table.
- **`python/README.md`** — API docs for the single **`label`** (always a string; curated vs
  composed), `is_standard` (now catalogue membership), and new **`uses_known_atoms`**. It
  documents the old meanings today.
- **`CONTRIBUTING.md`** — the one-line governance bar (§4) + any "label"/"standard" wording;
  the existing versioning/bump rules stay.
- **Docstrings** — `_sport.py` (`label`, `is_standard`, `uses_known_atoms`), `_modifier.py`
  (`label`).
- **CHANGELOG** (spec + package lines) — the redefinition + `code:`→`sport:` rename are
  breaking-ish; note in both per plan 024.

### 9.2 The `_LABELS` reshape (the crux of the code change)

Today `_LABELS` is `{code: label}` and several members key off it; the catalogue model reshapes
it to `{canonical_string: label}` (codes are just its modifier-free keys). Generation also
derives `_CODES` = the set of code keys (every bare entry; by tree-closure, every code-part)
and reuses the declared `modifiers:` set — the two inputs to the level-2 check. Every consumer
changes with the reshape; listed so none is silently missed:

| Member | Today (code-keyed) | After (catalogue-keyed) |
|---|---|---|
| `is_standard` | `code in _LABELS` (+ modifiers valid) | `self.canonical in _LABELS` (level 3) |
| `uses_known_atoms` | *(new)* | `code in _CODES` ∧ every modifier declared (level 2) |
| `label` | `_LABELS.get(code)` → `str \| None` | catalogue label if standard, else composed (§6) — always `str` |
| `resolve()` | climbs the code axis only | two ordered phases (§7.1), catalogue-keyed |
| `ALL()` | one `Sport` per code | one `Sport` per catalogue entry (now includes combinations) |
| `is_subsport_of` | code-hierarchy comparison | unchanged (independent of `_LABELS`) — re-verify, don't assume |

This is the heart of the implementation, not migration housekeeping — which is why it's a named
section rather than a sub-bullet of step 4.

## 10. Open decisions (resolve before implementing)

(All resolved — see below.)

Resolved: §7 → **A** (`is_standard` = catalogue membership), level-2 predicate =
**`uses_known_atoms`**; labels → a single **`label`** (curated-or-composed, §6/§6.1) with the
composition format fixed; governance bar → §4 (stay close to mappings; legitimate use case
beyond, strictest for new disciplines). **Schema naming:** keep the top-level **`sports:`**
key; rename the per-entry field **`code:` → `sport:`**. The field name should describe its
value: today every value is a bare code, so `code:` is exactly right; under the catalogue the
list also holds combinations (`cycling+stationary`), which are canonical **sport** strings (a
bare code is the modifier-free special case). The rename is itself the signal that the
contents broadened from codes-only to the full catalogue.

This round (standards-review pass): **`resolve()`** given a precise two-phase, drop-only
algorithm (§7.1, with the "never add modifiers" invariant); **catalogue stability** made an
append-only/deprecate guarantee binding from 1.0 (§4); **`_LABELS` reshape** promoted to a
named section enumerating every consumer (§9.2); **composed labels** confirmed universal
(level 1) with code and modifier fallbacks, and curated-label edits documented as propagating
(§6/§6.1); **catalogue ordering** fixed to a (code, modifier) two-key sort (§8); **hard
cutover** accepted — no external consumers, no staged rollout (§7).

**Bare codes: always explicit** (decided). No implied single-segment codes — the code string
isn't a usable label (it may be abbreviated, e.g. `xc_skiing`), so every code needs its own
hand-crafted label (§5). No open decisions remain.

## 11. Out of scope
- Localized labels (English only; a future layer keyed on the canonical string).
- Putting combinations into an *atom* vocabulary (they're standard *sports*, never new
  codes/modifiers — see the label discussion and `docs/taxonomy.md`).
