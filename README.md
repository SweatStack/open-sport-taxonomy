# OpenSportsSchema

An open standard for classifying sports and physical activities.

Every platform has invented its own list of sports. Apple HealthKit calls it `Cycling`, Strava calls it `Ride`, Garmin calls it `ROAD_CYCLING`. None of them are hierarchical, none map to each other, and none are open standards.

OpenSportsSchema provides a single canonical set of sport codes that any application can reference.

## How it works

An activity is identified by a **sport string**: a sport code optionally followed by modifiers.

```
cycling.road                        — road cycling
cycling.road+race                   — road cycling race
cycling.road+stationary+virtual     — road cycling on Zwift
cycling.gravel+assisted+commute     — e-bike gravel commute
running.trail+race                  — trail running race
```

**Sport codes** form a tree using dot notation. `cycling` contains `cycling.road`, `cycling.gravel`, `cycling.track`, and so on. The hierarchy is encoded in the code itself: the parent of `cycling.road` is `cycling`. Querying for `cycling` should naturally include all its children.

**Modifiers** describe circumstances, not disciplines. Road cycling on a trainer is still road cycling, performed on a stationary machine. Modifiers are appended with `+` and sorted alphabetically. They are independent: a Zwift ride is both `stationary` and `virtual`, set separately.

See the [full reference](dist/reference.md) for all sport codes and modifiers.

### Structured format

When your context needs separate fields (API payloads, database columns), the same information can be represented as:

```json
{ "sport": "cycling.road", "modifiers": ["stationary", "virtual"] }
```

The sport string is the canonical form. The structured format is derived from it.

## Design principles

**Sport code or modifier?** If you removed it, would an athlete still recognize the activity as the same sport? If yes, it's a modifier. If no, it's a sport code.

**One activity, one sport.** Multi-sport events like triathlons are composed of separate single-sport activities.

**Venues are not modifiers.** Track cycling happens in a velodrome. That's its natural setting, not a "modified" version of outdoor cycling.

**Modifiers are independent.** No modifier implies another. Absence is meaningful.

## Schema format

The canonical schema is [`schema.yaml`](schema.yaml), a single YAML file with two flat lists: `sports` (sorted alphabetically, hierarchy in the dot notation) and `modifiers` (with optional `group` for mutual exclusivity).

## Platform mappings

Mapping files in [`mappings/`](mappings/) translate OSS codes to platform-specific identifiers. One file per platform:

- [`apple_healthkit.yaml`](mappings/apple_healthkit.yaml) — HKWorkoutActivityType integer values
- [`garmin_fit.yaml`](mappings/garmin_fit.yaml) — sport + sub_sport integer pairs
- [`strava.yaml`](mappings/strava.yaml) — SportType string values

Translations are lossy by design. Some platforms are less granular than the schema: all cycling disciplines map to a single HealthKit value (`13`). This is the platform's limitation, not an error.

```yaml
# The same OSS code on three platforms:
- oss: cycling.road
  target: 13                            # Apple HealthKit
- oss: cycling.road
  target: { sport: 2, sub_sport: 7 }   # Garmin FIT
- oss: cycling.road
  target: Ride                          # Strava
```

## Python library

Install the reference implementation:

```bash
pip install open-sports-schema
```

```python
from open_sports_schema import Sport, Modifier

# Parse a sport string
sport = Sport("cycling.road+race+virtual")
sport.code          # "cycling.road"
sport.modifiers     # frozenset({Modifier.RACE, Modifier.VIRTUAL})
sport.label         # "road cycling"
str(sport)          # "cycling.road+race+virtual"

# Class constants with IDE autocomplete
Sport.CYCLING_ROAD
Sport.RUNNING_TRAIL

# Taxonomy navigation
Sport.CYCLING.disciplines   # (Sport('cycling.cyclocross'), Sport('cycling.gravel'), ...)
Sport.CYCLING_ROAD.parent   # Sport('cycling')

# Platform translation
from open_sports_schema.platforms import strava, apple_healthkit, garmin_fit

strava.translate(Sport("cycling.road+virtual"))     # "VirtualRide"
apple_healthkit.translate(Sport.CYCLING_ROAD)        # 13
garmin_fit.translate(Sport.CYCLING_ROAD)             # GarminFitCode(sport=2, sub_sport=7)
```

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
