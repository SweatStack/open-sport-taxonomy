# Pydantic SportField

> Pydantic v2 type annotations for `Sport`, with zero impact on the base package.

## Install

Pydantic is an optional dependency, declared as an extra:

```bash
pip install open-sport-taxonomy[pydantic]
uv add open-sport-taxonomy[pydantic]
```

The base package keeps zero runtime dependencies. The extra just adds `pydantic>=2.0`.

## Goal

Two field types that mirror the two Sport entry points:

```python
from pydantic import BaseModel
from open_sport_taxonomy.pydantic import SportField, StrictSportField

# Permissive — for APIs receiving external input
class Workout(BaseModel):
    sport: SportField

# Strict — for internal models, configs, prescriptions
class Prescription(BaseModel):
    sport: StrictSportField
```

## Behavior

### `SportField` (permissive, recommended default)

Uses `Sport.parse()`. Accepts any structurally valid sport string.

**Validation (JSON/dict to Sport):**
```python
w = Workout(sport="cycling.road+stationary", duration=3600)
w.sport              # Sport('cycling.road+stationary')
w.sport.code         # "cycling.road"
w.sport.modifiers    # frozenset({Modifier.STATIONARY})

# Forward-compatible: unknown codes preserved
w = Workout(sport="cycling.road.criterium+race", duration=3600)
w.sport.code         # "cycling.road.criterium"
w.sport.is_standard  # False

# Sport instance passthrough
w = Workout(sport=Sport.CYCLING_ROAD, duration=3600)

# Structural errors raise ValidationError
Workout(sport="", duration=3600)   # ValidationError
Workout(sport=123, duration=3600)  # ValidationError
```

**Serialization (Sport to JSON/dict):**
```python
w = Workout(sport="cycling.road.criterium+race", duration=3600)
w.model_dump()       # {"sport": "cycling.road.criterium+race", "duration": 3600}
w.model_dump_json()  # '{"sport":"cycling.road.criterium+race","duration":3600}'
```

Uses `str(sport)`, which is always faithful.

**JSON Schema:**
```python
Workout.model_json_schema()
# {"properties": {"sport": {"type": "string", "description": "..."}}, ...}
```

Not an enum. OST is extensible and forward-compatible by design.

**Application code resolves when needed:**
```python
w = Workout(sport="cycling.road.criterium+race", duration=3600)
resolved = w.sport.resolve()
resolved.code  # "cycling.road"
```

### `StrictSportField`

Uses `Sport()`. Rejects unknown codes and modifiers.

```python
class Prescription(BaseModel):
    sport: StrictSportField

Prescription(sport="cycling.road+race")         # ok
Prescription(sport="cycling.road.criterium")     # ValidationError (unknown code)
Prescription(sport="cycling.road+rainy")         # ValidationError (unknown modifier)
```

Same serialization and JSON schema behavior as `SportField`.

## Design

### Type aliases using `Annotated`

```python
from typing import Annotated
from pydantic import BeforeValidator, PlainSerializer, WithJsonSchema
from open_sport_taxonomy import Sport

_SPORT_SERIALIZER = PlainSerializer(str, return_type=str)
_SPORT_JSON_SCHEMA = WithJsonSchema({
    "type": "string",
    "description": (
        "Sport string in OpenSportTaxonomy format "
        "(e.g., 'cycling.road+stationary')"
    ),
})

def _parse_sport(value: object) -> Sport:
    if isinstance(value, Sport):
        return value
    if isinstance(value, str):
        return Sport.parse(value)
    raise ValueError(f"Expected str or Sport, got {type(value).__name__}")

def _validate_sport(value: object) -> Sport:
    if isinstance(value, Sport):
        return value
    if isinstance(value, str):
        return Sport(value)
    raise ValueError(f"Expected str or Sport, got {type(value).__name__}")

SportField = Annotated[
    Sport,
    BeforeValidator(_parse_sport),
    _SPORT_SERIALIZER,
    _SPORT_JSON_SCHEMA,
]

StrictSportField = Annotated[
    Sport,
    BeforeValidator(_validate_sport),
    _SPORT_SERIALIZER,
    _SPORT_JSON_SCHEMA,
]
```

Serializer and JSON schema are shared. Only the validator differs.

### Dependency approach

Pydantic stays optional. Public submodule at `src/open_sport_taxonomy/pydantic.py` that imports pydantic at the top. If pydantic isn't installed, the import fails naturally with a clear ImportError.

Optional extra in `pyproject.toml`:

```toml
[project.optional-dependencies]
pydantic = ["pydantic>=2.0"]
```

Import path:

```python
from open_sport_taxonomy.pydantic import SportField, StrictSportField
```

## Implementation

| File | Action |
|------|--------|
| `src/open_sport_taxonomy/pydantic.py` | Create. ~35 lines: two validators, shared serializer/schema, two type aliases |
| `pyproject.toml` | Add `[project.optional-dependencies]`, pydantic to dev group |
| `tests/test_pydantic.py` | Create. Skip with `pytest.importorskip("pydantic")` |

No changes to `_sport.py`, `__init__.py`, or any auto-generated files.

### Tests

**`TestSportField`:**
1. String validation produces correct Sport
2. Sport instance passthrough
3. Invalid input raises ValidationError (empty string, wrong type)
4. Non-standard sport preserved faithfully
5. `model_dump()` returns sport string
6. `model_dump_json()` returns JSON with sport string
7. `model_json_schema()` contains `{"type": "string"}`

**`TestStrictSportField`:**
1. Standard sport accepted
2. Sport instance passthrough
3. Unknown code raises ValidationError
4. Unknown modifier raises ValidationError
5. Serialization same as SportField

### Documentation

- **README.md**: Add a "Pydantic integration" section after "Platform translation". Show both `SportField` and `StrictSportField`, serialization round-tripping, and the install command.
- **CHANGELOG.md**: Add entry under `Added`.
