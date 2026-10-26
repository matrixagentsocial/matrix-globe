"""Proof loop with a mocked LLM: modes, guards, rollback, recovery (M2)."""
from dataclasses import dataclass, field

import pytest

from proof.loop import run_proof
from proof.sandbox.local import LocalSandbox

GOOD = "def add(a, b):\n    return a + b\n"
BAD = "def add(a, b):\n    return a - b\n"
EDGE_BAD = "def add(a, b):\n    return a + b if a >= 0 else 0\n"
BROKEN = "def add(a, b):\n    return 0\n"
PARTIAL2 = "def add(a, b):\n    return a + b if not (a == 10) else 0\n"

PUBLIC = (
    "from solution import add\n\n"
    "def test_add_ok():\n    assert add(1, 2) == 3\n\n"
    "def test_add_zero():\n    assert add(0, 5) == 5\n"
)
SPEC = "Implement `add(a, b)` returning a+b for all ints. add(-1, 2) must be 1. add(10, 1) must be 11."


@dataclass
class FakeTask:
    id: str = "add_task"
    spec: str = SPEC
    public_test: str = PUBLIC
    hidden_test: str = ""
    reference: str = GOOD
    meta: dict = field(default_factory=lambda: {"split": "dev"})


class FakeLedger:
    def __init__(self, per_call=0.0):
        self._total = 0.0
        self.per_call = per_call
        self._entries = []

    def total_usd(self):
        return self._total

    def run_usd(self, run_id):
        return sum(e["usd"] for e in self._entries if e["run_id"] == run_id)

    def entries(self):
        return list(self._entries)

    def charge(self, run_id, role):
        self._total += self.per_call
        self._entries.append({"run_id": run_id, "role": role, "usd": self.per_call,
                              "input_tokens": 10, "output_tokens": 5})


def claim(cid, body):
    return {"id": cid, "severity": "major", "title": f"claim {cid}", "spec_reference": SPEC,
            "explanation": "wrong", "failing_test": body}


class FakeClient:
    """Dispatches on role; reviewer behaviour is scripted by `reviewer_fn`."""

    def __init__(self, ledger=None, builder_code=BAD, reviewer_fn=None, reviser_code=GOOD,
                 reviewer_error=False):
        self.ledger = ledger
        self.builder_code = builder_code
        self.reviewer_fn = reviewer_fn
        self.reviser_code = reviser_code
        self.reviewer_error = reviewer_error
        self.calls = []
        self.settings = None

    def complete(self, role, messages, **kwargs):
        self.calls.append((role, kwargs))
        if self.ledger is not None:
            self.ledger.charge(kwargs.get("run_id"), role)
        text = messages[0]["content"]
        if role == "builder":
            code = self.builder_code(text) if callable(self.builder_code) else self.builder_code
            return {"code": code}
        if role == "reviewer":
            if kwargs.get("schema") is None:  # freeform (condition E)
                return "The add function is wrong for the spec; fix it."
            if self.reviewer_error:
                raise RuntimeError("reviewer exploded")
            if self.reviewer_fn is not None:
                return self.reviewer_fn(text)
            return {"verdict": "defects_found",
                    "claims": [claim("C1", "from solution import add\n\ndef test_c1():\n    assert add(1, 2) == 3\n")],
                    "untested_concerns": []}
        if role == "reviser":
            code = self.reviser_code(text) if callable(self.reviser_code) else self.reviser_code
            if kwargs.get("schema") is not None and "addressed" in str(kwargs["schema"]):
                # freeform schema uses string lists; loop coerces both, return claim form if possible
                try:
                    return {"code": code, "addressed": [{"claim_id": "C1", "change": "fixed"}], "contested": []}
                except Exception:
                    return {"code": code, "addressed": [], "contested": []}
            return {"code": code, "addressed": [{"claim_id": "C1", "change": "fixed"}], "contested": []}
        if role == "self_refine":
            schema = kwargs.get("schema") or {}
            props = schema.get("properties", {}) if isinstance(schema, dict) else {}
            if "tests" in props:
                return {"tests": "from solution import add\n\ndef test_self():\n    assert add(-1, 2) == 1\n"}
            return {"code": GOOD, "change_summary": "fixed"}
        if role == "freeform_reviewer":
            return "wrong"
        raise AssertionError(f"unexpected role {role}")


def run(task=None, mode="D", client=None, **kw):
    return run_proof(task or FakeTask(), mode, client=client or FakeClient(),
                     sandbox=LocalSandbox(), run_id="test-run", **kw)


def test_condition_a_single_shot():
    b = run(mode="A", client=FakeClient(builder_code=GOOD))
    assert b.status == "VERIFIED" and b.llmCalls == 1 and b.finalCode == GOOD


def test_condition_b_uses_wonder_max():
    client = FakeClient(builder_code=GOOD)
    b = run(mode="B", client=client)
    assert b.status == "VERIFIED"
    assert b.models.builder.model == "muse-wonder-1.0" and b.models.builder.effort == "max"
    assert client.calls[0][1].get("effort") == "max"


