from open_sport_taxonomy._platform import Platform
from open_sport_taxonomy._platforms import (
    APPLE_HEALTHKIT_ENTRIES_BY_TARGET,
    APPLE_HEALTHKIT_FALLBACK_DECODE,
    APPLE_HEALTHKIT_FALLBACK_ENCODE,
    APPLE_HEALTHKIT_PREFERRED_INDEX,
    APPLE_HEALTHKIT_TARGET_COARSENING,
)

apple_healthkit = Platform(
    entries_by_target=APPLE_HEALTHKIT_ENTRIES_BY_TARGET,
    preferred_index=APPLE_HEALTHKIT_PREFERRED_INDEX,
    fallback_encode=APPLE_HEALTHKIT_FALLBACK_ENCODE,
    fallback_decode=APPLE_HEALTHKIT_FALLBACK_DECODE,
    target_coarsening=APPLE_HEALTHKIT_TARGET_COARSENING,
)
