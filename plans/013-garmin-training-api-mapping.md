# Plan: Add Garmin Training API V2 Mapping

## Context

OST has a Garmin FIT mapping (`garmin_fit`) that translates sport codes to FIT SDK integer pairs (`sport`, `sub_sport`). But Garmin also has a **Training API V2** — a separate API for pushing structured workouts to devices. The Training API uses string sport types, not FIT integers.

The Structured Workout Format (SWF) project is adopting OST for sport classification and needs this mapping. Rather than SWF maintaining its own Garmin sport translation, it belongs in OST alongside the other platform mappings.

## Garmin Training API V2 sport types

From the official Garmin Training API V2 spec (version 1.0, 2025-05-26):

| Sport type | Notes |
|---|---|
| `CYCLING` | |
| `RUNNING` | |
| `LAP_SWIMMING` | |
| `STRENGTH_TRAINING` | No OST equivalent currently |
| `CARDIO_TRAINING` | No OST equivalent currently |
| `GENERIC` | Limited device support |
| `YOGA` | No OST equivalent currently |
| `PILATES` | No OST equivalent currently |

Only 3 of these map to current OST sport families: cycling, running, swimming. The rest (strength, cardio, yoga, pilates) have no OST codes — they're outside endurance sports. `GENERIC` maps to the OST `generic` code.

## Changes

### 1. Add mapping file

**File:** `mappings/garmin_training_api.yaml`

```yaml
# OpenSportTaxonomy — Garmin Training API V2 mapping
# See README.md for how mappings work.

platform: garmin_training_api
platform_version: "V2 1.0 (2025-05-26)"
fallback: CYCLING

mappings:

  - ost: cycling
    target: CYCLING

  - ost: generic
    target: GENERIC

  - ost: running
    target: RUNNING

  - ost: swimming
    target: LAP_SWIMMING
```

Notes:
- Only top-level codes needed. OST's hierarchical fallback handles disciplines: `cycling.road` → walks up to `cycling` → `CYCLING`.
- Fallback is `CYCLING` (matches SWF's current behavior for unknown sports).
- No modifier-specific entries — the Training API has no concept of virtual/stationary/etc.
- `rowing`, `walking`, `xc_skiing` have no Training API equivalent — they fall to `CYCLING` via the platform fallback. This is lossy but correct: the Training API simply doesn't support these sports.

### 2. Add platform module

**File:** `src/open_sport_taxonomy/platforms/_garmin_training_api.py`

```python
from open_sport_taxonomy._platform import Platform
from open_sport_taxonomy._platforms import (
    GARMIN_TRAINING_API_FALLBACK,
    GARMIN_TRAINING_API_MAPPINGS,
)

garmin_training_api = Platform(GARMIN_TRAINING_API_MAPPINGS, GARMIN_TRAINING_API_FALLBACK)
```

### 3. Update platforms `__init__.py`

**File:** `src/open_sport_taxonomy/platforms/__init__.py`

```python
from open_sport_taxonomy.platforms._apple_healthkit import apple_healthkit
from open_sport_taxonomy.platforms._garmin_fit import garmin_fit
from open_sport_taxonomy.platforms._garmin_training_api import garmin_training_api
from open_sport_taxonomy.platforms._strava import strava

__all__ = ["apple_healthkit", "garmin_fit", "garmin_training_api", "strava"]
```

### 4. Update code generation

**File:** `scripts/generate.py`

Add a Garmin Training API section in `generate_platforms()`, following the Strava pattern (string targets, string fallback):

```python
# Garmin Training API
gta = load_mapping("garmin_training_api")
lines.append(f'GARMIN_TRAINING_API_FALLBACK: str = "{gta["fallback"]}"')
lines.append("")
lines.append("GARMIN_TRAINING_API_MAPPINGS: dict[tuple[str, frozenset[str]], str] = {")
for entry in gta["mappings"]:
    key_code = entry["ost"]
    key_mods = frozenset(entry.get("modifiers", []))
    mods_repr = _frozenset_repr(key_mods)
    lines.append(f'    ("{key_code}", {mods_repr}): "{entry["target"]}",')
lines.append("}")
lines.append("")
```

The target type is `str` (like Strava), not a NamedTuple (like FIT).

### 5. Add tests

**File:** `tests/test_platform_garmin_training_api.py`

Following the pattern of `test_platform_strava.py`:

```python
from open_sport_taxonomy import Sport
from open_sport_taxonomy.platforms import garmin_training_api

class TestGarminTrainingAPI:
    def test_cycling(self):
        assert garmin_training_api.translate(Sport("cycling")) == "CYCLING"

    def test_cycling_road(self):
        """Disciplines fall back to parent."""
        assert garmin_training_api.translate(Sport("cycling.road")) == "CYCLING"

    def test_cycling_road_stationary(self):
        """Modifiers are ignored (no modifier-specific entries)."""
        assert garmin_training_api.translate(Sport("cycling.road+stationary")) == "CYCLING"

    def test_running(self):
        assert garmin_training_api.translate(Sport("running")) == "RUNNING"

    def test_running_trail(self):
        assert garmin_training_api.translate(Sport("running.trail")) == "RUNNING"

    def test_swimming(self):
        assert garmin_training_api.translate(Sport("swimming")) == "LAP_SWIMMING"

    def test_swimming_pool(self):
        assert garmin_training_api.translate(Sport("swimming.pool")) == "LAP_SWIMMING"

    def test_generic(self):
        assert garmin_training_api.translate(Sport("generic")) == "GENERIC"

    def test_unmapped_sport_falls_to_default(self):
        """Sports without a mapping fall to CYCLING."""
        assert garmin_training_api.translate(Sport("rowing")) == "CYCLING"
        assert garmin_training_api.translate(Sport("walking")) == "CYCLING"

    def test_all_sports_translate(self):
        """Every standard sport produces a string."""
        for sport in Sport.all():
            result = garmin_training_api.translate(sport)
            assert isinstance(result, str)
```

### 6. Update README

**File:** `README.md`

Add `garmin_training_api` to the platform translation example:

```python
from open_sport_taxonomy.platforms import garmin_training_api

garmin_training_api.translate(Sport("cycling.road+stationary"))  # "CYCLING"
```

Add to the mapping files list:

```
- [`garmin_training_api.yaml`](mappings/garmin_training_api.yaml) — Training API V2 sport type strings
```

### 7. Regenerate

```bash
uv run scripts/generate.py
```

This regenerates `_platforms.py` with the new `GARMIN_TRAINING_API_*` constants.

## Verification

```bash
uv run scripts/generate.py --check
uv run pytest tests/ -x
```

## Consumer usage (SWF)

After this change, SWF's Garmin export simplifies to:

```python
from open_sport_taxonomy.platforms import garmin_training_api

sport_str = garmin_training_api.translate(workout.sport)  # "CYCLING"
```

No manual mapping or ancestor walking needed. OST handles it all.
