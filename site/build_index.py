"""Build the static proof viewer's data folder from results/.

Usage: python site/build_index.py [--out site/data]

Copies every ProofBundle in results/bundles/ into <out>/bundles/ and writes
<out>/index.json with one row per bundle, including the SHA-256 of its
canonical JSON computed by proof.bundle (the same function the desk uses for
certificates). The browser recomputes that hash in JavaScript; bundles that
contain floats are skipped because JS and Python format floats differently.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from proof.bundle import canonical_json, sha256_text  # noqa: E402


def has_float(value) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(has_float(v) for v in value.values())
    if isinstance(value, list):
        return any(has_float(v) for v in value)
    return False


def summarize(bundle: dict, sha: str, name: str) -> dict:
    claims = [claim for round_ in bundle.get("rounds", []) for claim in round_.get("claims", [])]
    proven = [c for c in claims if c.get("status") == "PROVEN"]
    return {
        "runId": bundle.get("runId"),
        "task": (bundle.get("task") or {}).get("id"),
        "mode": bundle.get("mode"),
        "status": bundle.get("status"),
        "createdAt": bundle.get("createdAt"),
        "reviewer": ((bundle.get("models") or {}).get("reviewer") or {}).get("model"),
        "builder": ((bundle.get("models") or {}).get("builder") or {}).get("model"),
        "claims": {
            "proposed": len(claims),
            "proven": len(proven),
            "valid": sum(1 for c in proven if c.get("validity") == "VALID"),
        },
        "usd": (bundle.get("cost") or {}).get("usd"),
        "sha256": sha,
        "file": f"bundles/{name}",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(REPO / "site" / "data"))
    parser.add_argument("--bundles", default=str(REPO / "results" / "bundles"))
    args = parser.parse_args()
    out = Path(args.out)
    (out / "bundles").mkdir(parents=True, exist_ok=True)

    rows, skipped = [], []
    for path in sorted(Path(args.bundles).glob("*.json")):
        bundle = json.loads(path.read_text(encoding="utf-8"))
        if has_float(bundle):
            skipped.append(path.name)
            continue
        canonical = canonical_json(bundle)
        (out / "bundles" / path.name).write_text(canonical, encoding="utf-8")
        rows.append(summarize(bundle, sha256_text(canonical), path.name))

    rows.sort(key=lambda r: (r.get("createdAt") or ""), reverse=True)
    (out / "index.json").write_text(json.dumps({"bundles": rows, "skipped": skipped}, indent=1), encoding="utf-8")

    summary = REPO / "results" / "summary.json"
    if summary.exists():
        shutil.copyfile(summary, out / "summary.json")
    print(f"{len(rows)} bundles indexed, {len(skipped)} skipped (floats) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
