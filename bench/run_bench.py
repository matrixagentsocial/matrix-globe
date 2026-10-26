"""Benchmark runner (PLAN.md 5.7; Decisions of 2026-10-26 conditions A-E).

A Spark single shot medium; B Wonder single shot effort max; C Spark
self-refine; D Spark builder + Wonder reviewer (proof rule) + Spark
reviser; E like D with free-text review and no proof rule. Each run
writes a ProofBundle to ``results/bundles/`` and one JSONL line with
task id, condition, seed, model, effort, hidden/public passed/total,
all_pass, usd, reviewer_usd, duration; D/E also carry claims
proposed/proven/unproven/invalid/valid/unconfirmed, rounds, regressions.

Run from the repo root, e.g.:
``.venv\\Scripts\\python bench\\run_bench.py --cond D --split dev --limit 6 --seeds 1 --sandbox local``
Only this script and ``scripts/`` may call the API.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bench.task_loader import Task, discover_tasks
from proof.pytest_runner import run_pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MAX_USD_PER_SINGLE_RUN = 0.05


class SingleRunCostExceeded(RuntimeError):
    """One builder call cost more than the M1 stop threshold."""


def _counts(result) -> tuple[int, int]:
    return result.passed, result.total


def run_condition_a(
    tasks: list[Task],
    *,
    client: Any,
    sandbox: Any,
    seeds: int = 1,
    ledger: Any = None,
    model: str = "",
    effort: str = "",
    max_usd_per_run_check: float = MAX_USD_PER_SINGLE_RUN,
    on_row: Any = None,
) -> list[dict[str, Any]]:
    """Run condition A over *tasks*; return one row dict per task x seed."""
    from proof.roles.builder import build_solution

    rows: list[dict[str, Any]] = []
    for task in tasks:
        for seed in range(seeds):
            run_id = f"bench-A-{task.id}-s{seed}"
            before_usd = ledger.total_usd() if ledger is not None else 0.0
            started = time.monotonic()
            code = build_solution(client, task.spec, run_id=run_id)
            usd = (ledger.total_usd() - before_usd) if ledger is not None else 0.0
            if usd > max_usd_per_run_check:
                raise SingleRunCostExceeded(
                    f"single run for task {task.id!r} seed {seed} cost "
                    f"${usd:.4f} > ${max_usd_per_run_check:.2f}; stopping"
                )
            public_run = run_pytest(
                sandbox, code, {"public_test.py": task.public_test}
            )
            hidden_run = run_pytest(
                sandbox, code, {"hidden_test.py": task.hidden_test}
            )
            duration = time.monotonic() - started
            public_passed, public_total = _counts(public_run)
            hidden_passed, hidden_total = _counts(hidden_run)
            all_pass = (
                public_run.all_passed
                and hidden_run.all_passed
                and public_total > 0
                and hidden_total > 0
            )
            rows.append(
                {
                    "task_id": task.id,
                    "condition": "A",
                    "seed": seed,
                    "model": model,
                    "effort": effort,
                    "hidden_passed": hidden_passed,
                    "hidden_total": hidden_total,
                    "public_passed": public_passed,
                    "public_total": public_total,
                    "all_pass": all_pass,
                    "usd": round(float(usd), 6),
                    "duration": round(duration, 3),
                    "run_id": run_id,
                }
            )
            if on_row is not None:
                on_row(rows[-1])
    return rows


def _claim_counts(bundle: Any) -> dict[str, int]:
    counts = {"claims_proposed": 0, "claims_proven": 0, "claims_unproven": 0,
              "claims_invalid": 0, "claims_valid": 0, "claims_unconfirmed": 0}
    for rnd in getattr(bundle, "rounds", []) or []:
        for c in getattr(rnd, "claims", []) or []:
            counts["claims_proposed"] += 1
            status = str(getattr(c, "status", "")).upper()
            if status == "PROVEN":
                counts["claims_proven"] += 1
            elif status == "UNPROVEN":
                counts["claims_unproven"] += 1
            elif status == "INVALID":
                counts["claims_invalid"] += 1
            validity = str(getattr(c, "validity", "") or "").upper()
            if validity == "VALID":
                counts["claims_valid"] += 1
            elif validity == "UNCONFIRMED":
                counts["claims_unconfirmed"] += 1
    return counts


def run_condition(
    tasks: list[Task],
    cond: str,
    *,
    client: Any,
    sandbox: Any,
    seeds: int = 1,
    ledger: Any = None,
    settings: Any = None,
    bundles_dir: Path | None = None,
    sandbox_label: str = "local",
    max_usd_per_single_run: float = 0.40,
    on_row: Any = None,
) -> list[dict[str, Any]]:
    """Run any condition A-E via the proof loop; one row per task x seed."""
    from proof.loop import run_proof

    cond = str(cond).upper()
    rows: list[dict[str, Any]] = []
    for task in tasks:
        for seed in range(seeds):
            run_id = f"bench-{cond}-{task.id}-s{seed}"
            before_usd = ledger.total_usd() if ledger is not None and hasattr(ledger, "total_usd") else 0.0
            before_reviewer = 0.0
            if ledger is not None and hasattr(ledger, "entries"):
                before_reviewer = sum(float(r.get("usd", 0.0) or 0.0) for r in ledger.entries()
                                      if r.get("role") in ("reviewer", "freeform_reviewer"))
            started = time.monotonic()
            bundle = run_proof(task, cond, client=client, sandbox=sandbox, ledger=ledger,
                               settings=settings, run_id=run_id, sandbox_label=sandbox_label)
            code = bundle.finalCode or ""
            public_run = run_pytest(sandbox, code, {"public_test.py": task.public_test}) if code else None
            hidden_run = run_pytest(sandbox, code, {"hidden_test.py": task.hidden_test}) if code else None
            duration = time.monotonic() - started
            usd = (ledger.total_usd() - before_usd) if ledger is not None and hasattr(ledger, "total_usd") else float(bundle.cost.usd)
            if ledger is not None and hasattr(ledger, "entries"):
                reviewer_usd = sum(float(r.get("usd", 0.0) or 0.0) for r in ledger.entries()
                                   if r.get("role") in ("reviewer", "freeform_reviewer")) - before_reviewer
            else:
                reviewer_usd = float(bundle.cost.reviewerUsd)
            public_passed, public_total = _counts(public_run) if public_run else (bundle.tests.public.passed, bundle.tests.public.total)
            hidden_passed, hidden_total = _counts(hidden_run) if hidden_run else (0, 0)
            all_pass = bool(public_run and hidden_run and public_run.all_passed and hidden_run.all_passed)
            bundle_path = ""
            bundle_sha = ""
            if bundles_dir is not None:
                bundles_dir.mkdir(parents=True, exist_ok=True)
                p = bundles_dir / f"{run_id}.json"
                p.write_text(bundle.canonical_json(), encoding="utf-8")
                try:
                    bundle_path = str(p.resolve().relative_to(REPO_ROOT))
                except Exception:
                    bundle_path = str(p)
                bundle_sha = bundle.sha256()
            counts = _claim_counts(bundle)
            regressions = sum(1 for e in bundle.events if e.type == "regression")
            if cond == "B" and settings is not None:
                model, effort = settings.model_reviewer, "max"
            elif settings is not None:
                model, effort = settings.model_builder, settings.effort_builder
            else:
                model, effort = bundle.models.builder.model, bundle.models.builder.effort
            row = {
                "task_id": task.id, "condition": cond, "seed": seed,
                "model": model, "effort": effort,
                "hidden_passed": hidden_passed, "hidden_total": hidden_total,
                "public_passed": public_passed, "public_total": public_total,
                "all_pass": all_pass, "usd": round(float(usd), 6),
                "reviewer_usd": round(float(reviewer_usd), 6),
                "duration": round(duration, 3), "run_id": run_id,
                "status": bundle.status, "bundle": bundle_path, "bundle_sha256": bundle_sha,
                "llm_calls": bundle.llmCalls,
                **counts,
                "rounds": len(bundle.rounds), "regressions": regressions,
            }
            rows.append(row)
            if on_row is not None:
                on_row(row)
            if float(usd) > max_usd_per_single_run:
                raise SingleRunCostExceeded(
                    f"single run for task {task.id!r} seed {seed} cost ${float(usd):.4f} "
                    f"> ${max_usd_per_single_run:.2f}; stopping")
    return rows


def write_rows(rows: list[dict[str, Any]], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out_path


def format_results_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        f"{'task':<22} {'seed':<5} {'public':<9} {'hidden':<9} {'all_pass':<9} {'usd':<10} duration",
    ]
    for r in rows:
        lines.append(
            f"{r['task_id']:<22} {r['seed']:<5} "
            f"{r['public_passed']}/{r['public_total']:<7} "
            f"{r['hidden_passed']}/{r['hidden_total']:<7} "
            f"{str(r['all_pass']):<9} ${r['usd']:<9.4f} {r['duration']:.2f}s"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run FinCode benchmark (conditions A-E)")
    parser.add_argument("--cond", default="A", choices=["A", "B", "C", "D", "E"], help="condition")
    parser.add_argument("--split", default="dev", choices=["dev", "test"])
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--sandbox", default="local", choices=["local", "docker"])
    parser.add_argument("--task", default=None, help="only run the task with this id")
    parser.add_argument("--tasks", default=str(REPO_ROOT / "bench" / "tasks"))
    parser.add_argument("--out", default=None, help="output JSONL path")
    parser.add_argument("--bundles-dir", default=None, help="bundles output dir")
    parser.add_argument("--max-usd-per-run", type=float, default=0.40,
                        help="stop if a single run exceeds this USD cost")
    args = parser.parse_args(argv)

    if args.sandbox == "docker":
        from proof.sandbox.docker import DockerSandbox

        sandbox: Any = DockerSandbox()
    else:
        from proof.sandbox.local import LocalSandbox

        sandbox = LocalSandbox()

    tasks = discover_tasks(args.tasks, split=args.split)
    if args.task:
        tasks = [t for t in tasks if t.id == args.task]
    if args.limit is not None and args.limit >= 0:
        tasks = tasks[: args.limit]
    if not tasks:
        print("no tasks matched", file=sys.stderr)
        return 1

    from proof.config import load_settings
    from proof.ledger import Ledger
    from proof.llm import LLMClient

    settings = load_settings()
    ledger = Ledger(settings=settings)
    client = LLMClient(ledger=ledger, settings=settings)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = (
        Path(args.out)
        if args.out
        else REPO_ROOT / "results" / "runs" / f"cond{args.cond}_{args.split}_{stamp}.jsonl"
    )
    bundles_dir = Path(args.bundles_dir) if args.bundles_dir else REPO_ROOT / "results" / "bundles"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_handle = out_path.open("a", encoding="utf-8")

    def _on_row(row: dict[str, Any]) -> None:
        out_handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        out_handle.flush()

    try:
        rows = run_condition(
            tasks, args.cond,
            client=client, sandbox=sandbox, seeds=args.seeds, ledger=ledger,
            settings=settings, bundles_dir=bundles_dir, sandbox_label=args.sandbox,
            max_usd_per_single_run=args.max_usd_per_run, on_row=_on_row,
        )
    finally:
        out_handle.close()
    print(format_results_table(rows))
    print(f"wrote {len(rows)} rows to {out_path}")
    print(f"bundles in {bundles_dir}")
    total_usd = sum(r["usd"] for r in rows)
    reviewer_usd = sum(r.get("reviewer_usd", 0.0) for r in rows)
    print(f"total cost: ${total_usd:.4f} (reviewer: ${reviewer_usd:.4f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
