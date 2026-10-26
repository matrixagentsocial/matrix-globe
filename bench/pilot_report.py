"""Pilot report (M3 part 2): summarise pilot run JSONL files.

Usage: .venv\\Scripts\\python bench/pilot_report.py results/pilot/condA*.jsonl ...
Prints per variant: hidden all-pass rate, mean hidden-test pass rate,
USD per run, USD per fully solved task, reviewer claims
proposed/PROVEN/UNPROVEN/INVALID/VALID/UNCONFIRMED, reviewer precision
(VALID/PROVEN), regressions.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def load_rows(paths: list[str]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for p in paths:
        label = Path(p).stem
        rows = [json.loads(line) for line in Path(p).read_text(encoding="utf-8").splitlines() if line.strip()]
        groups[label] = rows
    return groups


def summarise(label: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    solved = sum(1 for r in rows if r.get("all_pass"))
    total_usd = sum(float(r.get("usd", 0.0)) for r in rows)
    mean_hidden = (sum(r["hidden_passed"] / r["hidden_total"] for r in rows if r.get("hidden_total")) / n) if n else 0.0
    return {
        "variant": label, "n": n, "solved": solved,
        "all_pass_rate": solved / n if n else 0.0,
        "mean_hidden_rate": mean_hidden,
        "total_usd": total_usd,
        "usd_per_run": total_usd / n if n else 0.0,
        "usd_per_solved": total_usd / solved if solved else None,
        "claims_proposed": sum(int(r.get("claims_proposed", 0)) for r in rows),
        "claims_proven": sum(int(r.get("claims_proven", 0)) for r in rows),
        "claims_unproven": sum(int(r.get("claims_unproven", 0)) for r in rows),
        "claims_invalid": sum(int(r.get("claims_invalid", 0)) for r in rows),
        "claims_valid": sum(int(r.get("claims_valid", 0)) for r in rows),
        "claims_unconfirmed": sum(int(r.get("claims_unconfirmed", 0)) for r in rows),
        "regressions": sum(int(r.get("regressions", 0)) for r in rows),
    }


def format_markdown(groups: dict[str, list[dict[str, Any]]]) -> str:
    lines = ["# Pilot summary (dev split, 1 seed)", "",
             "| variant | n | all-pass | mean hidden | USD/run | USD/solved | prop/PROV/UNPR/INV/VALID/UNCONF | precision | regressions |",
             "|---|---|---|---|---|---|---|---|---|"]
    for label, rows in groups.items():
        s = summarise(label, rows)
        solved = f"${s['usd_per_solved']:.4f}" if s["usd_per_solved"] is not None else "n/a"
        precision = f"{s['claims_valid'] / s['claims_proven']:.2f}" if s["claims_proven"] else "n/a"
        lines.append(
            f"| {label} | {s['n']} | {s['solved']}/{s['n']} ({s['all_pass_rate']:.0%}) | "
            f"{s['mean_hidden_rate']:.1%} | ${s['usd_per_run']:.4f} | {solved} | "
            f"{s['claims_proposed']}/{s['claims_proven']}/{s['claims_unproven']}/{s['claims_invalid']}/"
            f"{s['claims_valid']}/{s['claims_unconfirmed']} | {precision} | {s['regressions']} |")
    lines.append("")
    for label, rows in groups.items():
        lines.append(f"## {label}")
        lines.append("")
        lines.append("| task | public | hidden | all_pass | usd | reviewer usd | status |")
        lines.append("|---|---|---|---|---|---|---|")
        for r in rows:
            lines.append(f"| {r['task_id']} | {r['public_passed']}/{r['public_total']} | "
                         f"{r['hidden_passed']}/{r['hidden_total']} | {r['all_pass']} | "
                         f"${float(r.get('usd', 0)):.4f} | ${float(r.get('reviewer_usd', 0)):.4f} | {r.get('status', '')} |")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("usage: pilot_report.py <run.jsonl> [...]", file=sys.stderr)
        return 2
    text = format_markdown(load_rows(args))
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
