# Open Sport Taxonomy — developer workflows.
#
# Run `make` (or `make help`) to see all targets.
# Targets are organised by purpose: quality, generation, packaging, housekeeping.
# Each target has a single job; composition happens through dependencies.

UV ?= uv
PYTEST_FLAGS ?=

# The Python package lives in python/; spec tooling (PEP 723 scripts) lives at root.
# Package commands run with python/ as the working directory & project.
PY = $(UV) run --directory python

.DEFAULT_GOAL := help
.PHONY: help \
        lint test test-only check format fix mutmut \
        generate \
        tool \
        build publish \
        clean

# --------------------------------------------------------------------------
# Help — default target. Auto-generated from ## comments on target lines.
# --------------------------------------------------------------------------

help: ## Show this help and exit
	@printf "Usage: make <target>\n\n"
	@printf "Targets:\n"
	@awk 'BEGIN {FS = ":.*?## "} \
	     /^[a-zA-Z_-]+:.*?## / {printf "  \033[1m%-14s\033[0m %s\n", $$1, $$2}' \
	     $(MAKEFILE_LIST)
	@printf "\n"
	@printf "Variables:\n"
	@printf "  \033[1mPYTEST_FLAGS\033[0m   Extra flags passed to pytest. Example:\n"
	@printf "                 make test PYTEST_FLAGS=-v\n"
	@printf "  \033[1mUV\033[0m             Override the uv binary. Example:\n"
	@printf "                 make test UV=/opt/bin/uv\n"

# --------------------------------------------------------------------------
# Quality — static analysis and tests.
# --------------------------------------------------------------------------

lint: ## Run all static checks (ruff, mypy, schema, reference drift, generator)
	@$(UV) run scripts/lint.py

test-only: ## Run the test suite (pytest with coverage; skips lint)
	@$(PY) python -m pytest $(PYTEST_FLAGS)

test: lint test-only ## Run lint then the test suite (safe default for CI)

check: test ## Alias for `test`; preferred CI entry point

format: ## Apply ruff formatter (package + root scripts)
	@$(PY) ruff format --config pyproject.toml src tests scripts ../scripts

fix: ## Auto-fix what ruff can (lint + format)
	@$(PY) ruff check --fix --config pyproject.toml src tests scripts ../scripts
	@$(PY) ruff format --config pyproject.toml src tests scripts ../scripts

mutmut: ## Run mutation testing on the runtime (slow; periodic health check)
	@$(PY) mutmut run --paths-to-mutate=src/open_sport_taxonomy/_platform.py
	@$(PY) mutmut results

# --------------------------------------------------------------------------
# Generation — regenerate auto-generated source from schema and mappings.
# --------------------------------------------------------------------------

generate: ## Regenerate auto-generated Python (python/) + docs from schema.yaml + mappings/
	@$(PY) scripts/generate.py
	@$(UV) run scripts/generate_reference.py

# --------------------------------------------------------------------------
# Tooling — the browser-based translation explorer (tool/index.html).
# --------------------------------------------------------------------------

tool: ## Serve the translation explorer (open /tool/ at the address it prints)
	@printf "Translation explorer — open \033[1m/tool/\033[0m at the address printed below (Ctrl-C to stop)\n"
	@python3 -m http.server 0

# --------------------------------------------------------------------------
# Packaging.
# --------------------------------------------------------------------------

build: ## Build wheel and sdist into python/dist/
	@rm -rf python/dist
	@$(UV) build python

publish: build ## Upload python/dist/* to PyPI (requires credentials)
	@uvx twine upload python/dist/*

# --------------------------------------------------------------------------
# Housekeeping.
# --------------------------------------------------------------------------

clean: ## Remove caches and build artifacts
	@rm -rf dist/ build/ python/dist/ .pytest_cache/ python/.pytest_cache/ \
	        .mypy_cache/ python/.mypy_cache/ .ruff_cache/ python/.ruff_cache/ \
	        .hypothesis/ python/.hypothesis/ .mutmut-cache python/.mutmut-cache \
	        mutants/ htmlcov/ python/htmlcov/ .coverage python/.coverage
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
