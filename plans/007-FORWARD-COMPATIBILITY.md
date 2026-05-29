# Forward Compatibility

> How the standard guarantees that adding sport codes and modifiers is a non-breaking change.

**Status:** Proposed

---

## The problem

OpenSportTaxonomy is a versioned taxonomy. The semver promise says adding sport codes is a patch-level change — non-breaking. But if implementations reject unknown codes, adding `cycling.road.criterium` in v0.2 causes `ValueError` in every v0.1 client. The standard promises non-breaking additions, but strict validation makes them breaking. That's a contradiction.

**Concrete scenario:** SweatStack, a sports data platform, adopts OpenSportTaxonomy v0.1. Apps are built on SweatStack's API. When the schema grows to v0.2 and SweatStack's API starts returning new codes, every app on v0.1 of the library would break. Without forward compatibility in the standard, every new sport code is a forced ecosystem-wide upgrade.

Every successful evolving standard solves this: HTML ignores unknown tags, CSS ignores unknown properties, HTTP handles unknown status codes by class, protobuf preserves unknown fields. Unknown elements are non-fatal by design. That's what lets standards grow without coordinated rollouts.

---

## The standard's guarantee

**Adding sport codes and modifiers is a non-breaking change.** This is not just a semver label — the standard enforces it through mandatory resolution rules that every conforming implementation must support.

### Two levels of validity

1. **Syntactically valid** — conforms to the grammar (plan 006). The structure is parseable.
2. **Schema-valid** — all codes exist in a specific schema version. Properties like `label` and platform translation are fully available.

A syntactically valid string that is not schema-valid is not an error — it's a string from a newer schema version. The standard defines how to handle it.

### Resolution rules

Conforming implementations MUST provide a resolution mechanism that applies these rules:

**Unknown sport code — walk up the hierarchy:**

The dot notation encodes the parent relationship. `cycling.road.criterium`'s parent is `cycling.road` by definition. Strip the last segment and check if the result is known. Repeat until a known ancestor is found. If no ancestor is known (a new top-level sport), resolve to `generic`.

```
cycling.road.criterium      → cycling.road      (known parent)
cycling.road.criterium.u23  → cycling.road      (known grandparent)
parkour.freerunning         → parkour           → generic (no known ancestor)
```

**Unknown modifier — drop it:**

Modifiers are qualifiers, not identity. A sport with an unknown modifier is still that sport. Drop any modifier not in the implementation's schema version. Keep all recognized modifiers.

```
cycling.road+race+relay     → cycling.road+race (relay dropped)
cycling.road+relay          → cycling.road      (relay dropped, no modifiers remain)
```

**Both unknown — apply both rules:**

Walk up the sport code first, then drop unknown modifiers.

```
cycling.road.criterium+race+relay  → cycling.road+race
```

### Preserving the original

Resolution is lossy. The standard recommends storing the original raw string alongside the resolved result so that:

- Data can be re-interpreted later when the implementation upgrades
- The original can be forwarded to systems that may understand it
- Audit trails and debugging show what actually arrived

---

## What the standard does NOT prescribe

**Whether strict or lenient is the default.** The standard requires that conforming implementations provide both strict validation (catches typos, enforces schema membership) and resolution (handles unknown codes gracefully). Which is the default constructor behavior is an implementation choice — the standard requires both capabilities, not a specific default.

A Python library might default to strict (catches typos in application code). A JavaScript library parsing API responses might default to lenient. Both conform, as long as both paths are available.

---

## Schema validation is still important

Forward compatibility does not mean anything goes. The schema remains the authority on what constitutes a well-defined sport code. Strict validation:

