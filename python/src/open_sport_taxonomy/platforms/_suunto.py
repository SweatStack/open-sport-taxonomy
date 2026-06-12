from open_sport_taxonomy._platform import Platform
from open_sport_taxonomy._platforms import (
    SUUNTO_ENTRIES_BY_TARGET,
    SUUNTO_FALLBACK_DECODE,
    SUUNTO_FALLBACK_ENCODE,
    SUUNTO_PREFERRED_INDEX,
    SUUNTO_TARGET_COARSENING,
)

suunto = Platform(
    entries_by_target=SUUNTO_ENTRIES_BY_TARGET,
    preferred_index=SUUNTO_PREFERRED_INDEX,
    fallback_encode=SUUNTO_FALLBACK_ENCODE,
    fallback_decode=SUUNTO_FALLBACK_DECODE,
    target_coarsening=SUUNTO_TARGET_COARSENING,
)
