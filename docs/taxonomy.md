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
