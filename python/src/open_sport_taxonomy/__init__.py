# Auto-generated from schema.yaml — do not edit.
# Run: uv run scripts/generate.py

from importlib.metadata import PackageNotFoundError, version as _dist_version

from open_sport_taxonomy._modifier import Modifier
from open_sport_taxonomy._platform import GarminFitCode
from open_sport_taxonomy._sport import Sport, StandardSport

try:
    version = _dist_version("open-sport-taxonomy")
except PackageNotFoundError:  # running from a source tree without an install
    version = "0+unknown"

taxonomy_version = "0.10.0"

__all__ = [
    "GarminFitCode",
    "Modifier",
    "Sport",
    "StandardSport",
    "taxonomy_version",
    "version",
]
