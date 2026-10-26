"""LLM client with a mocked OpenAI client (no network)."""
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from proof.config import Settings
from proof.ledger import Ledger
from proof.llm import (
    ContributorGuardError,
    InvalidJSONError,
    LLMClient,
    TruncatedResponseError,
)


class Tiny(BaseModel):
    answer: str
    n: int


def _settings(per_run: float = 100.0, total: float = 1000.0) -> Settings:
    return Settings(
        base_url="https://api.meta.ai/v1",
        api_key="test-key-not-real",
        model_builder="muse-spark-1.3-contributor",
        model_builder_external="muse-spark-1.3",
        model_reviewer="muse-wonder-1.0",
        max_usd_total=total,
        max_usd_per_run=per_run,
    )


def make_response(content: str, finish_reason: str = "stop", prompt: int = 100, completion: int = 50):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
                finish_reason=finish_reason,
            )
        ],
        usage={
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "prompt_tokens_details": {"cached_tokens": 10},
            "completion_tokens_details": {"reasoning_tokens": 5},
        },
    )


class FakeCompletions:
    def __init__(self, script: list):
        self._script = list(script)
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self._script:
            raise AssertionError("Fake OpenAI client ran out of scripted responses")
        item = self._script.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item


class FakeHTTPError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


def make_client(tmp_path, script: list, **settings_kwargs):
    completions = FakeCompletions(script)
    fake_openai = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    settings = _settings(**settings_kwargs)
    ledger = Ledger(tmp_path / "ledger.jsonl", settings=settings)
    client = LLMClient(client=fake_openai, ledger=ledger, settings=settings, sleep=lambda _: None)
    return client, completions, ledger


MESSAGES = [{"role": "user", "content": "Return JSON"}]


def test_json_schema_dict_parsing(tmp_path):
    client, completions, ledger = make_client(
        tmp_path, [make_response('{"answer": "hi", "n": 3}')]
    )
    schema = {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "n": {"type": "integer"},
        },
        "required": ["answer", "n"],
        "additionalProperties": False,
    }
    result = client.complete("builder", MESSAGES, schema=schema, run_id="r1")
    assert result == {"answer": "hi", "n": 3}
    # json_schema strict wire format was used.
    assert completions.calls[0]["response_format"]["type"] == "json_schema"
    assert completions.calls[0]["response_format"]["json_schema"]["strict"] is True
    # The successful call was written to the ledger with its cost.
    rows = ledger.entries()
    assert len(rows) == 1
    assert rows[0]["run_id"] == "r1"
    assert rows[0]["role"] == "builder"
    assert rows[0]["input_tokens"] == 100
    assert rows[0]["cached_tokens"] == 10
    assert rows[0]["output_tokens"] == 50
    assert rows[0]["reasoning_tokens"] == 5
    assert rows[0]["usd"] > 0


def test_json_schema_pydantic_parsing(tmp_path):
    client, _, ledger = make_client(tmp_path, [make_response('{"answer": "ok", "n": 7}')])
    result = client.complete("reviewer", MESSAGES, schema=Tiny, run_id="r2")
    assert isinstance(result, Tiny)
    assert result.answer == "ok"
    assert result.n == 7
    assert ledger.total_usd() > 0


def test_invalid_json_single_repair_then_success(tmp_path):
    client, completions, _ = make_client(
        tmp_path,
        [make_response("not json at all"), make_response('{"answer": "fixed", "n": 1}')],
    )
    result = client.complete("builder", MESSAGES, schema=Tiny, run_id="r3")
    assert result.answer == "fixed"
    # Exactly one repair call: 1 original + 1 repair.
    assert len(completions.calls) == 2
    # The repair call sends the parse error back.
    repair_text = str(completions.calls[1]["messages"])
    assert "not valid JSON" in repair_text


def test_invalid_json_repair_fails_raises_typed(tmp_path):
    client, completions, _ = make_client(
        tmp_path, [make_response("nope"), make_response("still nope")]
    )
    with pytest.raises(InvalidJSONError):
        client.complete("builder", MESSAGES, schema=Tiny, run_id="r4")
    assert len(completions.calls) == 2


def test_retry_on_429_then_success(tmp_path):
    client, completions, _ = make_client(
        tmp_path,
        [
            FakeHTTPError("slow down", 429),
            FakeHTTPError("slow down", 429),
            make_response('{"answer": "after", "n": 2}'),
        ],
    )
    result = client.complete("builder", MESSAGES, schema=Tiny, run_id="r5")
    assert result.answer == "after"
    assert len(completions.calls) == 3


def test_non_retryable_error_not_retried(tmp_path):
    client, completions, _ = make_client(
        tmp_path, [FakeHTTPError("bad request", 400)]
    )
    with pytest.raises(FakeHTTPError):
        client.complete("builder", MESSAGES, run_id="r6")
    assert len(completions.calls) == 1


def test_truncated_empty_content_raises(tmp_path):
    client, _, _ = make_client(tmp_path, [make_response("", finish_reason="length")])
    with pytest.raises(TruncatedResponseError):
        client.complete("builder", MESSAGES, run_id="r7")


def test_contributor_guard_blocks_external_code(tmp_path):
    client, completions, _ = make_client(
        tmp_path, [make_response('{"answer": "x", "n": 1}')]
    )
    with pytest.raises(ContributorGuardError):
        client.complete(
            "builder",
            MESSAGES,
            schema=Tiny,
            run_id="r8",
            metadata={"external_code": True},
        )
    assert completions.calls == []


def test_contributor_guard_allows_external_on_standard_model(tmp_path):
    client, completions, _ = make_client(
        tmp_path, [make_response('{"answer": "x", "n": 1}')]
    )
    result = client.complete(
        "builder",
        MESSAGES,
        model="muse-spark-1.3",
        schema=Tiny,
        run_id="r9",
        metadata={"external_code": True},
    )
    assert result.answer == "x"
    assert len(completions.calls) == 1


def test_contributor_guard_allows_internal_on_contributor(tmp_path):
    client, completions, _ = make_client(
        tmp_path, [make_response('{"answer": "x", "n": 1}')]
    )
    result = client.complete("builder", MESSAGES, schema=Tiny, run_id="r10")
    assert result.answer == "x"
    assert len(completions.calls) == 1


def test_hard_cap_blocks_before_call(tmp_path):
    # per-run cap of 0 means the run is already at its cap.
    client, completions, _ = make_client(
        tmp_path, [make_response('{"answer": "x", "n": 1}')], per_run=0.0
    )
    from proof.ledger import HardCapExceeded

    with pytest.raises(HardCapExceeded):
        client.complete("builder", MESSAGES, schema=Tiny, run_id="r11")
    assert completions.calls == []
