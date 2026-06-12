# Changelog — open-sport-taxonomy (Python package)

Release notes for the Python **package**. Changes to the OST **spec** (the sport/modifier
vocabulary, the OST string format, the mapping format, and the bundled platform mappings)
are tracked in the [root CHANGELOG](../CHANGELOG.md). Package history through `0.9.0`
lives in that root changelog; the package's own changelog starts here, at the repo
restructure.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
package follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.10.0] - 2026-06-12

Implements OST spec **0.10.0** (the standard-sports catalogue; see the
[root CHANGELOG](../CHANGELOG.md)).

### Added

- **`Sport.uses_known_atoms`** — the level-2 predicate: `True` when the code and every modifier are declared atoms (and group-valid), even if the exact combination is not a catalogued standard sport.
- **`StandardSport`** — a `Literal` type of every standard-sport canonical string (codes *and* combinations), generated from the catalogue. Annotate your own variables/fields with it for autocomplete (Pyright/Pylance, PyCharm) and mypy typo-checking. The `Sport(...)` / `Sport.parse(...)` constructors deliberately take a plain `str` (they ingest runtime data and validate at runtime), so `StandardSport` is an opt-in static vocabulary for *your* code, not a runtime constraint.

### Removed

- **Per-code class constants (`Sport.CYCLING_ROAD`, …) are gone.** They were a bare-code-only projection that couldn't represent the catalogue's combinations and required an ugly naming scheme to complete. Use the string form — `Sport("cycling.road")`, `Sport("cycling+stationary")` — with `StandardSport` for autocomplete and type-checking.

### Changed

- **`Sport.is_standard` now means catalogue membership** (level 3), not "known code + modifiers" (which is now `uses_known_atoms`). For example `Sport("cycling.road+race").is_standard` is now `False` (it was `True`); it remains `uses_known_atoms`.
- **`Sport.label` always returns `str`** (was `str | None`): the hand-crafted catalogue label for a standard sport, otherwise a label composed from the parts (`cycling.road+race` → `"road cycling (race)"`). `is_standard` distinguishes curated from composed.
- **`Sport.resolve()` is now two-phase and drop-only** — climb the code tree to the nearest standard ancestor, then keep the largest modifier subset that forms a catalogue entry. It never adds a modifier (e.g. `cycling.road+race` resolves to `cycling.road`, not itself).
- **`Sport.all()` returns the full catalogue** (codes *and* combinations), one `Sport` per standard sport.


## [0.9.1] - 2026-06-12

### Changed

- **Package relocated to the `python/` subdirectory** as part of the spec-first repo
  layout ([`plans/025`](../plans/025-spec-first-repo-layout.md)). No API or runtime
  behaviour change — the built wheel's code payload is byte-identical to `0.9.0`. The
  spec version is unchanged (`taxonomy_version == 0.9.0`); only the package release moves.