- Catches typos (`cycling.raod` → error, not silent degradation)
- Prevents fragmentation (clients can't invent arbitrary codes and have them accepted as valid)
- Guarantees all properties work (`label`, `disciplines`, platform translation)

The standard simply recognizes that strict validation and forward compatibility serve different contexts — application logic vs. system boundaries — and requires both.

---

## Platform translation of resolved sports

Resolved sports translate through the existing platform fallback chain (plan 004). A sport that resolved from `cycling.road.criterium` to `cycling.road` translates to Strava `Ride`, HealthKit `13`, etc. — exactly as `cycling.road` would. Consistent and predictable.

---

## Python implementation

### Constructor is strict (default)

```python
Sport("cycling.road+race")              # Sport — schema-valid
Sport("cycling.road.criterium+relay")   # ValueError — unknown sport code
```

This is the right default for application code. Typos are caught. The developer uses class constants (`Sport.CYCLING_ROAD`) or known code strings.

### `Sport.resolve()` for forward compatibility

```python
@classmethod
def resolve(cls, raw: str) -> Sport:
    """Resolve an encoded string to the nearest known Sport.

    Walks up the sport code hierarchy for unknown codes.
    Drops unknown modifiers. Always returns a schema-valid Sport.
    """
```

**Behavior:**

```python
# Known code — identical to constructor
Sport.resolve("cycling.road+race")              # Sport("cycling.road+race")

# Unknown sport code — walks up hierarchy
Sport.resolve("cycling.road.criterium")          # Sport("cycling.road")
Sport.resolve("cycling.road.criterium+race")     # Sport("cycling.road+race")
Sport.resolve("parkour.freerunning")             # Sport("generic")

# Unknown modifier — dropped
Sport.resolve("cycling.road+race+relay")         # Sport("cycling.road+race")
Sport.resolve("cycling.road+relay")              # Sport("cycling.road")

# Both unknown
Sport.resolve("cycling.road.criterium+race+relay")  # Sport("cycling.road+race")

# Structurally invalid — still raises
Sport.resolve("")                                # ValueError
Sport.resolve("cycling.road+")                   # ValueError
Sport.resolve("cycling.road++relay")             # ValueError
```

`resolve()` validates structure (grammar) but not vocabulary. It parses, degrades, and returns a schema-valid `Sport`. Structurally invalid input still raises `ValueError` — resolution handles version mismatches, not malformed data.

### Where `resolve()` is used

At system boundaries — where external data enters the application:

```python
# Inside a platform SDK (e.g. SweatStack client)
activity = api_client.get_activity(id)
sport = Sport.resolve(activity["sport"])  # handles newer codes gracefully

# The app developer receives a valid Sport — no awareness of version mismatches needed
```

The app developer's own code uses `Sport.CYCLING_ROAD` and `Sport("cycling.road")` with full strict validation.

### Implementation sketch

```python
@classmethod
def resolve(cls, raw: str) -> Sport:
    if not isinstance(raw, str):
        raise TypeError(f"Expected str, got {type(raw).__name__}")

    if not raw:
        raise ValueError("Sport code cannot be empty")

    parts = raw.split("+")
    if "" in parts:
        raise ValueError(f"Invalid encoded string: {raw!r}")

    raw_code = parts[0]
    raw_modifiers = parts[1:]

    # Resolve sport code: walk up hierarchy until known.
    code = raw_code
    while code and code not in _LABELS:
        dot = code.rfind(".")
        code = code[:dot] if dot != -1 else ""

    if not code:
        code = "generic"

    # Resolve modifiers: keep only known ones, drop the rest.
    known_modifiers = set()
    for m in raw_modifiers:
        try:
            known_modifiers.add(Modifier(m))
        except ValueError:
            continue

    return cls(code, modifiers=known_modifiers)
```

### Modifier group conflicts during resolution

If the raw string contains conflicting modifiers (e.g. `race+commute`) and one is unknown, dropping the unknown one resolves the conflict naturally. If both are known and conflicting, `resolve()` still raises — that's invalid data, not a version mismatch.

### Generated code

`resolve()` is behavior, not data. The generator emits it as part of the `Sport` class in `_sport.py` since it references `_LABELS` and `Modifier`.

---

## Testing strategy

- **Known codes pass through** — `resolve()` returns same result as constructor
- **Unknown sport walks up** — each level of the hierarchy
- **Unknown sport with no known ancestor** — resolves to `generic`
- **Unknown modifier dropped** — known modifiers preserved
- **All modifiers unknown** — resolves to bare sport code
- **Both unknown** — sport walked up AND modifiers dropped
- **Structurally invalid input** — still raises `ValueError`
- **Known conflicting modifiers** — still raises `ValueError`
- **Conflict resolved by dropping unknown** — succeeds
