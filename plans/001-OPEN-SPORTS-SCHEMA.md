# OpenSportsSchema

> A structured, open taxonomy for sports and physical activities.

**Status:** Early design phase  
**License:** MIT  
**Maintained by:** [SweatStack](https://sweatstack.io) — a sports data platform for developers

---

## The Problem

Sports data is full of inconsistent activity naming. Every platform has invented its own list:

| Activity | Apple HealthKit | Strava | Garmin Connect |
|---|---|---|---|
| Road cycling | `Cycling` | `Ride` | `ROAD_CYCLING` |
| Gravel cycling | `Cycling` | `GravelRide` | `GRAVEL_UNPAVED_CYCLING` |
| Trail running | `Running` | `TrailRun` | `TRAIL_RUNNING` |
| Open water swimming | `Swimming` | `OpenWaterSwim` | `OPEN_WATER_SWIMMING` |

All of these are flat lists with no hierarchy, no open standard, no i18n, and no formal mapping between them. When you build a sports data application that ingests from multiple sources, you end up writing the same normalization code over and over.

OpenSportsSchema fixes this by providing a **canonical, hierarchical, open taxonomy** of sport and activity codes that any application can reference.

---

## Goals

- **Canonical codes** — a single authoritative identifier per sport/discipline, e.g. `cycling.road`, `running.trail`, `swimming.open_water`
- **Hierarchical** — disciplines nest under parent sports; prefix matching works naturally (`cycling.*` returns all cycling variants)
- **Language-agnostic** — the source of truth is YAML; generated artifacts are available for Python, TypeScript, JSON Schema, CSV, and SKOS/RDF
- **i18n-ready** — multilingual labels are a first-class citizen, not an afterthought
- **Platform mappings** — canonical codes map to Strava, Apple HealthKit, Garmin FIT, and Garmin Connect equivalents
- **MIT licensed** — use it anywhere, no strings attached

---

## Non-Goals

- This is not a database schema for your application
- This is not a governing body for sport definitions
- This does not define rules, scoring, or competition formats
- This does not cover athlete categories (age groups, ability levels) — that is a separate vocabulary
- This does not prescribe unit systems (metric vs imperial)

---

## Code Format

Sport codes use **dot-notation** to express hierarchy:

```
cycling
cycling.road
cycling.gravel
cycling.mountain
cycling.mountain.xco
cycling.mountain.dh
cycling.indoor
cycling.virtual
cycling.ebike

running
running.road
running.trail
running.track
running.indoor
running.ultra

swimming
swimming.pool
swimming.open_water

triathlon
triathlon.standard
triathlon.sprint
triathlon.ironman
```

Codes are:
- Lowercase, dot-separated
- Stable — once published, a code is never removed, only deprecated
- Prefix-matchable — `startsWith("cycling.")` returns all cycling disciplines
- Human-readable without a lookup table

---

## Canonical Schema Structure

The canonical source is a single YAML file:

```yaml
version: "0.1.0"
sports:
  - code: cycling
    label: Cycling
    children:
      - code: cycling.road
        label: Road Cycling
        short_label: Road
        emoji: 🚴
        mappings:
          strava: GravelRide        # closest, Strava has no pure road type
          strava_legacy: Ride
          healthkit: Cycling
          garmin_fit_sport: 2        # CYCLING
          garmin_fit_subsport: 8     # ROAD
          garmin_connect: ROAD_CYCLING

      - code: cycling.gravel
        label: Gravel Cycling
        short_label: Gravel
        emoji: 🚵
        mappings:
          strava: GravelRide
          strava_legacy: Ride
          healthkit: Cycling
          garmin_fit_sport: 2        # CYCLING
          garmin_fit_subsport: 25    # GRAVEL
          garmin_connect: GRAVEL_UNPAVED_CYCLING

  - code: running
    label: Running
    children:
      - code: running.trail
        label: Trail Running
        short_label: Trail
        emoji: 🏃
        mappings:
          strava: TrailRun
          strava_legacy: Run
          healthkit: Running
          garmin_fit_sport: 1        # RUNNING
          garmin_fit_subsport: 3     # TRAIL
          garmin_connect: TRAIL_RUNNING
```

---

## i18n Structure

Labels live in separate locale files, keyed by sport code:

```yaml
# i18n/de.yaml
cycling.road:
  label: Rennradfahren
  short_label: Rennrad

cycling.gravel:
  label: Gravel-Radfahren
  short_label: Gravel

running.trail:
  label: Trailrunning
  short_label: Trail
```

Target locales for v1: `en`, `de`, `fr`, `es`, `nl`, `ja`, `zh`

---

## Distribution

### Canonical files (always up to date, no package manager needed)

```bash
# Latest YAML
curl https://raw.githubusercontent.com/sweatstack/open-sports-schema/main/schema/sports.yaml

# Latest JSON
curl https://raw.githubusercontent.com/sweatstack/open-sports-schema/main/dist/sports.json

# Flat CSV (for spreadsheets, BI tools)
curl https://raw.githubusercontent.com/sweatstack/open-sports-schema/main/dist/sports.csv
```

### Language packages (generated from canonical YAML)

```bash
# Python
pip install open-sports-schema

# TypeScript / JavaScript
npm install @sweatstack/open-sports-schema
```

### Python usage

```python
from open_sports_schema import Sports

# Lookup by code
sport = Sports.get("cycling.road")
print(sport.label)        # "Road Cycling"
print(sport.emoji)        # "🚴"
print(sport.parent.code)  # "cycling"

# All cycling disciplines
cycling = [s for s in Sports.all() if s.code.startswith("cycling.")]

# Platform mapping
garmin_code = sport.mappings.garmin_connect  # "ROAD_CYCLING"
strava_type = sport.mappings.strava          # "GravelRide"
```

### TypeScript usage

```typescript
import { Sports, getSport, getChildren } from "@sweatstack/open-sports-schema";

const sport = getSport("cycling.road");
console.log(sport.label);              // "Road Cycling"
console.log(sport.mappings.strava);    // "GravelRide"

const allCycling = getChildren("cycling");
// [cycling.road, cycling.gravel, cycling.mountain, ...]
```

### JSON Schema validation

```json
{
  "$schema": "https://opensportsschema.org/schema/v1/sport-code.json",
  "type": "object",
  "properties": {
    "sport": {
      "$ref": "https://opensportsschema.org/schema/v1/sport-code.json"
    }
  }
}
```

---

## Repository Structure

```
open-sports-schema/
│
├── schema/
│   └── sports.yaml              # Canonical source of truth
│
├── i18n/
│   ├── en.yaml
│   ├── de.yaml
│   ├── fr.yaml
│   ├── es.yaml
│   ├── nl.yaml
│   ├── ja.yaml
│   └── zh.yaml
│
├── mappings/
│   └── platforms.yaml           # Platform-specific code mappings
│                                # (Strava, HealthKit, Garmin FIT, Garmin Connect)
│
├── dist/                        # Generated — do not edit manually
│   ├── sports.json
│   ├── sports.csv
│   ├── sports.skos.ttl          # SKOS/RDF for semantic web use
│   └── sports.jsonld            # JSON-LD
│
├── packages/
│   ├── python/                  # PyPI: open-sports-schema
│   └── typescript/              # npm: @sweatstack/open-sports-schema
│
├── scripts/
│   ├── build.py                 # Generates all dist/ artifacts from YAML
│   ├── validate.py              # Validates schema integrity
│   └── release.py               # Bumps version, tags, publishes packages
│
├── docs/
│   ├── codes.md                 # Full reference of all codes
│   ├── mappings.md              # Platform mapping reference
│   └── contributing.md
│
├── CHANGELOG.md
├── LICENSE                      # MIT
└── README.md
```

---

## Versioning

OpenSportsSchema follows [Semantic Versioning](https://semver.org):

- **Patch** (`0.1.x`) — new codes added, new i18n translations added
- **Minor** (`0.x.0`) — new platform mappings, new metadata fields, new locale support
- **Major** (`x.0.0`) — breaking changes to code structure or schema format (rare; codes are designed to be stable)

**Codes are never removed.** A deprecated code gets a `deprecated: true` flag and a `replaced_by` pointer:

```yaml
- code: cycling.mtb              # old code
  deprecated: true
  replaced_by: cycling.mountain
```

---

## Prior Art and References

### Existing platform taxonomies (the problem this solves)

| Platform | Format | Hierarchical | Open | i18n |
|---|---|---|---|---|
| [Apple HealthKit `HKWorkoutActivityType`](https://developer.apple.com/documentation/healthkit/hkworkoutactivitytype) | Integer enum | ❌ | ❌ | ❌ |
| [Garmin FIT Sport + SubSport](https://developer.garmin.com/fit/overview/) | Paired integer enums | ⚠️ 2-level | ⚠️ SDK only | ❌ |
| [Garmin Connect Activity Types](https://developer.garmin.com/gc-developer-program/activity-api/) | Flat string keys | ❌ | ❌ | ❌ |
| [Strava SportType](https://developers.strava.com/docs/reference/) | Flat string enum | ❌ | ❌ | ❌ |

### Standards this draws inspiration from

- [SKOS (Simple Knowledge Organization System)](https://www.w3.org/TR/skos-reference/) — W3C standard for hierarchical controlled vocabularies; OpenSportsSchema distributes a SKOS/RDF artifact
- [IPTC Sport Codes](https://cv.iptc.org/newscodes/sport/) — news industry sport taxonomy, distributed as RDF/SKOS
- [Google Product Taxonomy](https://support.google.com/merchants/answer/6324436) — simple, widely-adopted hierarchical taxonomy distributed as a flat text file
- [ISO 4217](https://en.wikipedia.org/wiki/ISO_4217) — currency codes; a model for how a simple code standard achieves universal adoption
- [CommonMark](https://commonmark.org/) — an example of an open community spec that achieved adoption without a formal standards body

---

## Roadmap

### v0.1 — Foundation
- [ ] Canonical YAML with core sports: running, cycling, swimming, triathlon, hiking, walking, strength training
- [ ] English labels + short labels + emoji
- [ ] Platform mappings: Strava, Apple HealthKit, Garmin FIT, Garmin Connect
- [ ] `dist/` build script generating JSON, CSV, SKOS/Turtle
- [ ] Python package on PyPI
- [ ] TypeScript package on npm

### v0.2 — Coverage
- [ ] Expand to 100+ sport codes covering major disciplines
- [ ] i18n: de, fr, es, nl
- [ ] Metrics hints per sport (e.g. `cycling.road` → `[power_watts, cadence_rpm, heart_rate_bpm, distance_km]`)
- [ ] JSON Schema validation artifact

### v0.3 — Ecosystem
- [ ] i18n: ja, zh, pt, no
- [ ] Additional mappings: Polar, Suunto, Wahoo, Fitbit
- [ ] Hosted docs site

### Future
- [ ] REST API for lookups and validation
- [ ] Webhook / feed for new code announcements

---

## Contributing

OpenSportsSchema is maintained by SweatStack but contributions are welcome.

**To propose a new sport code:** open an issue with the code, label, parent, and rationale. New codes must represent a meaningfully distinct activity — not a tag, environment modifier, or intensity level.

**To add or improve translations:** edit the relevant `i18n/*.yaml` file and open a pull request.

**To report a mapping error:** open an issue with the platform, the incorrect mapping, and the correct value with a source link.

See [docs/contributing.md](docs/contributing.md) for full guidelines.

---

*OpenSportsSchema is built and maintained by [SweatStack](https://sweatstack.io). MIT licensed.*
