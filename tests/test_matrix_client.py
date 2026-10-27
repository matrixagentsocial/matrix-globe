"""Matrix client with httpx MockTransport (no network, no real key)."""
import json

import httpx
import pytest

from proof.matrix_client import MatrixClient, MatrixError

KEY = "test-proofdesk-key-not-real"


def make_client(handler, **kw):
    transport = httpx.MockTransport(handler)
    return MatrixClient(
        base_url="https://example.test/api/proxy", api_key=KEY,
        transport=transport, sleep=lambda _: None, **kw,
    )


def test_feed_is_anonymous_and_unwraps_creations():
    seen = {}

    def handler(request):
        seen["headers"] = request.headers
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"data": {"creations": [
            {"id": "c1", "title": "t", "agent": {"slug": "alice"}, "createdAt": "2026-10-27T00:00:00Z"}
        ]}})

    client = make_client(handler)
    creations = client.list_proof_requests()
    assert [c["id"] for c in creations] == ["c1"]
    assert "page=1" in seen["url"] and "pageSize=20" in seen["url"]
    assert "x-matrix-key" not in seen["headers"]


def test_get_creation_unwraps_data():
    def handler(request):
        assert request.url.path.endswith("/v1/creations/c9")
        return httpx.Response(200, json={"data": {"id": "c9", "contentBody": "x", "reviews": []}})

    assert make_client(handler).get_creation("c9")["id"] == "c9"


def test_post_review_payload_and_attribution_headers():
    seen = {}

    def handler(request):
        seen["headers"] = request.headers
        seen["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"data": {"id": "rev-1"}})

    client = make_client(handler)
    out = client.post_review(
        "c1", body="hello", review_type="BUG_REPORT",
        code_suggestion="def test_x():\n    pass\n", model="muse-wonder-1.0",
    )
    assert out == {"id": "rev-1"}
    assert seen["payload"] == {
        "body": "hello", "reviewType": "BUG_REPORT",
        "codeSuggestion": "def test_x():\n    pass\n",
    }
    assert seen["headers"]["x-matrix-key"] == KEY
    assert seen["headers"]["x-matrix-provider"] == "meta"
    assert seen["headers"]["x-matrix-model"] == "muse-wonder-1.0"
    assert seen["headers"]["x-matrix-agent"] == "Matrix Globe"


def test_post_review_reply_parent_and_no_code_suggestion_when_omitted():
    seen = {}

    def handler(request):
        seen["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"data": {"id": "rev-2"}})

    make_client(handler).post_review(
        "c1", body="reply", review_type="SUGGESTION",
        parent_review_id="rev-1", model="muse-wonder-1.0",
    )
    assert seen["payload"] == {
        "body": "reply", "reviewType": "SUGGESTION", "parentReviewId": "rev-1",
    }


def test_retries_on_500_then_succeeds():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(500, json={"error": "boom"})
        return httpx.Response(200, json={"data": {"creations": []}})

    assert make_client(handler).list_proof_requests() == []
    assert calls["n"] == 3


def test_retries_exhausted_raise_without_key_in_message():
    def handler(request):
        return httpx.Response(503, json={"error": "down"})

    with pytest.raises(MatrixError) as exc:
        make_client(handler).list_proof_requests()
    assert KEY not in str(exc.value)


def test_is_fresh_true_and_stale_false():
    fresh = make_client(lambda r: httpx.Response(200, json={"data": []}))
    assert fresh.is_fresh() is True
    stale = make_client(
        lambda r: httpx.Response(200, json={"data": []}, headers={"X-Matrix-Cache": "STALE"})
    )
    assert stale.is_fresh() is False


def test_is_fresh_false_when_down():
    down = make_client(lambda r: httpx.Response(500, json={}))
    assert down.is_fresh() is False
