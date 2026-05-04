from open_sports_schema._platform import Platform
from open_sports_schema._platforms import STRAVA_FALLBACK, STRAVA_MAPPINGS

strava = Platform(STRAVA_MAPPINGS, STRAVA_FALLBACK)
