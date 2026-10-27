"""Desk with a mocked Matrix (MockTransport) and a mocked LLM."""
import hashlib
import json
import re

import httpx
import pytest

from proof.bundle import canonical_json
from proof.config import Settings
from proof.desk import (
    Desk,
    build_certificate_body,
    ledger_daily_usd,
)
from proof.llm import ContributorGuardError, LLMClient
from proof.matrix_client import MatrixClient
from proof.request_format import format_proof_request
from proof.roles.reviser import revise_code
from proof.sandbox.base import Sandbox
from proof.sandbox.local import LocalSandbox

GOOD = "def add(a, b):\n    return a + b\n"
BAD = "def add(a, b):\n    return a - b\n"
SPEC = "Implement `add(a, b)` returning a+b for all ints."
PUBLIC = "from solution import add\n\ndef test_add_ok():\n    assert add(1, 2) == 3\n"
CLAIM_TEST = "from solution import add\n\ndef test_c1_add():\n    assert add(1, 2) == 3\n"


def settings():
    return Settings(
        base_url="https://api.meta.ai/v1", api_key="test-model-key",
        model_builder="muse-spark-1.3-contributor",
        model_builder_external="muse-spark-1.3",
        model_reviewer="muse-wonder-1.0",
        max_usd_total=1000.0, max_usd_per_run=100.0,
    )


class FakeLedger:
    def __init__(self, entries=None):
        self._entries = list(entries or [])

    def entries(self):
        return list(self._entries)

    def total_usd(self):
        return sum(e["usd"] for e in self._entries)

    def run_usd(self, run_id):
        return sum(e["usd"] for e in self._entries if e.get("run_id") == run_id)


class FakeLLM:
    """Reviewer proves C1 on BAD code; reviser returns GOOD."""

    def __init__(self, settings_obj, claims=True):
        self.settings = settings_obj
        self.ledger = FakeLedger()
        self.calls = []
        self._claims = claims

    def complete(self, role, messages, **kwargs):
        self.calls.append((role, kwargs))
        if role == "reviewer":
            if not self._claims:
                return {"verdict": "no_proven_defects", "claims": [], "untested_concerns": []}
            return {"verdict": "defects_found", "claims": [{
                "id": "C1", "severity": "major", "title": "add subtracts",
                "spec_reference": SPEC, "explanation": "a-b != a+b",
                "failing_test": CLAIM_TEST,
            }], "untested_concerns": []}
        if role == "reviser":
            return {"code": GOOD, "addressed": [{"claim_id": "C1", "change": "use +"}],
                    "contested": []}
        raise AssertionError(role)


class LocalDockerLikeSandbox(Sandbox):
    """Runs like the Docker sandbox would, on trusted test code only."""

    python_cmd = LocalSandbox().python_cmd
    report_path = "report.xml"

    def run(self, files, cmd, timeout_s=10.0, *, origin=None):
        return LocalSandbox().run(files, cmd, timeout_s=timeout_s, origin="bench")


class FakeMatrixStore:
    def __init__(self, creations):
        self.creations = {c["id"]: c for c in creations}
        self.posts = []  # (creation_id, payload, headers)
        self._n = 0

    def handler(self, request):
        path = request.url.path
        if path.endswith("/v1/feed/topic/proof-request"):
            feed = [{
                "id": c["id"], "title": c.get("title", "t"),
                "agent": c.get("agent", {}), "createdAt": c.get("createdAt", ""),
            } for c in self.creations.values()]
            return httpx.Response(200, json={"data": {"creations": feed}})
        m = re.search(r"/v1/creations/([^/]+)$", path)
        if request.method == "GET" and m:
            return httpx.Response(200, json={"data": self.creations[m.group(1)]})
        m = re.search(r"/v1/reviews/creations/([^/]+)$", path)
        if request.method == "POST" and m:
            self._n += 1
            payload = json.loads(request.content)
            self.posts.append((m.group(1), payload, request.headers))
            return httpx.Response(200, json={"data": {"id": f"rev-{self._n}"}})
        return httpx.Response(404, json={"error": "not found"})


def make_creation(cid="c1", slug="alice", code=BAD, **over):
    creation = {
        "id": cid, "title": "Proof request: add", "contentBody": format_proof_request(SPEC, code, PUBLIC),
        "visibility": "public", "language": "python", "tags": ["proof-request"],
        "agent": {"slug": slug}, "createdAt": "2026-10-27T00:00:00Z", "reviews": [],
    }
    creation.update(over)
    return creation


def make_desk(tmp_path, store, llm=None, **kw):
    matrix = MatrixClient(
        base_url="https://example.test/api/proxy", api_key="test-proofdesk-key",
        transport=httpx.MockTransport(store.handler), sleep=lambda _: None,
    )
    llm = llm or FakeLLM(settings())
    desk = Desk(
        matrix=matrix, llm_client=llm, sandbox=LocalDockerLikeSandbox(),
        ledger=llm.ledger, settings=settings(),
        state_path=tmp_path / "desk.json", **kw,
    )
    return desk


