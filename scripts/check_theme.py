#!/usr/bin/env python3
"""Consistency checks for themes/atelier.yaml.

The theme has two layers: tokens (`atelier-*`) defined per mode under `modes:`,
and a semantic mapping at the root that only references those tokens with
`var(--atelier-*)`. This script fails when the layers drift apart.
"""
import re
import sys
from pathlib import Path

import yaml

THEME = Path("themes/atelier.yaml")
VAR_RE = re.compile(r"var\(--(atelier-[\w-]+)\)")
COLOUR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(")


def main() -> int:
    data = yaml.safe_load(THEME.read_text(encoding="utf-8"))
    theme = data["Atelier"]
    modes = theme.pop("modes")
    dark, light = modes["dark"], modes["light"]
    errors: list[str] = []

    if set(dark) != set(light):
        errors.append(f"token sets differ between modes: {sorted(set(dark) ^ set(light))}")

    non_token = [k for k in list(dark) + list(light) if not k.startswith("atelier-")]
    if non_token:
        errors.append(f"only atelier-* tokens belong under modes: {sorted(set(non_token))}")

    referenced = {m for v in theme.values() for m in VAR_RE.findall(str(v))}
    unresolved = referenced - set(dark)
    if unresolved:
        errors.append(f"var() references without a token: {sorted(unresolved)}")

    literals = [k for k, v in theme.items() if COLOUR_RE.search(str(v))]
    if literals:
        errors.append(f"colour literals outside modes: {sorted(literals)}")

    for name, mode in (("dark", dark), ("light", light)):
        empty = [k for k, v in mode.items() if v in (None, "")]
        if empty:
            errors.append(f"empty token values in {name}: {sorted(empty)}")

    for err in errors:
        print(f"✗ {err}")
    if errors:
        return 1

    exposed = sorted(set(dark) - referenced)
    print(f"✓ {len(dark)} tokens per mode, {len(referenced)} referenced by the mapping")
    print(f"ℹ {len(exposed)} tokens exposed for cards only: {', '.join(exposed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
