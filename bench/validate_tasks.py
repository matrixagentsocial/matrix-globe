"""Validate FinCode tasks (PLAN.md sections 4, 5.6).

For every task under ``bench/tasks/``:

- the reference solution passes all public + hidden tests,
- a naive stub/plausible-but-wrong solution fails at least one
  hidden test,
- the hidden test function names are not a subset of the public ones,
- every hidden test function name is unique,
- no task file imports a non-stdlib module (test files may also import
  ``solution`` and ``pytest``).

Prints a table and exits non-zero on any failure. Run from the repo
root: ``.venv\\Scripts\\python bench\\validate_tasks.py``
"""
from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bench.task_loader import Task, discover_tasks, load_task
from proof.pytest_runner import run_pytest
from proof.sandbox.local import LocalSandbox

# Plausible-but-wrong implementations: each ignores at least one trap
# in its spec, so a good hidden suite must catch it. Tasks without an
# entry get an empty stub, which fails at import/collection.
NAIVE_SOLUTIONS: dict[str, str] = {
    "split_installments": '''
from decimal import Decimal, ROUND_HALF_UP

def split_installments(total, n):
    if n < 1:
        raise ValueError("n")
    each = (Decimal(total) / n).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return [each] * n
''',
    "currency_rounding": '''
from decimal import Decimal, ROUND_HALF_UP

def round_money(amount, currency, mode="HALF_UP"):
    return Decimal(amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
''',
    "business_days": '''
from datetime import timedelta

def is_business_day(d, holidays=()):
    return d.weekday() < 5

def adjust_business_day(d, holidays=(), convention="modified_following"):
    cur = d
    while not is_business_day(cur, holidays):
        cur += timedelta(days=1)
    return cur

def add_business_days(start, n, holidays=()):
    cur = start
    remaining = abs(n)
    step = timedelta(days=1) if n >= 0 else timedelta(days=-1)
    while remaining:
        cur += step
        if is_business_day(cur, holidays):
            remaining -= 1
    return cur
''',
    "iban_validation": '''
def normalize_iban(iban):
    if not isinstance(iban, str):
        raise ValueError("str")
    return iban.replace(" ", "").upper()

def validate_iban(iban):
    if not isinstance(iban, str):
        return False
    return len(normalize_iban(iban)) >= 15
''',
    "number_parsing": '''
from decimal import Decimal

def parse_number(text):
    s = text.strip().replace(" ", "").replace(".", "").replace(",", ".")
    return Decimal(s)
''',
    "receivables_aging": '''
from datetime import date
from decimal import Decimal

def aging_buckets(invoices, as_of):
    if isinstance(as_of, str):
        as_of = date.fromisoformat(as_of)
    out = {"current": Decimal("0.00"), "1-30": Decimal("0.00"),
           "31-60": Decimal("0.00"), "61-90": Decimal("0.00"), "90+": Decimal("0.00")}
    for inv in invoices:
        due = inv["due_date"]
        if isinstance(due, str):
            due = date.fromisoformat(due)
        days = (as_of - due).days
        if days < 0:
            key = "current"
        elif days < 30:
            key = "1-30"
        elif days < 60:
            key = "31-60"
        elif days < 90:
            key = "61-90"
        else:
            key = "90+"
        out[key] += Decimal(inv["amount"])
    return {k: v.quantize(Decimal("0.01")) for k, v in out.items()}
''',
}

EMPTY_STUB = "# naive stub: no implementation\n"


def naive_solution_for(task_id: str) -> str:
    return NAIVE_SOLUTIONS.get(task_id, EMPTY_STUB)


def test_function_names(source: str) -> set[str]:
    return set(test_function_name_list(source))


def test_function_name_list(source: str) -> list[str]:
    tree = ast.parse(source)
    return [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test")
    ]


def imported_top_level_modules(source: str) -> set[str]:
    tree = ast.parse(source)
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            if node.module:
                modules.add(node.module.split(".")[0])
    return modules


