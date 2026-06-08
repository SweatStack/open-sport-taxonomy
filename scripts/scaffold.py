# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///

"""Scaffold a mapping/<platform>.yaml file from reference/<platform>/targets.yaml.

Two modes:

    uv run scripts/scaffold.py <platform>
        Generate a fresh skeleton: every target gets a row with `sport: null`.
        Used when bringing a new platform online.

    uv run scripts/scaffold.py <platform> --update
        Merge existing mappings/<platform>.yaml entries into a fresh skeleton.
        Preserves all annotations and adds rows for any new targets in
        targets.yaml that the existing mapping omits. Used after bumping
        a platform_version.

See docs/translation.md for the format v3 specification.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
MAPPINGS_DIR = ROOT / "mappings"
REFERENCE_DIR = ROOT / "reference"


# --------------------------------------------------------------------------
# Platform → reference directory and target shape.
# --------------------------------------------------------------------------

PLATFORM_REF_DIR = {
    "garmin_fit": "garmin-fit-sdk",
    "strava": "strava",
    "apple_healthkit": "apple-healthkit",
    "garmin_training_api": "garmin-training-api",
    "wahoo": "wahoo",
}


def target_key(target: Any) -> Any:
    """Hashable form of a target — dicts become sorted-item tuples."""
    if isinstance(target, dict):
        return tuple(sorted(target.items()))
    return target


def load_targets(platform: str) -> list[Any]:
    ref_path = REFERENCE_DIR / PLATFORM_REF_DIR[platform] / "targets.yaml"
    data = yaml.safe_load(ref_path.read_text(encoding="utf-8"))
    return data["targets"]


def load_existing(platform: str) -> dict | None:
    path = MAPPINGS_DIR / f"{platform}.yaml"
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# Rendering. The output is hand-tunable YAML, not a YAML dump — comments
# and column alignment matter for human review.
# --------------------------------------------------------------------------


def render_target(target: Any) -> str:
    """Render a target as inline YAML, aligned for column scan."""
    if isinstance(target, dict):
        # FIT-style {sport, sub_sport}. Right-align numerics for scan.
        pairs = ", ".join(f"{k}: {v:>3}" for k, v in target.items())
        return "{ " + pairs + " }"
    if isinstance(target, int):
        return f"{target:>4}"
    if isinstance(target, str):
        return target
    return str(target)


def render_entry(target: Any, sport: str | None, preferred: bool, comment: str | None) -> list[str]:
    """One entry as a list of YAML lines."""
    target_str = render_target(target)
    sport_str = "null" if sport is None else sport
    suffix = f"  # {comment}" if comment else ""
    lines = [
        f"  - target: {target_str}{suffix}",
        f"    sport: {sport_str}",
    ]
    if preferred:
        lines.append("    preferred: true")
    return lines


def render_file(
    platform: str,
    platform_version: str,
    fallback_encode: Any,
    fallback_decode: str,
    target_coarsening: list[dict[str, Any]],
    entries: list[dict[str, Any]],
    comments: dict[Any, str],
) -> str:
    """Render a complete v3 mapping file."""
    lines: list[str] = [
        f"# OpenSportTaxonomy — {platform} mapping (format v3).",
        "#",
        "# See docs/translation.md for the format specification.",
        "# See CONTRIBUTING.md for the workflow.",
        "",
        "format_version: 3",
        f"platform: {platform}",
        f'platform_version: "{platform_version}"',
        "",
        "fallback:",
        f"  encode: {render_target(fallback_encode)}",
        f"  decode: {fallback_decode}",
        "",
    ]
    if target_coarsening:
        lines.append("target_coarsening:")
        for rule in target_coarsening:
            if "reset" in rule:
                pairs = ", ".join(f"{k}: {v}" for k, v in rule["reset"].items())
                lines.append(f"  - reset: {{ {pairs} }}")
        lines.append("")

    lines.append("entries:")
    for entry in entries:
        lines.append("")
        lines.extend(
            render_entry(
                entry["target"],
                entry.get("sport"),
                entry.get("preferred", False),
                comments.get(target_key(entry["target"])),
            )
        )
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform", choices=sorted(PLATFORM_REF_DIR))
    parser.add_argument(
        "--update",
        action="store_true",
        help="merge with existing mappings/<platform>.yaml instead of overwriting",
    )
    args = parser.parse_args()

    targets = load_targets(args.platform)
    existing = load_existing(args.platform) if args.update else None

    # Build target → (sport, preferred) map from existing, if any.
    existing_by_target: dict[Any, dict] = {}
    if existing and "entries" in existing:
        for e in existing["entries"]:
            existing_by_target[target_key(e["target"])] = e

    # Defaults — overridden via existing file when present.
    defaults_by_platform = {
        "garmin_fit": {
            "platform_version": "FIT SDK 21.133",
            "fallback_encode": {"sport": 0, "sub_sport": 0},
            "fallback_decode": "generic",
            "target_coarsening": [
                {"reset": {"sub_sport": 0}},
                {"reset": {"sport": 0, "sub_sport": 0}},
            ],
        },
        "strava": {
            "platform_version": "v3 API, 2024",
            "fallback_encode": "Workout",
            "fallback_decode": "generic",
            "target_coarsening": [],
        },
        "apple_healthkit": {
            "platform_version": "iOS 18",
            "fallback_encode": 3000,
            "fallback_decode": "generic",
            "target_coarsening": [],
        },
        "garmin_training_api": {
            "platform_version": "V2 1.0 (2025-05-26)",
            "fallback_encode": "GENERIC",
            "fallback_decode": "generic",
            "target_coarsening": [],
        },
        "wahoo": {
            "platform_version": "Cloud API (changelog 2025-10-06)",
            "fallback_encode": 47,
            "fallback_decode": "generic",
            "target_coarsening": [],
        },
    }
    defaults = defaults_by_platform[args.platform]

    platform_version = (existing or {}).get("platform_version", defaults["platform_version"])
    fb = (existing or {}).get("fallback", {})
    fallback_encode = fb.get("encode", defaults["fallback_encode"])
    fallback_decode = fb.get("decode", defaults["fallback_decode"])
    target_coarsening = (existing or {}).get("target_coarsening", defaults["target_coarsening"])

    # Build entries: one row per target, sourcing annotations from existing.
    entries: list[dict[str, Any]] = []
    for target in targets:
        key = target_key(target)
        existing_entry = existing_by_target.get(key)
        if existing_entry is not None:
            entries.append(
                {
                    "target": target,
                    "sport": existing_entry.get("sport"),
                    "preferred": existing_entry.get("preferred", False),
                }
            )
        else:
            entries.append({"target": target, "sport": None, "preferred": False})

    # Optional comments — for FIT, annotate with sport/sub_sport names.
    comments: dict[Any, str] = {}
    if args.platform == "garmin_fit":
        comments = _fit_comments(targets)
    elif args.platform == "apple_healthkit":
        comments = _healthkit_comments(targets)
    elif args.platform == "wahoo":
        comments = _wahoo_comments(targets)

    text = render_file(
        args.platform,
        platform_version,
        fallback_encode,
        fallback_decode,
        target_coarsening,
        entries,
        comments,
    )
    out_path = MAPPINGS_DIR / f"{args.platform}.yaml"
    out_path.write_text(text, encoding="utf-8")
    print(f"wrote {out_path.relative_to(ROOT)}: {len(entries)} entries")
    return 0


def _fit_comments(targets: list[Any]) -> dict[Any, str]:
    """Annotate FIT targets with `sport_name / sub_sport_name`."""
    sports_path = REFERENCE_DIR / "garmin-fit-sdk" / "sports.yaml"
    sub_path = REFERENCE_DIR / "garmin-fit-sdk" / "sub_sports.yaml"
    sport_names = {s["value"]: s["name"] for s in yaml.safe_load(sports_path.read_text())["cases"]}
    sub_names = {ss["value"]: ss["name"] for ss in yaml.safe_load(sub_path.read_text())["cases"]}

    comments: dict[Any, str] = {}
    for t in targets:
        s, ss = t["sport"], t["sub_sport"]
        comments[target_key(t)] = f"{sport_names.get(s, '?')} / {sub_names.get(ss, '?')}"
    return comments


def _healthkit_comments(targets: list[Any]) -> dict[Any, str]:
    src_path = REFERENCE_DIR / "apple-healthkit" / "workout_activity_types.yaml"
    cases = yaml.safe_load(src_path.read_text())["cases"]
    names = {c["raw_value"]: c["name"] for c in cases}

    comments: dict[Any, str] = {}
    for t in targets:
        comments[target_key(t)] = names.get(t, "?")
    return comments


def _wahoo_comments(targets: list[Any]) -> dict[Any, str]:
    """Annotate Wahoo targets with `NAME (FAMILY/LOCATION)`."""
    src_path = REFERENCE_DIR / "wahoo" / "workout_types.yaml"
    cases = yaml.safe_load(src_path.read_text())["cases"]
    meta = {c["value"]: (c["name"], c["family"], c["location"]) for c in cases}

    comments: dict[Any, str] = {}
    for t in targets:
        name, family, location = meta.get(t, ("?", "?", "?"))
        comments[target_key(t)] = f"{name} ({family}/{location})"
    return comments


if __name__ == "__main__":
    sys.exit(main())
