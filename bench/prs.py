"""PR targets: pull-request-sized packages of three FinCode tasks.

A PR groups 3 tasks of the same split into one package: a directory
``bench/prs/<pr_id>/`` with one module per task (``task_a.py``,
``task_b.py``, ``task_c.py``, each the task's ``reference.py``), a
``spec.md`` (the three specs concatenated under headings, with a header
explaining that each section's ``solution.py`` is its module), a
``pr.json`` describing the grouping and targets, and the union of the
three tasks' public/hidden tests rewritten to import from their module
instead of ``solution`` (duplicate test names get a task suffix so the
union keeps every test).

Per PR the targets are 3 buggy variants (each replacing a different
module with that task's first validated mutant) plus 1 clean variant.
Validation mirrors the mutants: a buggy PR passes every public test and
fails at least one hidden test; the clean PR passes everything.

Build/validate (no LLM calls):
``.venv\\Scripts\\python bench\\prs.py --build --validate``
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bench.task_loader import Task, discover_tasks, load_mutants

MODULE_SLOTS = ["task_a.py", "task_b.py", "task_c.py"]

# Deterministic alphabetical groups of three. Dev: 9 of 10 tasks
# (vat_invoice left out). Test: 18 of 20 (weighted_average_cost, xirr left out).
PR_GROUPS: dict[str, list[tuple[str, list[str]]]] = {
    "dev": [
        ("pr_dev_1", ["amortization_schedule", "business_days", "currency_rounding"]),
        ("pr_dev_2", ["day_count", "fifo_cost", "iban_validation"]),
        ("pr_dev_3", ["number_parsing", "receivables_aging", "split_installments"]),
    ],
    "test": [
        ("pr_test_1", ["allocate_ratios", "apr_apy", "bank_reconciliation"]),
        ("pr_test_2", ["budget_variance", "depreciation_declining", "depreciation_straight_line"]),
        ("pr_test_3", ["duplicate_payments", "eom_roll", "fx_triangulation"]),
        ("pr_test_4", ["idempotent_ledger", "madrid_cutoff", "percent_change"]),
        ("pr_test_5", ["progressive_tax", "prorata_billing", "rf_reference"]),
        ("pr_test_6", ["running_balance", "spanish_bank_csv", "spanish_tax_id"]),
    ],
}


@dataclass
class PR:
    id: str
    dir: Path
    spec: str
    public_test: str
    hidden_test: str
    meta: dict
    clean_modules: dict[str, str] = field(default_factory=dict)

    @property
    def split(self) -> str:
        return str(self.meta.get("split", ""))

    @property
    def module_names(self) -> list[str]:
        return [slot for slot in MODULE_SLOTS if slot in self.clean_modules]


def rewrite_imports(source: str, module_file: str) -> str:
    """Rewrite ``from solution import ...`` to the task's module."""
    module = module_file[:-3] if module_file.endswith(".py") else module_file
    out = re.sub(r"^from solution import", f"from {module} import", source, flags=re.M)
    out = re.sub(r"^import solution\b", f"import {module}", out, flags=re.M)
    return out


def _rename_duplicates(source: str, seen: set[str], task_id: str) -> str:
    """Rename top-level test defs already seen in the union."""
    def repl(m: re.Match) -> str:
        name = m.group(1)
        if name in seen:
            new = f"{name}__{task_id}"
            seen.add(new)
            return f"def {new}("
        seen.add(name)
        return m.group(0)
    return re.sub(r"^def (test\w*)\(", repl, source, flags=re.M)


def union_tests(tasks: list[Task], kind: str) -> str:
    """Union of the tasks' ``kind`` tests, imports rewritten per module."""
    seen: set[str] = set()
    parts: list[str] = []
    for slot, task in zip(MODULE_SLOTS, tasks):
        source = task.public_test if kind == "public" else task.hidden_test
        source = rewrite_imports(source, slot)
        source = _rename_duplicates(source, seen, task.id)
        parts.append(f"# --- {kind} tests for {task.id} (module {slot}) ---\n{source.rstrip()}\n")
    return "\n".join(parts)


def build_spec(pr_id: str, tasks: list[Task]) -> str:
    header = (
        f"# Pull request {pr_id}\n\n"
        "This package contains three modules: "
        + ", ".join(f"`{slot}`" for slot in MODULE_SLOTS)
        + ". Each section below is the spec for one module. Where a section "
          "says `solution.py`, it means that section's module file. Implement "
          "and review the package as a whole; a defect may be in any module.\n"
    )
    sections = [header]
    for slot, task in zip(MODULE_SLOTS, tasks):
        sections.append(f"\n## Module `{slot}` — task `{task.id}`\n\n{task.spec.rstrip()}\n")
    return "\n".join(sections)


