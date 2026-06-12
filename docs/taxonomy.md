# OpenSportTaxonomy — Taxonomy principles

This document defines **what** OST classifies, the **vocabulary** we use to talk about
it, and the **rule** for deciding whether two things are the same modality, a discipline,
a modifier, or separate modalities. It is the canonical reference; `CONTRIBUTING.md` and
`AGENTS.md` point here, and the audit in `plans/021-cross-platform-mapping-audit.md`
applies it.

## Purpose & scope

OST classifies **modalities** — distinct patterns of human movement — so that activity
data from any platform can be normalized, grouped, and prescribed by *how the body
moves*.

It is **deliberately blind** to three things:

1. **Intensity.** A slow jog and an all-out sprint are the same modality. How hard and
   how long are recorded separately and modelled downstream; they are not part of a
   modality's identity.
2. **Metabolic / energy-system demand.** Rowing and cross-country skiing place similar
   demands on the cardiovascular system, yet they are *different modalities* — because
   the movement is different. We group by movement, not by metabolic cost.
3. **Circumstance.** Indoor vs outdoor, virtual, e-assisted, on rollers, raced — these
   are **modifiers**, not separate modalities.

OST is **purist about where one modality ends and another begins** (we will insist that
hand cycling is not cycling, because the body does fundamentally different work), and
**pragmatic about everything else** — names, structure, and granularity follow how
athletes and coaches actually think.

## Terminology

A small, fixed vocabulary. Prefer these words; avoid loose synonyms like "sport,"
"activity," or "type," which mean too many things in this domain.

| Term | Definition |
|---|---|
| **modality** | The unit OST classifies: a distinct **movement pattern** — which muscles do the work and how the body moves — independent of intensity, metabolic demand, and circumstance. |
| **code** | The canonical dotted identifier of a modality: `cycling`, `cycling.road`. |
| **discipline** | A child modality in the tree — a subdivision of a modality for terrain, format, or technique that athletes treat as one sport and that *substitutes upward* (`cycling.gravel` satisfies a plan that says "cycling"). |
| **modifier** | An orthogonal `+` tag for a **circumstance that does not change the movement**: `+stationary`, `+virtual`, `+assisted`, `+roller`, `+race`. Modifiers cross-cut modalities. |
| **canonical string** | The normative serialization and **identity** of a sport: a `code` plus any `+modifier`s, modifiers alphabetically sorted. Identity is the string itself — not catalogue membership. |
| **atom** | A code or a modifier — the declared building blocks a canonical string is composed from. |
| **standard sport** | An entry in the curated **standard-sports catalogue**: a canonical string (a bare code *or* a combination) with a hand-crafted label. The set OST recommends implementing. |
| **label** | The human display name of a sport. Always available — hand-crafted for a standard sport (and for each modifier), composed from the parts otherwise. Presentation only; never identity. |

> **A note on the code.** The Python API's `Sport` class and the term "sport code"
> denote a *modality*; the names are retained for API stability. In prose and new
> documentation, prefer **modality**. Renaming the class is a separate, breaking change
> and is out of scope here.

## What makes two things the same modality

There is **one question**: *do they share the same movement pattern?* Four complementary
lenses ask it from different angles; for a clear case they all agree.

1. **Muscular** — Do the same muscles do the work, in the same way?
2. **Kinematic** (the *shadow* test) — If you saw only the moving silhouette, would they
   look alike?
3. **Biomechanical load** — Do they load the same muscles, tendons, and joints, in the
   same way? *(Plain-language version: after a hard bout, would you be sore in the same
   places?)*
