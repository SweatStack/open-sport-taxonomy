from open_sport_taxonomy._platform import Platform
from open_sport_taxonomy._platforms import (
    APPLE_HEALTHKIT_FALLBACK,
    APPLE_HEALTHKIT_MAPPINGS,
)

apple_healthkit = Platform(APPLE_HEALTHKIT_MAPPINGS, APPLE_HEALTHKIT_FALLBACK)
