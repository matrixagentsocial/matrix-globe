"""run_bench condition A with a mocked LLM (M1, no API calls)."""
import json

from bench.run_bench import run_condition_a, write_rows
from bench.task_loader import discover_tasks
from proof.sandbox.local import LocalSandbox

TASKS_ROOT = "bench/tasks"


class FakeLedger:
    def __init__(self):
        self._total = 0.0

    def total_usd(self):
        return self._total


class FakeClient:
    """Returns the reference solution is not known here; return a stub
    that the fake ledger pretends cost a fraction of a cent. Each call
    serves the code queued for it."""

    def __init__(self, codes, ledger):
        self._codes = list(codes)
        self._ledger = ledger
        self.calls = []

    def complete(self, role, messages, **kwargs):
        self.calls.append((role, kwargs))
        self._ledger._total += 0.001
        return {"code": self._codes.pop(0)}


def test_run_bench_condition_a_mocked(tmp_path):
    tasks = discover_tasks(TASKS_ROOT, split="dev")[:2]
    assert len(tasks) == 2
    codes = [t.reference for t in tasks]
    ledger = FakeLedger()
    client = FakeClient(codes, ledger)
    rows = run_condition_a(
        tasks,
        client=client,
        sandbox=LocalSandbox(),
        seeds=1,
        ledger=ledger,
        model="fake-model",
        effort="medium",
    )
    assert len(rows) == 2
    for row, task in zip(rows, tasks):
        assert row["task_id"] == task.id
        assert row["condition"] == "A"
        assert row["seed"] == 0
        assert row["model"] == "fake-model"
        assert row["effort"] == "medium"
        assert row["public_total"] > 0
        assert row["hidden_total"] > 0
        assert row["public_passed"] == row["public_total"]
        assert row["hidden_passed"] == row["hidden_total"]
        assert row["all_pass"] is True
        assert row["usd"] == 0.001
        assert row["duration"] >= 0
    # JSONL round trip.
    out = write_rows(rows, tmp_path / "runs.jsonl")
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["task_id"] == tasks[0].id
    assert all(c[1].get("metadata") == {"origin": "bench"} for c in client.calls)
