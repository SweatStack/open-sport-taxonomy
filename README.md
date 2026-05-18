# OpenSportTaxonomy

An open taxonomy for classifying sports and physical activities.

Every platform has invented its own list of sports. Apple HealthKit calls it `Cycling`, Strava calls it `Ride`, Garmin calls it `ROAD_CYCLING`. None of them are hierarchical, none map to each other, and none are open standards.

OpenSportTaxonomy provides a single canonical set of sport codes that any application can reference.

> [!WARNING]
> This taxonomy is young and only covers a few sports at the moment.
> If yours is missing, [open an issue](https://github.com/sweatstack/open-sport-taxonomy/issues). We'd love to expand it together.

## How it works

An activity is identified by a **sport string**: dots (`.`) separate the sport from its disciplines in the sport hierarchy, plusses (`+`) attach modifiers.

Example: `cycling.road+stationary+virtual`

```
cycling . road + stationary + virtual
\-----/   \--/   \--------/   \-----/
 sport discipline modifier    modifier
```

More examples:

| Sport string | Meaning |
|---|---|
| `cycling.road` | road cycling |
| `cycling.road+race` | road cycling race |
| `cycling.road+stationary+virtual` | road cycling, for example on Zwift |
| `cycling.gravel+assisted+commute` | e-bike gravel commute |
| `running.trail+race` | trail running race |
| `xc_skiing.classic+roller` | classic roller skiing |

**Sport codes** form a tree using dot notation. `cycling` contains `cycling.road`, `cycling.gravel`, `cycling.track`, and so on. The hierarchy is encoded in the code itself: the parent of `cycling.road` is `cycling`. Querying for `cycling` should naturally include all its children.

**Modifiers** describe circumstances, not disciplines. Road cycling on a trainer is still road cycling, performed on a stationary machine. Modifiers are appended with `+` and sorted alphabetically. They are independent: a Zwift ride is both `stationary` and `virtual`, set separately.

See the [full reference](docs/reference.md) for all sport codes and modifiers.

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

**Modifiers are explicit.** No modifier implies another. A Zwift ride is `stationary+virtual` — both set separately, because a trainer without a screen is stationary but not virtual. Absence means unspecified, not "the opposite."

## Schema format

The canonical schema is [`schema.yaml`](schema.yaml), a single YAML file with two flat lists: `sports` (sorted alphabetically, hierarchy in the dot notation) and `modifiers` (with optional `group` for mutual exclusivity).

## Platform mappings

Mapping files in [`mappings/`](mappings/) translate OST codes to platform-specific identifiers. One file per platform:

- [`apple_healthkit.yaml`](mappings/apple_healthkit.yaml) — HKWorkoutActivityType integer values
- [`garmin_fit.yaml`](mappings/garmin_fit.yaml) — sport + sub_sport integer pairs
- [`strava.yaml`](mappings/strava.yaml) — SportType string values

Translations are lossy by design. Some platforms are less granular than the taxonomy: all cycling disciplines map to a single HealthKit value (`13`). This is the platform's limitation, not an error.

```yaml
# The same OST code on three platforms:
- ost: cycling.road
  target: 13                            # Apple HealthKit
- ost: cycling.road
  target: { sport: 2, sub_sport: 7 }   # Garmin FIT
- ost: cycling.road
  target: Ride                          # Strava
```

## Python library

Install the reference implementation:

```bash
pip install open-sport-taxonomy
```

### Working with sport strings

The library provides three ways to interpret a sport string:

| Method | Use when |
|---|---|
| `Sport.resolve(raw)` | You received a sport string and need to work with it **(recommended)** |
| `Sport.parse(raw)` | You need to store or forward a sport string without losing data |
| `Sport.validate(raw)` | You want to reject non-standard sports explicitly |

A **standard sport** is one where the code and all modifiers are defined in the current taxonomy version. A **non-standard sport** is structurally valid but contains codes or modifiers not yet in the taxonomy — typically from a newer version. Non-standard is not invalid, it's unrecognized.

`Sport.resolve()` is the recommended default. It maps any structurally valid sport string to the nearest standard sport, so your code never breaks when the taxonomy grows.

```python
from open_sport_taxonomy import Sport, Modifier

# Resolve a sport string (recommended)
sport = Sport.resolve("cycling.road+race+virtual")
sport.code          # "cycling.road"
sport.label         # "road cycling"
sport.modifiers     # frozenset({Modifier.RACE, Modifier.VIRTUAL})
sport.is_standard   # True
str(sport)          # "cycling.road+race+virtual"

# Forward-compatible: unknown codes resolve to the nearest known parent
sport = Sport.resolve("cycling.road.criterium+race")
sport.code          # "cycling.road" (resolved)
sport.label         # "road cycling"
sport.raw           # "cycling.road.criterium+race" (original preserved)

# Parse: preserve unknown codes and modifiers without interpretation
sport = Sport.parse("cycling.road.criterium+race+rainy")
sport.code          # "cycling.road.criterium" (preserved)
sport.is_standard   # False
sport.label         # None (unknown code)
str(sport)          # "cycling.road.criterium+race+rainy" (round-trips)

# Validate: strict, rejects unknowns
sport = Sport.validate("cycling.road+race")  # ok
sport = Sport.validate("cycling.road.criterium")  # ValueError
```

### Storage pattern

Always store `.raw` in your database — it's the original sport string with full fidelity. Use `Sport.resolve()` when loading for application logic. When you upgrade the library, previously non-standard sports become standard automatically. No data migration needed.

```python
# On ingest
sport = Sport.resolve(api_response["sport"])
db.activity.sport = sport.raw    # store original

# On load
sport = Sport.resolve(db.activity.sport)
```

### Class constants

For known sports in application code, use class constants:

```python
Sport.CYCLING_ROAD
Sport.RUNNING_TRAIL
Sport.SWIMMING_OPEN_WATER
```

### Taxonomy navigation

```python
Sport.CYCLING.disciplines   # (Sport('cycling.cyclocross'), Sport('cycling.gravel'), ...)
Sport.CYCLING_ROAD.parent   # Sport('cycling')
Sport.all()                 # all standard sports
```

### Platform translation

```python
from open_sport_taxonomy.platforms import strava, apple_healthkit, garmin_fit

strava.translate(Sport.resolve("cycling.road+virtual"))  # "VirtualRide"
apple_healthkit.translate(Sport.CYCLING_ROAD)              # 13
garmin_fit.translate(Sport.CYCLING_ROAD)                   # GarminFitCode(sport=2, sub_sport=7)
```

## What the taxonomy does not cover

- **Venue properties** like pool length (25m vs 50m) or track size. These matter for records and performance but are not distinct disciplines. Planned for a future version.

## Versioning

The taxonomy follows [Semantic Versioning](https://semver.org). Each release is a git tag and a GitHub Release. Sport codes are stable: once published, never removed, only deprecated.

```
# Latest
https://raw.githubusercontent.com/sweatstack/open-sport-taxonomy/main/schema.yaml

# Pinned to a version
https://raw.githubusercontent.com/sweatstack/open-sport-taxonomy/v0.1.0/schema.yaml
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. Maintained by [SweatStack](https://sweatstack.io).
