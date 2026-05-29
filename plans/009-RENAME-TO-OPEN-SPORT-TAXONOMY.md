# Rename to OpenSportTaxonomy

> Rename the project from OpenSportsSchema to OpenSportTaxonomy across all layers.

**Status:** Proposed

---

## Rationale

"OpenSportTaxonomy" is more accurate — this project defines a hierarchical classification (taxonomy) of sports, not a data schema. "Schema" implies a database structure or validation format. "Taxonomy" communicates exactly what it is: a classified vocabulary.

---

## Name mappings

| Context | Before | After |
|---|---|---|
| Display name | OpenSportsSchema | OpenSportTaxonomy |
| PyPI package | `open-sports-schema` | `open-sport-taxonomy` |
| Python import | `open_sports_schema` | `open_sport_taxonomy` |
| GitHub repo | `sweatstack/open-sports-schema` | `sweatstack/open-sport-taxonomy` |
| Abbreviation (mappings) | OSS | OST |

Note: "Sport" singular, not "Sports" — it's a taxonomy of sport, like "sport science" not "sports science." No domain name is associated with the project.

---

## Changes by layer

### 1. Python package

| File/directory | Change |
|---|---|
| `src/open_sports_schema/` | Rename to `src/open_sport_taxonomy/` |
| `pyproject.toml` | name = "open-sport-taxonomy" |
| All Python imports | `open_sports_schema` → `open_sport_taxonomy` |
| `scripts/generate.py` | Update OUT_DIR and `resources.files()` references |

**Files with import changes:**
- `src/open_sport_taxonomy/__init__.py`
- `src/open_sport_taxonomy/_sport.py`
- `src/open_sport_taxonomy/_platform.py`
- `src/open_sport_taxonomy/_platforms.py`
- `src/open_sport_taxonomy/platforms/__init__.py`
- `src/open_sport_taxonomy/platforms/_strava.py`
- `src/open_sport_taxonomy/platforms/_apple_healthkit.py`
- `src/open_sport_taxonomy/platforms/_garmin_fit.py`
- All test files (`tests/test_*.py`)

### 2. Schema and mapping files

| File | Change |
|---|---|
| `schema.yaml` | Header comment: `OpenSportTaxonomy` |
| `mappings/apple_healthkit.yaml` | Header comment |
| `mappings/garmin_fit.yaml` | Header comment |
| `mappings/strava.yaml` | Header comment |

**Mapping key rename:** The `oss` field in mapping files becomes `ost`:

```yaml
# Before
- oss: cycling.road
  target: Ride

# After
- ost: cycling.road
  target: Ride
```

This touches every entry in all three mapping files.

### 3. Documentation

| File | Change |
|---|---|
| `README.md` | Title, description, GitHub URLs, pip install command |
| `CONTRIBUTING.md` | Project name references |
| `dist/reference.md` | Title (auto-generated — regenerate after rename) |
| `plans/001-OPEN-SPORTS-SCHEMA.md` | Historical — leave as-is or add note at top |
| `plans/002-REPO-STRUCTURE.md` | References |
| `plans/003-TAXONOMY-DESIGN.md` | References |
| `plans/004-PLATFORM-MAPPINGS.md` | OSS → OST throughout |
| `plans/005-PYTHON-LIBRARY.md` | Package name, imports |
| `plans/006-STRING-ENCODING.md` | References |
| `plans/007-FORWARD-COMPATIBILITY.md` | References |
| `plans/008-STANDARD-AND-NON-STANDARD-SPORTS.md` | References |

### 4. Scripts and templates

| File | Change |
|---|---|
| `scripts/generate.py` | OUT_DIR path, generated import paths |
| `scripts/lint.py` | Header comment |
| `scripts/generate_reference.py` | Any string references |
| `scripts/templates/reference.md.jinja` | Title reference |

### 5. Configuration and metadata

| File | Change |
|---|---|
| `pyproject.toml` | `name = "open-sport-taxonomy"` |
| `uv.lock` | Regenerated automatically after pyproject.toml change |
| `.python-version` | No change |
| `.gitignore` | No change |

### 6. GitHub/infrastructure

| Item | Change |
|---|---|
| Repository name | `open-sports-schema` → `open-sport-taxonomy` |
| GitHub URLs in docs | Update all raw.githubusercontent.com references |
| PyPI registration | Register `open-sport-taxonomy` |

---

## Execution order

1. **Rename the package directory:** `src/open_sports_schema/` → `src/open_sport_taxonomy/`
2. **Update `pyproject.toml`:** package name
3. **Update `scripts/generate.py`:** OUT_DIR path and generated import strings
4. **Regenerate:** `uv run scripts/generate.py` (this fixes all generated imports)
5. **Update hand-written source files:** `_platform.py`, `platforms/*.py`, `__init__.py`
6. **Update all test files:** import paths
7. **Update mapping files:** `oss` → `ost` field name
8. **Update schema.yaml:** header comment
9. **Update documentation:** README, CONTRIBUTING, plans
10. **Update scripts:** lint.py, generate_reference.py, templates
11. **Regenerate reference:** `uv run scripts/generate_reference.py`
12. **Run tests:** verify everything passes
13. **Update uv.lock:** `uv lock`

Steps 1-6 can be done as a bulk find-and-replace. Steps 7-10 require more careful edits.

---

## What NOT to rename

- **Plan 001** (`001-OPEN-SPORTS-SCHEMA.md`) — this is historical. Add a note at the top: "Note: This plan was written under the original project name OpenSportsSchema. The project has since been renamed to OpenSportTaxonomy." Keep the filename as-is.
- **Git history** — commits reference the old name. This is fine. History is history.
- **The `oss` abbreviation in existing code comments** — only rename in functional code and documentation, not in historical plan content where it would be confusing.

---

## Verification checklist

After the rename:

- [ ] `uv run pytest tests/` passes
- [ ] `uv run scripts/generate.py --check` passes
- [ ] `from open_sport_taxonomy import Sport, Modifier` works
- [ ] `Sport.CYCLING_ROAD.label` returns "road cycling"
- [ ] `Sport.resolve("cycling.road+race")` works
- [ ] `uv run scripts/lint.py` passes
- [ ] `uv run scripts/generate_reference.py` produces valid output
- [ ] No remaining references to `open_sports_schema` in source or tests (grep check)
- [ ] No remaining `oss:` keys in mapping files
