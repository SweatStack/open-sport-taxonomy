# OpenSportsSchema

A canonical, open taxonomy for sports and physical activities.

## The problem

Every platform that tracks physical activity has invented its own list of sports.

| Activity | Apple HealthKit | Strava | Garmin Connect |
|---|---|---|---|
| Road cycling | `Cycling` | `Ride` | `ROAD_CYCLING` |
| Gravel cycling | `Cycling` | `GravelRide` | `GRAVEL_UNPAVED_CYCLING` |
| Trail running | `Running` | `TrailRun` | `TRAIL_RUNNING` |

Apple HealthKit, Garmin, Strava, Polar, Suunto all use different names, different granularity, and different structure. None of them are hierarchical, none map to each other, and none are open standards.

If you build software that works with sports data from multiple sources, you end up writing the same normalization code over and over.

## How it works

OpenSportsSchema classifies activities using two layers.

### Sport codes (what you're doing)

A sport code identifies the discipline. Sport codes form a tree using dot notation. `cycling` contains `cycling.road`, `cycling.gravel`, `cycling.track`, and so on. The hierarchy is encoded in the code itself: the parent of `cycling.road` is `cycling`. Querying for `cycling` should naturally include all its children.

### Modifiers (how or why you're doing it)

A modifier describes the circumstances of a specific activity, not the discipline itself. Road cycling on a stationary trainer is still road cycling, performed on a stationary machine.

Modifiers exist because some concepts cut across the sport tree. "Stationary" applies to cycling, running, skiing, rowing. Encoding these as branches in the tree would duplicate them under every parent. Instead, they live alongside the sport code as a flat set of flags.

### Example

```json
{ "sport": "cycling.road", "modifiers": [] }
{ "sport": "cycling.road", "modifiers": ["stationary"] }
{ "sport": "cycling.road", "modifiers": ["stationary", "virtual"] }
{ "sport": "cycling.road", "modifiers": ["stationary", "virtual", "race"] }
{ "sport": "cycling.gravel", "modifiers": ["assisted", "commute"] }
{ "sport": "running.trail", "modifiers": ["race"] }
```

## Design principles

### Sport code or modifier?

If you removed it, would an athlete still recognize the activity as the same sport? If yes, it's a modifier. If no, it's a sport code.

Remove "virtual" from a Zwift ride and you still have road cycling. Modifier. Remove "track" from track cycling and you have a different bike, different technique, a specialized venue. Sport code.

### One activity, one sport

An activity always has exactly one sport code. Multi-sport events like triathlons are composed of separate single-sport activities. Event grouping is a concern for the application, not the taxonomy.

### Venues are not modifiers

Track cycling happens in a velodrome. That's its natural venue, not a "modified" version of outdoor cycling. A velodrome cyclist and a Zwift cyclist are both physically indoors, but they have nothing in common. The distinction that matters is between performing a sport in its intended setting and performing it on a stationary substitute.

### Modifiers are independent and explicit

No modifier implies another. A Zwift ride is both `stationary` and `virtual`. These are two separate facts, set independently. Absence is meaningful: no modifier means the default.

## Schema format

The canonical schema lives in [`schema.yaml`](schema.yaml). A human-readable overview of all sports and modifiers is available in [`dist/reference.md`](dist/reference.md). The YAML file has two sections:

- **`sports`** — a flat list of sport codes, sorted alphabetically. Hierarchy is encoded in the dot notation, not in file structure. Every parent entry must exist (if `cycling.mountain.xco` exists, `cycling.mountain` and `cycling` must too).

- **`modifiers`** — a flat list of modifier codes. Each has a `code` and `label`. Modifiers with a `group` field are mutually exclusive within that group. Modifiers without a group are independent flags that combine freely.

## What the schema does not cover

- **Venue properties** — pool length (25m vs 50m), track size (200m, 400m), velodrome size (250m, 333m). These matter for performance and records but are not distinct disciplines. Standardized vocabularies for these may be added in a future version.

## Versioning

The schema follows [Semantic Versioning](https://semver.org). The `version` field in `schema.yaml` is the source of truth. Each release is a git tag (`v0.1.0`) and a GitHub Release with generated artifacts (JSON, CSV).

To fetch a specific version:

```
# Latest
https://raw.githubusercontent.com/sweatstack/open-sports-schema/main/schema.yaml

# Pinned
https://raw.githubusercontent.com/sweatstack/open-sports-schema/v0.1.0/schema.yaml
```

Sport codes are stable. Once published, a code is never removed, only deprecated.

## Status

Early development. The taxonomy currently covers cycling, running, and cross-country skiing. See the [roadmap](plans/) for what's planned.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).

Maintained by [SweatStack](https://sweatstack.io).
