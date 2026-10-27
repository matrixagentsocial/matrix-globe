"""Benchmark runner (Experiment redesign of 2026-10-27).

Review benchmark: targets are 3 mutants + 1 clean (reference) per task.
Conditions: R no review, C Spark self-check, E Wonder free-text review,
D Matrix Globe (Wonder proof-gated review), B Wonder effort max
regenerates from the spec (one run per task, ignores the target code).
Reviewer/reviser see spec + target code only, never reference/hidden.

Cost is attributed strictly by ``run_id`` from the ledger entries, so
concurrent bench processes sharing one ledger never mix costs.

Run from the repo root, e.g.:
``.venv\\Scripts\\python bench\\run_bench.py --cond D --split dev --targets all --limit 10 --seeds 1 --sandbox local``
Only this script and ``scripts/`` may call the API.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import replace as dc_replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bench.task_loader import Task, discover_tasks, load_targets
from proof.pytest_runner import run_pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MAX_USD_PER_SINGLE_RUN = 0.05


class SingleRunCostExceeded(RuntimeError):
    """One run cost more than the configured stop threshold."""


def cost_for_run(ledger: Any, run_id: str, *, roles: tuple[str, ...] | None = None) -> float:
    """USD for exactly *run_id* from ledger entries (never a time window).

    Falls back to ``total_usd`` deltas only for test doubles that expose
    neither ``entries()`` nor ``run_usd()``; the real Ledger has both.
    """
    if ledger is None:
        return 0.0
    if hasattr(ledger, "entries"):
        total = 0.0
        for row in ledger.entries():
            if row.get("run_id") != run_id:
                continue
            if roles is not None and row.get("role") not in roles:
                continue
            total += float(row.get("usd", 0.0) or 0.0)
        return total
    if hasattr(ledger, "run_usd"):
        if roles is None:
            return float(ledger.run_usd(run_id) or 0.0)
        return 0.0
    return 0.0


def _counts(result) -> tuple[int, int]:
    return result.passed, result.total


def _passed_names(result) -> set[str]:
    return {t.name for t in result.tests if t.outcome == "passed"}


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
    """Legacy condition A over *tasks*; cost strictly by run_id."""
    from proof.roles.builder import build_solution

    rows: list[dict[str, Any]] = []
    use_fallback = ledger is not None and not hasattr(ledger, "entries") and not hasattr(ledger, "run_usd")
    for task in tasks:
        for seed in range(seeds):
            run_id = f"bench-A-{task.id}-s{seed}"
            before_usd = ledger.total_usd() if (use_fallback and ledger is not None) else 0.0
            started = time.monotonic()
            code = build_solution(client, task.spec, run_id=run_id)
            usd = (ledger.total_usd() - before_usd) if use_fallback else cost_for_run(ledger, run_id)
            if usd > max_usd_per_run_check:
                raise SingleRunCostExceeded(
                    f"single run for task {task.id!r} seed {seed} cost "
                    f"${usd:.4f} > ${max_usd_per_run_check:.2f}; stopping"
                )
            public_run = run_pytest(sandbox, code, {"public_test.py": task.public_test})
            hidden_run = run_pytest(sandbox, code, {"hidden_test.py": task.hidden_test})
            duration = time.monotonic() - started
            public_passed, public_total = _counts(public_run)
            hidden_passed, hidden_total = _counts(hidden_run)
            all_pass = (public_run.all_passed and hidden_run.all_passed
                        and public_total > 0 and hidden_total > 0)
            rows.append({
                "task_id": task.id, "condition": "A", "seed": seed,
                "model": model, "effort": effort,
                "hidden_passed": hidden_passed, "hidden_total": hidden_total,
                "public_passed": public_passed, "public_total": public_total,
                "all_pass": all_pass, "usd": round(float(usd), 6),
                "duration": round(duration, 3), "run_id": run_id,
            })
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


def _contested_breakdown(bundle: Any) -> dict[str, int]:
    """UNCONFIRMED proven claims the reviser contested vs accepted."""
    contested_ids: set[str] = set()
    unconfirmed_ids: list[str] = []
    for rnd in getattr(bundle, "rounds", []) or []:
        for c in getattr(rnd, "contested", []) or []:
            cid = c.get("claim_id") if isinstance(c, dict) else getattr(c, "claim_id", "")
            if cid:
                contested_ids.add(str(cid).lower())
        for c in getattr(rnd, "claims", []) or []:
            if str(getattr(c, "status", "")).upper() == "PROVEN" and \
                    str(getattr(c, "validity", "") or "").upper() == "UNCONFIRMED":
                unconfirmed_ids.append(str(getattr(c, "id", "")).lower())
    contested = sum(1 for cid in unconfirmed_ids if cid in contested_ids)
    return {"claims_unconfirmed_contested": contested,
            "claims_unconfirmed_accepted": len(unconfirmed_ids) - contested}


def _write_bundle(bundle: Any, bundles_dir: Path | None, run_id: str) -> tuple[str, str]:
    if bundles_dir is None:
        return "", bundle.sha256()
    bundles_dir.mkdir(parents=True, exist_ok=True)
    p = bundles_dir / f"{run_id}.json"
    p.write_text(bundle.canonical_json(), encoding="utf-8")
    try:
        bundle_path = str(p.resolve().relative_to(REPO_ROOT))
    except Exception:
        bundle_path = str(p)
    return bundle_path, bundle.sha256()


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
    run_suffix: str = "",
) -> list[dict[str, Any]]:
    """Legacy builder-first conditions A-E via the proof loop."""
    from proof.loop import run_proof

    cond = str(cond).upper()
    rows: list[dict[str, Any]] = []
    for task in tasks:
        for seed in range(seeds):
            run_id = f"bench-{cond}-{task.id}-s{seed}{run_suffix}"
            started = time.monotonic()
            bundle = run_proof(task, cond, client=client, sandbox=sandbox, ledger=ledger,
                               settings=settings, run_id=run_id, sandbox_label=sandbox_label)
            code = bundle.finalCode or ""
            public_run = run_pytest(sandbox, code, {"public_test.py": task.public_test}) if code else None
            hidden_run = run_pytest(sandbox, code, {"hidden_test.py": task.hidden_test}) if code else None
            duration = time.monotonic() - started
            usd = cost_for_run(ledger, run_id) if ledger is not None else float(bundle.cost.usd)
            if ledger is None:
                usd = float(bundle.cost.usd)
            reviewer_usd = (cost_for_run(ledger, run_id, roles=("reviewer", "freeform_reviewer"))
                            if ledger is not None else float(bundle.cost.reviewerUsd))
            public_passed, public_total = _counts(public_run) if public_run else (bundle.tests.public.passed, bundle.tests.public.total)
            hidden_passed, hidden_total = _counts(hidden_run) if hidden_run else (0, 0)
            all_pass = bool(public_run and hidden_run and public_run.all_passed and hidden_run.all_passed)
            bundle_path, bundle_sha = _write_bundle(bundle, bundles_dir, run_id)
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


def run_review_bench(
    tasks: list[Task],
    cond: str,
    *,
    client: Any = None,
    sandbox: Any,
    seeds: int = 1,
    ledger: Any = None,
    settings: Any = None,
    bundles_dir: Path | None = None,
    sandbox_label: str = "local",
    targets: str = "all",
    reviewer_effort: str | None = None,
    max_usd_per_single_run: float = 10.0,
    on_row: Any = None,
    run_suffix: str = "",
) -> list[dict[str, Any]]:
    """Review benchmark (redesign): one row per (task, target, seed).

    B runs once per task (target_id ``regen``); R makes no LLM calls.
    """
    from proof.loop import run_proof

    cond = str(cond).upper()
    if cond not in ("R", "B", "C", "D", "E"):
        raise ValueError(f"review benchmark condition must be R|B|C|D|E, got {cond!r}")
    eff_settings = settings
    if reviewer_effort and settings is not None:
        try:
            eff_settings = dc_replace(settings, effort_reviewer=reviewer_effort)
        except Exception:
            settings.effort_reviewer = reviewer_effort  # type: ignore[attr-defined]
            eff_settings = settings
    rows: list[dict[str, Any]] = []
    for task in tasks:
        if cond == "B":
            target_list: list[tuple[str, str]] = [("regen", task.reference)]
        else:
            target_list = load_targets(task, targets)
        for target_id, target_code in target_list:
            for seed in range(seeds):
                run_id = f"bench-{cond}-{task.id}-{target_id}-s{seed}{run_suffix}"
                started = time.monotonic()
                hidden_before = run_pytest(sandbox, target_code, {"hidden_test.py": task.hidden_test})
                before_passed = _passed_names(hidden_before)
                if cond == "R":
                    bundle = run_proof(task, "R", client=None, sandbox=sandbox, ledger=ledger,
                                       settings=eff_settings, run_id=run_id,
                                       sandbox_label=sandbox_label,
                                       initial_code=target_code, target_id=target_id)
                elif cond == "B":
                    bundle = run_proof(task, "B", client=client, sandbox=sandbox, ledger=ledger,
                                       settings=eff_settings, run_id=run_id,
                                       sandbox_label=sandbox_label, target_id=target_id)
                else:
                    bundle = run_proof(task, cond, client=client, sandbox=sandbox, ledger=ledger,
                                       settings=eff_settings, run_id=run_id,
                                       sandbox_label=sandbox_label,
                                       initial_code=target_code, target_id=target_id)
                final_code = bundle.finalCode or target_code
                hidden_after = run_pytest(sandbox, final_code, {"hidden_test.py": task.hidden_test})
                after_passed = _passed_names(hidden_after)
                duration = time.monotonic() - started
                usd = cost_for_run(ledger, run_id) if ledger is not None else float(bundle.cost.usd)
                reviewer_usd = (cost_for_run(ledger, run_id, roles=("reviewer", "freeform_reviewer"))
                                if ledger is not None else float(bundle.cost.reviewerUsd))
                regression_names = sorted(before_passed - after_passed)
                fixed = bool(hidden_after.all_passed)
                damaged = bool(target_id == "clean" and not fixed)
                bundle_path, bundle_sha = _write_bundle(bundle, bundles_dir, run_id)
                counts = _claim_counts(bundle)
                row = {
                    "task_id": task.id, "target_id": target_id, "condition": cond,
                    "seed": seed,
                    "hidden_before_passed": hidden_before.passed,
                    "hidden_before_total": hidden_before.total,
                    "hidden_after_passed": hidden_after.passed,
                    "hidden_after_total": hidden_after.total,
                    # legacy aliases for older reports
                    "hidden_passed": hidden_after.passed, "hidden_total": hidden_after.total,
                    "all_pass": fixed,
                    "fixed": fixed,
                    "regressions": len(regression_names),
                    "regressions_detail": regression_names,
                    "damaged": damaged,
                    **counts,
                    "usd": round(float(usd), 6),
                    "reviewer_usd": round(float(reviewer_usd), 6),
                    "duration": round(duration, 3),
                    "status": bundle.status, "bundle": bundle_path,
                    "bundle_sha256": bundle_sha, "llm_calls": bundle.llmCalls,
                    "rounds": len(bundle.rounds), "run_id": run_id,
                    **_contested_breakdown(bundle),
                }
                rows.append(row)
                if on_row is not None:
                    on_row(row)
                if float(usd) > max_usd_per_single_run:
                    raise SingleRunCostExceeded(
                        f"run {run_id} cost ${float(usd):.4f} > ${max_usd_per_single_run:.2f}; stopping")
    return rows



def run_review_bench_prs(
    prs: list[Any],
    cond: str,
    *,
    client: Any = None,
    sandbox: Any,
    seeds: int = 1,
    ledger: Any = None,
    settings: Any = None,
    bundles_dir: Path | None = None,
    sandbox_label: str = "local",
    tasks_root: str | Path = "bench/tasks",
    reviewer_effort: str | None = None,
    max_usd_per_single_run: float = 10.0,
    on_row: Any = None,
    run_suffix: str = "",
    target_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Review benchmark on PR packages: one row per (PR, target, seed).

    B runs once per PR (target ``regen``); R makes no LLM calls.
    """
    from bench.prs import load_pr_targets
    from proof.loop import run_proof
    from proof.package import parse_package
    from proof.pytest_runner import run_pytest_files

    cond = str(cond).upper()
    if cond not in ("R", "B", "C", "D", "E"):
        raise ValueError(f"PR review condition must be R|B|C|D|E, got {cond!r}")
    eff_settings = settings
    if reviewer_effort and settings is not None:
        try:
            eff_settings = dc_replace(settings, effort_reviewer=reviewer_effort)
        except Exception:
            settings.effort_reviewer = reviewer_effort  # type: ignore[attr-defined]
            eff_settings = settings
    rows: list[dict[str, Any]] = []
    for pr in prs:
        if cond == "B":
            target_list: list[tuple[str, dict[str, str]]] = [("regen", dict(pr.clean_modules))]
        else:
            target_list = load_pr_targets(pr, tasks_root, "all")
        if target_filter:
            target_list = [(t, m) for t, m in target_list if t == target_filter]
        for target_id, target_modules in target_list:
            for seed in range(seeds):
                run_id = f"bench-{cond}-{pr.id}-{target_id}-s{seed}{run_suffix}"
                started = time.monotonic()
                hidden_before = run_pytest_files(sandbox, target_modules,
                                                 {"hidden_test.py": pr.hidden_test})
                before_passed = _passed_names(hidden_before)
                common = dict(sandbox=sandbox, ledger=ledger, settings=eff_settings,
                              run_id=run_id, sandbox_label=sandbox_label,
                              target_id=target_id, reference_modules=dict(pr.clean_modules))
                if cond == "R":
                    bundle = run_proof(pr, "R", client=None,
                                       initial_modules=target_modules, **common)
                elif cond == "B":
                    bundle = run_proof(pr, "B", client=client, **common)
                else:
                    bundle = run_proof(pr, cond, client=client,
                                       initial_modules=target_modules, **common)
                final_modules = (parse_package(bundle.finalCode or "", pr.module_names)
                                 if bundle.finalCode else dict(target_modules))
                if not final_modules:
                    final_modules = dict(target_modules)
                hidden_after = run_pytest_files(sandbox, final_modules,
                                                {"hidden_test.py": pr.hidden_test})
                after_passed = _passed_names(hidden_after)
                duration = time.monotonic() - started
                usd = cost_for_run(ledger, run_id) if ledger is not None else float(bundle.cost.usd)
                reviewer_usd = (cost_for_run(ledger, run_id, roles=("reviewer", "freeform_reviewer"))
                                if ledger is not None else float(bundle.cost.reviewerUsd))
                regression_names = sorted(before_passed - after_passed)
                fixed = bool(hidden_after.all_passed)
                damaged = bool(target_id == "clean" and not fixed)
                bundle_path, bundle_sha = _write_bundle(bundle, bundles_dir, run_id)
                counts = _claim_counts(bundle)
                mutated = next((tt["mutated_module"] for tt in pr.meta.get("targets", [])
                                if tt["target_id"] == target_id), None)
                row = {
                    "task_id": pr.id, "pr_id": pr.id, "target_id": target_id,
                    "condition": cond, "seed": seed,
                    "tasks": list(pr.meta.get("tasks", [])),
                    "mutated_module": mutated,
                    "hidden_before_passed": hidden_before.passed,
                    "hidden_before_total": hidden_before.total,
                    "hidden_after_passed": hidden_after.passed,
                    "hidden_after_total": hidden_after.total,
                    "hidden_passed": hidden_after.passed, "hidden_total": hidden_after.total,
                    "all_pass": fixed, "fixed": fixed,
                    "regressions": len(regression_names),
                    "regressions_detail": regression_names,
                    "damaged": damaged,
                    **counts,
                    **_contested_breakdown(bundle),
                    "usd": round(float(usd), 6),
                    "reviewer_usd": round(float(reviewer_usd), 6),
                    "duration": round(duration, 3),
                    "status": bundle.status, "bundle": bundle_path,
                    "bundle_sha256": bundle_sha, "llm_calls": bundle.llmCalls,
                    "rounds": len(bundle.rounds), "run_id": run_id,
                }
                rows.append(row)
                if on_row is not None:
                    on_row(row)
                if float(usd) > max_usd_per_single_run:
                    raise SingleRunCostExceeded(
                        f"run {run_id} cost ${float(usd):.4f} > ${max_usd_per_single_run:.2f}; stopping")
    return rows


