"""Cost must be attributed strictly by run_id, not by time window."""
from bench.run_bench import cost_for_run, run_review_bench
from bench.task_loader import discover_tasks
from proof.sandbox.local import LocalSandbox


class InterleavedLedger:
    """Two concurrent runs share one ledger; entries interleave."""

    def __init__(self):
        self._entries = [
            {"run_id": "run-A", "role": "reviewer", "usd": 0.30},
            {"run_id": "run-B", "role": "reviewer", "usd": 0.50},
            {"run_id": "run-A", "role": "reviser", "usd": 0.01},
            {"run_id": "run-B", "role": "builder", "usd": 0.02},
            {"run_id": "run-A", "role": "builder", "usd": 0.01},
        ]

    def entries(self):
        return list(self._entries)

    def total_usd(self):
        return sum(e["usd"] for e in self._entries)

    def run_usd(self, run_id):
        return sum(e["usd"] for e in self._entries if e["run_id"] == run_id)


def test_cost_for_run_ignores_other_concurrent_runs():
    ledger = InterleavedLedger()
    assert abs(cost_for_run(ledger, "run-A") - 0.32) < 1e-9
    assert abs(cost_for_run(ledger, "run-B") - 0.52) < 1e-9
    # reviewer-only slice also strictly by run_id
    assert abs(cost_for_run(ledger, "run-A", roles=("reviewer",)) - 0.30) < 1e-9
    assert abs(cost_for_run(ledger, "run-B", roles=("reviewer",)) - 0.50) < 1e-9
    assert cost_for_run(ledger, "run-missing") == 0.0


def test_review_bench_r_clean_and_mutant_rows_no_llm(tmp_path):
    tasks = [t for t in discover_tasks("bench/tasks", split="dev") if t.id == "split_installments"]
    rows = run_review_bench(tasks, "R", client=None, sandbox=LocalSandbox(), seeds=1,
                            ledger=InterleavedLedger(), targets="clean",
                            bundles_dir=tmp_path / "b")
    assert len(rows) == 1
    row = rows[0]
    assert row["target_id"] == "clean" and row["condition"] == "R"
    assert row["fixed"] is True and row["damaged"] is False
    assert row["hidden_before_passed"] == row["hidden_after_passed"]
    assert row["usd"] == 0.0  # ledger has no entries for this run_id
    import json
    from pathlib import Path
    bundle = json.loads(Path(row["bundle"]).read_text(encoding="utf-8")) if row["bundle"] else {}
    # bundle path may be absolute in tmp; read via bundles_dir
    files = list((tmp_path / "b").glob("*.json"))
    data = json.loads(files[0].read_text(encoding="utf-8"))
    assert data["target"] == "clean"
    assert isinstance(data["cost"]["usd"], str)
