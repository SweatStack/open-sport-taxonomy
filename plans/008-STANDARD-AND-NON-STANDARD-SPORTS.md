# Standard and Non-Standard Sports

> Terminology, operations, and behavior for sport strings that are structurally valid but not (yet) in the schema.

**Status:** Draft

---

# Part 1: The Standard

This section defines language-agnostic rules that all conforming implementations must follow.

---

## Terminology

A sport string can be **structurally valid** (conforms to the grammar in plan 006) without being defined in a particular schema version. This gives us two categories:

- **Standard sport** — a sport string where the code AND all modifiers are defined in the schema. Fully interpretable: has a label, disciplines, and platform translations.
- **Non-standard sport** — a sport string that is structurally valid but contains a sport code or modifiers not defined in the schema. Partially interpretable.

A non-standard sport is not invalid. It is structurally sound and may be standard in a newer schema version. The term "non-standard" means "not in the standard as known to this implementation" — it describes the relationship between the data and the schema version, not a quality judgement about the data itself.

### Trust model

The standard trusts that structurally valid codes entering the ecosystem originate from a schema version — current, future, or from a conforming extension. The grammar (plan 006) is the structural contract. Codes that conform to the grammar are legitimate participants in the ecosystem, even when unrecognized by a particular implementation.

### Detection

Conforming implementations must provide an explicit mechanism to distinguish standard from non-standard sports. The check is: is the sport code defined in the schema AND are all modifiers defined in the schema?

---

## Three operations

The standard defines three operations for interpreting a sport string. Conforming implementations must provide all three.

| Operation | Accepts | Result | Lossy | Recommended for |
|---|---|---|---|---|
| **Resolve** | Any structurally valid string | Standard sport | Yes (via hierarchy) | General use (recommended default) |
| **Parse** | Any structurally valid string | Standard or non-standard | No | Data passthrough, storage, forwarding |
| **Validate** | Standard sports only | Standard sport | No | Strict enforcement, testing, admin |

### Resolve (recommended default)

Maps any structurally valid sport string to the nearest standard sport using the hierarchy encoded in the dot notation. The result is always a standard sport — fully functional with label, platform translations, and taxonomy navigation.

**The standard recommends resolve as the default operation.** It guarantees forward compatibility: implementations on older schema versions can work with data produced by newer versions without breaking.

Rules:
1. Unknown sport code → strip the last dot-separated segment, repeat until a defined code is found. If no ancestor is found, use `generic`.
2. Unknown modifier → drop it.
3. Structural errors (empty string, malformed syntax) → reject.
4. Modifier group conflicts among recognized modifiers → reject.

```
resolve("cycling.road+race")                     → cycling.road+race (already standard)
resolve("cycling.road.criterium+race")           → cycling.road+race
resolve("cycling.road.criterium+race+rainy")     → cycling.road+race
resolve("parkour.freerunning")                   → generic
resolve("cycling.road+race+commute")             → error (group conflict)
```

**Equivalence:** A resolved sport is semantically equivalent to the standard sport it resolves to. Two inputs that resolve to the same standard sport are equivalent.

**Preservation:** Conforming implementations should provide a mechanism to access the original input string alongside the resolved result, so that:
- The original can be stored for future re-interpretation when the schema upgrades
- The original can be forwarded to systems that may recognize it
- Audit trails retain what was actually received

### Parse (data passthrough)

Accepts any structurally valid sport string and preserves it exactly as-is. Unknown sport codes and unknown modifiers are kept. The result may be standard or non-standard.

Parse validates only structure (grammar). It does NOT validate:
- Whether the sport code exists in the schema
- Whether modifiers exist in the schema
- Modifier group conflicts (since unknown modifiers may belong to unknown groups)

```
parse("cycling.road+race")                       → standard sport: cycling.road+race
parse("cycling.road.criterium+race")             → non-standard sport: cycling.road.criterium+race
parse("cycling.road+relay")                      → non-standard sport: cycling.road+relay
parse("cycling.road+race+commute")               → non-standard sport: cycling.road+race+commute
parse("cycling.road+")                           → error (structural)
```

**Round-trip guarantee:** `str(parse(x)) == x` for any canonically-ordered input. No data is lost.

