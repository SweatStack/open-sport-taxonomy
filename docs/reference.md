> **This file is generated from [schema.yaml](../schema.yaml). Do not edit directly.**

# OpenSportTaxonomy Reference

10 sport families, 25 sports, 11 modifiers — version 0.8.5

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

## Modifiers

Modifiers describe the circumstances of an activity, not the
discipline itself. They are attached alongside a sport code.
For example, a Zwift race is `cycling.road` with modifiers
`stationary`, `virtual`, and `race`.

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
