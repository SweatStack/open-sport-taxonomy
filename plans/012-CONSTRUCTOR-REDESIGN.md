# Constructor Redesign

> Simplify the Sport API to two entry points, make `resolve()` an instance method, and unify modifiers as a single `frozenset[str]`.

## Problem

The current API has three classmethods (`resolve`, `parse`, `validate`) that mix two concerns: parsing a string into a Sport, and checking whether that Sport is standard. This leads to:

- `str(sport)` being lossy for resolved sports (`str()` uses `.code`, but `.raw` holds the original)
- Two extra fields (`raw`, `unknown_modifiers`) that only exist because of this conflation
- The recommended default (`resolve`) silently discards information, making it hard for consumers to work with non-standard sports from newer taxonomy versions

Additionally, the permissive-by-default `resolve` constructor weakens the standard vocabulary by making it frictionless to work with non-standard codes without ever noticing.

## API

### Two entry points

**`Sport(raw)` — strict constructor.** Enforces the standard vocabulary. Rejects unknown codes and modifiers with `ValueError`. Use in application code, constants, prescriptions, tests.

```python
sport = Sport("cycling.road+race")              # ok
sport = Sport("cycling.road.criterium+race")    # ValueError: Unknown sport code
sport = Sport("cycling.road+rainy")             # ValueError: Unknown modifier
```

The keyword form stays for constructing from code + modifiers programmatically:

```python
sport = Sport("cycling.road", modifiers={Modifier.RACE})  # ok, strict
```

Both forms enforce the standard. Used internally by class constants.

**`Sport.parse(raw)` — permissive classmethod.** Parses any structurally valid sport string. Use when receiving external input.

```python
sport = Sport.parse("cycling.road.criterium+race+rainy")
sport.code          # "cycling.road.criterium"
sport.modifiers     # frozenset({Modifier.RACE, "rainy"})
sport.is_standard   # False
str(sport)          # "cycling.road.criterium+race+rainy"
```

`parse` skips both vocabulary validation and modifier group conflict checks. It only rejects structural errors (empty string, trailing `+`, double `+`).

### Unified modifiers

`modifiers` is a `frozenset[str]` containing both known (`Modifier` enum members) and unknown (plain strings) modifiers in a single set. Since `Modifier` is a `str` enum, everything is a string:

```python
sport = Sport.parse("cycling.road+race+rainy")
sport.modifiers                    # frozenset({Modifier.RACE, "rainy"})

Modifier.RACE in sport.modifiers   # True
"rainy" in sport.modifiers         # True
"race" in sport.modifiers          # True (Modifier.RACE == "race")

# After resolve, only known modifiers survive
resolved = sport.resolve()
resolved.modifiers                 # frozenset({Modifier.RACE})
```

For strict constructor sports, all modifiers are guaranteed to be `Modifier` instances:

```python
sport = Sport("cycling.road+race")
sport.modifiers     # frozenset({Modifier.RACE})
```

`is_standard` checks both code and modifiers: code must be in the vocabulary, and all modifiers must be `Modifier` instances.

### `resolve()` as instance method

Moves from classmethod to instance method. Maps a non-standard sport to its nearest standard equivalent: walks the code up to the nearest known parent, drops unknown modifiers.

```python
sport = Sport.parse("cycling.road.criterium+race+rainy")
resolved = sport.resolve()
resolved.code          # "cycling.road"
resolved.modifiers     # frozenset({Modifier.RACE})
resolved.is_standard   # True
str(resolved)          # "cycling.road+race"
```

Calling `.resolve()` on a standard sport returns itself:

```python
sport = Sport("cycling.road+race")
sport.resolve() is sport  # True
```

The resolved sport is constructed via the strict constructor, since the result is guaranteed to be standard.

**Conflicting modifiers during resolve:** If a parsed sport has conflicting known modifiers (e.g. `race+training`, both in the `purpose` group), `resolve()` raises `ValueError`. Resolution can fix vocabulary gaps (unknown codes/modifiers) but not logical conflicts. The input is structurally valid but semantically broken — that's the caller's problem.