**Equality:** A non-standard sport is NOT equivalent to any standard sport:

```
parse("cycling.road.criterium+race") ≠ validate("cycling.road+race")
parse("cycling.road.criterium+race") = parse("cycling.road.criterium+race")
```

### Validate (strict enforcement)

Accepts only standard sports. Rejects any input containing sport codes or modifiers not defined in the schema. Also rejects modifier group conflicts.

```
validate("cycling.road+race")                    → standard sport: cycling.road+race
validate("cycling.road.criterium")               → error (unknown code)
validate("cycling.road+relay")                   → error (unknown modifier)
validate("cycling.road+race+commute")            → error (group conflict)
```

---

## Properties of non-standard sports

Non-standard sports are partially interpretable. The dot notation provides hierarchy without requiring schema knowledge:

| Property | Standard sport | Non-standard sport |
|---|---|---|
| Code | Defined in schema | Preserved (may be undefined) |
| Modifiers | All defined in schema | May include undefined modifiers |
| Is standard | Yes | No |
| Label | Human-readable name | Not available |
| Parent | From schema | Derived from dot notation (strip last segment) |
| Disciplines | From schema | Not available |
| String representation | Canonical form | Preserved form (round-trips) |
| Platform translation | Direct lookup or fallback chain | Fallback chain to nearest defined ancestor |

**Parent derivation:** The dot notation encodes hierarchy structurally. `cycling.road.criterium`'s parent is `cycling.road` by definition, regardless of schema membership. This allows non-standard sports to participate in hierarchical queries and platform translation fallback.

---

## Transmission semantics

When transmitting a sport string between systems (API responses, message queues, data exports), **always transmit the most specific form available.** If the original string was `cycling.road.criterium+race+rainy`, transmit that — not the resolved `cycling.road+race`.

The receiving system can resolve, parse, or validate as appropriate for its schema version and use case. Transmitting the original preserves information across the ecosystem and allows systems with newer schema versions to fully interpret the data.

---

## Equivalence

Two sport values are equivalent if and only if they represent the same sport identity:

- Same code
- Same set of modifiers (recognized)
- Same set of unrecognized modifiers

The original input string does NOT participate in equivalence. Two resolved sports from different inputs that yield the same standard sport are equivalent:

```
resolve("cycling.road.criterium+race") = resolve("cycling.road.sprint+race")  → True
```

Both resolve to `cycling.road+race` — same identity.

---

## Relationship to schema versioning

Adding sport codes and modifiers is a non-breaking change (semver patch). This guarantee is enforced through the resolve operation:

- A v0.1 implementation receiving v0.2 data can resolve it to a v0.1 standard sport
- No errors, no crashes, no data loss (original preserved)
- When the implementation upgrades to v0.2, previously non-standard sports become standard automatically

No coordinated ecosystem rollout is needed. No forced upgrades. Adding to the schema is always safe.

---

# Part 2: Python Binding

This section maps the standard's rules to the Python reference implementation.

---

## API

### Three entry points

```python
from open_sport_taxonomy import Sport, Modifier

# Resolve (recommended default) — forward-compatible
sport = Sport.resolve("cycling.road.criterium+race+rainy")

# Parse (passthrough) — preserves unknowns
sport = Sport.parse("cycling.road.criterium+race+rainy")

# Validate (strict) — rejects unknowns
sport = Sport.validate("cycling.road+race")

# Class constants — for hardcoded references in application code
Sport.CYCLING_ROAD
```

The constructor (`Sport()`) behaves as validate. It is a standard Python constructor and works as expected. Documentation and examples lead with `Sport.resolve()` — the constructor is not the recommended primary interface for string input.

### Detection

```python
sport.is_standard       # True if code AND all modifiers are defined in the schema
```

### Properties

