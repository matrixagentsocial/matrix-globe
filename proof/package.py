"""Package helpers for PR targets: several modules as one code unit.

A package is stored in bundles / loop state as one deterministic text:
``# === task_a.py ===`` headers followed by each module's source. The
sandbox receives the modules as separate files.
"""
from __future__ import annotations

import re

_HEADER = re.compile(r"^# === (.+?) ===\s*$", re.M)


def format_package(modules: dict[str, str]) -> str:
    parts: list[str] = []
    for name in sorted(modules):
        parts.append(f"# === {name} ===\n{modules[name].rstrip()}\n")
    return "\n".join(parts)


def parse_package(text: str, module_names: list[str] | None = None) -> dict[str, str]:
    matches = list(_HEADER.finditer(text or ""))
    if not matches:
        return {}
    out: dict[str, str] = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():end]
        if body.startswith("\n"):
            body = body[1:]
        out[m.group(1).strip()] = body.rstrip() + "\n"
    if module_names is not None:
        return {n: out[n] for n in module_names if n in out}
    return out


def is_package_text(text: str) -> bool:
    return bool(_HEADER.search(text or ""))
