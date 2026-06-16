# Plan 029: Filtering demo on the site (hierarchical filtering over a synthetic activity log)

> **Status: implemented.** Shipped as `site/filtering.html` (the fourth nav
> entry, and a third landing-page card). A single text input filters a seeded
> ~150-activity log by **sub-sport containment**: `cycling` matches 59 activities
> across 12 distinct cycling sports, `cycling.road` narrows to 9, and
> `cycling+stationary` to the 2 indoor variants. A live validity badge reports the
> tier the typed string reaches (`malformed` / `well-formed` / `known-atoms` /
> `standard`), and aggressive autocomplete surfaces catalogue sports. The
> canonical `WELL_FORMED` regex was added to [`docs/taxonomy.md`](../docs/taxonomy.md)
> §"The well-formed grammar" (with the `Sport.parse`-is-more-permissive divergence
> flagged as a follow-up); the page mirrors it via a new pure `site/taxonomy.js`
> (`WELL_FORMED`, `classifyTier`, `isSubsport`, `canonical`, `buildAtoms`). The
> seeded generator lives in `site/taxonomy.js`'s sibling `site/activities.js`
> (deterministic `xmur3`→`mulberry32`, weighted-sample-then-repair coverage).
> `translate.js` gained two exports (`parseSport`, `ancestry`) and `parseSchema`
> now also returns the `modifiers:` atoms. Each activity row reuses the shared
> `xlate-popover.js` ⇄ button. Verified end-to-end in headless Chrome.
>
> A fourth view on the static site — a **live demo of OST's
> headline feature, hierarchical filtering** — beside the overview, the
> standard-sports browser ([`plans/028`](028-site-standard-sports-browser.md)),
> and the translation explorer. Same no-build, fetch-from-GitHub-raw, single
> pure-engine model as [`plans/026`](026-docs-site-cloudflare-pages.md). Where
> `sports.html` shows the *vocabulary* and `translate.html` shows
> *interoperability*, this page shows **what the hierarchy buys you in a real
> product**: a synthetic ~150-activity log with a single text-input filter that
> demonstrates sub-sport containment — pick `cycling` and every road, gravel,
> mountain, indoor, and e-bike ride lights up; tighten to `cycling.road` and it
> narrows.

## Goal

A page that makes OST's hierarchical-filtering promise **tangible**: an
artificial but believable activity log filtered by one text box. Typing a
canonical OST string filters the log by **sub-sport containment** (the operation
already specified in [`docs/taxonomy.md`](../docs/taxonomy.md)), with
*aggressive autocomplete* to discover the vocabulary and a *live validity badge*
reporting which canonical tier the typed string reaches. Nothing more — no real
data, no account connection, no editing, no persistence.

## Why (the dev value)

