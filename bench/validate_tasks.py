"""Validate FinCode tasks (PLAN.md sections 4, 5.6).

For every task under ``bench/tasks/``:

- the reference solution passes all public + hidden tests,
- a naive stub/plausible-but-wrong solution fails at least one
  hidden test,
- the hidden test function names are not a subset of the public ones.

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
    tree = ast.parse(source)
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test")
    }


@dataclass
class TaskValidation:
    task_id: str
    reference_ok: bool
    naive_fails_hidden: bool
    hidden_not_subset: bool
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.reference_ok and self.naive_fails_hidden and self.hidden_not_subset


def validate_task(task: Task, sandbox: LocalSandbox | None = None) -> TaskValidation:
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
    hidden_names = test_function_names(task.hidden_test)
    hidden_not_subset = not hidden_names.issubset(public_names)
    if not hidden_not_subset:
        detail_parts.append("hidden test names are a subset of public ones")
    if not hidden_names:
        detail_parts.append("no hidden tests found")

    return TaskValidation(
        task_id=task.id,
        reference_ok=reference_ok,
        naive_fails_hidden=naive_fails,
        hidden_not_subset=hidden_not_subset,
        detail="; ".join(detail_parts),
    )


def validate_all(tasks_root: str | Path) -> list[TaskValidation]:
    sandbox = LocalSandbox()
    return [validate_task(task, sandbox) for task in discover_tasks(tasks_root)]


def format_table(results: list[TaskValidation]) -> str:
    def mark(ok: bool) -> str:
        return "ok" if ok else "FAIL"

    lines = [
        f"{'task':<22} {'reference':<10} {'naive fails':<12} {'hidden not subset':<18} result",
    ]
    for r in results:
        lines.append(
            f"{r.task_id:<22} {mark(r.reference_ok):<10} "
            f"{mark(r.naive_fails_hidden):<12} {mark(r.hidden_not_subset):<18} "
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
