from __future__ import annotations

from open_sport_taxonomy._platform import GarminFitCode, Platform
from open_sport_taxonomy._platforms import (
    GARMIN_FIT_ENTRIES_BY_TARGET,
    GARMIN_FIT_FALLBACK_DECODE,
    GARMIN_FIT_FALLBACK_ENCODE,
    GARMIN_FIT_PREFERRED_INDEX,
    GARMIN_FIT_TARGET_COARSENING,
)
from open_sport_taxonomy._sport import Sport


class _GarminFitPlatform(Platform):
    """Garmin FIT — ``decode`` accepts ``(sport, sub_sport)`` directly.

    Users hold ``sport`` and ``sub_sport`` as separate values when reading
    a FIT file, so the natural call shape is ``decode(2, 7)``. ``None``
    in either position is treated as the FIT ``generic`` value (``0``)
    — useful when a FIT parser returns ``None`` for an absent field.
    """

    def decode(
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
    entries_by_target=GARMIN_FIT_ENTRIES_BY_TARGET,
    preferred_index=GARMIN_FIT_PREFERRED_INDEX,
    fallback_encode=GARMIN_FIT_FALLBACK_ENCODE,
    fallback_decode=GARMIN_FIT_FALLBACK_DECODE,
    target_coarsening=GARMIN_FIT_TARGET_COARSENING,
)
