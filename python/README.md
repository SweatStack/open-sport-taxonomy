# open-sport-taxonomy (Python)

The reference Python implementation of [Open Sport Taxonomy](https://github.com/sweatstack/open-sport-taxonomy) — an open standard for classifying sports and translating sport identifiers between platforms (Garmin, Strava, Suunto, Wahoo, Polar, Apple HealthKit, …).

This package bundles a snapshot of the OST spec as typed Python. The standard itself — the vocabulary, the mapping format, and the platform mappings — lives at the repository root; see the [project README](https://github.com/sweatstack/open-sport-taxonomy#readme) and [`docs/`](https://github.com/sweatstack/open-sport-taxonomy/tree/main/docs).

```bash
pip install open-sport-taxonomy
```

The library reports two versions: `open_sport_taxonomy.version` (this package release) and `open_sport_taxonomy.taxonomy_version` (the OST spec it implements).

## Working with sport strings

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

## Storage pattern

Always store `str(sport)` in your database. It preserves the original sport string with full fidelity. Use `Sport.parse()` when loading, then `.resolve()` for application logic. When you upgrade the library, previously non-standard sports become standard automatically. No data migration needed.

```python
# On ingest
sport = Sport.parse(api_response["sport"])
db.activity.sport = str(sport)    # store faithfully

# On load
sport = Sport.parse(db.activity.sport)
resolved = sport.resolve()         # for application logic
```

## Class constants

For known sports in application code, use class constants:

```python
Sport.CYCLING_ROAD
Sport.RUNNING_TRAIL
Sport.SWIMMING_OPEN_WATER
```

## Taxonomy navigation

```python
Sport.CYCLING.disciplines   # (Sport('cycling.cyclocross'), Sport('cycling.gravel'), ...)
Sport.CYCLING_ROAD.parent   # Sport('cycling')
Sport.all()                 # all standard sports

# Parent preserves modifiers
Sport("cycling.road+stationary").parent  # Sport('cycling+stationary')
```

## Sport matching

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

## Platform translation

Every platform supports `encode` (OST → platform code) and `decode` (platform code → OST):

```python
from open_sport_taxonomy.platforms import strava, apple_healthkit, garmin_fit, garmin_training_api, wahoo, polar, suunto

# Encode: OST → platform
strava.encode(Sport("cycling.road+virtual"))     # "VirtualRide"
apple_healthkit.encode(Sport.CYCLING_ROAD)       # 13
garmin_fit.encode(Sport.CYCLING_ROAD)            # GarminFitCode(sport=2, sub_sport=0)
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

Garmin FIT `decode` accepts both raw integer enum values and FIT enum names (interchangeably), and tolerates `None` for missing fields. Note that Garmin has no road/classic profile, so generic codes decode to the dominant discipline (e.g. `cycling/generic` → `cycling.road`):

```python
garmin_fit.decode(2, 7)                # ints → Sport('cycling.road')
garmin_fit.decode("cycling", "road")   # names → Sport('cycling.road')
garmin_fit.decode(2)                   # sub_sport omitted → Sport('cycling.road') (generic = road)
garmin_fit.decode(2, None)             # None → Sport('cycling.road') (e.g. from a FIT parser)
```

Translation is lossy by design — see [`docs/translation.md`](https://github.com/sweatstack/open-sport-taxonomy/blob/main/docs/translation.md) for the mapping-format specification, the encode/decode algorithms, and the structural-coverage rules that make both directions well-defined.

## Pydantic integration

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

## Contributing & license

This package is generated from, and versioned with, the OST standard. See [`CONTRIBUTING.md`](https://github.com/sweatstack/open-sport-taxonomy/blob/main/CONTRIBUTING.md) for the workflow and versioning policy, and [`LICENSE`](https://github.com/sweatstack/open-sport-taxonomy/blob/main/LICENSE) (MIT).