# Test files may import the solution under test and pytest; everything
# else (and everything in reference.py) must be stdlib.
_TEST_ONLY_MODULES = {"pytest", "solution"}


def non_stdlib_imports(task: Task) -> list[str]:
    bad: list[str] = []
    sources = {
        "reference.py": (task.reference, set()),
        "public_test.py": (task.public_test, _TEST_ONLY_MODULES),
        "hidden_test.py": (task.hidden_test, _TEST_ONLY_MODULES),
    }
    for filename, (source, extra_allowed) in sources.items():
        allowed = set(sys.stdlib_module_names) | extra_allowed
        for module in sorted(imported_top_level_modules(source) - allowed):
            bad.append(f"{filename}: {module}")
    return bad


ALLOWED_MUTANT_KINDS = {
    "rounding_mode", "rounding_step", "boundary", "tie_break",
    "missing_validation", "convention", "float_money", "timezone", "other",
}


def validate_mutants(task: Task, sandbox) -> tuple[bool, str]:
    """Each mutant: differs from reference, passes public, fails >=1 hidden."""
    import json as _json

    mutants_dir = task.dir / "mutants"
    meta_path = mutants_dir / "mutants.json"
    if not meta_path.exists():
        return False, "mutants/mutants.json missing"
    try:
        entries = _json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"mutants.json unreadable: {exc}"
    if not isinstance(entries, list) or len(entries) != 3:
        return False, f"mutants.json must list exactly 3 mutants, got {entries!r}"
    problems: list[str] = []
    seen_ids: set[str] = set()
    sources: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            problems.append(f"mutant entry not an object: {entry!r}")
            continue
        mid = str(entry.get("id", ""))
        if mid in seen_ids or mid not in ("m1", "m2", "m3"):
            problems.append(f"bad or duplicate mutant id {mid!r}")
        seen_ids.add(mid)
        if str(entry.get("kind", "")) not in ALLOWED_MUTANT_KINDS:
            problems.append(f"{mid}: kind {entry.get('kind')!r} not allowed")
        if not str(entry.get("rule", "")).strip():
            problems.append(f"{mid}: rule empty")
        if not str(entry.get("description", "")).strip():
            problems.append(f"{mid}: description empty")
        mpath = mutants_dir / f"{mid}.py"
        if not mpath.exists():
            problems.append(f"{mid}: file missing")
            continue
        source = mpath.read_text(encoding="utf-8")
        sources.append(source)
        if source == task.reference:
            problems.append(f"{mid}: identical to reference")
            continue
        pub = run_pytest(sandbox, source, {"public_test.py": task.public_test})
        if not pub.all_passed:
            problems.append(f"{mid}: fails public tests ({pub.passed}/{pub.total})")
        hid = run_pytest(sandbox, source, {"hidden_test.py": task.hidden_test})
        failed = sum(1 for t in hid.tests if t.outcome in ("failed", "error"))
        if failed < 1 and not hid.collection_errors:
            problems.append(f"{mid}: passes all hidden tests")
        if hid.collection_errors:
            problems.append(f"{mid}: hidden run has collection errors")
    if len(set(sources)) != len(sources):
        problems.append("mutants are not pairwise distinct")
    return (not problems), "; ".join(problems)


@dataclass
class TaskValidation:
    task_id: str
    reference_ok: bool
    naive_fails_hidden: bool
    hidden_not_subset: bool
    hidden_names_unique: bool = True
    stdlib_only: bool = True
    mutants_ok: bool = True
    detail: str = ""

    @property
    def ok(self) -> bool:
        return (
            self.reference_ok
            and self.naive_fails_hidden
            and self.hidden_not_subset
            and self.hidden_names_unique
            and self.stdlib_only
            and self.mutants_ok
        )