### `str()` always faithful

`str(sport)` reconstructs from `.code` and all modifiers sorted alphabetically, so it always round-trips.

```python
sport = Sport.parse("cycling.road.criterium+race+rainy")
str(sport)          # "cycling.road.criterium+race+rainy"
Sport.parse(str(sport)) == sport  # True
```

### `__repr__`

For standard sports, `repr` is a valid constructor call:

```python
repr(Sport("cycling.road+race"))  # "Sport('cycling.road+race')"
```

For non-standard sports, `repr` shows `Sport.parse(...)` since the constructor would reject it:

```python
repr(Sport.parse("cycling.road.criterium"))  # "Sport.parse('cycling.road.criterium')"
```

### `__eq__` and `__hash__`

Compare on `code` and `modifiers`. Since `modifiers` now contains both known and unknown modifiers, this naturally handles all cases:

```python
Sport.parse("cycling.road+rainy") != Sport.parse("cycling.road+foggy")  # True
Sport("cycling.road+race") == Sport("cycling.road+race")                 # True
```

### Fields removed

| Field | Replacement |
|---|---|
| `raw` | `str(sport)` is always faithful |
| `unknown_modifiers` | Merged into `modifiers` |

### Fields that remain

- `code: str` — the sport code as given (not resolved)
- `modifiers: frozenset[str]` — all modifiers, known (`Modifier`) and unknown (plain `str`)
- `is_standard: bool` — True if code is in the vocabulary and all modifiers are `Modifier` instances
- `label: str | None` — human-readable label, None for non-standard
- `parent` — see plan 010
- `disciplines` — unchanged

### Classmethods removed

| Classmethod | Replacement |
|---|---|
| `Sport.resolve(raw)` | `Sport.parse(raw).resolve()` |
| `Sport.validate(raw)` | `Sport(raw)` |

## Recommended usage

**Application code (known sports):**
```python
sport = Sport("cycling.road+race")
Sport.CYCLING_ROAD
```

**Receiving external input:**
```python
sport = Sport.parse(raw)
```

**Application logic on external input:**
```python
sport = Sport.parse(raw)
resolved = sport.resolve()
```

**Storage:**
```python
# On ingest
sport = Sport.parse(api_response["sport"])
db.activity.sport = str(sport)          # always faithful

# On load
sport = Sport.parse(db.activity.sport)
resolved = sport.resolve()              # for application logic
```

**Checking if input is standard:**
```python
sport = Sport.parse(raw)
if not sport.is_standard:
    log.info(f"Non-standard sport: {sport}")
```

**Inspecting what's non-standard:**
```python
sport = Sport.parse("cycling.road.criterium+race+rainy")
resolved = sport.resolve()

sport.code                              # "cycling.road.criterium"
resolved.code                           # "cycling.road"

sport.modifiers - resolved.modifiers    # frozenset({"rainy"}) — the unknowns
```

## Implementation

### `scripts/generate.py`

`_sport.py` is auto-generated. All changes to the Sport class must go through the generate script, not by editing `_sport.py` directly. The generated data (`_LABELS`, `_PARENTS`, `_CHILDREN`, class constants) doesn't change. The class logic (constructor, methods, dunders) is also in the template/script and needs updating there.

Changes to the generated output:

