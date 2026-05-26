from __future__ import annotations

from collections.abc import Iterator

from open_sport_taxonomy._platform import GarminFitCode, Platform
from open_sport_taxonomy._platforms import GARMIN_FIT_FALLBACK, GARMIN_FIT_MAPPINGS
from open_sport_taxonomy._sport import Sport


def _reduce(code: GarminFitCode) -> Iterator[GarminFitCode]:
    """Yield progressively coarser FIT codes for fallback lookup.

    FIT carries discipline detail in ``sub_sport``; when the exact pair
    is unknown, the natural coarsening is to keep ``sport`` and reset
    ``sub_sport`` to ``0`` (the FIT ``generic`` sub_sport).
    """
    yield code
    if code.sub_sport_id != 0:
        yield GarminFitCode(code.sport_id, 0)


class _GarminFitPlatform(Platform):
    """Garmin FIT platform — ``decode`` takes ``(sport, sub_sport)`` directly.

    Users hold ``sport`` and ``sub_sport`` as separate values when reading
    a FIT file, so the natural call shape is ``decode(2, 7)``. The
    underlying ``Platform.decode`` operates on a ``GarminFitCode`` target;
    this override builds one from the user's primitives.

    Both arguments accept ``None`` — useful when a FIT parser returns
    ``None`` for a field that wasn't present in the session message.
    ``None`` is treated as ``0`` (the FIT ``generic`` enum value).
    """

    def decode(  # type: ignore[override]
        self,
        sport: int | str | None,
        sub_sport: int | str | None = None,
    ) -> Sport:
        if sport is None:
            sport = 0
        if sub_sport is None:
            sub_sport = 0
        return super().decode(GarminFitCode(sport, sub_sport))


garmin_fit = _GarminFitPlatform(
    GARMIN_FIT_MAPPINGS,
    GARMIN_FIT_FALLBACK,
    reducer=_reduce,
)
