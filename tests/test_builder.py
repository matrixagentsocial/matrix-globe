"""Builder role with a mocked LLM client (M1)."""
from proof.roles.builder import BUILDER_SCHEMA, build_solution


class FakeClient:
    def __init__(self):
        self.calls = []

    def complete(self, role, messages, **kwargs):
        self.calls.append((role, messages, kwargs))
        return {"code": "def f():\n    return 1\n"}


def test_builder_uses_bench_origin_and_schema():
    client = FakeClient()
    code = build_solution(client, "Implement f.", run_id="r-test")
    assert code == "def f():\n    return 1\n"
    role, messages, kwargs = client.calls[0]
    assert role == "builder"
    assert kwargs["metadata"] == {"origin": "bench"}
    assert kwargs["schema"] is BUILDER_SCHEMA
    assert kwargs["run_id"] == "r-test"
    assert "Implement f." in messages[0]["content"]


def test_builder_schema_is_strict_explicit_dict():
    assert BUILDER_SCHEMA["type"] == "object"
    assert BUILDER_SCHEMA["required"] == ["code"]
    assert BUILDER_SCHEMA["additionalProperties"] is False
    assert list(BUILDER_SCHEMA["properties"]) == ["code"]
