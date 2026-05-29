# String Encoding

> The canonical string representation for a sport with modifiers.

**Status:** Proposed
**Separator:** `+`
**Format:** `<sport_code>` or `<sport_code>+<modifier>+<modifier>+...`

---

## This is the primary representation

The encoded string is the canonical way to represent a sport in OpenSportTaxonomy. It is what developers see first, what libraries accept as input, and what applications store.

```
cycling.road
cycling.road+race
cycling.road+race+virtual
```

A bare sport code is a valid encoded string. The `+` modifier syntax is an extension of the code, not a separate concept. This means the schema's existing sport codes (`cycling.road`, `running.trail`) are already valid encoded strings — the encoding is backwards-compatible by design.

The structured representation (separate `sport` and `modifiers` fields in JSON/YAML) is a derived form for contexts that need it, not the primary format.

### README and documentation

The README should lead with encoded strings, not JSON objects:

```diff
- { "sport": "cycling.road", "modifiers": ["stationary", "virtual", "race"] }
+ cycling.road+race+stationary+virtual
```

The "How it works" section should introduce the format directly:

```markdown
An activity is identified by a **sport string**: a sport code optionally followed
by modifiers.

    cycling.road                    — road cycling
    cycling.road+race               — road cycling race
    cycling.road+stationary+virtual — road cycling on Zwift
    running.trail+race              — trail running race
```

The JSON representation can appear later in a "Structured format" section for API and database contexts where separate fields are useful:

```json
{ "sport": "cycling.road", "modifiers": ["stationary", "virtual"] }
```

But the string encoding comes first.

---

## Format

A sport code on its own is a valid encoded string. When modifiers are present, they are appended with `+` as the separator. Modifiers are sorted alphabetically to guarantee a single canonical form per sport+modifier combination.

```
cycling.road
cycling.road+race
cycling.road+race+virtual
cycling.road+stationary+virtual
xc_skiing.roller.classic+race
generic+stationary
```

## Grammar

```
encoded    ::= sport_code ("+" modifier)*
sport_code ::= segment ("." segment)*
segment    ::= [a-z] [a-z0-9_]*
modifier   ::= [a-z] [a-z_]*
```

Where `sport_code` is a valid OpenSportTaxonomy sport code (lowercase, dot-separated hierarchy) and each `modifier` is a valid modifier code. Modifiers must appear in alphabetical order.

Encoded strings are case-sensitive. Only lowercase is valid.

## Parsing rules

1. Split the string on `+`.
2. The first token is the sport code.
3. All remaining tokens are modifiers.

This is unambiguous because sport codes never contain `+` (they use `.` for hierarchy and `_` for word separation) and modifier codes never contain `+` either.

### Invalid input

The following are invalid and must be rejected by conforming implementations:

- Empty string
- Leading or trailing `+` (`+cycling.road`, `cycling.road+`)
- Consecutive separators (`cycling.road++virtual`)
- Duplicate modifiers (`cycling.road+race+race`)
- Unsorted modifiers in strict mode (see canonicalization)
- Unknown sport codes or modifier codes (validation against the schema)
- Modifiers from the same group (`cycling.road+race+commute` — both in `purpose`)

## Canonicalization

There is exactly one canonical form per sport+modifier combination: the sport code followed by modifiers in alphabetical order.

Two encoded strings represent the same sport if and only if their canonical forms are identical.

Implementations must always produce canonical form when encoding. When decoding, implementations should accept non-canonical modifier order (Postel's law: be liberal in what you accept) but may reject it in strict mode.

## Why `+`

The `+` separator was chosen over alternatives (`:`, `;`, `@`) for:

- **Readability** — reads as natural language: "road cycling *plus* race *plus* virtual"
- **Flat grammar** — one separator for everything, no secondary delimiter needed
- **Visual distinction** — clearly different from `.` (hierarchy) and `_` (word separation)
- **Precedent** — semver build metadata (`1.0.0+build`), email sub-addressing (`user+tag`)

### Trade-off: URL query strings

In `application/x-www-form-urlencoded` query strings, `+` represents a space and must be percent-encoded as `%2B`. This encoding is used by HTML form submissions and by many HTTP client libraries when constructing query parameters.

This does not apply to:

- URL path segments (`/sport/cycling.road+race`)
- JSON request/response bodies
- HTTP headers
- Database fields, log lines, CSV cells

This trade-off was accepted because the encoded string primarily lives in storage and structured data, not in URL query strings.

## Examples

| Sport | Modifiers | Encoded |
|---|---|---|
| `cycling.road` | — | `cycling.road` |
| `cycling.road` | `race` | `cycling.road+race` |
| `cycling.road` | `race`, `virtual` | `cycling.road+race+virtual` |
| `cycling.road` | `assisted` | `cycling.road+assisted` |
| `cycling.mountain` | `assisted`, `race` | `cycling.mountain+assisted+race` |
| `running.trail` | `race` | `running.trail+race` |
| `rowing` | `stationary`, `virtual` | `rowing+stationary+virtual` |
| `generic` | — | `generic` |
