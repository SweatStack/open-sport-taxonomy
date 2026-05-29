# Sport Matching

> Check if a sport is a more specific version of another, and navigate the hierarchy with full context.

## Problem

A prescription says `cycling+stationary` and a user executes `cycling.road+stationary`. Does the execution match?

Yes: the execution's code is equal to or below the prescription's code, and its modifiers are a superset. The current API has no way to ask this question. Additionally, `.parent` drops modifiers, which loses context.

## API

Two additions:

### `is_subsport_of(other: Sport) -> bool`

"Is this sport a more specific version of that sport?"

Two conditions must hold:
1. `self.code` equals or is below `other.code` in the dot hierarchy
2. `self.modifiers` is a superset of `other.modifiers`

```python
Sport("cycling.road+stationary").is_subsport_of(Sport("cycling+stationary"))        # True
Sport("cycling.road+stationary+race").is_subsport_of(Sport("cycling+stationary"))   # True
Sport("cycling+stationary").is_subsport_of(Sport("cycling+stationary"))              # True
Sport("cycling.road").is_subsport_of(Sport("cycling"))                               # True
Sport("cycling").is_subsport_of(Sport("cycling"))                                    # True

Sport("cycling.road").is_subsport_of(Sport("cycling+stationary"))                    # False
Sport("running+stationary").is_subsport_of(Sport("cycling+stationary"))              # False
Sport("cycling").is_subsport_of(Sport("cycling.road"))                               # False
```

Mirrors `issubclass`: a sport is always a subsport of itself.

### `.parent` — change: preserve modifiers

Currently `.parent` drops modifiers. Change it to carry them through.

```python
Sport("cycling.road+stationary").parent  # Sport('cycling+stationary')
Sport("cycling.road").parent             # Sport('cycling')
Sport("cycling").parent                  # None
```

The parent of a stationary road cycling session is stationary cycling, not all cycling. Modifiers are part of the sport's identity.

When you want the bare tree without modifiers:

```python
Sport(sport.code).parent  # Sport('cycling') — explicit, no special method needed
```

## Use cases

**Prescription matching:**
```python
executed.is_subsport_of(prescribed)  # one call, done
```

**Grouping activities by family:**
```python
Sport(sport.code).parent  # Sport('cycling') — clean grouping key
```

**Same discipline, different context?**
```python
sport_a.code == sport_b.code  # True if same code regardless of modifiers
```

**Generalizing a prescription:**
```python
Sport("cycling.road+stationary").parent  # Sport('cycling+stationary') — broader, context intact
```

**Filtering by modifier:**
```python
Modifier.STATIONARY in sport.modifiers  # no new API needed, it's a frozenset
```

## Implementation

### `_sport.py`

**Helper (module-level):**

```python
def _is_subsport_code(child: str, parent: str) -> bool:
    """True if child == parent or child is below parent in the dot hierarchy."""
    return child == parent or child.startswith(parent + ".")
```

String prefix check is O(1) and correct by the dot-notation contract. Works for non-standard codes too.

**Method on Sport:**

```python
def is_subsport_of(self, other: Sport) -> bool:
    if not _is_subsport_code(self.code, other.code):
        return False
    if not other.modifiers.issubset(self.modifiers):
        return False
    return True
```

**Change `.parent`:** reconstruct with the same modifiers from `self`.

### Tests

**`TestIsSubsportOf`:**
- Identity (same sport)
- Child of parent, code only
- Child of parent with matching modifiers
- Extra modifiers on self still matches
- Missing required modifier returns False
- Wrong hierarchy returns False
- Parent is not subsport of child
- Non-standard sports

**`TestParentPreservesModifiers`:**
- Parent carries modifiers through
- Parent of root is still None
- Parent without modifiers unchanged
- `Sport(sport.code).parent` for bare tree navigation

### Documentation

- **README.md**: Update the "Taxonomy navigation" section. Add `is_subsport_of` examples. Update `.parent` example to show modifier preservation. Add a use case example for prescription matching.
- **CHANGELOG.md**: Add entries for `is_subsport_of` and the `.parent` behavior change. The `.parent` change is breaking, call it out.

## Decisions

- **One matching method.** `is_subsport_of` covers hierarchy checks, prescription matching, and exact matching. No need for separate methods.
- **String prefix for hierarchy.** `child.startswith(parent + ".")` is O(1) and works for non-standard codes.
- **Identity is True.** Consistent with `issubclass(int, int)` and `{1}.issubset({1})`.
- **`.parent` preserves modifiers.** Modifiers are part of the sport's identity. Dropping them silently is surprising.
- **No `.base` property.** `Sport(sport.code)` is trivial and self-explanatory. No need for a dedicated method.

## Depends on

This plan assumes the constructor changes from plan 012 (permissive constructor, `str()` always faithful). If implemented before 012, the modifier preservation in `.parent` needs to account for `unknown_modifiers` as well.