4. **Substitution** (the *coach's* test) — If you had planned a session of one, would you
   accept the other as a valid execution of it?

**Explicitly excluded** from the judgment: intensity, metabolic/energy-system demand,
environment and equipment, and the name itself. A shared word (`…cycling`, `…skiing`,
`…skating`) or shared hardware is **not** evidence of sameness — movement is.

### The ladder

- **Same movement → discipline.** Subdivide a modality for terrain/format/technique.
  *road vs mountain cycling; road vs trail running; pool vs open-water swimming.* Where
  two variants differ slightly in technique but athletes treat them as one sport (*skate
  vs classic XC skiing*), the **substitution test governs**: a coach accepts either for
  an "XC ski" plan, so they are disciplines of one modality.
- **Same movement, only the circumstance differs → modifier.** *indoor cycling =
  `cycling+stationary`; e-bike = `cycling+assisted`; roller skiing = `xc_skiing+roller`.*
  A modifier never changes *which muscles do the work*; if it does, it is not a modifier.
- **Different movement → separate modality.** *hand cycling (arm-powered) vs cycling;
  alpine vs cross-country skiing; kayaking vs rowing; inline skating vs roller skiing.*
  No amount of shared naming or shared equipment overrides this.

### Worked examples

| Pair | Muscular | Kinematic | Biomechanical load | Substitutable | Verdict |
|---|:--:|:--:|:--:|:--:|---|
| Slow jog vs sprint | ✓ | ✓ | ✓ | ✓ | **same modality** (intensity ignored) |
| Road vs mountain cycling | ✓ | ✓ | ✓ | ✓ | same modality → **discipline** |
| Treadmill vs road running | ✓ | ✓ | ✓ | ✓ | same → **modifier** (`+stationary`) |
| Roller skiing vs XC skiing | ✓ | ✓ | ✓ | ✓ | same → **modifier** (`+roller`) |
| Rowing vs XC skiing | ✗ | ✗ | ✗ | ✗ | **separate modalities** (cardio overlap ignored) |
| Hand cycling vs cycling | ✗ | ✗ | ✗ | ✗ | **separate modalities** |
| Inline skating vs roller skiing | ✗ | ✗ | ✗ | ✗ | **separate modalities** |

The biomechanical-load and substitution lenses are operational restatements of the
movement criterion — intuitive for scientists and coaches, and most valuable as the
**tiebreaker at the discipline-vs-separate boundary**, where pure kinematics gets fuzzy.

## Standard sports, atoms, and labels

OST is a **recommended profile over an open format**. The canonical string is an open
identity space; the **standard-sports catalogue** is the curated subset OST recommends.
Three nested levels describe any sport — conflating them (especially under the word
"standard") is the main hazard, so they are named separately:

| Level | Name | Holds when | API |
|---|---|---|---|
| 1 | **well-formed** | the string parses as `code(+modifier)*` (modifiers sorted) | `Sport.parse(s)` succeeds |
| 2 | **known-atoms** | well-formed **and** the code and every modifier are declared atoms (and group-valid) | `Sport.uses_known_atoms` |
| 3 | **standard sport** | the exact canonical string is in the catalogue | `Sport.is_standard` |

Strictly nested: **standard ⊆ known-atoms ⊆ well-formed.** `cycling.road+race` is
well-formed and known-atoms, yet *not* a standard sport — valid and usable, just outside
the recommended catalogue.

- **The catalogue is the primary artifact** (`schema.yaml`'s `sports:`): a hand-maintained
  list, each entry a canonical string + a hand-crafted label, holding **bare codes and
  recommended combinations** uniformly. A combination is just a standard sport whose
  string carries modifiers (`cycling+stationary` → "indoor cycling").
- **Atoms are declared, not derived.** Modifiers are declared in `modifiers:` (they carry
  a group and a label). Codes are the **modifier-free catalogue entries** — every code is
  an explicit bare entry (no implied codes), because the code string is not a usable label
  (it may be abbreviated, e.g. `xc_skiing`).
- **Identity is the canonical string, never catalogue membership.** Adding or removing a
  catalogue entry never changes what a stored string *means* — only whether it is
  *recommended*. Catalogue membership is append-only within a major version (deprecate,
  never remove), binding from 1.0.
- **Mappings reference standard sports only.** Every OST sport used in any
  `mappings/*.yaml` must be a catalogue entry — the catalogue's floor.

### Labels

A sport's **`label`** is its human display name, and is **always available**:

- **standard sport** → its hand-crafted catalogue label (verbatim);
- **anything else** → a label **composed** from the parts: the code's label (or, for an
  unknown code, the code string with `.`/`_` turned to spaces), then, if there are
  modifiers, `" ("` + the modifier labels joined by `", "` + `")"`. An unknown modifier
  falls back to its raw token. Example: `cycling.road+race` → "road cycling (race)";
  `climbing.mountain+solo` → "climbing mountain (solo)".

Labels are **presentation only** — never serialized, never identity, never branched on.
`is_standard` tells a consumer whether a label is curated or composed. Because composed
labels reuse curated ones, re-wording a label re-renders the composed labels built on it;
this is intended and harmless (still an editorial change).

## Operations

Behaviors a conforming implementation should reproduce. They are defined purely over the
canonical string and the catalogue — no platform is involved. (The Python reference
implements them on `Sport`; other ports must match.)

### Modifier groups

Some modifiers declare a **group** (in `modifiers:`) and are then mutually exclusive: a
sport may carry **at most one** modifier from any group. A string with two modifiers from
the same group is *well-formed* (it parses) but is **not** known-atoms and **not** standard,
and the strict constructor rejects it. For example `race` and `commute` are both `purpose`,
so `cycling+commute+race` is invalid; `cycling+race+virtual` is fine (`virtual` is
ungrouped).

### Sub-sport containment

Sport *S* is a **sub-sport** of sport *T* (S is the more specific) iff **both** hold:

- S's code equals T's code or is a descendant of it in the dot tree (`cycling.road` is under
  `cycling`); **and**
- S's modifiers are a **superset** of T's (S carries at least every modifier T does).

So `cycling.road+race` is a sub-sport of `cycling`, of `cycling+race`, and of `cycling.road`;
every sport is a sub-sport of itself (reflexive).

### Resolving to a standard sport

`resolve(s)` maps any well-formed sport to the nearest **standard** sport. It only ever
**drops** information — it never adds a modifier and never adds code specificity. Two
ordered phases:

1. **Climb the code tree.** From s's code, walk *up* the dotted hierarchy to the nearest
   ancestor whose bare form is a standard sport; call it `C`. If none is, `C = generic` (the
   universal fallback, always catalogued).
2. **Drop modifiers to a catalogue entry.** Among all subsets `M′` of s's *known* modifiers
   for which `C + M′` is a standard sport, take the **largest** (ties broken by the smallest
   canonical string). The bare code (`M′ = ∅`) always qualifies, so a result always exists.

The result is `C + M′`. Invariants: `resolve(s)` is always standard; its code is an
ancestor-or-equal of s's code; its modifiers are a subset of s's. Resolution moves only *up
or out*, never *down or in* — the same discipline as decode coarsening
([`translation.md`](translation.md)). Examples: `cycling.road+race` → `cycling.road` (race is
not a catalogued `cycling.road` combination); `running.fell+race` → `running+race`; `parkour`
→ `generic`.

## `null` vs `generic` in mappings

A related convention, for platform mapping files (`mappings/<platform>.yaml`). A row's
`sport` is an OST code, `generic`, or `null`. Choose by **what the platform target
denotes**, not by how granular OST is:

- **`generic`** — the target is the platform's own *unspecified / catch-all* bucket
  ("Other", "Workout", "Unknown", "Sports"). The source genuinely did not say which
  modality.
- **`null`** — the target names a **specific** activity OST has no code for (yoga,
  tennis, elliptical, alpine skiing). You are asserting "no OST equivalent."

**Rule: named-but-unmodelled → `null`; catch-all → `generic`.** Do not route a named
fitness/cardio activity (elliptical, stair climber, cardio class) to `generic` merely
because it is a vague workout — it is a specific activity OST does not model, so it is
`null`. (Both decode to `generic` at runtime via `fallback.decode`; the distinction is
semantic and keeps the data auditable.)
