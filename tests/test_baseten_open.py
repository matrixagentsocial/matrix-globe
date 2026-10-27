"""Baseten (open-weights) routing, caps, open conditions and desk stack."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from proof.config import OPEN_MODEL, Settings, compute_cost, provider_for_model
from proof.ledger import HardCapExceeded, Ledger
from proof.llm import LLMClient

GOOD = "def add(a, b):\n    return a + b\n"
BAD = "def add(a, b):\n    return a - b\n"
SPEC = "Implement `add(a, b)` returning a+b for all ints."
PUBLIC = "from solution import add\n\ndef test_add_ok():\n    assert add(1, 2) == 3\n"
HIDDEN = "from solution import add\n\ndef test_add_neg():\n    assert add(-1, 2) == 1\n"
CLAIM_TEST = "from solution import add\n\ndef test_c1():\n    assert add(1, 2) == 3\n"


def _settings(**kw):
    base = dict(
        base_url="https://api.meta.ai/v1", api_key="meta-key-not-real",
        model_builder="muse-spark-1.3-contributor",
        model_builder_external="muse-spark-1.3",
        model_reviewer="muse-wonder-1.0",
        max_usd_total=1000.0, max_usd_per_run=100.0,
        baseten_api_key="baseten-key-not-real", baseten_max_usd=90.0,
    )
    base.update(kw)
    return Settings(**base)


def _response(content):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content), finish_reason="stop")],
        usage={"prompt_tokens": 100, "completion_tokens": 50,
               "prompt_tokens_details": {"cached_tokens": 10},
               "completion_tokens_details": {"reasoning_tokens": 40}},
    )


class FakeCompletions:
    def __init__(self, content='{"answer": "hi", "n": 3}'):
        self.calls = []
        self._content = content

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _response(self._content)


def _fake_client(content='{"answer": "hi", "n": 3}'):
    comp = FakeCompletions(content)
    return SimpleNamespace(chat=SimpleNamespace(completions=comp)), comp


def test_provider_routing_by_model_id():
    assert provider_for_model(OPEN_MODEL) == "baseten"
    assert provider_for_model("meta-models/muse-spark-open") == "baseten"
    assert provider_for_model("muse-wonder-1.0") == "meta"
    assert provider_for_model("muse-spark-1.3") == "meta"


def test_open_model_pricing():
    # Baseten published price: $1.25 / $0.15 / $4.25 per 1M.
    assert compute_cost(OPEN_MODEL, 1_000_000, 1_000_000, 0) == pytest.approx(5.50)
    assert compute_cost(OPEN_MODEL, 1_000_000, 0, cached_tokens=1_000_000) == pytest.approx(0.15)


def test_llm_routes_open_to_baseten_and_records_provider(tmp_path):
    meta, meta_calls = _fake_client()
    baseten, baseten_calls = _fake_client()
    settings = _settings()
    ledger = Ledger(tmp_path / "ledger.jsonl", settings=settings)
    client = LLMClient(client=meta, baseten_client=baseten, ledger=ledger,
                       settings=settings, sleep=lambda _: None)
    msgs = [{"role": "user", "content": "hi"}]
    client.complete("reviewer", msgs, model="muse-wonder-1.0", run_id="r-meta")
    assert len(meta_calls.calls) == 1 and len(baseten_calls.calls) == 0
    client.complete("reviewer", msgs, model=OPEN_MODEL, run_id="r-open")
    assert len(baseten_calls.calls) == 1
    assert baseten_calls.calls[0]["model"] == OPEN_MODEL
    rows = ledger.entries()
    assert rows[0]["provider"] == "meta" and rows[0]["model"] == "muse-wonder-1.0"
    assert rows[1]["provider"] == "baseten" and rows[1]["model"] == OPEN_MODEL
    assert rows[1]["reasoning_tokens"] == 40 and rows[1]["cached_tokens"] == 10


def test_baseten_cap_is_separate_from_meta_cap(tmp_path):
    settings = _settings(max_usd_total=0.10, baseten_max_usd=0.10)
    ledger = Ledger(tmp_path / "ledger.jsonl", settings=settings)
    ledger.append({"run_id": "a", "role": "reviewer", "model": OPEN_MODEL,
                   "provider": "baseten", "usd": 0.10,
                   "input_tokens": 1, "cached_tokens": 0, "output_tokens": 1, "reasoning_tokens": 0})
    with pytest.raises(HardCapExceeded, match="BASETEN_MAX_USD"):
        ledger.check_caps("x", provider="baseten", model=OPEN_MODEL)
    # Meta calls are unaffected by Baseten spend.
    ledger.check_caps("x", provider="meta", model="muse-wonder-1.0")
    # And the reverse: Meta spend at its cap does not block Baseten.
    settings2 = _settings(max_usd_total=0.10, baseten_max_usd=90.0)
    ledger2 = Ledger(tmp_path / "ledger2.jsonl", settings=settings2)
    ledger2.append({"run_id": "a", "role": "reviewer", "model": "muse-wonder-1.0",
                    "provider": "meta", "usd": 0.10,
                    "input_tokens": 1, "cached_tokens": 0, "output_tokens": 1, "reasoning_tokens": 0})
    with pytest.raises(HardCapExceeded, match="MAX_USD_TOTAL"):
        ledger2.check_caps("x", provider="meta", model="muse-wonder-1.0")
    ledger2.check_caps("x", provider="baseten", model=OPEN_MODEL)


def test_baseten_cap_blocks_llm_before_call(tmp_path):
    meta, meta_calls = _fake_client()
    baseten, baseten_calls = _fake_client()
    settings = _settings(baseten_max_usd=0.0)
    ledger = Ledger(tmp_path / "ledger.jsonl", settings=settings)
    client = LLMClient(client=meta, baseten_client=baseten, ledger=ledger,
                       settings=settings, sleep=lambda _: None)
    with pytest.raises(HardCapExceeded):
        client.complete("reviewer", [{"role": "user", "content": "hi"}],
                        model=OPEN_MODEL, run_id="r1")
    assert baseten_calls.calls == [] and meta_calls.calls == []


class FakeOpenClient:
    """Mocked LLM for open conditions: self-check passes, D proves+fixes."""

    def __init__(self):
        self.calls = []
        self.settings = None

    def complete(self, role, messages, **kwargs):
        self.calls.append((role, kwargs))
        schema = kwargs.get("schema") or {}
        props = schema.get("properties", {}) if isinstance(schema, dict) else {}
        if role == "self_refine":
            if "tests" in props:
                return {"tests": CLAIM_TEST}
            return {"code": GOOD, "change_summary": "fixed"}
        if role == "reviewer":
            if schema is None or not props:
                return "The add function subtracts instead of adding; fix it."
            return {"verdict": "defects_found", "claims": [{
                "id": "C1", "severity": "major", "title": "add subtracts",
                "spec_reference": SPEC, "explanation": "a-b",
                "failing_test": CLAIM_TEST}], "untested_concerns": []}
        if role == "reviser":
            return {"code": GOOD,
                    "addressed": [{"claim_id": "C1", "change": "use +"}], "contested": []}
        raise AssertionError(role)


def _tiny_task():
    from bench.task_loader import Task
    return Task(id="add_task", dir=Path("."), spec=SPEC, public_test=PUBLIC,
                hidden_test=HIDDEN, reference=GOOD, meta={"split": "test"})


def test_open_conditions_mocked(tmp_path):
    import json as _json
    from bench.run_bench import run_review_bench
    from proof.sandbox.local import LocalSandbox

    for cond, target_code in (("C_open", GOOD), ("E_open", BAD), ("D_open", BAD)):
        bundles = tmp_path / cond
        rows = run_review_bench(
            [_tiny_task()], cond, client=FakeOpenClient(), sandbox=LocalSandbox(),
            seeds=1, ledger=None, settings=_settings(), bundles_dir=bundles,
            targets="clean")
        assert len(rows) == 1
        row = rows[0]
        assert row["condition"] == cond
        assert row["provider"] == "baseten"
        assert row["model"] == OPEN_MODEL
        assert row["fixed"] is True
        bundle = _json.loads((bundles / f"{row['run_id']}.json").read_text(encoding="utf-8"))
        assert bundle["models"]["builder"]["provider"] == "baseten"
        assert bundle["models"]["builder"]["model"] == OPEN_MODEL
        assert bundle["models"]["reviewer"]["provider"] == "baseten"
        assert bundle["models"]["reviewer"]["model"] == OPEN_MODEL
        if cond == "D_open":
            # Clean target: the claim test passes, so it is discarded as UNPROVEN.
            assert row["claims_proposed"] == 1
            assert row["claims_unproven"] == 1


def test_desk_stack_open_switch(tmp_path):
    from proof.desk import Desk
    from proof.sandbox.local import LocalSandbox

    class _Sandbox(LocalSandbox):
        pass

    def make(stack):
        return Desk(matrix=None, llm_client=None, sandbox=LocalSandbox(),
                    settings=_settings(), state_path=tmp_path / "desk.json",
                    desk_stack=stack)

    default = make(None)
    assert default.reviewer_model == "muse-wonder-1.0"
    assert default.reviser_model == "muse-spark-1.3"
    opened = make("open")
    assert opened.reviewer_model == OPEN_MODEL
    assert opened.reviser_model == OPEN_MODEL
    eff = opened.effective_settings()
    assert eff.model_reviewer == OPEN_MODEL
    assert eff.model_builder_external == OPEN_MODEL


def test_desk_stack_open_via_env(tmp_path, monkeypatch):
    from proof.desk import Desk
    from proof.sandbox.local import LocalSandbox
    monkeypatch.setenv("DESK_STACK", "open")
    desk = Desk(matrix=None, llm_client=None, sandbox=LocalSandbox(),
                settings=_settings(), state_path=tmp_path / "desk.json")
    assert desk.reviewer_model == OPEN_MODEL
    assert desk.reviser_model == OPEN_MODEL
