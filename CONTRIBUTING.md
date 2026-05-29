# Contributing

OpenSportTaxonomy is maintained by SweatStack. Contributions are welcome.

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

Examples of sport codes: `cycling.track` (different bike, different technique, specialized venue). `xc_skiing.double_poling` (distinct technique, own racing category).

Examples of things that are NOT sport codes: indoor cycling (it's `cycling.road` + `stationary`), e-bike gravel (it's `cycling.gravel` + `assisted`), roller skiing (it's `xc_skiing.classic` + `roller` — same technique, different surface), a cycling race (it's any cycling code + `race`).

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

Mapping files in `mappings/` translate platform-native sport identifiers to OST sport strings. The format (v3) is specified in [`docs/translation.md`](docs/translation.md). Briefly:

```yaml
format_version: 3
platform: <platform_id>
platform_version: <version of the bundled platform spec>

fallback:
  encode: <platform value returned when encoding has no match>
  decode: <OST sport string returned when decoding has no match>

target_coarsening:                  # optional, only for hierarchical targets
  - reset: { <field>: <root_value> }

entries:
  - target: <platform value>
    sport: <OST sport string> | null
    preferred: <bool>               # optional, default false
```

Files are **keyed by platform target** — every legal target in `reference/<platform>/targets.yaml` has exactly one row. Rows with no OST equivalent get `sport: null`. Exactly one row per non-null sport carries `preferred: true`; that row is used for encoding. Other rows decode to the same sport (synonyms).

The generator (`scripts/generate.py`) enforces 13 validation rules against every mapping file. The rule that mattered most for the 0.4.0 oversight: **every value in `reference/<platform>/targets.yaml` must have a row.** New SDK release → new rows or generation fails.

### Adding mappings to an existing file

Find the relevant row by its target. Change `sport: null` to the OST sport string. If multiple platform codes mean the same OST concept (e.g. FIT's `spin` and `indoor_cycling` both meaning `cycling+stationary`), mark exactly one as `preferred: true` and leave the others non-preferred.

**Auditing tip.** Many platforms encode OST modifiers as distinct platform types (FIT's `indoor_*` sub_sports, Strava's `Virtual*` types, Garmin Training API's `INDOOR_*` / `VIRTUAL_*` activities). When working through a platform's targets, search for prefixes like `indoor_`, `virtual_`, `e_`, `treadmill` — these almost always belong as OST sport-with-modifier entries (e.g. `cycling+stationary`, `cycling.road+virtual`), not as new OST sport codes.

### Bumping a platform version

When the upstream SDK adds new values:

1. Update the upstream source files in `reference/<platform>/`.
2. Run `uv run scripts/build_reference/<platform>.py` to regenerate `targets.yaml`.
3. Run `uv run scripts/scaffold.py <platform> --update` to add rows for the new targets (annotated with `sport: null`).
4. Annotate the new rows where they correspond to existing OST sports/modifiers.
5. Run `uv run scripts/lint.py`. If lint complains about missing OST codes, file a schema PR first.

### Adding a new platform

1. Create `reference/<platform>/` and document the upstream source in a `README.md`.
2. Write `scripts/build_reference/<platform>.py` that produces `reference/<platform>/targets.yaml` (a flat list of every legal target).
3. Register the platform in `PLATFORM_REF_DIR` and the defaults in `scripts/scaffold.py` and `scripts/generate.py`.
4. Run `uv run scripts/scaffold.py <platform>` to generate a skeleton mapping. Annotate where OST equivalents exist.
5. Add the platform's runtime instance under `src/open_sport_taxonomy/platforms/`.
6. Run `uv run scripts/lint.py` and the test suite.

## Versioning

The `version` field in `schema.yaml` follows [Semantic Versioning](https://semver.org):

- **Patch** (0.1.x) — new sport codes or modifiers added
- **Minor** (0.x.0) — new fields, new metadata, structural additions
- **Major** (x.0.0) — breaking changes to the schema format

Sport codes are never removed. A deprecated code gets a `deprecated: true` field and a `replaced_by` pointer.

Each release is tagged in git (`v0.1.0`) and published as a GitHub Release.

## Reporting errors

If a sport is miscategorized or a modifier applies incorrectly, open an issue describing the problem and the expected correction.
