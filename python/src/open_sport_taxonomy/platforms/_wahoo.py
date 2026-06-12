from open_sport_taxonomy._platform import Platform
from open_sport_taxonomy._platforms import (
    WAHOO_ENTRIES_BY_TARGET,
    WAHOO_FALLBACK_DECODE,
    WAHOO_FALLBACK_ENCODE,
    WAHOO_PREFERRED_INDEX,
    WAHOO_TARGET_COARSENING,
)

wahoo = Platform(
    entries_by_target=WAHOO_ENTRIES_BY_TARGET,
    preferred_index=WAHOO_PREFERRED_INDEX,
    fallback_encode=WAHOO_FALLBACK_ENCODE,
    fallback_decode=WAHOO_FALLBACK_DECODE,
    target_coarsening=WAHOO_TARGET_COARSENING,
)