The site today *asserts* the killer feature ("filter on `cycling.road`
specifically, or on `cycling` to also include `cycling.gravel`") but never lets a
dev *feel* it. This page closes that gap and is the strongest single argument for
adoption:

- **It makes the marquee feature tangible.** Click `cycling`, watch road + gravel
  + mountain + indoor + e-bike all light up; tighten to `cycling.road`, watch it
  narrow. That "*that's* what the hierarchy buys me" moment can't come from prose.
- **It is the "what would my own app look like?" preview.** Every fitness app has
  an activity feed with sport filters. Seeing OST drive a familiar feed lets a dev
  map it onto their product in seconds, lowering perceived adoption cost.
- **It proves the catalogue is rich enough for real athletes.** A log spanning
  ~25 sport codes with believable frequency reassures that the vocabulary covers
  actual training, not toy examples.
- **It demos two real OST operations, not a bespoke widget.** The validity badge
  is a live view of the three nested tiers (`Sport.parse`); the filter is a live
  view of **sub-sport containment** (`is_subsport`). The page teaches the spec by
  *running* it.

## Decisions locked (from design discussion)

1. **Data** — a deterministic, **seeded generator at load time** (stable across
   reloads), ~150 activities, a cyclist-runner-who-dabbles persona, **no
   seasonality** (uniform across ~12 months).
2. **Filter UI** — a **single text input** doing triple duty: aggressive
   autocomplete, a live validity badge, and hierarchical filtering. No chips, no
   tree, no separate modifier toggles — modifiers are just part of the string.
3. **Match scope** — a query with no modifier (e.g. `cycling`) includes **all**
   descendants *and* modifier variants. This is the entire point of the page.
4. **No cross-axis filter** — a bare `+modifier` (e.g. `+stationary`) is **not** a
   recognized filter; it has no code to anchor containment, so it reads as invalid.
5. **Canonical grammar** — codify the well-formedness **regex in
   `docs/taxonomy.md`** (the existing home of the validity-tier table); the site
   **reuses** it with a pointer comment. So this PR is *site + a small spec/docs
   addition*, not site-only.

## The canonical well-formedness grammar (the spec/docs change)

[`docs/taxonomy.md`](../docs/taxonomy.md) §"Standard sports, atoms, and labels"
already names the three nested validity tiers but defines tier 1 only by prose
("parses as `code(+modifier)*`") and by "`Sport.parse(s)` succeeds". This plan
adds the **lexical grammar as a single canonical regex** next to that table:

```
# A well-formed OST string: a dotted code path, then zero or more +modifiers.
# Each segment is lowercase letters with single internal underscores; ≥1 letter
# per segment; dots only within the code (never after a +); no empty segments.
WELL_FORMED = /^[a-z]+(?:_[a-z]+)*(?:\.[a-z]+(?:_[a-z]+)*)*(?:\+[a-z]+(?:_[a-z]+)*)*$/
```

The rules it encodes (matching the discussion):

- a **segment** is `[a-z]+(?:_[a-z]+)*` — lowercase letters, single internal
  underscores only (no leading/trailing/doubled `_`), always ≥1 letter;
- the **code** is one segment plus zero or more `.segment` (dot hierarchy, no
  `..`, no leading/trailing dot);
- then zero or more `+segment` **modifiers** — and because modifiers come *after*
  all dots, a dot can never follow a `+` (`cycling+stationary.foo` is rejected);
- no trailing `+`/`.`, no empty parts (`cycling+`, `+stationary`, `cycling..road`
  all rejected); uppercase rejected.

Validated against the catalogue: every entry passes (`xc_skiing.skate+roller`,
`alpine_skiing`, `cycling+stationary+virtual`, `generic`, …). Counter-examples
correctly rejected: `+stationary`, `cycling.`, `cycling..road`, `Cycling`,
`cycling__road`, `cycling+stationary.foo`.

**Scope note — sortedness/dedup is canonicalization, not lexical
well-formedness.** `docs/taxonomy.md` says the canonical string carries modifiers
*sorted*; the regex cannot express ordering. The badge treats a lexical match as
**well-formed**; canonical (sorted, de-duplicated) form is computed separately for
the *standard* check. (Optional refinement: a subtle "non-canonical order" hint;
not required for v1.)

**Known divergence to call out honestly (pre-existing, not fixed here).** The
Python `Sport.parse` is intentionally *more permissive* than this regex — it only
splits on `+` and rejects empty parts, so it would accept uppercase, doubled
underscores, etc. This plan makes the **regex the canonical lexical grammar in the
docs** and has the **site enforce it**; tightening `Sport.parse` (and any port) to
match is a **separate follow-up**, not this PR. The docs addition will note this so
the spec and the lenient reference don't silently contradict.

## Reused OST operations (no bespoke logic)

- **Validity badge = the three nested tiers** (`docs/taxonomy.md`): `malformed`
  (fails the regex) → `well-formed` → `known-atoms` → `standard`. Strictly nested:
  `standard ⊆ known-atoms ⊆ well-formed`. The badge shows the highest tier the
  string reaches, which teaches the "open format, recommended profile" pitch far
  better than a binary valid/invalid — e.g. `cycling.road+race` shows
  **known-atoms** (valid and usable, just not catalogued).
- **Filter = sub-sport containment** (`docs/taxonomy.md` §"Sub-sport
  containment"): activity `S` matches query `Q` iff **`S`'s code equals `Q`'s code
  or is a descendant in the dot tree, AND `S`'s modifiers are a superset of `Q`'s**.
  `Q = cycling` (empty modifier set ⊆ everything) pulls in `cycling.road`,
  `cycling+stationary`, `cycling.mountain+assisted`, … exactly as decided. `Q =
  cycling+stationary` narrows to cycling-family activities carrying `stationary`. A
  bare `+stationary` parses to an empty code and can't be a containment query →
  not a recognized filter, as decided.

## Pure engine: what to add (reuse, don't duplicate)

`translate.js` already holds the line-by-line parsers and the private primitives
this page needs (`parseSport`, `ancestry`). Today only `normalizeTarget`,
`parseMapping`, `parseSchema`, `decode`, `encode` are **exported**, and
`parseSchema` returns only `{ version, sports }` (it stops at `modifiers:`).
Two small, backward-compatible changes:

1. **Export the existing primitives** `parseSport(s) -> {code, mods}` and
   `ancestry(code) -> string[]` from `translate.js` (they already exist, just
   private). No logic change. *(Plan 028's prose already assumed these were
   importable; this makes it true.)*
2. **Extend `parseSchema`** to also parse the `modifiers:` block →
   `{ version, sports, modifiers: [{code, group, label}] }`. Needed for the
   `known-atoms` tier (declared modifiers + their groups). This finally matches the
   shape `plans/028` documented but never implemented — a clean follow-through.

3. **New pure module `site/taxonomy.js`** (no I/O, no DOM), the taxonomy-operations
   counterpart to `translate.js`'s translation engine:
   - `WELL_FORMED` — the regex above, with a comment pointing at
     `docs/taxonomy.md` as the source of truth.
   - `isWellFormed(s)` — `WELL_FORMED.test(s)`.
   - `canonical(s)` — recompose `code + sorted-unique mods` (reuses `parseSport`).
   - `classifyTier(s, atoms)` where `atoms = { codes:Set, mods:Map<code,group>,
     catalogue:Set }` → `"malformed" | "well-formed" | "known-atoms" | "standard"`.
     `known-atoms` requires: known code, every modifier declared, ≤1 modifier per
     group, no duplicate modifiers. `standard` requires `catalogue.has(canonical(s))`.
   - `isSubsport(activitySport, query)` — the containment predicate above (reuses
     `parseSport`); the filter's core.

   *(Lighter alternative: inline these helpers in the page's `<script>`. Rejected —
   a pure, testable module mirrors the project's `translate.js` ethos and keeps the
   regex reusable, which decision 5 calls for.)*

## The synthetic activity log (seeded generator)

A small **deterministic generator** runs at load (no `schema.yaml` dependency for
the *data* — sport strings are chosen from the fetched catalogue so labels and
tiers stay live and correct):

- **PRNG** — a self-contained seeded generator (`xmur3` string-hash → `mulberry32`)
  with a **fixed seed constant**, so the same 150 activities appear every reload.
  (We need our own PRNG regardless — `Math.random` would reshuffle each load.)
- **Persona via weights** — a weighted sport table encoding a cyclist-runner who
  dabbles broadly: heavy `cycling.road` / `running.road` / indoor variants; a long
  tail of swims, hikes, indoor rows, alpine/snowboard, and XC/roller skiing.
  `generic` and `hand_cycling` excluded (not this athlete).
- **Coverage floor, then weighted fill** — seed **one** activity for each showcase
  sport first (so deep branches like `xc_skiing.skate+roller` and combos like
  `cycling+stationary+virtual` always exist for the filter to reveal), then fill
  the remaining ~ (150 − floor) by weighted sampling. Guarantees a non-empty result
  for any catalogued query while keeping a realistic distribution.
- **No seasonality** — day offsets are sampled uniformly across the trailing ~12
  months; rendered relative to "today". Spacing/order are deterministic via the PRNG.
- **Each activity** — `{ date, sport, label, durationSec, distanceM? }`:
  - `sport` from the weighted pick; `label` looked up from the catalogue (all
    generated activities are standard, so labels are curated and exact);
  - `durationSec` / `distanceM` sampled from per-sport plausible ranges (distance
    derived from duration × a plausible speed with light noise; omitted where it
    reads oddly);
  - a deterministic `title` from a small per-sport-family pool ("Z2 endurance",
    "Trainer session", "Lunch run", "Pool intervals", …).
- **Order** — newest first, like a real feed.

The known-atoms teaching (e.g. `cycling.road+race`) happens in the **validity
badge** when a dev *types* such a string — the *log itself* stays all-standard for
realism. Clean separation of concerns.

## The page (`site/filtering.html`)

Reuses the shared header / nav / footer and the established CSS system (variables,
outlined canonical-string pills, zebra rows), matching the other three pages.

- **Lede** — one short paragraph in the existing voice: type a sport, and the log
  filters to it *and everything under it*; tighten the string to narrow.
- **The filter input** (the heart of the page), doing triple duty:
  - **Aggressive autocomplete** over the catalogue (bare codes + combinations),
    matching on both the canonical string and the label, surfaced as a keyboard-
    navigable dropdown (↑/↓/Enter/Esc) with each suggestion showing its tier dot.
    Selecting fills the box and filters.
  - **Live validity badge** beside the field, updating per keystroke, showing the
    highest tier reached: `malformed` / `well-formed` / `known-atoms` / `standard`
    (with a one-line gloss, e.g. "valid and usable, just not in the catalogue").
  - **Filtering** of the log via `isSubsport`, applied for any non-empty
    `well-formed`+ query (empty or `malformed` → no filter, log shown in full; the
    badge carries the state so the page stays calm while mid-token).
- **Teachable match summary** — restates the rule it applied, e.g. *"Showing 38 of
  150 · `cycling` matches its code and 11 sub-sports/variants by sub-sport
  containment."* Surfaces the instructive edge too: a well-formed-but-unknown code
  (`cycling.bmx`, or a partial like `cyc`) → *"well-formed, but no activity's code
  sits under it — 0 of 150"*, teaching that hierarchy matches on **dot segments**,
  not raw substrings (which is what autocomplete bridges).
- **The activity log** — a table consistent with `translate.html`: **Date** ·
  **Sport** (curated label + the canonical OST string in the outlined pill, so the
  value driving every match is always visible) · **Duration** · **Distance**.
  Newest first.
- **Optional ⇄ per row (recommended stretch)** — reuse `xlate-popover.js` to let a
  dev see how each activity's sport translates to all seven platforms, tying all
  four pages together. Costs the seven mapping fetches the other pages already
  make; can land in the same PR or a follow-up.

## Site structure & navigation

- Add **`site/filtering.html`** (sibling of the others), sharing header/styles.
- **Nav gains a fourth entry** — "Filtering" — added to all four pages
  (`index.html`, `sports.html`, `translate.html`, `filtering.html`), each marking
  its own link `aria-current="page"`.
- **Surface it on the landing page** — a third card on `index.html` alongside
  "Standard sports" and "Translate" (the landing's two-column card grid becomes
  three; it already collapses to one column on narrow screens).

## No build / deploy

Still just static files. `make serve` (local preview) and `make deploy`
(Cloudflare Pages, uploads all of `site/`) are **unchanged** — no `Makefile`
change. The page fetches `schema.yaml` (and, for the optional ⇄, the seven
`mappings/*.yaml`) from GitHub raw on `main`, same availability / ~5-min CDN-cache
trade-off documented in `plans/026`.

## Steps

1. **Docs/spec:** add the `WELL_FORMED` regex + rule prose to `docs/taxonomy.md`
   beside the validity-tier table; note the pre-existing `Sport.parse` divergence
   as a flagged follow-up.
2. **Engine:** export `parseSport` / `ancestry` from `translate.js`; extend
   `parseSchema` to return `modifiers`. Add `site/taxonomy.js`
   (`WELL_FORMED`, `isWellFormed`, `canonical`, `classifyTier`, `isSubsport`) with
   a pointer comment back to `docs/taxonomy.md`.
3. **Data:** the seeded generator (PRNG + persona weights + coverage floor) → ~150
   activities; verify determinism (identical across reloads) and branch coverage.
4. **Page:** `filtering.html` — header/nav/footer, fetch+parse the catalogue, render
   the log, wire the text input → autocomplete + validity badge + `isSubsport`
   filter + match summary.
5. **Nav + landing:** add the "Filtering" nav link to all four pages and the third
   card to `index.html`.
6. **(Optional)** wire the per-row ⇄ via `xlate-popover.js`.
7. `make serve` → verify behaviours below; `make deploy`.

## Verification

- **Grammar:** `WELL_FORMED` accepts every catalogue string and rejects
  `+stationary`, `cycling.`, `cycling..road`, `Cycling`, `cycling__road`,
  `cycling+stationary.foo`, `cycling+`.
- **Tiers:** `cycling.road` → standard; `cycling.road+race` → known-atoms;
  `cycling.bmx` → well-formed; `Cycling` → malformed. Badge matches.
- **Containment:** `cycling` matches every cycling descendant *and* modifier
  variant in the log; `cycling.road` narrows; `cycling+stationary` keeps only
  stationary cycling-family activities; `+stationary` is rejected as not a filter;
  the match count is correct and the summary states the rule.
- **Data:** exactly ~150 activities, identical across reloads (determinism);
  every showcase branch present (no catalogued query yields an empty log by
  accident); distribution reads cyclist-runner-with-range.
- **Integration:** nav shows four entries with correct `aria-current`; landing has
  three cards; DevTools shows `schema.yaml` 200 from GitHub raw; (if built) the ⇄
  popover lists all seven platforms.

## Out of scope / future

- **Real data / account connection / editing / persistence** — this is a static
  showcase; the synthetic log is hardcoded-by-seed, not fetched from anyone.
- **Cross-axis (bare-modifier) filtering** — `+stationary` as "everything indoor
  across sports" is deliberately excluded (decision 4). A future enhancement could
  add a second, explicit modifier axis to tell that orthogonality story.
- **Tightening `Sport.parse` (and ports) to the new regex** — the spec/site adopt
  the strict lexical grammar now; aligning the permissive reference parser is a
  separate, flagged follow-up.
- **Seasonality** — uniform now (decision 1); seasonal clustering (winter skiing,
  summer open-water) would add realism later at the cost of generation logic.
- **Per-activity metrics depth** (pace/HR/elevation) — the log carries only what
  the filter demo needs; richer metrics are not the point of this page.
