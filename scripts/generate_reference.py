# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml", "jinja2"]
# ///

"""Generate docs/reference.md from schema.yaml.

Usage:
    uv run scripts/generate_reference.py
"""

import sys
from collections import defaultdict
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema.yaml"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
OUTPUT_PATH = ROOT / "docs" / "reference.md"


def load_schema():
    return yaml.safe_load(SCHEMA_PATH.read_text())


def build_tree(sports):
    """Build a nested tree from the flat sport list."""
    nodes = {s["code"]: {**s, "children": []} for s in sports}
    roots = []

    for code in sorted(nodes):
        parts = code.split(".")
        if len(parts) == 1:
            roots.append(nodes[code])
        else:
            parent_code = ".".join(parts[:-1])
            if parent_code in nodes:
                nodes[parent_code]["children"].append(nodes[code])
            else:
                roots.append(nodes[code])

    return roots


def group_modifiers(modifiers):
    """Split modifiers into grouped (by group name) and ungrouped."""
    groups = defaultdict(list)
    ungrouped = []

    for m in modifiers:
        if "group" in m:
            groups[m["group"]].append(m)
        else:
            ungrouped.append(m)

    return sorted(groups.items()), ungrouped


def render_sport(node, depth):
    """Recursively render a sport node as nested markdown list items."""
    indent = "  " * depth
    line = f"{indent}- **{node['code']}** — {node['label']}"
    children = "\n".join(render_sport(c, depth + 1) for c in node["children"])
    if children:
        return f"{line}\n{children}"
    return line


def main():
    schema = load_schema()
    sports = schema.get("sports", [])
    modifiers = schema.get("modifiers", [])

    tree = build_tree(sports)
    groups, ungrouped = group_modifiers(modifiers)
    families = sum(1 for s in sports if "." not in s["code"])

    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["render_sport"] = render_sport

    template = env.get_template("reference.md.jinja")
    content = template.render(
        taxonomy_version=schema.get("version", "unknown"),
        families=families,
        total_sports=len(sports),
        total_modifiers=len(modifiers),
        tree=tree,
        groups=groups,
        ungrouped=ungrouped,
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(content)
    print(f"generated: {OUTPUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