1. Change `__init__` to reject unknown codes and modifiers (current `validate` behavior). Keep the keyword `modifiers=` form. Modifiers stored as `frozenset[Modifier]` (all known, guaranteed by validation).
2. Change `parse` classmethod to accept any structurally valid string. Convert known modifier strings to `Modifier` instances, keep unknown ones as plain strings. Store as `frozenset[str]`. Skip vocabulary validation and modifier group checks.
3. Add `resolve` as an instance method (logic from current `Sport.resolve` classmethod). Filter modifiers to `Modifier` instances only. Return `self` for standard sports. Raise `ValueError` on modifier group conflicts. Construct result via strict constructor.
4. Change `__str__` to reconstruct from `.code` and all modifiers (using `str(m)` for each, works for both `Modifier` and plain strings), sorted alphabetically.
5. Change `__repr__` to show `Sport.parse(...)` for non-standard sports.
6. Simplify `__eq__` and `__hash__` to use `code` and `modifiers` only (no separate `unknown_modifiers` field).
7. Remove `raw` field.
8. Remove `unknown_modifiers` field.
9. Remove `validate` classmethod.
10. Remove `resolve` classmethod.
11. Update `is_standard` to check code is in vocabulary and all modifiers are `Modifier` instances.
12. Class constants unchanged (they use the strict constructor).

### `_platform.py`

The platform translation fallback chain calls `sport.parent` in a loop. When plan 010 changes `.parent` to preserve modifiers, the walk-up check `(parent.code, frozenset())` will stop matching parents that carry modifiers. This needs to be coordinated: either update the platform translation to use `Sport(parent.code)` for the lookup key, or implement 012 before 010 and update platform translation as part of 010.

### `__init__.py`

No changes. `Sport` and `Modifier` exports stay the same.

### Existing tests

The test files map cleanly to the old API structure:

| Test file | Impact |
|---|---|
| `test_validate.py` | Rename/merge into constructor tests. `Sport.validate(raw)` becomes `Sport(raw)` |
| `test_parse.py` | Update: `.unknown_modifiers` assertions become checks on `.modifiers` (e.g. `"rainy" in sport.modifiers`). Remove `.raw` assertions, use `str()` |
| `test_resolve.py` | Update: `Sport.resolve(raw)` becomes `Sport.parse(raw).resolve()`. Remove `.raw` assertions |
| `test_cross_operation.py` | Update: `.raw` becomes `str()`, `.unknown_modifiers` references become `.modifiers` checks |
| `test_sport.py` | Update constructor usage if any non-standard sports were passed directly |
| `test_modifier.py` | No changes expected |
| `test_platform_*.py` | No changes expected (they use standard sports) |

### New tests

- Constructor rejects unknown codes
- Constructor rejects unknown modifiers
- Constructor accepts keyword `modifiers=` form
- `Sport.parse` accepts anything structurally valid
- `Sport.parse` puts known modifiers as `Modifier` instances and unknown as plain strings in `modifiers`
- `Sport.parse` skips modifier group validation
- `sport.resolve()` returns standard sport with only `Modifier` instances in `modifiers`
- `sport.resolve()` on standard sport returns `self`
- `sport.resolve()` raises on modifier group conflicts
- `str()` round-trips for both standard and non-standard
- `repr` shows `Sport(...)` for standard, `Sport.parse(...)` for non-standard
- `is_standard` checks code vocabulary and modifier types
- Equality works correctly with mixed modifier types
- Set operations on modifiers (`sport.modifiers - resolved.modifiers`) yield unknowns

### Documentation

- **README.md**: Rewrite the "Working with sport strings" section. Replace the three entry points table with the two-path story (constructor for application code, `parse` for external input). Update all code examples. Remove references to `.raw` and `.unknown_modifiers`. Rewrite the "Storage pattern" section to use `str(sport)` instead of `.raw`. Show `resolve()` as instance method. Update the "Taxonomy navigation" examples if they reference the old API.
- **CHANGELOG.md**: Breaking changes section. Call out: constructor is now strict by default, `resolve`/`validate` classmethods removed, `resolve` is now an instance method, `raw`/`unknown_modifiers` fields removed, `modifiers` now `frozenset[str]` containing both known and unknown, `str()` behavior changed, `repr` changed for non-standard sports.
- **docs/reference.md**: Auto-generated, re-run `scripts/generate_reference.py`.

## Order

This plan must be implemented before plans 010 and 011.
