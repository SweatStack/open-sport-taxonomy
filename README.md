# OpenSportsSchema

An open standard for classifying sports and physical activities.

Every platform has invented its own list of sports. Apple HealthKit calls it `Cycling`, Strava calls it `Ride`, Garmin calls it `ROAD_CYCLING`. None of them are hierarchical, none map to each other, and none are open standards.

OpenSportsSchema provides a single canonical set of sport codes that any application can reference.

## How it works

An activity has a **sport code** (what you're doing) and zero or more **modifiers** (how or why).

```json
{ "sport": "cycling.road", "modifiers": [] }
{ "sport": "cycling.road", "modifiers": ["stationary", "virtual", "race"] }
{ "sport": "cycling.gravel", "modifiers": ["assisted", "commute"] }
{ "sport": "running.trail", "modifiers": ["race"] }
```

**Sport codes** form a tree using dot notation. `cycling` contains `cycling.road`, `cycling.gravel`, `cycling.track`, and so on. The hierarchy is encoded in the code itself: the parent of `cycling.road` is `cycling`. Querying for `cycling` should naturally include all its children.

**Modifiers** describe circumstances, not disciplines. Road cycling on a trainer is still road cycling, performed on a stationary machine. Modifiers are independent: a Zwift ride is both `stationary` and `virtual`, set separately.

See the [full reference](dist/reference.md) for all sport codes and modifiers.

## Design principles

**Sport code or modifier?** If you removed it, would an athlete still recognize the activity as the same sport? If yes, it's a modifier. If no, it's a sport code.

**One activity, one sport.** Multi-sport events like triathlons are composed of separate single-sport activities.

**Venues are not modifiers.** Track cycling happens in a velodrome. That's its natural setting, not a "modified" version of outdoor cycling.

**Modifiers are independent.** No modifier implies another. Absence is meaningful.

## Schema format

The canonical schema is [`schema.yaml`](schema.yaml), a single YAML file with two flat lists: `sports` (sorted alphabetically, hierarchy in the dot notation) and `modifiers` (with optional `group` for mutual exclusivity).

## What the schema does not cover

- **Venue properties** like pool length (25m vs 50m) or track size. These matter for records and performance but are not distinct disciplines. Planned for a future version.

## Versioning

The schema follows [Semantic Versioning](https://semver.org). Each release is a git tag and a GitHub Release. Sport codes are stable: once published, never removed, only deprecated.

```
# Latest
https://raw.githubusercontent.com/sweatstack/open-sports-schema/main/schema.yaml

# Pinned to a version
https://raw.githubusercontent.com/sweatstack/open-sports-schema/v0.1.0/schema.yaml
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. Maintained by [SweatStack](https://sweatstack.io).
