# Taxonomy Design

> Designing the sport code hierarchy and modifier system for OpenSportTaxonomy.

**Status:** In progress

---

## Design Principles

1. **The sport code describes the discipline, not the circumstances.** A Zwift ride is still `cycling.road`, not a separate code. Track cycling is `cycling.track`, not "indoor cycling."
2. **An activity is always single-sport.** A triathlon is three separate activities (swim, bike, run), not a sport code. Event grouping is above the taxonomy layer.
3. **Cross-cutting concerns use modifiers, not tree branches.** Virtual, stationary, race, commute, assisted — these describe how/why, not what.
4. **The hierarchy uses dot-notation**, up to 3 levels: `cycling.mountain.downhill`.

## The test for "is this a sport code or a modifier?"

> If you removed it, would an athlete still recognize the underlying activity as the same sport?

- Remove "virtual" from a Zwift ride → road cycling. Same sport. → **Modifier.**
- Remove "assisted" from an e-bike gravel ride → gravel cycling. Same sport. → **Modifier.**
- Remove "track" from track cycling → just cycling? Different bike, technique, venue. → **Sport code.**
- Remove "roller" from roller skiing → XC skiing? Different equipment, surface, skills. → **Sport code.**

---

## Layer 1: Sport Tree

Dot-notation hierarchy. Prefix-matchable. Up to 3 levels.

```yaml
sports:
  - code: cycling
    label: Cycling
    children:
      - code: cycling.road
      - code: cycling.gravel
      - code: cycling.mountain
        children:
          - code: cycling.mountain.xco
          - code: cycling.mountain.downhill
          - code: cycling.mountain.enduro
      - code: cycling.cyclocross
      - code: cycling.track          # velodrome — a discipline, not "indoor cycling"
      - code: cycling.bmx
      - code: cycling.hand_cycling
      - code: cycling.recumbent

  - code: running
    children:
      - code: running.road
      - code: running.trail
      - code: running.track          # 400m track — a discipline, not "indoor running"
      - code: running.ultra

  - code: skiing.xc
    label: Cross-Country Skiing
    children:
      - code: skiing.xc.classic
      - code: skiing.xc.skate
      - code: skiing.xc.backcountry

  - code: skiing.roller
    label: Roller Skiing
    children:
      - code: skiing.roller.classic
      - code: skiing.roller.skate

  - code: transition
    label: Transition
```

---

## Layer 2: Modifiers

A flat set of modifier codes that can be attached to an activity alongside its sport code.

Some modifiers belong to a **group** — at most one modifier per group.
Other modifiers are **independent flags** — combinable freely.

```yaml
modifiers:
  # --- Grouped: at most one per group ---

  - code: stationary
    group: locomotion
    label: Stationary
    description: >
      Performed on a fixed machine (trainer, treadmill, erg).
      No movement through physical space.
    applies_to: ["cycling.*", "running.*", "skiing.*"]

  - code: race
    group: purpose
    label: Race
    description: Competitive event.
    applies_to: ["*"]

  - code: commute
    group: purpose
    label: Commute
    description: Transportation, not exercise.
    applies_to: ["cycling.*", "running.*"]

  # --- Independent flags: combine freely ---

  - code: virtual
    label: Virtual
    description: In a digital environment (Zwift, Rouvy).
    applies_to: ["cycling.*", "running.*"]

  - code: assisted
    label: Assisted
    description: Motor-assisted variant (e-bike, e-MTB).
    applies_to: ["cycling.*"]
```

### Rules

1. **At most one modifier per group.** `race` and `commute` are both `purpose` — pick one.
2. **Independent flags combine freely** with each other and with grouped modifiers.
3. **`applies_to` defines sport compatibility.** `assisted` only makes sense for `cycling.*`.
4. **No modifier implies another.** Each is set explicitly. Zwift = `stationary` + `virtual`.
5. **Absence is the default.** No `stationary` = moving. No `virtual` = real world. No modifier from `purpose` = training.

### Activity record format

```json
{ "sport": "cycling.road", "modifiers": ["stationary", "virtual"] }
```

Short codes, flat list. Group validation is optional for consumers.

---

## Examples

| Activity | Sport code | Modifiers |
|---|---|---|
| Road cycling | `cycling.road` | *(none)* |
| Dumb trainer | `cycling.road` | `stationary` |
| Zwift ride | `cycling.road` | `stationary`, `virtual` |
| Zwift race | `cycling.road` | `stationary`, `virtual`, `race` |
| E-bike gravel | `cycling.gravel` | `assisted` |
| E-bike commute | `cycling.road` | `assisted`, `commute` |
| Trail race | `running.trail` | `race` |
| Treadmill run | `running.road` | `stationary` |
| Track cycling (velodrome) | `cycling.track` | *(none)* |
| XC ski classic on snow | `skiing.xc.classic` | *(none)* |
| Roller skiing classic | `skiing.roller.classic` | *(none)* |
| Roller ski on treadmill | `skiing.roller.classic` | `stationary` |
| SkiErg | `skiing.xc` | `stationary` |

---

## Resolved Decisions

- **`simulated` modifier removed.** Roller skiing fails the modifier test — it's a different discipline with its own equipment, skills, races, and culture. It belongs in the sport tree as `skiing.roller.*`.
- **`virtual` is an independent flag, not in a group.** A Zwift ride is both stationary (on a trainer) AND virtual (in a digital world). These are independent facts, not exclusive choices.
- **`assisted` is an independent flag.** Nothing conflicts with it — it combines with any other modifier.
- **Triathlon is not a sport code.** An activity is always single-sport. A triathlon is three activities.
- **`commute` and `race` are modifiers, not sport codes.** You can commute on any bike; you can race any discipline.

---

## Iteration History

1. **Version A** — Pure hierarchy (all variants as sport codes, including indoor/virtual). Problem: duplicates concepts across branches.
2. **Version B** — Hierarchy + tags + modifiers. Problem: tags AND modifiers is confusing/unintuitive.
3. **Version C** — Hierarchy + typed attributes (environment, surface, propulsion). Problem: over-engineered.
4. **Version D** — Hierarchy + traits (intrinsic) + context (per-activity). Problem: traits/context distinction not intuitive.
5. **Version E** — Hierarchy + 3 axes (mode, purpose, propulsion) with exclusive values. Clean design model, but axes are abstract — hard to implement across languages.
6. **Version F** — Hierarchy + grouped modifiers. Axes become `group` metadata on flat modifier list. Exclusivity via "one per group" rule.
7. **Version G (current)** — Refined Version F. Removed `simulated` (roller skiing is a sport, not a modifier). Split modifiers into grouped (exclusive within group) and independent flags (combine freely). `virtual` and `assisted` are independent flags; `stationary` is grouped under `locomotion`; `race`/`commute` grouped under `purpose`.