```python
# Standard sport
sport = Sport.resolve("cycling.road+race")
sport.code                  # "cycling.road"
sport.modifiers             # frozenset({Modifier.RACE})
sport.unknown_modifiers     # frozenset() — always empty for standard sports
sport.is_standard           # True
sport.label                 # "road cycling"
sport.parent                # Sport("cycling")
sport.disciplines           # ()
sport.raw                   # "cycling.road+race" (same as input — was already standard)
str(sport)                  # "cycling.road+race"

# Resolved sport (from non-standard input)
sport = Sport.resolve("cycling.road.criterium+race+rainy")
sport.code                  # "cycling.road"
sport.modifiers             # frozenset({Modifier.RACE})
sport.unknown_modifiers     # frozenset() — unknowns are dropped by resolve
sport.is_standard           # True
sport.label                 # "road cycling"
sport.raw                   # "cycling.road.criterium+race+rainy" (original preserved)
str(sport)                  # "cycling.road+race" (reflects resolved identity)

# Parsed non-standard sport
sport = Sport.parse("cycling.road.criterium+race+rainy")
sport.code                  # "cycling.road.criterium" (preserved)
sport.modifiers             # frozenset({Modifier.RACE}) — recognized modifiers
sport.unknown_modifiers     # frozenset({"rainy"}) — unrecognized modifiers
sport.is_standard           # False
sport.label                 # None (code not in schema)
sport.parent                # Sport.parse("cycling.road") — derived from dot notation
sport.raw                   # "cycling.road.criterium+race+rainy"
str(sport)                  # "cycling.road.criterium+race+rainy" (round-trips)
```

### Equality

```python
# Resolve yields standard sport — equals equivalent validated sport
Sport.resolve("cycling.road.criterium+race") == Sport.validate("cycling.road+race")  # True

# Parse preserves non-standard — different identity
Sport.parse("cycling.road.criterium+race") == Sport.validate("cycling.road+race")    # False

# raw does not participate in equality
a = Sport.resolve("cycling.road.criterium+race")
b = Sport.resolve("cycling.road+race")
a == b          # True (same identity: cycling.road+race)
a.raw == b.raw  # False (different original inputs)
```

### Platform translation

Works for both standard and non-standard sports. The fallback chain (plan 004) handles non-standard codes by walking up the hierarchy:

```python
from open_sport_taxonomy.platforms import strava

strava.translate(Sport.resolve("cycling.road.criterium+race"))  # "Ride" (via cycling.road)
strava.translate(Sport.parse("cycling.road.criterium+race"))    # "Ride" (same fallback chain)
```

---

## Implementation

### Fields

```python
@dataclass(frozen=True, init=False, slots=True)
class Sport:
    code: str
    modifiers: frozenset[Modifier]
    unknown_modifiers: frozenset[str]
    raw: str
```

### Custom `__eq__` and `__hash__`

`raw` is excluded from equality. Equality is based on `code`, `modifiers`, and `unknown_modifiers`:

```python
def __eq__(self, other: object) -> bool:
    if not isinstance(other, Sport):
        return NotImplemented
    return (
        self.code == other.code
        and self.modifiers == other.modifiers
        and self.unknown_modifiers == other.unknown_modifiers
    )

def __hash__(self) -> int:
    return hash((self.code, self.modifiers, self.unknown_modifiers))
```

### `__str__`

Includes unknown modifiers for lossless serialization of non-standard sports:

```python
def __str__(self) -> str:
    all_mods = sorted(
        [m.value for m in self.modifiers] +
        list(self.unknown_modifiers)
    )
    if all_mods:
        return f"{self.code}+{'+'.join(all_mods)}"
    return self.code
```

### `Sport.resolve()`

```python
@classmethod
def resolve(cls, raw: str) -> Sport:
    # Structural validation.
    # Walk up hierarchy for unknown code.
    # Drop unknown modifiers.
    # Validate modifier group conflicts among recognized modifiers.
    # Construct standard sport, set raw to original input.
    sport = cls(code, modifiers=known_modifiers)
    object.__setattr__(sport, "raw", raw)
    return sport
```

### `Sport.parse()`

```python
@classmethod
def parse(cls, raw: str) -> Sport:
    # Structural validation only.
    # Separate known from unknown modifiers. No group conflict check.
    # Construct sport bypassing schema validation.
    sport = object.__new__(cls)
    object.__setattr__(sport, "code", code)
    object.__setattr__(sport, "modifiers", frozenset(known))
    object.__setattr__(sport, "unknown_modifiers", frozenset(unknown))
    object.__setattr__(sport, "raw", raw)
    return sport
```

