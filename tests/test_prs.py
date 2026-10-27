"""PR targets: building, validation targets and mocked-LLM conditions."""
import json
from pathlib import Path

from bench.prs import discover_prs, load_pr_targets, rewrite_imports, validate_pr
from bench.run_bench import run_review_bench_prs
from proof.loop import run_proof
from proof.sandbox.local import LocalSandbox

PRS_ROOT = "bench/prs"
TASKS_ROOT = "bench/tasks"

CLAIM_TEST = (
    "from task_c import split_installments\n"
    "import pytest\n\n"
    "def test_c1():\n"
    "    with pytest.raises(ValueError):\n"
    "        split_installments('10.005', 2)\n"
)


def _modules_payload(modules):
    return [{"name": n, "code": c} for n, c in sorted(modules.items())]


class FakePRClient:
    """Mocked LLM serving every PR condition from the clean modules."""

    def __init__(self, clean_modules):
        self.clean = clean_modules
        self.calls = []
        self._review_calls = 0

    def complete(self, role, messages, **kwargs):
        self.calls.append((role, kwargs))
        schema = kwargs.get("schema") or {}
        props = schema.get("properties", {}) if isinstance(schema, dict) else {}
        if role == "reviewer" and schema is None:
            return "A defect in task_c: validation is missing."
        if role == "reviewer":
            self._review_calls += 1
            return {"verdict": "defects_found",
                    "claims": [{"id": "C1", "severity": "major", "title": "missing validation",
                                "spec_reference": "must have at most 2 decimal places",
                                "explanation": "mutant accepts 10.005",
                                "failing_test": CLAIM_TEST}],
                    "untested_concerns": []}
        if role in ("reviser", "builder", "self_refine"):
            if "modules" in props:
                out = {"modules": _modules_payload(self.clean)}
                if "addressed" in props:
                    out["addressed"] = [{"claim_id": "C1", "change": "fixed"}] \
                        if schema_has_objects(schema) else ["fixed"]
                    out["contested"] = []
                if "change_summary" in props:
                    out["change_summary"] = "fixed"
                return out
            if "tests" in props:
                return {"tests": CLAIM_TEST}
            return {"code": "package", "addressed": [], "contested": []}
        raise AssertionError(role)


def schema_has_objects(schema):
    try:
        return schema["properties"]["addressed"]["items"].get("type") == "object"
    except Exception:
        return False


def _dev_pr():
    prs = discover_prs(PRS_ROOT, split="dev")
    assert len(prs) == 3
    return {p.id: p for p in prs}["pr_dev_3"]


def test_pr_structure_and_targets():
    pr = _dev_pr()
    assert pr.module_names == ["task_a.py", "task_b.py", "task_c.py"]
    assert set(pr.meta["tasks"]) == {"number_parsing", "receivables_aging", "split_installments"}
    for slot in pr.module_names:
        assert (Path(PRS_ROOT) / pr.id / slot).exists()
    targets = load_pr_targets(pr, TASKS_ROOT, "all")
    assert [t for t, _ in targets] == ["clean", "buggy_a", "buggy_b", "buggy_c"]
    clean = dict(targets)["clean"]
    assert clean == pr.clean_modules
    for target_id, modules in targets[1:]:
        changed = [n for n in modules if modules[n] != clean[n]]
        assert len(changed) == 1, (target_id, changed)


def test_rewrite_imports():
    src = "from solution import parse_number\nimport pytest\n"
    assert rewrite_imports(src, "task_a.py").startswith("from task_a import parse_number")


def test_pr_validation_dev():
    pr = _dev_pr()
    ok, detail = validate_pr(pr, TASKS_ROOT, LocalSandbox())
    assert ok, detail


def _run_pr_condition(cond):
    pr = _dev_pr()
    client = None if cond == "R" else FakePRClient(pr.clean_modules)
    rows = run_review_bench_prs([pr], cond, client=client, sandbox=LocalSandbox(),
                                seeds=1, tasks_root=TASKS_ROOT)
    assert len(rows) == (1 if cond == "B" else 4)
    return rows, client


def test_pr_condition_r_unreviewed_no_llm():
    rows, _ = _run_pr_condition("R")
    assert all(r["status"] == "UNREVIEWED" for r in rows)
    assert all(r["usd"] == 0 for r in rows)
    by_target = {r["target_id"]: r for r in rows}
    assert by_target["clean"]["fixed"] is True
    assert by_target["buggy_c"]["fixed"] is False


def test_pr_condition_d_fixes_buggy_c():
    rows, _ = _run_pr_condition("D")
    by_target = {r["target_id"]: r for r in rows}
    assert by_target["buggy_c"]["fixed"] is True
    assert by_target["buggy_c"]["claims_proven"] >= 1
    assert by_target["buggy_c"]["claims_valid"] >= 1
    assert by_target["clean"]["damaged"] is False


def test_pr_condition_c_and_e_and_b():
    rows_c, _ = _run_pr_condition("C")
    assert {r["target_id"]: r for r in rows_c}["buggy_c"]["fixed"] is True
    rows_e, _ = _run_pr_condition("E")
    assert {r["target_id"]: r for r in rows_e}["buggy_c"]["fixed"] is True
    rows_b, _ = _run_pr_condition("B")
    assert rows_b[0]["target_id"] == "regen" and rows_b[0]["fixed"] is True


def test_single_task_r_status_unreviewed():
    from tests.test_loop import FakeTask, GOOD
    bundle = run_proof(FakeTask(), "R", client=None, sandbox=LocalSandbox(),
                       run_id="test-r", initial_code=GOOD)
    assert bundle.status == "UNREVIEWED"
    assert bundle.llmCalls == 0
