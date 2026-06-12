"""Shared test fixtures and project-path constants.

Tests are organized into ``domain/``, ``algorithm/``, ``integration/``, and
``properties/`` subdirectories. Project paths are defined here once so each
test file does not need to count parent traversals.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAPPINGS_DIR = ROOT / "mappings"
REFERENCE_DIR = ROOT / "reference"
SCRIPTS_DIR = ROOT / "scripts"
SCHEMA_PATH = ROOT / "schema.yaml"
