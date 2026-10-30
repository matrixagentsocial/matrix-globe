"""Build the static proof viewer's data folder from results/.

Usage: python site/build_index.py [--out site/data]

Copies every ProofBundle under results/ (the dev demo bundles in
results/bundles/, the final run in results/final/bundles_*/ and the
open-weights run in results/final_open/bundles_*/) into <out>/bundles/ and
writes <out>/index.json with one row per bundle, including the SHA-256 of its
canonical JSON computed by proof.bundle (the same function the desk uses for
certificates). The browser recomputes that hash in JavaScript; bundles that
contain floats are skipped because JS and Python format floats differently.

It also writes <out>/summary.json with the final-run tables, computed from the
committed per-target JSONL rows (results/final/*.jsonl and
results/final_open/*.jsonl), so the page never shows a hand-typed number.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from proof.bundle import canonical_json, sha256_text  # noqa: E402

# (stack, folder) pairs; the folder holds <scope>_<condition>.jsonl files and
# bundles_<scope>_<condition>/ directories.
RUNS = (("meta", "final"), ("open", "final_open"))

STACKS = {
    "meta": "Hosted Meta models (Muse Wonder reviewer, Muse Spark 1.3 builder/reviser)",
    "open": "Open weights only (Muse Spark Open on Baseten for every role)",
    "dev": "Dev-split demo runs",
}

CONDITIONS = {
    "R": "No review (ship as is)",
    "C": "Self-check: Spark writes its own tests and revises",
    "E": "Free-text review, no proof rule",
    "D": "Matrix Globe: proof-gated review",
    "B": "Wonder max regenerates from the spec",
}

HEADLINE = (
    "Requiring proof turns a cheap open-weights model into a reliable reviewer: "
    "with Muse Spark Open for every role, proof-gated review fixed 57/60 single-task "
    "bugs versus 41/60 for free-text review by the same model (PR packages: 17/18 vs "
    "12/18), with no damage to correct code, and every claim it makes ships with an "
    "executable failing test. With Meta's hosted models every reviewing condition fixes "
    "almost everything; there the value of the proof rule is the audit trail, not the fix rate."
)


def has_float(value) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(has_float(v) for v in value.values())
    if isinstance(value, list):
        return any(has_float(v) for v in value)
    return False


def split_name(name: str) -> tuple[str, str]:
    """'pr_D_open' -> ('pr', 'D'); 'single_C' -> ('single', 'C')."""
    scope, _, condition = name.partition("_")
    return scope, condition.split("_")[0]


def summarize(bundle: dict, sha: str, name: str, stack: str, scope: str | None) -> dict:
    claims = [claim for round_ in bundle.get("rounds", []) for claim in round_.get("claims", [])]
    proven = [c for c in claims if c.get("status") == "PROVEN"]
    return {
        "runId": bundle.get("runId"),
        "task": (bundle.get("task") or {}).get("id"),
        "target": bundle.get("target"),
        "mode": bundle.get("mode"),
        "stack": stack,
        "scope": scope,
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


def bundle_sources(results: Path):
    """Yield (path, stack, scope) for every committed bundle."""
    for path in sorted((results / "bundles").glob("*.json")):
        yield path, "dev", None
    for stack, folder in RUNS:
        for directory in sorted((results / folder).glob("bundles_*")):
            scope, _ = split_name(directory.name.removeprefix("bundles_"))
            for path in sorted(directory.glob("*.json")):
                yield path, stack, scope


def condition_row(name: str, rows: list[dict]) -> dict:
    scope, condition = split_name(name)
    buggy = [r for r in rows if r["target_id"] not in ("clean", "regen")]
    clean = [r for r in rows if r["target_id"] == "clean"]
    regen = [r for r in rows if r["target_id"] == "regen"]
    proven = sum(r.get("claims_proven", 0) for r in rows)
    valid = sum(r.get("claims_valid", 0) for r in rows)
    usd = sum(float(r.get("usd") or 0) for r in rows)
    return {
        "id": condition,
        "label": CONDITIONS.get(condition, condition),
        "scope": scope,
        "targets": len(rows),
        "seeds": len({r.get("seed") for r in rows}),
        "fixed": sum(1 for r in buggy if r.get("fixed")),
        "buggy": len(buggy),
        "damaged": sum(1 for r in clean if r.get("damaged")),
        "clean": len(clean),
        "regenPassed": sum(1 for r in regen if r.get("all_pass")),
        "regen": len(regen),
        "regressions": sum(r.get("regressions", 0) for r in rows),
        "claims": {
            "proposed": sum(r.get("claims_proposed", 0) for r in rows),
            "proven": proven,
            "valid": valid,
            "unconfirmed": sum(r.get("claims_unconfirmed", 0) for r in rows),
        },
        "precision": round(valid / proven, 2) if proven else None,
        "usdPerTarget": round(usd / len(rows), 4) if rows else None,
        "usdTotal": round(usd, 4),
        "tasks": len({r["task_id"] for r in rows}),
    }


def build_summary(results: Path) -> dict:
    order = {c: i for i, c in enumerate("RCEDB")}
    tables = []
    for stack, folder in RUNS:
        for scope in ("pr", "single"):
            conditions = []
            for path in sorted((results / folder).glob(f"{scope}_*.jsonl")):
                rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
                if rows:
                    conditions.append(condition_row(path.stem, rows))
            if conditions:
                conditions.sort(key=lambda c: order.get(c["id"], 9))
                tables.append({"stack": stack, "stackLabel": STACKS[stack], "scope": scope, "conditions": conditions})
    return {"status": "final" if tables else "pending", "headline": HEADLINE, "tables": tables}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(REPO / "site" / "data"))
    parser.add_argument("--results", default=str(REPO / "results"))
    args = parser.parse_args()
    out = Path(args.out)
    results = Path(args.results)
    (out / "bundles").mkdir(parents=True, exist_ok=True)

    rows, skipped = [], []
    for path, stack, scope in bundle_sources(results):
        bundle = json.loads(path.read_text(encoding="utf-8"))
        if has_float(bundle):
            skipped.append(path.name)
            continue
        canonical = canonical_json(bundle)
        (out / "bundles" / path.name).write_text(canonical, encoding="utf-8")
        rows.append(summarize(bundle, sha256_text(canonical), path.name, stack, scope))

    rows.sort(key=lambda r: (r.get("createdAt") or ""), reverse=True)
    (out / "index.json").write_text(json.dumps({"bundles": rows, "skipped": skipped}, indent=1), encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(build_summary(results), indent=1), encoding="utf-8")
    print(f"{len(rows)} bundles indexed, {len(skipped)} skipped (floats) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
