"""Benchmark runner (PLAN.md section 5.7). Condition A only for M1.

Condition A: Spark builder, single shot, effort medium
(Decisions of 2026-10-26). For each task x seed: builder -> run
public + hidden tests in the sandbox -> one JSONL line with task id,
condition, seed, model, effort, hidden passed/total, public
passed/total, all_pass, usd and duration.

Run from the repo root, e.g.:
``.venv\\Scripts\\python bench\\run_bench.py --cond A --split dev --limit 6 --seeds 1 --sandbox local``
Only this script and ``scripts/smoke.py`` may call the API.
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
    parser = argparse.ArgumentParser(description="Run FinCode benchmark (condition A)")
    parser.add_argument("--cond", default="A", choices=["A"], help="condition (only A in M1)")
    parser.add_argument("--split", default="dev", choices=["dev", "test"])
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--sandbox", default="local", choices=["local", "docker"])
    parser.add_argument("--tasks", default=str(REPO_ROOT / "bench" / "tasks"))
    parser.add_argument("--out", default=None, help="output JSONL path")
    args = parser.parse_args(argv)

    if args.sandbox == "docker":
        from proof.sandbox.docker import DockerSandbox

        sandbox: Any = DockerSandbox()
    else:
        from proof.sandbox.local import LocalSandbox

        sandbox = LocalSandbox()

    tasks = discover_tasks(args.tasks, split=args.split)
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
    model = settings.model_for_role("builder")
    effort = settings.effort_for_role("builder")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = (
        Path(args.out)
        if args.out
        else REPO_ROOT / "results" / "runs" / f"condA_{args.split}_{stamp}.jsonl"
    )
    # Write each row as it completes so a later failure keeps earlier rows.
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_handle = out_path.open("a", encoding="utf-8")

    def _on_row(row: dict[str, Any]) -> None:
        out_handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        out_handle.flush()

    try:
        rows = run_condition_a(
            tasks,
            client=client,
            sandbox=sandbox,
            seeds=args.seeds,
            ledger=ledger,
            model=model,
            effort=effort,
            on_row=_on_row,
        )
    finally:
        out_handle.close()
    print(format_results_table(rows))
    print(f"wrote {len(rows)} rows to {out_path}")
    total_usd = sum(r["usd"] for r in rows)
    print(f"total builder cost: ${total_usd:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