def build_pr(pr_id: str, tasks: list[Task], prs_root: Path) -> Path:
    pr_dir = prs_root / pr_id
    pr_dir.mkdir(parents=True, exist_ok=True)
    split = tasks[0].split
    assert all(t.split == split for t in tasks), "PR tasks must share a split"
    modules_map: dict[str, str] = {}
    targets: list[dict] = [{"target_id": "clean", "mutated_module": None, "mutant": None, "task_id": None}]
    for slot, task in zip(MODULE_SLOTS, tasks):
        modules_map[slot] = task.id
        (pr_dir / slot).write_text(task.reference, encoding="utf-8")
        mutants = load_mutants(task)
        mutant_id = str(mutants[0]["id"]) if mutants else "m1"
        suffix = slot.replace("task_", "").replace(".py", "")
        targets.append({
            "target_id": f"buggy_{suffix}",
            "mutated_module": slot,
            "mutant": mutant_id,
            "task_id": task.id,
        })
    meta = {
        "id": pr_id,
        "split": split,
        "tasks": [t.id for t in tasks],
        "modules": modules_map,
        "targets": targets,
    }
    (pr_dir / "pr.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    (pr_dir / "spec.md").write_text(build_spec(pr_id, tasks), encoding="utf-8")
    (pr_dir / "public_test.py").write_text(union_tests(tasks, "public"), encoding="utf-8")
    (pr_dir / "hidden_test.py").write_text(union_tests(tasks, "hidden"), encoding="utf-8")
    return pr_dir


def build_all_prs(tasks_root: str | Path, prs_root: str | Path) -> list[Path]:
    tasks_root, prs_root = Path(tasks_root), Path(prs_root)
    by_split: dict[str, dict[str, Task]] = {}
    for split in PR_GROUPS:
        by_split[split] = {t.id: t for t in discover_tasks(tasks_root, split=split)}
    built: list[Path] = []
    for split, groups in PR_GROUPS.items():
        for pr_id, task_ids in groups:
            tasks = [by_split[split][tid] for tid in task_ids]
            built.append(build_pr(pr_id, tasks, prs_root))
    return built


def load_pr(pr_dir: str | Path) -> PR:
    pr_dir = Path(pr_dir)
    meta = json.loads((pr_dir / "pr.json").read_text(encoding="utf-8"))
    clean = {slot: (pr_dir / slot).read_text(encoding="utf-8") for slot in MODULE_SLOTS}
    return PR(
        id=str(meta.get("id") or pr_dir.name),
        dir=pr_dir,
        spec=(pr_dir / "spec.md").read_text(encoding="utf-8"),
        public_test=(pr_dir / "public_test.py").read_text(encoding="utf-8"),
        hidden_test=(pr_dir / "hidden_test.py").read_text(encoding="utf-8"),
        meta=meta,
        clean_modules=clean,
    )


def discover_prs(prs_root: str | Path, split: str | None = None) -> list[PR]:
    root = Path(prs_root)
    prs: list[PR] = []
    if not root.exists():
        return prs
    for child in sorted(root.iterdir()):
        if not child.is_dir() or not (child / "pr.json").exists():
            continue
        pr = load_pr(child)
        if split is not None and pr.split != split:
            continue
        prs.append(pr)
    return prs


def load_pr_targets(pr: PR, tasks_root: str | Path, targets: str = "all") -> list[tuple[str, dict[str, str]]]:
    """Return [(target_id, modules)] for buggy/clean/all selection."""
    out: list[tuple[str, dict[str, str]]] = []
    for entry in pr.meta.get("targets", []):
        target_id = str(entry["target_id"])
        is_clean = target_id == "clean"
        if targets == "clean" and not is_clean:
            continue
        if targets in ("mutants", "buggy") and is_clean:
            continue
        modules = dict(pr.clean_modules)
        if not is_clean:
            task_id = str(entry["task_id"])
            mutant_id = str(entry["mutant"])
            mutant_src = (Path(tasks_root) / task_id / "mutants" / f"{mutant_id}.py").read_text(encoding="utf-8")
            modules[str(entry["mutated_module"])] = mutant_src
        out.append((target_id, modules))
    return out


def validate_pr(pr: PR, tasks_root: str | Path, sandbox) -> tuple[bool, str]:
    """Buggy PRs pass all public and fail >=1 hidden; clean passes all."""
    from proof.pytest_runner import run_pytest_files
    problems: list[str] = []
    for target_id, modules in load_pr_targets(pr, tasks_root, "all"):
        pub = run_pytest_files(sandbox, modules, {"public_test.py": pr.public_test})
        hid = run_pytest_files(sandbox, modules, {"hidden_test.py": pr.hidden_test})
        if target_id == "clean":
            if not pub.all_passed:
                problems.append(f"clean fails public ({pub.passed}/{pub.total})")
            if not hid.all_passed:
                problems.append(f"clean fails hidden ({hid.passed}/{hid.total})")
        else:
            if not pub.all_passed:
                problems.append(f"{target_id} fails public ({pub.passed}/{pub.total})")
            failed = sum(1 for t in hid.tests if t.outcome in ("failed", "error"))
            if failed < 1 and not hid.collection_errors:
                problems.append(f"{target_id} passes all hidden tests")
            if hid.collection_errors:
                problems.append(f"{target_id} hidden run has collection errors")
    return (not problems), "; ".join(problems)


def validate_all_prs(prs_root: str | Path, tasks_root: str | Path, split: str | None = None) -> list[tuple[str, bool, str]]:
    from proof.sandbox.local import LocalSandbox
    sandbox = LocalSandbox()
    return [(pr.id, *validate_pr(pr, tasks_root, sandbox)) for pr in discover_prs(prs_root, split=split)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build / validate PR targets")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--split", default=None, choices=["dev", "test"])
    parser.add_argument("--tasks", default=str(Path(__file__).parent / "tasks"))
    parser.add_argument("--prs", default=str(Path(__file__).parent / "prs"))
    args = parser.parse_args(argv)
    if args.build:
        built = build_all_prs(args.tasks, args.prs)
        print(f"built {len(built)} PRs")
    if args.validate:
        results = validate_all_prs(args.prs, args.tasks, split=args.split)
        for pr_id, ok, detail in results:
            print(f"{pr_id:<12} {'ok' if ok else 'FAIL'}  {detail}")
        if not results or not all(ok for _, ok, _ in results):
            return 1
    if not args.build and not args.validate:
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