# Python port of extractCertificate from apps/web/src/lib/proof.ts.
CERT_RE = re.compile(r"```matrix-proof[^\n]*\n([\s\S]*?)\n```")
SHA_RE = re.compile(r"sha256:\s*`?([0-9a-fA-F]{64})`?")


def extract_certificate(text):
    if not text:
        return None
    block = CERT_RE.search(text)
    if not block:
        return None
    bundle_text = block.group(1).strip()
    try:
        bundle = json.loads(bundle_text)
        if not isinstance(bundle, dict):
            bundle = None
    except ValueError:
        bundle = None
    after = text[block.end():]
    sha = SHA_RE.search(after) or SHA_RE.search(text)
    return {"bundleText": bundle_text, "bundle": bundle,
            "sha256": sha.group(1).lower() if sha else None}


def test_desk_happy_path_three_posts_exact_shapes(tmp_path):
    store = FakeMatrixStore([make_creation()])
    desk = make_desk(tmp_path, store)
    summary = desk.run_once()
    assert summary["processed"] == 1 and summary["posted"] == 3
    assert len(store.posts) == 3

    (_, review, headers), (_, revision, _), (_, cert, _) = store.posts
    assert review["reviewType"] == "BUG_REPORT"
    assert "parentReviewId" not in review
    assert "Status: VERIFIED" in review["body"]
    assert "- C1 [PROVEN] add subtracts" in review["body"]
    assert "Claims that could not be reproduced were discarded (no proof, no bug)." in review["body"]
    assert "def test_c1_add" in review["codeSuggestion"]
    assert headers["x-matrix-provider"] == "meta"
    assert headers["x-matrix-model"] == "muse-wonder-1.0"
    assert headers["x-matrix-agent"] == "Matrix Globe"

    assert revision["reviewType"] == "SUGGESTION"
    assert revision["parentReviewId"] == "rev-1"
    assert revision["body"].startswith("Suggested verified revision")
    assert revision["codeSuggestion"] == GOOD

    assert cert["reviewType"] == "SUGGESTION"
    assert cert["parentReviewId"] == "rev-1"
    assert "https://matrixagentnet.com/proof?id=c1" in cert["body"]

    parsed = extract_certificate(cert["body"])
    assert parsed and parsed["bundle"] is not None
    bundle = parsed["bundle"]
    assert bundle["schema"] == "matrix-proof/v1"
    assert bundle["status"] == "VERIFIED"
    assert bundle["target"] == "desk:c1"
    assert bundle["models"]["reviewer"]["model"] == "muse-wonder-1.0"
    assert bundle["models"]["builder"]["model"] == "muse-spark-1.3"
    # No floats anywhere (money as strings).
    assert not isinstance(bundle["cost"]["usd"], float)
    # Hash verifies against the canonical JSON, like the web viewer.
    computed = hashlib.sha256(canonical_json(bundle).encode("utf-8")).hexdigest()
    assert parsed["sha256"] == computed

    # State persisted the processed id.
    state = json.loads((tmp_path / "desk.json").read_text(encoding="utf-8"))
    assert state["processed"] == ["c1"]
    assert state["daily"]["total"] == 1
    assert state["daily"]["per_agent"] == {"alice": 1}


def test_desk_llm_calls_use_external_origin_and_external_reviser_model(tmp_path):
    store = FakeMatrixStore([make_creation()])
    llm = FakeLLM(settings())
    desk = make_desk(tmp_path, store, llm=llm)
    desk.run_once()
    by_role = {}
    for role, kwargs in llm.calls:
        by_role.setdefault(role, []).append(kwargs)
    assert by_role["reviewer"][0]["metadata"] == {"origin": "external"}
    assert by_role["reviser"][0]["metadata"] == {"origin": "external"}
    assert by_role["reviser"][0]["model"] == "muse-spark-1.3"


def test_desk_praise_when_nothing_proven(tmp_path):
    store = FakeMatrixStore([make_creation(code=GOOD)])
    llm = FakeLLM(settings(), claims=False)
    desk = make_desk(tmp_path, store, llm=llm)
    summary = desk.run_once()
    assert summary["processed"] == 1
    assert len(store.posts) == 2  # review + certificate, no revision
    review = store.posts[0][1]
    assert review["reviewType"] == "PRAISE"
    assert "codeSuggestion" not in review


def test_desk_skips_already_answered(tmp_path):
    creation = make_creation()
    creation["reviews"] = [{
        "id": "r0", "body": "done", "reviewType": "PRAISE",
        "agent": {"slug": "proofdesk"}, "createdAt": "2026-10-27T01:00:00Z", "replies": [],
    }]
    store = FakeMatrixStore([creation])
    desk = make_desk(tmp_path, store)
    summary = desk.run_once()
    assert summary["skipped"] == 1 and store.posts == []


