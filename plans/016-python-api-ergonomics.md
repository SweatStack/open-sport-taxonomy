# 016 — Python API ergonomics (follow-up to 015)

## Background

During the format v3 redesign (plan 015), several Python API ideas surfaced that were not required by the format change. They were initially folded into 015 and then pulled back out because they belong to a separate review surface: someone disagreeing with the API direction should not block the mapping-format work, and vice versa.

This plan captures those ideas as a follow-up. It is **not** urgent. The existing API is functional and reasonable; the items below are refinements, not corrections. Land 015 first, run a release cycle, then decide whether any of these earn their churn.

## Current state (post-015)

For reference, the API surface after format v3 is shipped:

```python
from open_sport_taxonomy import Sport
from open_sport_taxonomy.platforms import GarminFit  # already structured this way

Sport("cycling.road+stationary")        # __init__ accepts a sport string today via parsing
Sport.parse("cycling.road+stationary")  # explicit classmethod (current canonical form)
sport.code, sport.modifiers, str(sport) # already exposed
sport.parent, sport.is_subsport_of(...) # already exposed

GarminFit().decode(target)              # platform classes already exist as _GarminFitPlatform etc.
GarminFit().encode(sport)
```

So the API is already in roughly the right shape. The items below are surface polish.

## Candidate refinements

### 1. Promote `Sport.parse` to the primary constructor form

Today: `Sport.parse("cycling.road+stationary")` is the documented way to construct from a string; the `__init__` signature takes positional arguments.

Proposal: make `Sport("cycling.road+stationary")` (single string arg) the documented primary form, with `Sport.parse` retained as an alias. Matches `Path("...")`, `datetime.fromisoformat`, `URL("...")` conventions where the type accepts its canonical string form.

**Cost:** none, if `__init__` already supports it. Mostly a documentation change.

### 2. Explicit `Sport.from_parts(code, modifiers)`

For programmatic construction without going through string parsing: `Sport.from_parts("cycling.road", {"stationary"})`. Clearer than overloaded positional args and avoids accidental misuse (e.g., passing a sport string to the `code` parameter).

**Cost:** one classmethod, ~5 lines.

### 3. Expose platform classes as public, not underscore-prefixed

Today: `_GarminFitPlatform` is private (leading underscore). Public access goes through a registry or generated re-export.

Proposal: rename to `GarminFit`, `Strava`, `AppleHealthKit`, `GarminTrainingApi` and expose under `open_sport_taxonomy.platforms`. The class IS the public API for a platform; the underscore prefix is a vestige.

**Cost:** rename + export updates. Pure cosmetics; behavior unchanged.

### 4. Remove the platform-string indirection if any survives

If any encode/decode helper takes a platform identifier string (e.g. `encode(sport, "garmin_fit")`), drop it in favor of `GarminFit().encode(sport)`. Stringly-typed platform identifiers are a code smell once platform classes exist.

**Cost:** audit + delete. Likely a small change.

### 5. Document the `target` type per platform

Each platform's `decode` accepts and `encode` returns a platform-specific shape (FIT: a dataclass or `TypedDict`; Strava: `str`; HealthKit: `int`). These types should be exported and type-annotated on the platform class so consumers get IDE completion.

```python
target: GarminFitCode = GarminFit().encode(Sport("cycling+stationary"))
target.sport, target.sub_sport  # typed, autocomplete works
```

**Cost:** type annotation work + `__all__` updates. Possibly already done for `GarminFitCode`; audit the others.

## Out of scope

- **Sport class redesign** (renaming `.code`, restructuring modifiers). The current shape is fine.
- **Async API.** No use case.
- **Sport string canonicalization helpers** beyond what `__str__` already does.
- **Platform-specific helpers on the classes** (e.g., `GarminFit().decode_partial(sport_id)`). Add only when an actual consumer needs them.

## Validation

Each refinement should ship with:
- A docstring example demonstrating the new form.
- A test that exercises the new form alongside the old (where the old is retained).
- A `CHANGELOG.md` entry.

No refinement should break existing call sites. All five items above are additive or rename-with-alias.

## Recommendation

Bundle items 1–4 into one PR if pursued; item 5 is independent and can land alongside or after. None of this is urgent. Revisit after 015 has shipped and at least one downstream consumer (e.g. pyroparse) has integrated against the new format — their feedback will sharpen which refinements actually matter.
