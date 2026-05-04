<!-- Generated from schema.yaml — do not edit directly. -->

# OpenSportsSchema Reference

4 sport families, 16 sports, 6 modifiers — version 0.1.0

## Sports

Sport codes identify the discipline. They form a hierarchy using
dot notation. A parent groups related disciplines; children
specialize further. Prefix matching works naturally: `cycling.*`
returns all cycling disciplines.

- **cycling** — cycling
  - **cycling.cyclocross** — cyclocross
  - **cycling.road** — road cycling
  - **cycling.track** — track cycling
- **generic** — generic
- **running** — running
  - **running.road** — road running
  - **running.track** — track running
  - **running.trail** — trail running
- **xc_skiing** — XC skiing
  - **xc_skiing.backcountry** — backcountry XC skiing
  - **xc_skiing.classic** — classic XC skiing
  - **xc_skiing.roller** — roller skiing
    - **xc_skiing.roller.classic** — classic roller skiing
    - **xc_skiing.roller.skate** — skate roller skiing
  - **xc_skiing.skate** — skate XC skiing

## Modifiers

Modifiers describe the circumstances of an activity, not the
discipline itself. They are attached alongside a sport code.
For example, a Zwift race is `cycling.road` with modifiers
`stationary`, `virtual`, and `race`.

### Grouped

Pick at most one modifier from each group.

#### purpose

- **commute** — commute
- **race** — race
- **training** — training

### Ungrouped

Independent flags. Combine freely with each other and
with grouped modifiers.

- **assisted** — assisted
- **stationary** — stationary
- **virtual** — virtual
