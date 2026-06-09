# OpenSportTaxonomy

An open taxonomy for classifying sports and physical activities.

Every platform has invented its own list of sports. Apple HealthKit calls it `Cycling`, Strava calls it `Ride`, Garmin calls it `ROAD_CYCLING`. None of them are hierarchical, none map to each other, and none are open standards.

OpenSportTaxonomy provides a single canonical set of sport codes that any application can reference. It classifies activities by **how the body moves** — see [`docs/taxonomy.md`](docs/taxonomy.md) for the purpose, terminology, and the rule for what counts as a distinct modality, discipline, or modifier.

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
\___________/   \____________________/
  sport code          modifiers
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
- [`garmin_training_api.yaml`](mappings/garmin_training_api.yaml) — Training API V2 sport type strings
- [`polar.yaml`](mappings/polar.yaml) — AccessLink `detailed_sport_info` string values
- [`strava.yaml`](mappings/strava.yaml) — SportType string values
- [`suunto.yaml`](mappings/suunto.yaml) — Activities integer ID values
- [`wahoo.yaml`](mappings/wahoo.yaml) — Cloud API `workout_type_id` integer values

Mappings are bidirectional: every entry supports both encoding (OST → platform) and decoding (platform → OST). Translations are lossy by design — some platforms are less granular than the taxonomy, so multiple OST codes may encode to the same platform value (e.g. all cycling disciplines map to HealthKit `13`). The decoded result is the most-specific OST code that the platform actually represents.

See [`docs/translation.md`](docs/translation.md) for the language-agnostic encode/decode specification.

## Python library

Install the reference implementation:

```bash
pip install open-sport-taxonomy
```

### Working with sport strings

The library has two entry points for creating Sport objects:

| Method | Use when |
|---|---|
| `Sport(raw)` | Application code, constants, prescriptions. Enforces the standard vocabulary. |
| `Sport.parse(raw)` | Receiving external input. Accepts any structurally valid sport string. |

A **standard sport** is one where the code and all modifiers are defined in the current taxonomy version. A **non-standard sport** is structurally valid but contains codes or modifiers not yet in the taxonomy, typically from a newer version. Non-standard is not invalid, it's unrecognized.

```python
from open_sport_taxonomy import Sport, Modifier

# Strict constructor for application code
sport = Sport("cycling.road+race+virtual")
sport.code          # "cycling.road"
sport.label         # "road cycling"
sport.modifiers     # frozenset({Modifier.RACE, Modifier.VIRTUAL})
sport.is_standard   # True
str(sport)          # "cycling.road+race+virtual"

# Unknown codes and modifiers are rejected
Sport("cycling.road.criterium")  # ValueError: Unknown sport code
Sport("cycling.road+rainy")     # ValueError (unknown modifier)

# Parse: for external input, preserves everything
sport = Sport.parse("cycling.road.criterium+race+rainy")
sport.code          # "cycling.road.criterium" (preserved)
sport.modifiers     # frozenset({Modifier.RACE, "rainy"})
sport.is_standard   # False
str(sport)          # "cycling.road.criterium+race+rainy" (round-trips)

# Resolve: map a non-standard sport to the nearest standard equivalent
resolved = sport.resolve()
resolved.code       # "cycling.road"
resolved.modifiers  # frozenset({Modifier.RACE})
resolved.is_standard  # True
```

### Storage pattern

Always store `str(sport)` in your database. It preserves the original sport string with full fidelity. Use `Sport.parse()` when loading, then `.resolve()` for application logic. When you upgrade the library, previously non-standard sports become standard automatically. No data migration needed.

```python
# On ingest
sport = Sport.parse(api_response["sport"])
db.activity.sport = str(sport)    # store faithfully

# On load
sport = Sport.parse(db.activity.sport)
resolved = sport.resolve()         # for application logic
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

# Parent preserves modifiers
Sport("cycling.road+stationary").parent  # Sport('cycling+stationary')
```

### Sport matching

Check if a sport is a more specific version of another:

```python
# Prescription matching: does the execution satisfy the prescription?
executed = Sport("cycling.road+stationary")
prescribed = Sport("cycling+stationary")
executed.is_subsport_of(prescribed)   # True

# Extra modifiers are fine
Sport("cycling.road+stationary+race").is_subsport_of(Sport("cycling+stationary"))  # True

# Missing modifiers or wrong hierarchy: no match
Sport("cycling.road").is_subsport_of(Sport("cycling+stationary"))  # False
Sport("running").is_subsport_of(Sport("cycling"))                  # False
```

### Platform translation

Every platform supports `encode` (OST → platform code) and `decode` (platform code → OST):

```python
from open_sport_taxonomy.platforms import strava, apple_healthkit, garmin_fit, garmin_training_api, wahoo, polar, suunto

# Encode: OST → platform
strava.encode(Sport("cycling.road+virtual"))     # "VirtualRide"
apple_healthkit.encode(Sport.CYCLING_ROAD)       # 13
garmin_fit.encode(Sport.CYCLING_ROAD)            # GarminFitCode(sport=2, sub_sport=7)
garmin_training_api.encode(Sport.CYCLING_ROAD)   # "CYCLING"
wahoo.encode(Sport.CYCLING_ROAD)                 # 15
polar.encode(Sport.CYCLING_ROAD)                 # "ROAD_BIKING"
suunto.encode(Sport("cycling.gravel"))           # 99

# Decode: platform → OST
strava.decode("VirtualRide")                     # Sport('cycling.road+virtual')
apple_healthkit.decode(13)                       # Sport('cycling')
garmin_fit.decode(2, 7)                          # Sport('cycling.road')
garmin_training_api.decode("CYCLING")            # Sport('cycling')
wahoo.decode(68)                                 # Sport('cycling+stationary+virtual')
polar.decode("INDOOR_CYCLING")                   # Sport('cycling+stationary')
suunto.decode(106)                               # Sport('cycling.mountain+assisted')
```

Garmin FIT `decode` accepts both raw integer enum values and FIT enum names (interchangeably), and tolerates `None` for missing fields:

```python
garmin_fit.decode(2, 7)                # ints
garmin_fit.decode("cycling", "road")   # names
garmin_fit.decode(2)                   # sub_sport omitted → generic
garmin_fit.decode(2, None)             # None → generic (e.g. from a FIT parser)
```

Translation is lossy by design — see [`docs/translation.md`](docs/translation.md) for the format v3 specification, the encode/decode algorithms, and the structural-coverage rules that make both directions well-defined.

### Pydantic integration

Install with the pydantic extra:

```bash
pip install open-sport-taxonomy[pydantic]
```

Use `SportField` in Pydantic models for permissive parsing, or `StrictSportField` to enforce the standard vocabulary:

```python
from pydantic import BaseModel
from open_sport_taxonomy.pydantic import SportField, StrictSportField

class Workout(BaseModel):
    sport: SportField       # accepts any structurally valid sport string

class Prescription(BaseModel):
    sport: StrictSportField  # rejects unknown codes and modifiers

w = Workout(sport="cycling.road+stationary")
w.sport.code      # "cycling.road"
w.model_dump()    # {"sport": "cycling.road+stationary"}
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

See [CONTRIBUTING.md](CONTRIBUTING.md). For local development, `make` is the entry point: `make test` runs lint and the full test suite (the safe default for CI), `make lint` runs static checks only, and `make help` lists every available target.

## License

MIT. Maintained by [SweatStack](https://sweatstack.io).
