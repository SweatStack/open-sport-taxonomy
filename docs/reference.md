> **This file is generated from [schema.yaml](../schema.yaml). Do not edit directly.**

# OpenSportTaxonomy Reference

10 sport families, 25 codes, 14 recommended combinations, 11 modifiers — taxonomy version 0.10.0

OST identifies a sport by a canonical string — a `code` plus any number of
`+modifier`s. Three nested levels apply (see [taxonomy.md](taxonomy.md)): any
well-formed string is usable; this page lists the **standard sports** — the
curated catalogue OST recommends, each with a hand-crafted label. Codes form the
modality tree; recommended combinations name idiomatic activities built from a
code and modifiers.

## Sports

Sport codes identify the discipline. They form a hierarchy using
dot notation. A parent groups related disciplines; children
specialize further.

- **alpine_skiing** — alpine skiing
- **cycling** — cycling
  - **cycling.cyclocross** — cyclocross
  - **cycling.gravel** — gravel cycling
  - **cycling.mountain** — mountain biking
  - **cycling.road** — road cycling
  - **cycling.time_trial** — time trial cycling
  - **cycling.track** — track cycling
- **generic** — generic
- **hand_cycling** — hand cycling
- **rowing** — rowing
- **running** — running
  - **running.road** — road running
  - **running.track** — track running
  - **running.trail** — trail running
- **snowboarding** — snowboarding
- **swimming** — swimming
  - **swimming.open_water** — open water swimming
  - **swimming.pool** — pool swimming
- **walking** — walking
  - **walking.hiking** — hiking
- **xc_skiing** — XC skiing
  - **xc_skiing.classic** — classic XC skiing
  - **xc_skiing.double_poling** — double poling XC skiing
  - **xc_skiing.skate** — skate XC skiing

## Recommended combinations

Standard sports that pair a code with one or more modifiers. These are the named
activities OST recommends; any other well-formed combination is still valid, it
just composes its label from the parts instead of carrying a curated one.

- **cycling+assisted** — e-bike ride
- **cycling+commute** — bike commute
- **cycling+stationary** — indoor cycling
- **cycling+stationary+virtual** — virtual indoor cycling
- **cycling.mountain+assisted** — e-mountain biking
- **rowing+stationary** — indoor rowing
- **rowing+stationary+virtual** — virtual indoor rowing
- **running+race** — running race
- **running+stationary** — treadmill running
- **running+stationary+virtual** — virtual treadmill running
- **walking+stationary** — treadmill walking
- **xc_skiing+roller** — roller skiing
- **xc_skiing.classic+roller** — classic roller skiing
- **xc_skiing.skate+roller** — skate roller skiing

## Modifiers

Modifiers describe the circumstances of an activity, not the
discipline itself. They are attached alongside a sport code.
For example, a virtual indoor race ride is `cycling` with modifiers
`race`, `stationary`, and `virtual` — `cycling+race+stationary+virtual`.

### Grouped

Pick at most one modifier from each group.

#### company

- **group** — group
- **solo** — solo

#### purpose

- **commute** — commute
- **leisure** — leisure
- **race** — race
- **test** — test
- **training** — training

### Ungrouped

Independent flags. Combine freely with each other and
with grouped modifiers.

- **assisted** — assisted
- **roller** — roller
- **stationary** — stationary
- **virtual** — virtual
