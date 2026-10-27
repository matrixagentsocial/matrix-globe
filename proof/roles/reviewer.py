"""Reviewer role: spec + code + public results -> ReviewReport (5.2).

The strict ``json_schema`` is built as an explicit dict: every object has
``additionalProperties: false`` and lists all properties as required
(a pydantic ``model_json_schema()`` does not emit that). Role
``reviewer`` defaults to muse-wonder-1.0 / effort high from settings.
Fresh context on every call: one self-contained user message.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

PROMPT_PATH = Path(__file__).parent / "prompts" / "reviewer.md"
FREEFORM_PROMPT_PATH = Path(__file__).parent / "prompts" / "reviewer_freeform.md"

REVIEWER_MAX_TOKENS = 32768

CLAIM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "severity": {"type": "string", "enum": ["critical", "major", "minor"]},
        "title": {"type": "string"},
        "spec_reference": {"type": "string"},
        "explanation": {"type": "string"},
        "failing_test": {"type": "string"},
    },
    "required": ["id", "severity", "title", "spec_reference", "explanation", "failing_test"],
    "additionalProperties": False,
}

REVIEWER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["defects_found", "no_proven_defects"]},
        "claims": {"type": "array", "maxItems": 5, "items": CLAIM_SCHEMA},
        "untested_concerns": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["verdict", "claims", "untested_concerns"],
    "additionalProperties": False,
}


class ReviewClaim(BaseModel):
    id: str
    severity: str
    title: str
    spec_reference: str = ""
    explanation: str = ""
    failing_test: str


class ReviewReport(BaseModel):
    verdict: str
    claims: list[ReviewClaim] = Field(default_factory=list)
    untested_concerns: list[str] = Field(default_factory=list)


def _fill(template: str, **kw: str) -> str:
    out = template
    for k, v in kw.items():
        out = out.replace("{" + k + "}", v)
    return out


def build_reviewer_prompt(spec: str, code: str, public_results: str, history: str = "") -> str:
    return _fill(PROMPT_PATH.read_text(encoding="utf-8"), spec=spec, code=code,
                 public_results=public_results, history=history or "(none)")


def _coerce_report(result: Any) -> ReviewReport:
    if isinstance(result, ReviewReport):
        return result
    if isinstance(result, dict):
        return ReviewReport.model_validate(result)
    return ReviewReport.model_validate(result.model_dump())  # type: ignore[attr-defined]


def review_code(client: Any, spec: str, code: str, public_results: str, *,
                run_id: str | None = None, history: str = "",
                model: str | None = None, effort: str | None = None,
                module_names: list[str] | None = None,
                max_tokens: int = REVIEWER_MAX_TOKENS) -> ReviewReport:
    prompt = build_reviewer_prompt(spec, code, public_results, history)
    if module_names:
        prompt += (
            "\n\n## Package note\n\nThe code under review is a package of modules: "
            + ", ".join(f"`{m}`" for m in module_names)
            + ". In this package, each `failing_test` may import from those modules "
              "(not from `solution`). Claims may touch any module.\n")
    extra: dict[str, Any] = {}
    if model is not None:
        extra["model"] = model
    if effort is not None:
        extra["effort"] = effort
    result = client.complete("reviewer", [{"role": "user", "content": prompt}],
                             schema=REVIEWER_SCHEMA, run_id=run_id,
                             max_tokens=max_tokens, metadata={"origin": "bench"}, **extra)
    report = _coerce_report(result)
    # Enforce the <=5 claim limit even if a model over-reports.
    if len(report.claims) > 5:
        report = report.model_copy(update={"claims": report.claims[:5]})
    return report


def build_freeform_prompt(spec: str, code: str, public_results: str, history: str = "") -> str:
    return _fill(FREEFORM_PROMPT_PATH.read_text(encoding="utf-8"), spec=spec, code=code,
                 public_results=public_results, history=history or "(none)")


def review_freeform(client: Any, spec: str, code: str, public_results: str, *,
                    run_id: str | None = None, history: str = "",
                    model: str | None = None, effort: str | None = None,
                    module_names: list[str] | None = None,
                    max_tokens: int = REVIEWER_MAX_TOKENS) -> str:
    """Condition E: plain-text feedback, no schema, no tests, no proof rule."""
    prompt = build_freeform_prompt(spec, code, public_results, history)
    if module_names:
        prompt += (
            "\n\n## Package note\n\nThe code under review is a package of modules: "
            + ", ".join(f"`{m}`" for m in module_names)
            + ". Feedback may concern any module.\n")
    extra: dict[str, Any] = {}
    if model is not None:
        extra["model"] = model
    if effort is not None:
        extra["effort"] = effort
    result = client.complete("reviewer", [{"role": "user", "content": prompt}],
                             run_id=run_id, max_tokens=max_tokens,
                             metadata={"origin": "bench"}, **extra)
    if isinstance(result, str):
        return result
    return str(result)
