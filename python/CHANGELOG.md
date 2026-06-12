# Changelog — open-sport-taxonomy (Python package)

Release notes for the Python **package**. Changes to the OST **spec** (the sport/modifier
vocabulary, the OST string format, the mapping format, and the bundled platform mappings)
are tracked in the [root CHANGELOG](../CHANGELOG.md). Package history through `0.9.0`
lives in that root changelog; the package's own changelog starts here, at the repo
restructure.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
package follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Package relocated to the `python/` subdirectory** as part of the spec-first repo
  layout ([`plans/025`](../plans/025-spec-first-repo-layout.md)). No API or runtime
  behaviour change — the built wheel's code payload is byte-identical to `0.9.0`. The
  spec version is unchanged (`taxonomy_version == 0.9.0`); only the package release moves.
