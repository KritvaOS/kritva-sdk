#!/usr/bin/env python3
"""docs-check: every relative link in the Markdown files must point at an existing file."""
import re, sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
# Vendored upstream files are byte-exact copies pinned by PROVENANCE.json (make schema-drift); their relative links
# point into the upstream repository, so they are not checked here and must never be edited.
VENDORED = (("src", "kritva_sdk", "_schemas"), ("tests", "data"))
bad = []
for md in sorted(root.rglob("*.md")):
    if ".git" in md.parts or any(md.relative_to(root).parts[:len(v)] == v for v in VENDORED):
        continue
    for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
        if re.match(r"^[a-z]+:", target):
            continue
        if not (md.parent / target).exists():
            bad.append(f"{md.relative_to(root)}: broken link {target}")
print("\n".join(bad) or "docs-check ok")
sys.exit(1 if bad else 0)