def test_condition_d_proves_and_fixes():
    b = run(mode="D")
    assert b.status == "VERIFIED"
    assert b.finalCode == GOOD
    assert b.rounds[0].claims[0].status == "PROVEN"
    assert b.rounds[0].claims[0].validity == "VALID"
    assert b.tests.proven.passed == 1


def test_condition_d_unproven_claim_discarded():
    def reviewer(text):
        return {"verdict": "defects_found",
                "claims": [claim("C1", "from solution import add\n\ndef test_c1():\n    assert add(1, 2) == 3\n")],
                "untested_concerns": []}
    # builder is GOOD, so the claim test passes -> UNPROVEN, no revision
    client = FakeClient(builder_code=GOOD, reviewer_fn=reviewer)
    b = run(mode="D", client=client)
    assert b.rounds[0].claims[0].status == "UNPROVEN"
    assert b.status == "VERIFIED"
    assert not any(r == "reviser" for r, _ in client.calls)


def test_condition_d_contested_claim_excluded_from_verified():
    def reviewer(text):
        return {"verdict": "defects_found",
                "claims": [claim("C1", "from solution import add\n\ndef test_c1():\n    assert add(-1, 2) == 1\n")],
                "untested_concerns": []}

    class ContestingClient(FakeClient):
        def complete(self, role, messages, **kwargs):
            if role == "reviser":
                self.calls.append((role, kwargs))
                return {"code": EDGE_BAD, "addressed": [],
                        "contested": [{"claim_id": "c1",
                                       "reason": "The spec does not require this case."}]}
            return super().complete(role, messages, **kwargs)

    client = ContestingClient(builder_code=EDGE_BAD, reviewer_fn=reviewer)
    b = run(mode="D", client=client)
    # The proven test still fails on the final code, but the claim was
    # contested, so it is excluded from the proven count (PLAN.md 5.4).
    assert b.rounds[0].contested[0]["claim_id"] == "c1"
    assert b.tests.proven.total == 0
    assert b.status == "VERIFIED"


def test_condition_e_freeform_no_proof():
    client = FakeClient(builder_code=BAD)
    b = run(mode="E", client=client)
    assert b.finalCode == GOOD and b.status == "VERIFIED"
    assert b.rounds and b.rounds[0].claims == []


def test_condition_c_self_refine():
    b = run(mode="C", client=FakeClient(builder_code=EDGE_BAD))
    assert b.finalCode == GOOD and b.status == "VERIFIED"


def test_loop_round_cap():
    def reviewer(text):
        if "return a - b" in text:
            return {"verdict": "defects_found", "claims": [claim("C1", "from solution import add\n\ndef test_c1():\n    assert add(1, 2) == 3\n")], "untested_concerns": []}
        return {"verdict": "defects_found", "claims": [claim("C2", "from solution import add\n\ndef test_c2():\n    assert add(10, 1) == 11\n")], "untested_concerns": []}

    def reviser(text):
        if "C1" in text:
            return PARTIAL2
        return GOOD

    client = FakeClient(builder_code=BAD, reviewer_fn=reviewer, reviser_code=reviser)
    b = run(mode="D", client=client, max_rounds=2)
    assert len(b.rounds) == 2


def test_loop_call_cap():
    b = run(mode="D", client=FakeClient(), max_llm_calls=2)
    assert b.llmCalls <= 2
    assert any(e.type == "guard_call_cap" for e in b.events)


def test_loop_usd_cap():
    ledger = FakeLedger(per_call=0.10)
    client = FakeClient(ledger=ledger)
    b = run(mode="D", client=client, ledger=ledger, max_usd_per_run=0.15)
    assert any(e.type == "guard_usd_cap" for e in b.events)
    assert b.llmCalls <= 3


def test_loop_wall_clock_cap():
    times = iter([0.0, 1000.0, 1000.0, 1000.0, 1000.0])
    b = run(mode="D", client=FakeClient(), max_wall_s=360.0, clock=lambda: next(times, 1000.0))
    assert any(e.type == "guard_wall_clock" for e in b.events)
    assert b.llmCalls == 0


def test_rollback_on_regression():
    def reviewer(text):
        return {"verdict": "defects_found", "claims": [claim("C1", "from solution import add\n\ndef test_c1():\n    assert add(-1, 2) == 1\n")], "untested_concerns": []}

    client = FakeClient(builder_code=EDGE_BAD, reviser_code=BROKEN, reviewer_fn=reviewer)
    b = run(mode="D", client=client)
    assert b.finalCode == EDGE_BAD
    assert any(e.type == "regression" for e in b.events)
    assert b.status == "PARTIAL"


def test_recovery_after_failed_reviewer():
    client = FakeClient(builder_code=GOOD, reviewer_error=True)
    b = run(mode="D", client=client)
    assert any(e.type == "step_failed" for e in b.events)
    assert b.finalCode == GOOD and b.status == "VERIFIED"


def test_recovery_after_failed_builder():
    class BadBuilder(FakeClient):
        def complete(self, role, messages, **kwargs):
            if role == "builder":
                raise RuntimeError("builder down")
            return super().complete(role, messages, **kwargs)

    b = run(mode="D", client=BadBuilder())
    assert any(e.type == "step_failed" for e in b.events)
    assert b.status == "FAILED"