def validate_task(task: Task, sandbox: LocalSandbox | None = None,
                  require_mutants: bool = False) -> TaskValidation:
    sandbox = sandbox or LocalSandbox()
    detail_parts: list[str] = []

    ref_run = run_pytest(
        sandbox,
        task.reference,
        {"public_test.py": task.public_test, "hidden_test.py": task.hidden_test},
    )
    reference_ok = ref_run.all_passed
    if not reference_ok:
        detail_parts.append(
            f"reference {ref_run.passed}/{ref_run.total} passed"
            + (f", collection={ref_run.collection_errors}" if ref_run.collection_errors else "")
            + (", timed_out" if ref_run.timed_out else "")
        )

    naive_run = run_pytest(
        sandbox,
        naive_solution_for(task.id),
        {"hidden_test.py": task.hidden_test},
    )
    naive_failed = sum(1 for t in naive_run.tests if t.outcome in ("failed", "error"))
    naive_fails = naive_failed >= 1 or bool(naive_run.collection_errors)
    if not naive_fails:
        detail_parts.append("naive stub passed all hidden tests")

    public_names = test_function_names(task.public_test)
    hidden_name_list = test_function_name_list(task.hidden_test)
    hidden_names = set(hidden_name_list)
    hidden_not_subset = not hidden_names.issubset(public_names)
    if not hidden_not_subset:
        detail_parts.append("hidden test names are a subset of public ones")
    if not hidden_names:
        detail_parts.append("no hidden tests found")
    hidden_names_unique = len(hidden_name_list) == len(hidden_names)
    if not hidden_names_unique:
        dupes = sorted({n for n in hidden_name_list if hidden_name_list.count(n) > 1})
        detail_parts.append(f"duplicate hidden test names: {', '.join(dupes)}")
    bad_imports = non_stdlib_imports(task)
    stdlib_only = not bad_imports
    if not stdlib_only:
        detail_parts.append(f"non-stdlib imports: {', '.join(bad_imports)}")

    mutants_ok = True
    if require_mutants or (task.dir / "mutants").exists():
        mutants_ok, mutant_detail = validate_mutants(task, sandbox)
        if not mutants_ok:
            detail_parts.append(f"mutants: {mutant_detail}")

    return TaskValidation(
        task_id=task.id,
        reference_ok=reference_ok,
        naive_fails_hidden=naive_fails,
        hidden_not_subset=hidden_not_subset,
        hidden_names_unique=hidden_names_unique,
        stdlib_only=stdlib_only,
        mutants_ok=mutants_ok,
        detail="; ".join(detail_parts),
    )


def validate_all(tasks_root: str | Path, require_mutants: bool = True) -> list[TaskValidation]:
    sandbox = LocalSandbox()
    return [validate_task(task, sandbox, require_mutants=require_mutants)
            for task in discover_tasks(tasks_root)]


def format_table(results: list[TaskValidation]) -> str:
    def mark(ok: bool) -> str:
        return "ok" if ok else "FAIL"

    lines = [
        f"{'task':<26} {'reference':<10} {'naive fails':<12} {'hidden not subset':<18} "
        f"{'unique names':<13} {'stdlib only':<12} {'mutants':<9} result",
    ]
    for r in results:
        lines.append(
            f"{r.task_id:<26} {mark(r.reference_ok):<10} "
            f"{mark(r.naive_fails_hidden):<12} {mark(r.hidden_not_subset):<18} "
            f"{mark(r.hidden_names_unique):<13} {mark(r.stdlib_only):<12} "
            f"{mark(r.mutants_ok):<9} "
            f"{'ok' if r.ok else 'FAIL'}"
            + (f"  ({r.detail})" if r.detail else "")
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate FinCode tasks")
    parser.add_argument(
        "--tasks",
        default=str(Path(__file__).resolve().parent / "tasks"),
        help="tasks root directory",
    )
    args = parser.parse_args(argv)
    results = validate_all(args.tasks)
    print(format_table(results))
    if not results:
        print("no tasks found", file=sys.stderr)
        return 1
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
