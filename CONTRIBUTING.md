# Contributing

OpenSportsSchema is maintained by SweatStack. Contributions are welcome.

## Schema format

The canonical schema is [`schema.yaml`](schema.yaml). It contains two flat lists:

**Sports** are sorted alphabetically by code. Each entry has a `code` and a `label`. Hierarchy is encoded in the dot notation: `cycling.mountain.xco` is a child of `cycling.mountain`, which is a child of `cycling`. Every parent must have its own entry.

**Modifiers** are sorted alphabetically by code. Each entry has a `code` and `label`. Modifiers with a `group` field are mutually exclusive within that group. Modifiers without a group are independent flags.

## Adding a sport code

Open an issue or pull request with:

- **Code** — lowercase, dot-separated. Must nest under an existing parent or introduce a new top-level sport.
- **Label** — English display name.
- **Rationale** — why this is a distinct discipline, not a variant of an existing code.

Apply the test: if you removed this level from the code, would an athlete still recognize the activity as the same sport? If yes, it probably belongs as a modifier, not a sport code. If no, it's a distinct discipline and belongs in the tree.

Examples of sport codes: `cycling.track` (different bike, different technique, specialized venue). `skiing.roller` (different equipment, different surface, own racing circuit).

Examples of things that are NOT sport codes: indoor cycling (it's `cycling.road` + `stationary`), e-bike gravel (it's `cycling.gravel` + `assisted`), a cycling race (it's any cycling code + `race`).

## Adding a modifier

Modifiers should be rare. A new modifier must apply to multiple sport codes and represent a concept that cuts across the sport tree. Open an issue with:

- **Code** — lowercase, single word.
- **Group** — if mutually exclusive with existing modifiers, which group? If independent, leave blank.
- **Rationale** — why this can't be a sport code.

## Conventions

- Codes are lowercase, using underscores for multi-word segments: `hand_cycling`, not `handCycling`.
- Codes use full words, not abbreviations: `cycling.time_trial`, not `cycling.tt`. Abbreviations are acceptable only when the full form is rarely used (e.g. `xc_skiing`).
- Labels are lowercase, with capitals only for acronyms: "road cycling", "classic XC skiing", "BMX".
- Both sports and modifiers are sorted alphabetically by code.
- Keep entries minimal. Descriptions, emoji, mappings, and translations live in separate files, not in the core schema.

Before submitting a pull request, run the linter:

```bash
uv run scripts/lint.py          # check for ordering and orphan issues
uv run scripts/lint.py --fix    # auto-fix ordering
```

## Platform mappings

Mapping files in `mappings/` translate OSS codes to platform-specific identifiers. Every file follows the same structure:

```yaml
platform: <platform_id>
platform_version: <version of the platform spec>
fallback: <platform's generic/catch-all value>

mappings:
  - oss: <sport_code>
    modifiers: [<modifier>, ...]     # optional
    target: <platform_specific_value>
```

When adding or updating mappings:

- **Every OSS sport code should have an entry in every mapping file**, even when the mapping is lossy. If the platform doesn't distinguish the discipline, map to the closest equivalent.
- **Entries are sorted by `oss`**, then by `modifiers`.
- When a platform encodes an OSS modifier as a distinct sport type (e.g. Strava's `VirtualRide`), add an entry with `modifiers`. The entry without modifiers is the default.
- For numeric targets, add a YAML comment with the human-readable name: `target: 13  # cycling`.
- The `fallback` field documents the platform's catch-all value. It's a safety net for codes not yet in the file, not a replacement for explicit entries.

### Adding a new platform

Create a new file in `mappings/` following the format above. Add reference data for the platform in `reference/<platform>/` with a README explaining the source.

## Versioning

The `version` field in `schema.yaml` follows [Semantic Versioning](https://semver.org):

- **Patch** (0.1.x) — new sport codes or modifiers added
- **Minor** (0.x.0) — new fields, new metadata, structural additions
- **Major** (x.0.0) — breaking changes to the schema format

Sport codes are never removed. A deprecated code gets a `deprecated: true` field and a `replaced_by` pointer.

Each release is tagged in git (`v0.1.0`) and published as a GitHub Release.

## Reporting errors

If a sport is miscategorized or a modifier applies incorrectly, open an issue describing the problem and the expected correction.
