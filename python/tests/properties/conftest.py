"""Shared Hypothesis strategies for property-based tests.

Strategies are built from the taxonomy data in
``open_sport_taxonomy._sport`` and the modifier enum. They generate
inputs that satisfy the construction contracts of :class:`Sport` and
:meth:`Sport.parse`, so tests can focus on the property under test
without re-asserting structural validity.

Determinism
-----------
The strategies use ``sampled_from`` over fixed taxonomy lists; no
random seeds or system-time inputs. Hypothesis records failing
examples in ``.hypothesis/`` (gitignored) for replay; CI uses the
default ``settings.derandomize`` profile.
"""

from __future__ import annotations

from hypothesis import strategies as st

from open_sport_taxonomy import Modifier, Sport
from open_sport_taxonomy._sport import _LABELS

# Standard sport codes from schema.yaml.
STANDARD_CODES = sorted(_LABELS)
KNOWN_MODIFIERS = sorted(m.value for m in Modifier)

# Modifier groups for conflict filtering.
_MODIFIER_GROUPS: dict[str, str] = {m.value: m.group for m in Modifier if m.group}


def _has_group_conflict(mods: frozenset[str]) -> bool:
    """True if mods contains two modifiers from the same group."""
    seen: set[str] = set()
    for code in mods:
        group = _MODIFIER_GROUPS.get(code)
        if group is None:
            continue
        if group in seen:
            return True
        seen.add(group)
    return False


def standard_codes() -> st.SearchStrategy[str]:
    """Sport code from schema.yaml."""
    return st.sampled_from(STANDARD_CODES)


def conflict_free_modifier_sets(max_size: int = 4) -> st.SearchStrategy[frozenset[str]]:
    """Subsets of known modifier codes with no within-group conflicts.

    Filters out sets containing e.g. both 'race' and 'commute' (purpose group).
    Returns frozensets so they are hashable for Sport's modifier field.
    """
    return (
        st.sets(st.sampled_from(KNOWN_MODIFIERS), max_size=max_size)
        .map(frozenset)
        .filter(lambda mods: not _has_group_conflict(mods))
    )


def standard_sports() -> st.SearchStrategy[Sport]:
    """Standard Sport instances (valid code + conflict-free known modifiers)."""
    return st.builds(
        _build_standard_sport,
        standard_codes(),
        conflict_free_modifier_sets(),
    )


def _build_standard_sport(code: str, mods: frozenset[str]) -> Sport:
    if not mods:
        return Sport(code)
    return Sport(code, modifiers={Modifier(m) for m in mods})
