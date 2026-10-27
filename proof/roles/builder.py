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

_MODULE_ITEM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"name": {"type": "string"}, "code": {"type": "string"}},
    "required": ["name", "code"],
    "additionalProperties": False,
}
MODULES_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"modules": {"type": "array", "items": _MODULE_ITEM_SCHEMA}},
    "required": ["modules"],
    "additionalProperties": False,
}


def modules_from_result(result: Any, module_names: list[str]) -> dict[str, str]:
    """Coerce a {modules:[{name,code}]} result into a complete module dict."""
    data = result if isinstance(result, dict) else result.model_dump()
    items = data.get("modules") or []
    out: dict[str, str] = {}
    for item in items:
        if isinstance(item, dict) and item.get("name") in module_names:
            out[str(item["name"])] = str(item.get("code") or "")
    missing = [n for n in module_names if not out.get(n, "").strip()]
    if missing:
        raise ValueError(f"model returned no usable code for modules: {missing}")
    return {n: out[n] for n in module_names}


def build_modules(client: Any, spec: str, module_names: list[str], *,
                  run_id: str | None = None, max_tokens: int = BUILDER_MAX_TOKENS,
                  model: str | None = None, effort: str | None = None) -> dict[str, str]:
    """Condition B on a PR: regenerate every module from the spec."""
    prompt = build_prompt(spec)
    prompt += (
        "\n\n## Package output\n\nReturn every module of the package in `modules`, "
        "one item per file, using exactly these names: "
        + ", ".join(f"`{n}`" for n in module_names)
        + ". Each section of the spec that says `solution.py` means the module "
          "named in that section's heading. Use only the stdlib.\n")
    extra: dict[str, Any] = {}
    if model is not None:
        extra["model"] = model
    if effort is not None:
        extra["effort"] = effort
    result = client.complete("builder", [{"role": "user", "content": prompt}],
                             schema=MODULES_SCHEMA, run_id=run_id,
                             max_tokens=max_tokens, metadata={"origin": "bench"}, **extra)
    return modules_from_result(result, module_names)


def build_solution(
    client: Any,
    spec: str,
    *,
    run_id: str | None = None,
    max_tokens: int = BUILDER_MAX_TOKENS,
    model: str | None = None,
    effort: str | None = None,
) -> str:
    """Ask the builder model for a full ``solution.py`` and return its code.

    ``max_tokens`` is generous: reasoning tokens count inside it
    (Decisions of 2026-10-26), and the default client budget truncates
    hard specs to an empty reply.
    """
    prompt = build_prompt(spec)
    extra: dict[str, Any] = {}
    if model is not None:
        extra["model"] = model
    if effort is not None:
        extra["effort"] = effort
    result = client.complete(
        "builder",
        [{"role": "user", "content": prompt}],
        schema=BUILDER_SCHEMA,
        run_id=run_id,
        max_tokens=max_tokens,
        metadata={"origin": "bench"},
        **extra,
    )
    if isinstance(result, dict):
        code = result.get("code")
    else:
        code = getattr(result, "code", None)
    if not isinstance(code, str) or not code.strip():
        raise ValueError(f"builder returned no usable code field: {result!r}")
    return code
