# OpenSportTaxonomy

An open taxonomy for classifying sports and physical activities.

Every platform has invented its own list of sports. Apple HealthKit calls it `Cycling`, Strava calls it `Ride`, Garmin calls it `ROAD_CYCLING`. None of them are hierarchical, none map to each other, and none are open standards.

OpenSportTaxonomy provides a single canonical set of sport codes that any application can reference. It classifies activities by **how the body moves** — see [`docs/taxonomy.md`](docs/taxonomy.md) for the purpose, terminology, and the rule for what counts as a distinct modality, discipline, or modifier.

**Try it live** at **[open-sport-taxonomy.sweatstack.no](https://open-sport-taxonomy.sweatstack.no)**: browse the standard sports and see how each one translates, or open the platform-to-platform translation explorer.

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

The canonical schema is [`schema.yaml`](schema.yaml), a single YAML file with two flat lists. `sports` is the **standard-sports catalogue** — the curated set OST recommends, each entry a canonical `sport` string with a hand-crafted `label`. It holds both bare codes (the modality tree, in dot notation) and recommended combinations (`cycling+stationary` → "indoor cycling"), ordered by code then modifiers. `modifiers` declares each modifier (with an optional `group` for mutual exclusivity). Any well-formed sport string is usable; the catalogue is the recommended profile over that open space — see [`docs/taxonomy.md`](docs/taxonomy.md).

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

The reference implementation is a Python package in [`python/`](python/):

```bash
pip install open-sport-taxonomy
```

```python
from open_sport_taxonomy import Sport
from open_sport_taxonomy.platforms import garmin_fit

garmin_fit.decode(2, 0)                   # Sport('cycling.road')
garmin_fit.encode(Sport("cycling.road"))  # GarminFitCode(sport=2, sub_sport=0)
```

Full API docs — sport strings, storage, matching, platform translation, Pydantic
integration — are in [`python/README.md`](python/README.md). The library exposes
`open_sport_taxonomy.version` (package release) and `open_sport_taxonomy.taxonomy_version`
(the OST spec it implements).

## What the taxonomy does not cover

- **Venue properties** like pool length (25m vs 50m) or track size. These matter for records and performance but are not distinct disciplines. Planned for a future version.

## Versioning

OST has two [SemVer](https://semver.org) version numbers:

- **Spec version** (`schema.yaml`) — the standard: vocabulary, OST string format, mapping format, and bundled mappings, versioned together. Spec releases are tagged **`spec/vX.Y.Z`** (e.g. `spec/v0.9.0`), so a tag pins a snapshot of the whole standard.
- **Package version** (`pyproject.toml`) — this Python library; what you `pip install`. It *implements* a spec version, and is tagged **`python/vX.Y.Z`** (each line has its own tag namespace). The library exposes both as `open_sport_taxonomy.version` (package) and `open_sport_taxonomy.taxonomy_version` (spec).

Compatibility is by spec major version; sport codes are stable (once published, never removed — only deprecated). See [`CONTRIBUTING.md`](CONTRIBUTING.md#versioning) for the bump rules.

```
# Latest
https://raw.githubusercontent.com/sweatstack/open-sport-taxonomy/main/schema.yaml

# Pinned to a spec version (git tag)
https://raw.githubusercontent.com/sweatstack/open-sport-taxonomy/spec/v0.9.0/schema.yaml
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). For local development, `make` is the entry point: `make test` runs lint and the full test suite (the safe default for CI), `make lint` runs static checks only, and `make help` lists every available target.

## License

MIT. Maintained by [SweatStack](https://sweatstack.io).
