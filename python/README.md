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

Three nested levels describe any sport (see [`docs/taxonomy.md`](https://github.com/sweatstack/open-sport-taxonomy/blob/main/docs/taxonomy.md)):

- **well-formed** — the string parses (`Sport.parse` succeeds);
- **known-atoms** (`uses_known_atoms`) — the code and every modifier are declared in the current taxonomy version;
- **standard sport** (`is_standard`) — the exact canonical string is in the curated standard-sports catalogue.

The strict `Sport(raw)` constructor enforces **known-atoms**; `is_standard` additionally checks catalogue membership. A sport can be valid and usable without being standard.

```python
from open_sport_taxonomy import Sport, Modifier

# Strict constructor: enforces known atoms (known code + declared modifiers)
sport = Sport("cycling+stationary")
sport.code             # "cycling"
sport.label            # "indoor cycling" — hand-crafted catalogue label
sport.is_standard      # True  (in the catalogue)
sport.uses_known_atoms # True
str(sport)             # "cycling+stationary"

# Known atoms, but not a catalogued combination
sport = Sport("cycling.road+race")
sport.is_standard      # False — valid and usable, just not a recommended sport
sport.uses_known_atoms # True
sport.label            # "road cycling (race)" — composed from the parts

# Unknown atoms are rejected by the strict constructor
Sport("cycling.road.criterium")  # ValueError: Unknown sport code
Sport("cycling+rainy")           # ValueError (unknown modifier)

# Parse: for external input, preserves everything
sport = Sport.parse("cycling.road.criterium+race+rainy")
sport.code             # "cycling.road.criterium" (preserved)
sport.is_standard      # False
sport.uses_known_atoms # False — criterium and rainy aren't declared
sport.label            # "cycling road criterium (race, rainy)" — composed
str(sport)             # "cycling.road.criterium+race+rainy" (round-trips)

# Resolve: nearest standard sport — climbs the code tree, drops modifiers; never adds
resolved = sport.resolve()
resolved               # Sport('cycling.road')
resolved.is_standard   # True
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

## Typed sport vocabulary

There are no per-code class constants. Instead, `StandardSport` is a `Literal` of every
standard-sport canonical string (codes *and* combinations), generated from the catalogue.
**Annotate your own variables and fields with it** — type-aware editors (Pyright/Pylance,
PyCharm) autocomplete the catalogue strings and mypy flags typos:

```python
from open_sport_taxonomy import Sport, StandardSport

favourite: StandardSport = "cycling+stationary"   # autocompleted; mypy errors on a typo
```

The `Sport(...)` / `Sport.parse(...)` constructors take a plain `str` on purpose — they
ingest runtime data (API and database values) and validate at runtime, so they accept any
string and you check standardness with `is_standard`. `StandardSport` is the static,
opt-in vocabulary for *your* code; it never constrains what the library accepts. To browse
the full catalogue, see [`docs/reference.md`](https://github.com/sweatstack/open-sport-taxonomy/blob/main/docs/reference.md) or call `Sport.all()`.

## Taxonomy navigation

```python
Sport("cycling").disciplines       # (Sport('cycling.cyclocross'), Sport('cycling.gravel'), ...)
Sport("cycling.road").parent       # Sport('cycling')
Sport.all()                        # all standard sports (codes and combinations)

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
apple_healthkit.encode(Sport("cycling.road"))    # 13
garmin_fit.encode(Sport("cycling.road"))         # GarminFitCode(sport=2, sub_sport=0)
garmin_training_api.encode(Sport("cycling.road")) # "CYCLING"
wahoo.encode(Sport("cycling.road"))              # 15
polar.encode(Sport("cycling.road"))              # "ROAD_BIKING"
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

Use `SportField` in Pydantic models for permissive parsing, or `StrictSportField` to enforce known atoms (known code + declared modifiers, via the `Sport()` constructor):

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
