# Plan 028: Browse the standard sports on the site (catalogue tree)

> **Status: implemented.** A second view on the static site — an interactive,
> always-current tree of the standard-sports catalogue — beside the existing
> translation explorer. Same no-build, fetch-from-GitHub-raw model as
> [`plans/026`](026-docs-site-cloudflare-pages.md). The interactive counterpart of
> the generated [`docs/reference.md`](../docs/reference.md).
>
> **Final site shape:** a landing page at `site/index.html` (hero + two cards) routes to the
> **standard-sports browser** (`site/sports.html`) and the **translation explorer**
> (`site/translate.html`); `translate.js` is the shared pure engine. All three pages share an
> identical header (title linked home, the subtitle "The sport vocabulary your app was
> missing.", and an Overview / Standard sports / Translate nav) and a single SweatStack-voice
> footer. The landing is black/bold (no accent colour); the ⇄ button sits next to its pill. Built on a pure `parseSchema()` in `translate.js`. The browser:
> fixed twisty slot so labels align; CLI-`tree`-style connectors (`│ ├ └`, black, longer
> elbows) via a depth-independent left-gutter; custom expand/collapse (not `<details>`, so the
> action button never toggles a node); strong outlined canonical-string pills. Each sport row
> has a ⇄ button that opens a **native HTML popover** (`popover="auto"` + `popovertarget`,
> one per row) listing how the sport `encode()`s to all seven platforms — the browser handles
> outside-click/Escape dismissal and closing others; JS only positions it on `toggle`. The
> ⇄ button + popover live in a shared `site/xlate-popover.js` module (behaviour and injected
> styles), reused by **both** the browser and the explorer's OST column. Copy is em-dash-free. Scope still excludes a separate modifier panel; compose-and-preview and a
> platform-coverage matrix remain future work.

## Goal

A page where anyone can **browse every standard sport** as a single tree: the modality
codes, with their recommended combinations (which carry the modifiers in their canonical
string) nested under each — filterable, collapsible, and shareable by link. Nothing more —
no separate modifier vocabulary, no grouping explainer.

## Why

- The explorer answers *"how does platform X's sport map to OST?"* Nothing on the site
  yet answers *"what sports does OST define?"* — today the catalogue is only browsable as
  raw `schema.yaml` or the static `reference.md`.
- `0.10.0` made the catalogue a first-class artifact (codes **and** combinations, each
  labelled). It deserves a first-class browsing surface that tracks `main` live.

## Data (reuse the 026 pattern)

- **Fetch `schema.yaml` from GitHub raw:**
  `SCHEMA_URL = https://raw.githubusercontent.com/sweatstack/open-sport-taxonomy/main/schema.yaml`.
  Tracks `main` (edits appear without redeploying); pin to a `spec/vX.Y.Z` tag in the URL to
  freeze. Same availability / ~5-min CDN-cache trade-off documented in 026, and `main` is
  CI-gated.
- **Parse line-by-line, mirroring `parseMapping()`** — `schema.yaml` is regular
  (`- sport:` / `label:`, and `- code:` / `group:` / `label:`). No YAML library: keeps the
  zero-dependency, no-build ethos. Add one pure helper `parseSchema(text)` →
  `{ version, sports: [{sport, label, code, mods}], modifiers: [{code, label, group}] }`.
- **Reuse the existing pure helpers** `parseSport(s) -> {code, mods}` and `ancestry(code)`
  from `translate.js` to split entries and build the tree — no logic duplicated.

## Model → visualization

One tree, the standard sports only:

- **Codes form the tree** (dot notation): modality → disciplines. Collapsible nodes; each
  shows the **label** as the headline and the canonical `code` in mono as the secondary line.
- **Combinations nest under their base code** as leaf rows, showing the full canonical string
  (`cycling+stationary`, `cycling+stationary+virtual`) and its curated label ("indoor
  cycling", "virtual indoor cycling"). The modifiers are simply part of that string — no
  separate modifier list, no group commentary. They render distinctly from child
  *disciplines* (deeper codes) so the two kinds read differently, but both just live under
  their code.
- **Header**: `N codes · M combinations · spec vX.Y.Z` (version read straight from the
  fetched schema).

## Browsability

- **Substring filter** — reuse the explorer's filter box + match-highlighting; matches
  across both the canonical string and the label; auto-expand branches containing a match;
  live match count. (Mirrors the explorer so the two views feel like one tool.)
- **Expand / collapse all.**
- **Deep links** — `#cycling.road` (or `#cycling+stationary`) selects and expands that entry;
  shareable and bookmarkable.

## Site structure & navigation

- Add **`site/sports.html`** (sibling of `index.html`), sharing the header and styles. A
  small top nav switches **Translate** ↔ **Sports**.
- **Why a second page, not in-page tabs:** keeps each view a focused static file (matches
  026's "plain static files" ethos) and is the first concrete step toward 026's planned
  multi-page site (landing page + `explorer/`). The shared logic lives in `translate.js`'s
  exported pure helpers, so there's no duplication. *(Alternative: in-page tabs in a single
  `index.html` — lower nav friction, one file, but a fatter page; recommend the second page.)*
- **Cross-link the views:** clicking a sport offers "see how platforms map this" → opens
  Translate with that sport pre-selected. Ties the catalogue and the translator together
  (nice-to-have; can land in a follow-up).

## No build / deploy

Still just static files. `make serve` (local preview) and `make deploy` (Cloudflare Pages)
are **unchanged** — deploy uploads all of `site/`. No `Makefile` change.

## Steps

1. Confirm `parseSport` / `ancestry` are importable from `translate.js`'s pure layer; add
   `parseSchema(text)`.
2. Build `sports.html`: header + nav, fetch + parse `schema.yaml`, render the code tree with
   combinations nested under their code.
3. Wire the filter (reuse), expand/collapse-all, and deep-linking.
4. Add the nav link from `index.html`; factor shared header/CSS.
5. `make serve` → verify against the live schema (counts equal `reference.md`); `make deploy`.

## Verification

- Every bare code nests correctly; every combination appears under its base code.
- Counts equal `docs/reference.md` (codes / combinations) and the spec version matches
  `schema.yaml`.
- Filter highlights + expands; deep links resolve; DevTools shows `schema.yaml` 200 from
  GitHub raw.

## Out of scope / future

- **Editing** the catalogue — this is a viewer; `schema.yaml` + PRs stay the source of truth.
- **Compose-and-preview widget (compelling stretch):** pick a code + modifiers → live
  canonical string, the **label** (curated or composed), and the level it reaches
  (well-formed / `uses_known_atoms` / `is_standard`). It would showcase the `0.10.0` label
  and three-level logic, but requires porting label-composition + `resolve()` to JS — a
  separate phase, kept honest as its own scope.
- **Per-sport platform coverage** (which platforms map each sport) — needs loading all
  mappings; a future enrichment of the cross-link above.
