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
    if "# === " in code:
        prompt += ("\n\nThe code above is a package of modules (see the `# === name ===` "
                   "headers). Your tests may import from those modules, not from `solution`.\n")
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


def generate_self_tests_modules(client: Any, spec: str, modules: dict[str, str], *,
                                run_id: str | None = None, model: str | None = None,
                                effort: str | None = None) -> str:
    from proof.package import format_package
    tests = generate_self_tests(client, spec, format_package(modules), run_id=run_id,
                                model=model, effort=effort)
    return tests


def refine_code_modules(client: Any, spec: str, modules: dict[str, str], self_tests: str,
                        failing_output: str, *, run_id: str | None = None,
                        model: str | None = None, effort: str | None = None) -> dict[str, str]:
    """Self-refine revise step for a PR package; returns all modules."""
    from proof.package import format_package
    from proof.roles.builder import modules_from_result
    module_names = sorted(modules)
    context = (f"Revise now (step 2). Your tests:\n```python\n{self_tests}\n```\n"
               f"Failing output:\n```\n{failing_output[:3000]}\n```\n"
               "Return every module in `modules`, one item per file, using exactly "
               "these names: " + ", ".join(f"`{n}`" for n in module_names) + ".")
    prompt = _prompt(spec, format_package(modules), context)
    prompt = prompt.replace("return the complete revised `solution.py` in `code`",
                            "return every module in `modules`")
    extra: dict[str, Any] = {}
    if model is not None:
        extra["model"] = model
    if effort is not None:
        extra["effort"] = effort
    schema = {
        "type": "object",
        "properties": {
            "modules": {"type": "array", "items": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "code": {"type": "string"}},
                "required": ["name", "code"], "additionalProperties": False}},
            "change_summary": {"type": "string"},
        },
        "required": ["modules", "change_summary"],
        "additionalProperties": False,
    }
    result = client.complete("self_refine", [{"role": "user", "content": prompt}],
                             schema=schema, run_id=run_id, max_tokens=MAX_TOKENS,
                             metadata={"origin": "bench"}, **extra)
    return modules_from_result(result, module_names)


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