def write_rows(rows: list[dict[str, Any]], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out_path


def format_results_table(rows: list[dict[str, Any]]) -> str:
    lines = [f"{'task':<22} {'target':<7} {'seed':<5} {'before':<9} {'after':<9} {'fixed':<6} {'usd':<10} duration"]
    for r in rows:
        lines.append(
            f"{r['task_id']:<22} {r.get('target_id', ''):<7} {r['seed']:<5} "
            f"{r.get('hidden_before_passed', r.get('hidden_passed'))}/{r.get('hidden_before_total', r.get('hidden_total')):<7} "
            f"{r.get('hidden_after_passed', r.get('hidden_passed'))}/{r.get('hidden_after_total', r.get('hidden_total')):<7} "
            f"{str(r.get('fixed', r.get('all_pass'))):<6} ${r['usd']:<9.4f} {r['duration']:.2f}s"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run FinCode review benchmark")
    parser.add_argument("--cond", default="D", choices=["R", "B", "C", "D", "E", "A"])
    parser.add_argument("--split", default="dev", choices=["dev", "test"])
    parser.add_argument("--targets", default="all", choices=["mutants", "clean", "all", "prs"])
    parser.add_argument("--prs", default=str(REPO_ROOT / "bench" / "prs"))
    parser.add_argument("--pr-target", default=None,
                        help="PR mode only: run only this target id (e.g. buggy_a)")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--sandbox", default="local", choices=["local", "docker"])
    parser.add_argument("--task", default=None)
    parser.add_argument("--tasks", default=str(REPO_ROOT / "bench" / "tasks"))
    parser.add_argument("--out", default=None)
    parser.add_argument("--bundles-dir", default=None)
    parser.add_argument("--reviewer-effort", default=None, choices=["minimal", "low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--max-usd-per-run", type=float, default=10.0)
    parser.add_argument("--run-suffix", default="")
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
    prs = None
    if args.targets == "prs":
        from bench.prs import discover_prs
        prs = discover_prs(args.prs, split=args.split)
        if args.task:
            prs = [p for p in prs if p.id == args.task]
        if args.limit is not None and args.limit >= 0:
            prs = prs[: args.limit]
        if not prs:
            print("no PRs matched", file=sys.stderr)
            return 1
    elif not tasks:
        print("no tasks matched", file=sys.stderr)
        return 1

    from proof.config import load_settings
    from proof.ledger import Ledger
    from proof.llm import LLMClient

    settings = load_settings()
    ledger = Ledger(settings=settings)
    client = None if args.cond == "R" else LLMClient(ledger=ledger, settings=settings)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = Path(args.out) if args.out else REPO_ROOT / "results" / "runs" / f"cond{args.cond}_{args.split}_{stamp}.jsonl"
    bundles_dir = Path(args.bundles_dir) if args.bundles_dir else REPO_ROOT / "results" / "bundles"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_handle = out_path.open("a", encoding="utf-8")

    def _on_row(row: dict[str, Any]) -> None:
        out_handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        out_handle.flush()
        print(f"{row['task_id']} {row.get('target_id','')} {row['condition']} fixed={row.get('fixed')} usd=${row['usd']:.4f}", flush=True)

    try:
        if prs is not None:
            rows = run_review_bench_prs(prs, args.cond, client=client, sandbox=sandbox,
                                        seeds=args.seeds, ledger=ledger, settings=settings,
                                        bundles_dir=bundles_dir, sandbox_label=args.sandbox,
                                        tasks_root=args.tasks,
                                        reviewer_effort=args.reviewer_effort,
                                        max_usd_per_single_run=args.max_usd_per_run,
                                        on_row=_on_row, run_suffix=args.run_suffix,
                                        target_filter=args.pr_target)
        elif args.cond == "A":
            rows = run_condition(tasks, "A", client=client, sandbox=sandbox, seeds=args.seeds,
                                 ledger=ledger, settings=settings, bundles_dir=bundles_dir,
                                 sandbox_label=args.sandbox, on_row=_on_row, run_suffix=args.run_suffix)
        else:
            rows = run_review_bench(tasks, args.cond, client=client, sandbox=sandbox,
                                    seeds=args.seeds, ledger=ledger, settings=settings,
                                    bundles_dir=bundles_dir, sandbox_label=args.sandbox,
                                    targets=args.targets, reviewer_effort=args.reviewer_effort,
                                    max_usd_per_single_run=args.max_usd_per_run,
                                    on_row=_on_row, run_suffix=args.run_suffix)
    finally:
        out_handle.close()
    print(format_results_table(rows))
    print(f"wrote {len(rows)} rows to {out_path}")
    total_usd = sum(r["usd"] for r in rows)
    reviewer_usd = sum(r.get("reviewer_usd", 0.0) for r in rows)
    print(f"total cost: ${total_usd:.4f} (reviewer: ${reviewer_usd:.4f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
