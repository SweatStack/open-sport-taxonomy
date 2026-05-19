"""Pydantic v2 field types for Sport.

Install with: pip install open-sport-taxonomy[pydantic]
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BeforeValidator, PlainSerializer, WithJsonSchema

from open_sport_taxonomy._sport import Sport

_SPORT_SCHEMA = WithJsonSchema({
    "type": "string",
    "description": "Sport string in OpenSportTaxonomy format (e.g., 'cycling.road+stationary')",
})

_SPORT_SERIALIZER = PlainSerializer(str, return_type=str)


def _parse_sport(value: object) -> Sport:
    """Permissive: accepts any structurally valid sport string."""
    if isinstance(value, Sport):
        return value
    if isinstance(value, str):
        return Sport.parse(value)
    raise ValueError(f"Expected str or Sport, got {type(value).__name__}")


def _validate_sport(value: object) -> Sport:
    """Strict: rejects unknown codes and modifiers."""
    if isinstance(value, Sport):
        return value
    if isinstance(value, str):
        return Sport(value)
    raise ValueError(f"Expected str or Sport, got {type(value).__name__}")


SportField = Annotated[Sport, BeforeValidator(_parse_sport), _SPORT_SERIALIZER, _SPORT_SCHEMA]
"""Permissive sport field. Accepts any structurally valid sport string via Sport.parse()."""

StrictSportField = Annotated[Sport, BeforeValidator(_validate_sport), _SPORT_SERIALIZER, _SPORT_SCHEMA]
"""Strict sport field. Rejects unknown codes and modifiers via Sport()."""
