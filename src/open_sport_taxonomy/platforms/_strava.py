from open_sport_taxonomy._platform import Platform
from open_sport_taxonomy._platforms import (
    STRAVA_ENTRIES_BY_TARGET,
    STRAVA_FALLBACK_DECODE,
    STRAVA_FALLBACK_ENCODE,
    STRAVA_PREFERRED_INDEX,
    STRAVA_TARGET_COARSENING,
)

strava = Platform(
    entries_by_target=STRAVA_ENTRIES_BY_TARGET,
    preferred_index=STRAVA_PREFERRED_INDEX,
    fallback_encode=STRAVA_FALLBACK_ENCODE,
    fallback_decode=STRAVA_FALLBACK_DECODE,
    target_coarsening=STRAVA_TARGET_COARSENING,
)
