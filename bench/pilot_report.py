"""Pilot v2 report: summarise review-benchmark JSONL rows.

Usage: .venv\\Scripts\\python bench/pilot_report.py results/pilot/v2/condD.jsonl [...]
Writes markdown to stdout (redirect to summary.md). Per condition:
fixed rate on mutants, damage rate on clean, regressions, claim
precision (VALID/PROVEN), $/target.
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
    mutants = [r for r in rows if r.get("target_id") in ("m1", "m2", "m3")
               or str(r.get("target_id", "")).startswith("buggy_")]
    clean = [r for r in rows if r.get("target_id") == "clean"]
    regen = [r for r in rows if r.get("target_id") == "regen"]
    total_usd = sum(float(r.get("usd", 0.0)) for r in rows)

    def _fixed(r: dict[str, Any]) -> bool:
        if "fixed" in r:
            return bool(r["fixed"])
        return bool(r.get("all_pass"))

    n_mut = len(mutants)
    fixed_mut = sum(1 for r in mutants if _fixed(r))
    damaged_clean = sum(1 for r in clean if r.get("damaged", (not _fixed(r))))
    proven = sum(int(r.get("claims_proven", 0)) for r in rows)
    valid = sum(int(r.get("claims_valid", 0)) for r in rows)
    return {
        "variant": label, "n": len(rows),
        "n_mutants": n_mut, "fixed_mutants": fixed_mut,
        "fixed_rate": (fixed_mut / n_mut) if n_mut else None,
        "n_clean": len(clean), "damaged_clean": damaged_clean,
        "damage_rate": (damaged_clean / len(clean)) if clean else None,
        "n_regen": len(regen), "regen_fixed": sum(1 for r in regen if _fixed(r)),
        "regressions": sum(int(r.get("regressions", 0)) for r in rows),
        "claims_proposed": sum(int(r.get("claims_proposed", 0)) for r in rows),
        "claims_proven": proven,
        "claims_unproven": sum(int(r.get("claims_unproven", 0)) for r in rows),
        "claims_invalid": sum(int(r.get("claims_invalid", 0)) for r in rows),
        "claims_valid": valid,
        "claims_unconfirmed": sum(int(r.get("claims_unconfirmed", 0)) for r in rows),
        "claims_unconfirmed_contested": sum(int(r.get("claims_unconfirmed_contested", 0)) for r in rows),
        "claims_unconfirmed_accepted": sum(int(r.get("claims_unconfirmed_accepted", 0)) for r in rows),
        "precision": (valid / proven) if proven else None,
        "total_usd": total_usd,
        "usd_per_target": (total_usd / len(rows)) if rows else 0.0,
    }


def _pct(v: float | None) -> str:
    return "n/a" if v is None else f"{v:.0%}"


def format_markdown(groups: dict[str, list[dict[str, Any]]],
                    title: str = "Pilot v2 summary (dev split, 1 seed)") -> str:
    lines = [f"# {title}", "",
             "| condition | targets | fixed on mutants | damage on clean | regressions | claims prop/prov/valid/unconf | precision | $/target | total $ |",
             "|---|---|---|---|---|---|---|---|---|"]
    for label, rows in groups.items():
        s = summarise(label, rows)
        fixed_s = f"{s['fixed_mutants']}/{s['n_mutants']} ({_pct(s['fixed_rate'])})" if s["n_mutants"] else (
            f"regen {s['regen_fixed']}/{s['n_regen']}" if s["n_regen"] else "n/a")
        damage_s = f"{s['damaged_clean']}/{s['n_clean']} ({_pct(s['damage_rate'])})" if s["n_clean"] else "n/a"
        precision = f"{s['precision']:.2f}" if s["precision"] is not None else "n/a"
        lines.append(
            f"| {label} | {s['n']} | {fixed_s} | {damage_s} | {s['regressions']} | "
            f"{s['claims_proposed']}/{s['claims_proven']}/{s['claims_valid']}/{s['claims_unconfirmed']} | "
            f"{precision} | ${s['usd_per_target']:.4f} | ${s['total_usd']:.4f} |")
    lines.append("")
    for label, rows in groups.items():
        lines.append(f"## {label}")
        lines.append("")
        lines.append("| task | target | before | after | fixed | regressions | damaged | usd | reviewer usd | status |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            lines.append(
                f"| {r['task_id']} | {r.get('target_id', '')} | "
                f"{r.get('hidden_before_passed', '?')}/{r.get('hidden_before_total', '?')} | "
                f"{r.get('hidden_after_passed', r.get('hidden_passed', '?'))}/{r.get('hidden_after_total', r.get('hidden_total', '?'))} | "
                f"{r.get('fixed', r.get('all_pass'))} | {r.get('regressions', 0)} | {r.get('damaged', '')} | "
                f"${float(r.get('usd', 0)):.4f} | ${float(r.get('reviewer_usd', 0)):.4f} | {display_status(r)} |")
        lines.append("")
    return "\n".join(lines)


def write_report(paths: list[str], out_path: str | Path,
                 title: str = "Pilot v2 summary (dev split, 1 seed)") -> Path:
    """Write the markdown report as UTF-8 (never rely on shell redirection)."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(format_markdown(load_rows(paths), title=title), encoding="utf-8")
    return out


def display_status(row: dict[str, Any]) -> str:
    """Unreviewed code (condition R) is UNREVIEWED, never VERIFIED."""
    if str(row.get("condition", "")).upper() == "R":
        return "UNREVIEWED"
    return str(row.get("status", ""))


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    title = "Pilot v2 summary (dev split, 1 seed)"
    if "--title" in args:
        i = args.index("--title")
        title = args[i + 1]
        args = args[:i] + args[i + 2:]
    out_path: str | None = None
    if "--out" in args:
        i = args.index("--out")
        out_path = args[i + 1]
        args = args[:i] + args[i + 2:]
    if not args:
        print("usage: pilot_report.py [--out summary.md] <run.jsonl> [...]", file=sys.stderr)
        return 2
    if out_path:
        write_report(args, out_path, title=title)
        print(f"wrote {out_path} (UTF-8)")
    else:
        sys.stdout.write(format_markdown(load_rows(args)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
