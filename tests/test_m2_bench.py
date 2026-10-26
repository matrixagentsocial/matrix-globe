"""bench/run_bench conditions B-E wiring with a mocked LLM (M2)."""
import json

from bench.run_bench import run_condition
from bench.task_loader import discover_tasks
from proof.sandbox.local import LocalSandbox


class FakeLedger:
    def __init__(self):
        self._entries = []

    def total_usd(self):
        return sum(e["usd"] for e in self._entries)

    def run_usd(self, run_id):
        return sum(e["usd"] for e in self._entries if e["run_id"] == run_id)

    def entries(self):
        return list(self._entries)


class FakeClient:
    def __init__(self, code, ledger):
        self.code = code
        self.ledger = ledger
        self.settings = None

    def complete(self, role, messages, **kwargs):
        self.ledger._entries.append({"run_id": kwargs.get("run_id"), "role": role,
                                     "usd": 0.001, "input_tokens": 10, "output_tokens": 5})
        if role == "builder":
            return {"code": self.code}
        if role == "reviewer" and kwargs.get("schema") is not None:
            return {"verdict": "no_proven_defects", "claims": [], "untested_concerns": []}
        raise AssertionError(role)


def test_run_condition_d_mocked_writes_bundle(tmp_path):
    tasks = [t for t in discover_tasks("bench/tasks", split="dev") if t.id == "split_installments"]
    ledger = FakeLedger()
    client = FakeClient(tasks[0].reference, ledger)
    rows = run_condition(tasks, "D", client=client, sandbox=LocalSandbox(), seeds=1,
                         ledger=ledger, bundles_dir=tmp_path / "bundles")
    assert len(rows) == 1
    row = rows[0]
    assert row["condition"] == "D"
    assert row["claims_proposed"] == 0 and row["claims_proven"] == 0
    assert row["claims_unproven"] == 0 and row["claims_invalid"] == 0
    assert row["claims_valid"] == 0 and row["claims_unconfirmed"] == 0
    assert row["rounds"] == 1 and row["regressions"] == 0
    assert row["all_pass"] is True
    bundle_file = tmp_path / "bundles" / f"{row['run_id']}.json"
    assert bundle_file.exists()
    data = json.loads(bundle_file.read_text(encoding="utf-8"))
    assert data["status"] == "VERIFIED" and data["schema"] == "matrix-proof/v1"
