from open_sport_taxonomy._platform import Platform
from open_sport_taxonomy._platforms import (
    POLAR_ENTRIES_BY_TARGET,
    POLAR_FALLBACK_DECODE,
    POLAR_FALLBACK_ENCODE,
    POLAR_PREFERRED_INDEX,
    POLAR_TARGET_COARSENING,
)

polar = Platform(
    entries_by_target=POLAR_ENTRIES_BY_TARGET,
    preferred_index=POLAR_PREFERRED_INDEX,
    fallback_encode=POLAR_FALLBACK_ENCODE,
    fallback_decode=POLAR_FALLBACK_DECODE,
    target_coarsening=POLAR_TARGET_COARSENING,
)
