"""Self-refine role for condition C: builder writes its own tests, then revises."""
from __future__ import annotations

from pathlib import Path
from typing import Any

PROMPT_PATH = Path(__file__).parent / "prompts" / "self_refine.md"
MAX_TOKENS = 32768

SELF_TESTS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"tests": {"type": "string"}},
    "required": ["tests"],
    "additionalProperties": False,
}
SELF_REFINE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"code": {"type": "string"}, "change_summary": {"type": "string"}},
    "required": ["code", "change_summary"],
    "additionalProperties": False,
}


def _prompt(spec: str, code: str, context: str) -> str:
    t = PROMPT_PATH.read_text(encoding="utf-8")
    return t.replace("{spec}", spec).replace("{code}", code).replace("{context}", context)


def generate_self_tests(client: Any, spec: str, code: str, *, run_id: str | None = None,
                        model: str | None = None, effort: str | None = None) -> str:
    prompt = _prompt(spec, code, "Write your own tests now (step 1). Return only the test file in `tests`.")
    extra: dict[str, Any] = {}
    if model is not None:
        extra["model"] = model
    if effort is not None:
        extra["effort"] = effort
    result = client.complete("self_refine", [{"role": "user", "content": prompt}],
                             schema=SELF_TESTS_SCHEMA, run_id=run_id, max_tokens=MAX_TOKENS,
                             metadata={"origin": "bench"}, **extra)
    tests = result.get("tests") if isinstance(result, dict) else getattr(result, "tests", None)
    if not isinstance(tests, str) or not tests.strip():
        raise ValueError(f"self-refine returned no usable tests field: {result!r}")
    return tests


def refine_code(client: Any, spec: str, code: str, self_tests: str, failing_output: str, *,
                run_id: str | None = None, model: str | None = None,
                effort: str | None = None) -> str:
    context = (f"Revise now (step 2). Your tests:\n```python\n{self_tests}\n```\n"
               f"Failing output:\n```\n{failing_output[:3000]}\n```")
    prompt = _prompt(spec, code, context)
    extra: dict[str, Any] = {}
    if model is not None:
        extra["model"] = model
    if effort is not None:
        extra["effort"] = effort
    result = client.complete("self_refine", [{"role": "user", "content": prompt}],
                             schema=SELF_REFINE_SCHEMA, run_id=run_id, max_tokens=MAX_TOKENS,
                             metadata={"origin": "bench"}, **extra)
    code_out = result.get("code") if isinstance(result, dict) else getattr(result, "code", None)
    if not isinstance(code_out, str) or not code_out.strip():
        raise ValueError(f"self-refine returned no usable code field: {result!r}")
    return code_out
