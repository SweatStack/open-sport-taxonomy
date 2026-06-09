# Plan 021: Cross-Platform Mapping Audit

A consistency audit across all seven platform mappings (`apple_healthkit`,
`garmin_fit`, `garmin_training_api`, `polar`, `strava`, `suunto`, `wahoo`), plus the set
of sports that recur across platforms but have no OST code yet.

## Method

All **649 mapping entries** were extracted programmatically from the seven
`mappings/*.yaml` files and joined `target → name → OST sport → preferred`. Every claim
below is grounded in that dataset, not in recollection. Per-platform shape:

| platform | mapped | generic | null | total |
|---|---:|---:|---:|---:|
| apple_healthkit | 8 | 1 | 75 | 84 |
| garmin_fit | 27 | 1 | 115 | 143 |
| garmin_training_api | 3 | 1 | 5 | 9 |
| polar | 42 | 2 | 131 | 175 |
| strava | 16 | 1 | 39 | 56 |
| suunto | 27 | 6 | 88 | 121 |
| wahoo | 30 | 10 | 21 | 61 |

The `generic` column already flags the headline: **Wahoo uses `generic` 10×; every other
platform uses it 1–2× (Suunto's 6 are duplicate "Sports" slots).**

---

## Part 0 — Purpose & scope (decided)

The audit surfaced that we were resolving inconsistencies without a written purpose. That
purpose is now settled and lives in **[`docs/taxonomy.md`](../docs/taxonomy.md)** (the
canonical reference). In brief:

> OST classifies **modalities** — distinct patterns of human movement — so data from any
> platform can be normalized, grouped, and prescribed by *how the body moves*. It is
> blind to **intensity** (jog ≡ sprint), **metabolic demand** (rowing ≠ XC skiing despite
> similar cardio), and **circumstance** (indoor/virtual/assisted → modifiers). Purist
> about modality boundaries; pragmatic about names and structure.

Vocabulary is narrowed to four terms — **modality** (the unit; the Python `Sport` class
denotes one), **code**, **discipline**, **modifier**. The relatedness rule (one criterion
— *same movement pattern?* — viewed through the muscular, kinematic, biomechanical-load,
and substitution lenses) and the `null` vs `generic` rule are both specified in
`docs/taxonomy.md`. Everything below is an application of it.

---

## Part 1 — Inconsistencies in how we map

### 1.1 Correctness bugs (fix first)

Two activities that are **not roller skiing** are mapped to `xc_skiing+roller`:

| Platform | Target | Name | Maps to | Should be |
|---|---|---|---|---|
| `apple_healthkit` | `30` | `mixedMetabolicCardioTraining` | `xc_skiing+roller` | `null` |
| `garmin_fit` | `{30,0}` | `inline_skating / generic` | `xc_skiing+roller` | `null` (or a future skating code) |

- `mixedMetabolicCardioTraining` is a deprecated HealthKit **cardio** type — nothing to
  do with roller skiing. HealthKit has no roller-skiing type at all, so no row should
  map to `xc_skiing+roller`.
- `inline_skating` is roller-blading, a distinct sport. **Every other platform maps
  inline skating to `null`** (`polar` Inline skating, `strava` InlineSkate, `suunto`
  Roller skating, `wahoo` SKATING_INLINE). Garmin FIT conflating it with cross-country
  roller skiing is an outright error.

These are genuine correctness issues, not stylistic ones. ✅ **Fixed in 0.8.1** — both set
to `null` (they now decode to `generic`). If a `skating` code is added later (Part 2),
revisit `inline_skating`.

### 1.2 `null` vs `generic` — the cross-cutting convention split

**The pure catch-all bucket → `generic` is consistent across all seven platforms**
(`apple` other 3000, `fit` {0,0} generic, `gta` GENERIC, `polar` OTHER_INDOOR/OUTDOOR,
`strava` Workout, `suunto` Sports, `wahoo` OTHER/UNKNOWN). No issue there.

The split is in **named indoor cardio / fitness-equipment activities**:

| Concept | Wahoo | Polar | Suunto | Apple | Garmin FIT |
|---|---|---|---|---|---|
| Elliptical / cross-trainer | `generic` (FE_ELLIPTICAL) | `null` (Cross-trainer) | `null` (Crosstrainer) | `null` (elliptical) | `null` (fitness_equipment/elliptical) |
| Stair climber | `generic` (STAIR_CLIMBER) | `null` | `null` | `null` (stairClimbing) | `null` (stair_climbing) |
| Cardio class / aerobics | `generic` (CARDIO_CLASS) | `null` | `null` (Aerobics) | — | — |
| Generic fitness equipment | `generic` (FE, FE_GENERAL, FE_CLIMBER) | — | — | — | — |
| Offline HR recording | `generic` (TICKR_OFFLINE) | — | — | — | — |

**Wahoo is the lone outlier** (5 of 7 platforms route named non-endurance activities to
`null`). The divergence is **semantic, not functional** — both `null` and `generic`
decode to `generic` at runtime via `fallback.decode`. It only matters for intent: "we
classified this as the generic sport" vs "no OST equivalent".

**Recommendation (refined against [`docs/taxonomy.md`](../docs/taxonomy.md) §`null` vs
`generic`):** the rule is *named-but-unmodelled → `null`; catch-all → `generic`*. The
sharper split is between **named machines/classes** and **genuinely-unspecified**
targets:

- → `null` (named, OST doesn't model the modality): `FE_ELLIPTICAL`, `FE_CLIMBER`,
  `CARDIO_CLASS`, `STAIR_CLIMBER`.
- → stay `generic` (the modality is genuinely unknown): `FE` and `FE_GENERAL`
  ("fitness equipment, type unspecified"), `TICKR_OFFLINE` (offline HR recording, sport
  unknown), plus `WORKOUT`, `OTHER`, `UNKNOWN`.

This is a refinement of an earlier draft that nulled `FE`/`FE_GENERAL`/`TICKR_OFFLINE`
too — re-assessing with the crisp rule, those are catch-alls, not named activities.
✅ **Fixed in 0.8.1.** (`FE_BIKE`/`FE_ROWER`/`FE_TREADMILL` keep their correct
`*+stationary` codes.)

### 1.3 Same real-world sport → different OST code

| Concept | → `cycling`/mapped | → `null` | Note |
|---|---|---|---|
| **Hand cycling** | `wahoo` HANDCYCLING, `polar` Handcycling, `suunto` Hand cycling → `cycling` | `apple` handCycling, `garmin_fit` cycling/hand_cycling → `null` | Hand cycling is arm-powered — a separate modality, not a cycling discipline ([`docs/taxonomy.md`](../docs/taxonomy.md)). ✅ **Fixed in 0.8.1**: all five now `null`/`generic`. A `hand_cycling` root (Part 2) would let them carry the real modality. |
| **Backcountry skiing** | — | — | ✅ **Resolved** (0.8.2–0.8.3): all of `strava` BackcountrySki, `polar` Backcountry skiing, and `suunto` Backcountry skiing now decode to `alpine_skiing` (backcountry skiing is alpine touring). A `.backcountry` discipline may follow. |
| **Lap / pool swimming** | `garmin_fit`, `polar`, `wahoo` → `swimming.pool` | — | **Re-assessed: not a bug.** `garmin_training_api` maps its *only* swim type (`LAP_SWIMMING`) to bare `swimming` so any swim plan encodes to it; its `fallback.encode` is `GENERIC`, so forcing `swimming.pool` would send `encode(swimming)` to `GENERIC`. The other platforms map lap/pool to `swimming.pool` *because they also have a generic swim type*; gta does not. **Left as-is.** The clean way to get precise decode *and* correct encode here — decoupling a target's decode meaning from the broader sport it encodes — is specified as the `encode_for` extension in [`docs/translation.md`](../docs/translation.md) (documented, not implemented; adopt on a second instance). |

### 1.4 Modifier / discipline conventions for the same concept

The clearest cross-platform disagreements are around cycling modifiers, all centered on
**Strava's `.road` default** and **whether `+virtual` implies `+stationary`**:

| Concept | Strava | Wahoo | Polar / Suunto |
|---|---|---|---|
| E-bike (base) | `cycling.road+assisted` (EBikeRide) | `cycling+assisted` | `cycling+assisted` |
| E-mtb | `cycling.mountain+assisted` (EMountainBikeRide) | — | `cycling.mountain+assisted` (Suunto) ✅ |
| Virtual ride | `cycling.road+virtual` (VirtualRide) | `cycling+stationary+virtual` | — |
| Virtual run | `running.road+virtual` (VirtualRun) | `running+stationary+virtual` | — |
| Virtual row | `rowing+virtual` (VirtualRow) | — | indoor rowing → `rowing+stationary` |

Two underlying questions — **both resolved in 0.8.2**, with the convention recorded in
`CONTRIBUTING.md`:

1. **Base e-bike / virtual ride no `.road`.** ✅ Strava `EBikeRide → cycling+assisted`
   (was `cycling.road+assisted`); a base e-bike/virtual ride asserts no discipline. The
   `.mountain`/`.gravel` variants stay, as those are genuine disciplines the platform
   names (`EMountainBikeRide → cycling.mountain+assisted`).
2. **`+virtual` implies `+stationary`.** ✅ Strava `VirtualRide → cycling+stationary+virtual`,
   `VirtualRun → running+stationary+virtual`, `VirtualRow → rowing+stationary+virtual` —
   a Zwift-style session *is* on a trainer. Strava now agrees with Wahoo's
   `*_INDOOR_VIRTUAL` mappings.

### 1.5 Minor / discretionary

- `garmin_fit` `cycling / downhill` (downhill MTB) → `null`, though `cycling/cyclocross`
  → `cycling.cyclocross` etc. are mapped. Arguably `cycling.mountain`. Low impact.
- Orienteering: Polar maps ski/MTB orienteering to their locomotion but plain
  orienteering (Polar, Suunto) → `null`. Defensible, noted for consistency.

---

## Part 2 — Sports standard across platforms but missing from OST

Every concept below currently decodes to `generic` (via `null` or, for hand cycling, a
coarser code). Ranked by how many of the seven platforms carry a **dedicated** activity
for it. OST today models: cycling, running, swimming, walking, xc_skiing, rowing (+
modifiers) — an outdoor/endurance/GPS scope.

### Group A — fit OST's scope; recommended candidates

| Concept | #platforms | Example platform names | Current OST | Suggested code |
|---|---:|---|---|---|
| **Alpine / downhill skiing** | 6 | AlpineSki, ALPINE_SKIING, downhillSkiing, Downhill skiing, SKIING_DOWNHILL, Telemark | `null` | `alpine_skiing` (or a `skiing` parent — see note) |
| **Snowboarding** | 6 | Snowboard, snowboarding, SNOWBOARDING, Splitboarding | `null` | `snowboarding` |
| **Stand-up paddle (SUP)** | 6 | StandUpPaddling, stand_up_paddleboarding, SUP, paddleSports | `null` | `sup` / `paddling.sup` |
| **Surfing** | 6 | Surfing, surfingSports, SURFING | `null` | `surfing` |
| **Sailing** | 6 | Sail, sailing, SAILING | `null` | `sailing` |
| **Golf** | 6 | Golf, GOLFING (walking-based) | `null` | borderline (outdoor, not endurance) |
| **Climbing** | 5–6 | RockClimbing, rock_climbing, Climbing, climbing | `null` | `climbing` |
| **Kayaking + canoeing** | 5 | Kayaking, KAYAKING, Canoeing, kayaking/whitewater | `null` | `kayaking`, `canoeing` (or `paddling.*`) |
| **Kite / wind-surfing** | 5 | Kitesurf, Windsurf, kitesurfing, windsurfing | `null` | watersports family |
| **Hand cycling** | 5 | HANDCYCLING, Handcycling, Hand cycling, handCycling, hand_cycling | `cycling` (3, wrong) / `null` (2) | **`hand_cycling` (separate root)** — arm-powered; fails the relatedness test against cycling. Resolves §1.3. |
| **Snowshoeing** | 4 | Snowshoe, snowshoeing, Snow shoeing, Snowshoe trekking | `null` | `walking.snowshoeing` or top-level |
| **Ski touring / mountaineering** | 4 | Ski touring, Ski mountaineering, mountaineering, MOUNTAINEERING | `null` (+ backcountry split) | `ski_touring` / `alpine_skiing.touring` |
| **Inline / roller skating** | 4 | InlineSkate, Inline skating, Roller skating, SKATING_INLINE | `null` (+ the FIT bug §1.1) | `skating.inline` |
| **Ice skating** | 3 | ice_skating, Ice skating | `null` | `skating.ice` |
| **Horseback riding** | 3 | horseback_riding, Riding, Horseback riding | `null` | `horseback_riding` |

**Highest-value, lowest-risk additions:** the **winter-sports gap** is the most glaring
— OST has `xc_skiing` but no **alpine skiing** or **snowboarding**, yet all six
non-trivial platforms carry both. Adding a `hand_cycling` root simultaneously fixes the
hand-cycling inconsistency (§1.3). A **paddling family** (kayaking / canoeing / SUP) is
the biggest water-sports gap.

> **Schema-structure note (alpine skiing).** OST's only skiing root is `xc_skiing`.
> Adding alpine could be either a sibling top-level `alpine_skiing`, or a restructure
> introducing a `skiing` parent with `skiing.cross_country` / `skiing.alpine`. The
> relatedness test (Part 3) argues **against** a shared parent: alpine (isometric,
> gravity-driven, legs braced) and XC (whole-body endurance propulsion) have different
> muscular loads *and* different shadows — they are not disciplines of one sport.
> Recommend the non-breaking sibling `alpine_skiing`; the restructure would also be a
> breaking change to `xc_skiing.*` and its class constants (against OST's "codes are
> never removed" rule).

### Group B — multisport containers (different modeling problem)

| Concept | #platforms | Names |
|---|---:|---|
| Triathlon / duathlon / aquathlon / multisport / swimrun | 4 | Triathlon, Duathlon, MULTISPORT, Swimrun, Aquathlon, transition |

These are **containers of multiple sports**, not a single discipline. They all decode to
`generic` today. Representing them properly is a separate design question (a multisport
type, or a sequence of child sports) — flagged, not a simple code addition.

### Group C — common across platforms but outside OST's current scope

Listed for completeness (the user asked for the full set). All decode to `generic`
today. These are non-endurance / indoor-fitness / ball-and-team / combat activities;
recommend **not** adding unless OST deliberately broadens scope.

| Concept | #platforms | | Concept | #platforms |
|---|---:|---|---|---:|
| Yoga | 7 | | Tennis | 5 |
| Strength / weight training | 7 | | Soccer / football | 5 |
| Pilates | 6 | | Basketball | 5 |
| Dance | 5 | | Team sports (hockey/rugby/…) | 5 |
| HIIT / crossfit / functional | 5 | | Boxing / martial arts | 4 |
| Elliptical / cross-trainer | 5 | | Motorsports | 3 |
| Stair climber / stepper | 4 | | | |

---

## Part 3 — Conventions to prevent recurrence

The inconsistencies above trace to two previously-undocumented decisions: *when is a
target `null` vs `generic`*, and *when are two things the same modality, a discipline, a
modifier, or separate modalities*. Both are now specified canonically in
**[`docs/taxonomy.md`](../docs/taxonomy.md)**. This section summarizes them and lists how
to propagate them.

### 3.1 Relatedness is biomechanical, not nominal — *(canonical: `docs/taxonomy.md`)*

One criterion — **do they share the same movement pattern?** — viewed through four
lenses: **muscular** (same muscles, same way), **kinematic** (the *shadow* test —
silhouettes alike?), **biomechanical load** (same muscles/tendons/joints loaded the same
way; plainly: *sore in the same places?*), and **substitution** (would a coach accept
either for the planned session?). Explicitly excluded: **intensity**, **metabolic
demand**, **circumstance**, and the **name**. Ladder: same movement → **discipline**;
same movement, only circumstance differs → **modifier**; different movement → **separate
modality**.

**Consequence for this audit:** *hand cycling* is arm-powered — it fails every lens
against cycling, so it is a **separate modality**. The three rows that currently map it to
`cycling` (`wahoo`, `polar`, `suunto`) are therefore wrong (see §1.3 / Part 2).

### 3.2 `null` vs `generic` in mappings — *(canonical: `docs/taxonomy.md`)*

**named-but-unmodelled → `null`; catch-all bucket → `generic`.** A specific activity OST
doesn't model (elliptical, stair climber, yoga, alpine skiing) is `null`, even though it
is a "vague workout"; only the platform's own unspecified bucket ("Other"/"Workout"/
"Unknown"/"Sports") is `generic`.

### 3.3 Propagation

- **`docs/taxonomy.md`** — **created** (this change). The canonical reference for purpose,
  terminology, the relatedness rule, and the `null`/`generic` rule.
- **`CONTRIBUTING.md`** — "Adding a sport code" / "Adding a modifier" / "Adding mappings"
  should link to `docs/taxonomy.md` rather than restate it (one source of truth).
- **`AGENTS.md`** — add a short "Taxonomy & mapping conventions" pointer:

  ```markdown
  ## Taxonomy & mapping conventions

  See docs/taxonomy.md before adding or editing modality codes or platform mappings.
  Two rules that are easy to get wrong:

  - Relatedness is biomechanical, not nominal. A shared name or shared equipment does
    not make two things the same modality. Same movement pattern -> same modality
    (subdivide as a discipline). A circumstance that doesn't change the movement
    (indoor, virtual, assisted, roller, race) -> modifier (+). Different movement ->
    separate modality (hand cycling is NOT cycling; alpine skiing is NOT xc_skiing).
    Intensity and metabolic load are ignored.
  - null vs generic in mappings. A platform's catch-all bucket -> generic. A specific
    activity OST doesn't model -> null. Never send a named activity to generic just
    because it's a vague workout.
  ```

- **Optional build-time guard:** a `generate.py` lint that **warns when a non-catch-all
  target maps to `generic`** would have caught the Wahoo cases mechanically (whitelist
  each platform's catch-all row — the one that is also `fallback.encode`).

## Recommended follow-ups (in priority order)

0. ✅ **Conventions written** — `docs/taxonomy.md` (canonical), `CONTRIBUTING.md` and
   `AGENTS.md` now link to it.
1. ✅ **Two `xc_skiing+roller` bugs fixed** (§1.1) → `null` (0.8.1).
2. ✅ **Wahoo named-fitness aligned** (§1.2) → `null` for `FE_ELLIPTICAL`, `FE_CLIMBER`,
   `CARDIO_CLASS`, `STAIR_CLIMBER`; `FE`/`FE_GENERAL`/`TICKR_OFFLINE` stay `generic`
   (0.8.1).
3. ✅ **Hand cycling** (§1.3) — `cycling` rows fixed to `null` (0.8.1); **`hand_cycling`
   root added** (0.8.2) and all six platform rows now decode to it.
4. ✅ **Winter sports added** (0.8.2): `alpine_skiing` + `snowboarding` roots, wired into
   all six platforms that distinguish them (separate roots, not a shared `skiing`
   parent — §3.1). Touring/mountaineering variants stay `null`. All `Backcountry
   skiing` rows (incl. Suunto, 0.8.3) decode to `alpine_skiing`; `.backcountry`
   disciplines for alpine and XC may follow.
5. ✅ **Cycling-modifier conventions settled** (§1.4, 0.8.2): no `.road` on base
   e-bike/virtual; `+virtual` implies `+stationary`. Convention recorded in
   `CONTRIBUTING.md`.
6. ~~Fix `garmin_training_api` LAP_SWIMMING → `swimming.pool`~~ — **withdrawn on
   re-assessment** (§1.3): correct as-is for a single-swim-type platform; the clean
   `encode_for` path is specified in `docs/translation.md`.
7. Optional: a `generate.py` lint warning for non-catch-all targets → `generic` (§3.3),
   so the Wahoo class of issue can't recur silently.
8. Consider a **paddling family** (kayaking/canoeing/SUP) and **skating** codes if
   broadening scope; design a **multisport/container** model separately (Group B).

Items 0–5 are **done** (0.8.1–0.8.2). Remaining: item 7 (tooling) and item 8 (further
schema scope — to be run through `docs/taxonomy.md` per-candidate). None require
algorithm changes.