@pytest.mark.parametrize("over,reason", [
    ({"visibility": "private"}, "private"),
    ({"language": "javascript"}, "not_python"),
    ({"contentBody": "## Code\n```python\nx=1\n```\n"}, "missing_spec"),
    ({"contentBody": "## Spec\nhi\n\n## Code\n```python\n" + "x=1\n" * 6000 + "```\n"}, "code_too_large"),
])
def test_desk_rejects_with_single_question(tmp_path, over, reason):
    store = FakeMatrixStore([make_creation(**over)])
    desk = make_desk(tmp_path, store)
    summary = desk.run_once()
    assert summary["rejected"] == 1
    assert len(store.posts) == 1
    payload = store.posts[0][1]
    assert payload["reviewType"] == "QUESTION"
    assert "codeSuggestion" not in payload
    assert "parentReviewId" not in payload


def test_desk_daily_total_limit(tmp_path):
    store = FakeMatrixStore([make_creation()])
    desk = make_desk(tmp_path, store)
    from proof.desk import _daily_counters, _today
    _daily_counters(desk.state, _today())["total"] = 20
    summary = desk.run_once()
    assert summary.get("stopped") == "daily limit reached"
    assert store.posts == []


def test_desk_per_agent_limit_skips(tmp_path):
    store = FakeMatrixStore([make_creation()])
    desk = make_desk(tmp_path, store)
    from proof.desk import _daily_counters, _today
    daily = _daily_counters(desk.state, _today())
    daily["per_agent"] = {"alice": 3}
    summary = desk.run_once()
    assert summary["skipped"] == 1 and store.posts == []


def test_desk_daily_spend_limit_from_ledger(tmp_path):
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ledger = FakeLedger([{"ts": f"{today}T00:00:00Z", "run_id": "x", "role": "reviewer", "usd": 5.0}])
    assert ledger_daily_usd(ledger, today) == 5.0
    store = FakeMatrixStore([make_creation()])
    llm = FakeLLM(settings())
    llm.ledger = ledger
    desk = make_desk(tmp_path, store, llm=llm)
    desk.ledger = ledger
    summary = desk.run_once()
    assert summary.get("stopped") == "daily limit reached"
    assert store.posts == []


def test_desk_near_limit_processes_only_one_per_cycle(tmp_path):
    store = FakeMatrixStore([make_creation("c1"), make_creation("c2")])
    desk = make_desk(tmp_path, store)
    from proof.desk import _daily_counters, _today
    _daily_counters(desk.state, _today())["total"] = 18
    summary = desk.run_once()
    assert summary["processed"] == 1
    assert len(store.posts) == 3


def test_desk_refuses_local_sandbox_unless_dry_run(tmp_path):
    store = FakeMatrixStore([make_creation()])
    desk = make_desk(tmp_path, store)
    desk.sandbox = LocalSandbox()
    desk.dry_run = False
    summary = desk.run_once()
    assert summary["processed"] == 0 and summary["errors"] == 1
    assert store.posts == []
    assert "local sandbox" in desk.state["last_error"]


def test_contributor_guard_triggered_by_external_origin(tmp_path):
    from types import SimpleNamespace

    completions_calls = []

    class FakeCompletions:
        def create(self, **kwargs):
            completions_calls.append(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(
                    content='{"code": "x=1", "addressed": [], "contested": []}'),
                    finish_reason="stop")],
                usage={"prompt_tokens": 10, "completion_tokens": 5},
            )

    fake_openai = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    client = LLMClient(client=fake_openai, ledger=FakeLedgerAdapter(tmp_path),
                       settings=settings(), sleep=lambda _: None)
    with pytest.raises(ContributorGuardError):
        revise_code(client, SPEC, BAD, [{"id": "C1"}], run_id="desk-x",
                    model="muse-spark-1.3-contributor", origin="external")
    assert completions_calls == []
    # The Standard external model is allowed for external code.
    rev = revise_code(client, SPEC, BAD, [{"id": "C1"}], run_id="desk-x",
                      model="muse-spark-1.3", origin="external")
    assert rev.code == "x=1"


class FakeLedgerAdapter:
    """Real Ledger on a temp file so LLMClient can record calls."""

    def __init__(self, tmp_path):
        from proof.ledger import Ledger
        self._ledger = Ledger(tmp_path / "ledger.jsonl", settings=settings())

    def __getattr__(self, name):
        return getattr(self._ledger, name)


def test_certificate_body_shape():
    from proof.bundle import ProofBundle
    bundle = ProofBundle.model_validate({
        "schema": "matrix-proof/v1", "runId": "r1", "createdAt": "2026-10-27T00:00:00Z",
        "task": {"id": "c1", "specSha256": "a" * 64},
        "models": {"builder": {"model": "muse-spark-1.3", "effort": "medium"},
                   "reviewer": {"model": "muse-wonder-1.0", "effort": "high"}},
        "status": "VERIFIED", "target": "desk:c1",
    })
    body = build_certificate_body(bundle, "c1")
    parsed = extract_certificate(body)
    assert parsed["sha256"] == bundle.sha256()
    assert parsed["bundle"]["runId"] == "r1"
