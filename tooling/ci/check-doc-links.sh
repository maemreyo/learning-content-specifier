#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import re
from pathlib import Path

root = Path('docs')
broken = []

for md in list(root.rglob('*.md')) + [Path('README.md'), Path('spec-driven.md')]:
    if not md.exists():
        continue
    text = md.read_text(encoding='utf-8')
    for m in re.finditer(r'\[[^\]]+\]\(([^)]+)\)', text):
        link = m.group(1).strip()
        if link.startswith(('http://','https://','mailto:','#')):
            continue
        link = link.split('#',1)[0]
        if not link or link.startswith('<'):
            continue
        target = (md.parent / link).resolve()
        if not target.exists():
            broken.append((str(md), link))

if broken:
    for src, link in broken:
        print(f"BROKEN: {src} -> {link}")
    raise SystemExit(1)

print('Docs link check passed')
PY