### `Sport.validate()`

```python
@classmethod
def validate(cls, raw: str) -> Sport:
    return cls(raw)
```

### Constructor

Behaves as validate. Sets `unknown_modifiers = frozenset()` and `raw = str(self)`:

```python
def __init__(self, code: str, *, modifiers: Iterable[Modifier] | None = None) -> None:
    # Parse, validate against schema, validate modifier group conflicts.
    object.__setattr__(self, "unknown_modifiers", frozenset())
    object.__setattr__(self, "raw", str(self))
```

### `parent` for non-standard codes

```python
@property
def parent(self) -> Sport | None:
    if self.code in _PARENTS:
        parent_code = _PARENTS[self.code]
    else:
        dot = self.code.rfind(".")
        parent_code = self.code[:dot] if dot != -1 else None

    if parent_code is None:
        return None
    return Sport.parse(parent_code)
```

### `label`

```python
@property
def label(self) -> str | None:
    return _LABELS.get(self.code)
```

### `is_standard`

```python
@property
def is_standard(self) -> bool:
    return self.code in _LABELS and not self.unknown_modifiers
```

---

## Documentation requirements

The README and library docs must include:

### 1. Standard vs. non-standard

- A standard sport is fully defined in the current schema version
- A non-standard sport is structurally valid but contains codes or modifiers not yet defined
- Non-standard is not invalid — it means the implementation doesn't recognize it yet
- `sport.is_standard` is the explicit check

### 2. The three operations

A prominent section showing all three entry points side by side:

| Method | Use when |
|---|---|
| `Sport.resolve(raw)` | You received a sport string and need to work with it (recommended) |
| `Sport.parse(raw)` | You need to store or forward a sport string without losing data |
| `Sport.validate(raw)` | You want to reject non-standard sports explicitly |

With clear statement: `Sport.resolve()` is the recommended default.

### 3. The storage pattern

- Always store `.raw` in the database
- Use `Sport.resolve()` when loading for application logic
- When the library upgrades, previously non-standard sports become standard automatically
- No data migration needed

### 4. Transmission

- Always transmit the most specific form (`.raw`, not `str()` of resolved)
- The receiving system decides how to interpret

### 5. Class constants

For hardcoded sport references in application code, class constants are preferred:

```python
Sport.CYCLING_ROAD          # preferred
Sport.validate("cycling.road")   # equivalent but verbose
```

---

## Testing strategy

### Resolve
- Returns standard sport (`is_standard = True`, `unknown_modifiers` empty)
- Equals equivalent validated sport
- `str()` is the canonical standard form
- `.raw` is the original input (may differ from `str()`)
- Two resolves from different inputs yielding same standard sport are equal
- Unknown sport walks up hierarchy
- Unknown modifiers dropped
- No known ancestor resolves to generic
- Structural errors raise `ValueError`
- Known modifier group conflicts raise `ValueError`

### Parse
- Standard input: `is_standard = True`, equals constructor equivalent
- Non-standard input: `is_standard = False`, NOT equal to any standard sport
- Unknown modifiers preserved in `unknown_modifiers`
- Unknown code preserved in `code`
- `str()` round-trips: `str(Sport.parse(x)) == x` for canonical input
- `label` returns `None` for non-standard codes
- `parent` derived from dot notation for non-standard codes
- Platform translation walks up to nearest defined ancestor
- Modifier group conflicts among known modifiers do NOT raise
- Structural errors still raise

### Validate
- Accepts only standard sports
- Rejects unknown codes with `ValueError`
- Rejects unknown modifiers with `ValueError`
- Rejects modifier group conflicts with `ValueError`
- `is_standard` always `True`
- `raw == str(sport)` always
- Equivalent to constructor

### Cross-operation
- `Sport.resolve(x) == Sport.validate(y)` when resolve(x) produces y
- `Sport.parse(x).is_standard` correctly reflects schema membership
- `.raw` is always the original input regardless of operation
- Class constants: `Sport.CYCLING_ROAD == Sport.validate("cycling.road")`
- Platform translation produces same result for resolve and parse of same input
