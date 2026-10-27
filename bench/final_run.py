"""Final FinCode-30 run on the held-out test split (PLAN.md final-run design, 2026-10-27).

Runs the conditions in order, writes everything under results/final/, and applies the
cut rule: if condition D on PR targets costs more than CUT_USD_PER_TARGET, single-task D
is skipped (and the summary says so). Each step is skipped when its output file already
has the expected number of rows, so the script can be resumed after an interruption.

    .venv\\Scripts\\python bench\\final_run.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "final"
CUT_USD_PER_TARGET = 0.45
PR_TARGETS = 24  # 6 test PRs x (3 buggy + 1 clean)
SINGLE_TARGETS = 80  # 20 test tasks x (3 mutants + 1 clean)

STEPS = [
    # (name, condition, targets, seeds, expected rows, max usd per run)
    ("pr_R", "R", "prs", 2, PR_TARGETS * 2, 0.60),
    ("pr_C", "C", "prs", 2, PR_TARGETS * 2, 0.60),
    ("pr_E", "E", "prs", 1, PR_TARGETS, 1.00),
    ("pr_D", "D", "prs", 1, PR_TARGETS, 1.00),
    ("pr_B", "B", "prs", 1, 6, 1.00),
    ("single_R", "R", "all", 2, SINGLE_TARGETS * 2, 0.60),
    ("single_C", "C", "all", 2, SINGLE_TARGETS * 2, 0.60),
    ("single_E", "E", "all", 1, SINGLE_TARGETS, 0.60),
    ("single_D", "D", "all", 1, SINGLE_TARGETS, 0.60),
]


def rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    notes: list[str] = []
    for name, cond, targets, seeds, expected, max_usd in STEPS:
        out = OUT / f"{name}.jsonl"
        if name == "single_D":
            pr_d = rows(OUT / "pr_D.jsonl")
            per_target = sum(float(r.get("usd", 0) or 0) for r in pr_d) / max(1, len(pr_d))
            if per_target > CUT_USD_PER_TARGET:
                note = f"single_D skipped: PR D cost ${per_target:.3f}/target > ${CUT_USD_PER_TARGET}"
                print(note, flush=True)
                notes.append(note)
                continue
        if len(rows(out)) >= expected:
            print(f"{name}: already complete ({expected} rows)", flush=True)
            continue
        out.unlink(missing_ok=True)
        cmd = [
            sys.executable, str(REPO / "bench" / "run_bench.py"),
            "--cond", cond, "--split", "test", "--targets", targets, "--seeds", str(seeds),
            "--sandbox", "local", "--out", str(out), "--bundles-dir", str(OUT / f"bundles_{name}"),
            "--reviewer-effort", "medium", "--max-usd-per-run", str(max_usd), "--run-suffix", f"final-{name}",
        ]
        print(f"=== {name}: {' '.join(cmd[2:])}", flush=True)
        code = subprocess.call(cmd, cwd=REPO)
        got = rows(out)
        usd = sum(float(r.get("usd", 0) or 0) for r in got)
        print(f"=== {name}: exit {code}, {len(got)}/{expected} rows, ${usd:.4f}", flush=True)
    (OUT / "run-notes.txt").write_text("\n".join(notes) + ("\n" if notes else ""), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
