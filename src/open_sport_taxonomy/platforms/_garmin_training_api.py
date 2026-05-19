from open_sport_taxonomy._platform import Platform
from open_sport_taxonomy._platforms import (
    GARMIN_TRAINING_API_FALLBACK,
    GARMIN_TRAINING_API_MAPPINGS,
)

garmin_training_api = Platform(GARMIN_TRAINING_API_MAPPINGS, GARMIN_TRAINING_API_FALLBACK)
