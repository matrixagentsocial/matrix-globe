"""Builder role: spec -> full solution.py (PLAN.md section 4).

Uses :class:`~proof.llm.LLMClient` with role ``"builder"`` and
metadata ``origin="bench"``, so the cheap contributor model is only
ever fed our own benchmark specs. The result is returned through a
``json_schema`` with a single ``"code"`` string field; the schema is
built as an explicit dict with ``additionalProperties: false`` (a
pydantic ``model_json_schema()`` does not emit that for strict mode).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

PROMPT_PATH = Path(__file__).parent / "prompts" / "builder.md"

BUILDER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "code": {"type": "string"},
    },
    "required": ["code"],
    "additionalProperties": False,
}


def load_builder_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def build_prompt(spec: str) -> str:
    template = load_builder_prompt()
    if "{spec}" in template:
        return template.replace("{spec}", spec)
    return f"{template}\n\n## Task spec\n\n{spec}\n"


BUILDER_MAX_TOKENS = 32768


def build_solution(
    client: Any,
    spec: str,
    *,
    run_id: str | None = None,
    max_tokens: int = BUILDER_MAX_TOKENS,
) -> str:
    """Ask the builder model for a full ``solution.py`` and return its code.

    ``max_tokens`` is generous: reasoning tokens count inside it
    (Decisions of 2026-10-26), and the default client budget truncates
    hard specs to an empty reply.
    """
    prompt = build_prompt(spec)
    result = client.complete(
        "builder",
        [{"role": "user", "content": prompt}],
        schema=BUILDER_SCHEMA,
        run_id=run_id,
        max_tokens=max_tokens,
        metadata={"origin": "bench"},
    )
    if isinstance(result, dict):
        code = result.get("code")
    else:
        code = getattr(result, "code", None)
    if not isinstance(code, str) or not code.strip():
        raise ValueError(f"builder returned no usable code field: {result!r}")
    return code
