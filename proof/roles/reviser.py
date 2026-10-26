"""Reviser role: code + proven claims -> Revision (5.3). Role ``reviser`` (Spark)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

PROMPT_PATH = Path(__file__).parent / "prompts" / "reviser.md"
REVISER_MAX_TOKENS = 32768

_ADDRESSED_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"claim_id": {"type": "string"}, "change": {"type": "string"}},
    "required": ["claim_id", "change"],
    "additionalProperties": False,
}
_CONTESTED_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"claim_id": {"type": "string"}, "reason": {"type": "string"}},
    "required": ["claim_id", "reason"],
    "additionalProperties": False,
}
REVISER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "code": {"type": "string"},
        "addressed": {"type": "array", "items": _ADDRESSED_SCHEMA},
        "contested": {"type": "array", "items": _CONTESTED_SCHEMA},
    },
    "required": ["code", "addressed", "contested"],
    "additionalProperties": False,
}
# Schema for revising from free-form feedback (condition E): same code
# contract, feedback is prose rather than claim ids.
FREEFORM_REVISION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "code": {"type": "string"},
        "addressed": {"type": "array", "items": {"type": "string"}},
        "contested": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["code", "addressed", "contested"],
    "additionalProperties": False,
}


class AddressedItem(BaseModel):
    claim_id: str
    change: str = ""


class ContestedItem(BaseModel):
    claim_id: str
    reason: str = ""


class Revision(BaseModel):
    code: str
    addressed: list[AddressedItem] = Field(default_factory=list)
    contested: list[ContestedItem] = Field(default_factory=list)


def _claim_text(claims: list[Any]) -> str:
    parts: list[str] = []
    for c in claims:
        get = (lambda k: c.get(k, "")) if isinstance(c, dict) else (lambda k: getattr(c, k, ""))
        output = get("output") if not isinstance(c, dict) else c.get("output", "")
        proof = get("proof_status") if isinstance(c, dict) else getattr(c, "proof_status", "")
        parts.append(
            f"### Claim {get('id')} [{get('severity')}] {get('title')}\n"
            f"Spec reference: {get('spec_reference')}\n"
            f"Explanation: {get('explanation')}\n"
            f"Proof status: {proof}\n"
            f"Failing test:\n```python\n{get('failing_test')}\n```\n"
            f"Failing output:\n```\n{str(output)[:2000]}\n```"
        )
    return "\n\n".join(parts) if parts else "(none)"


def _coerce(result: Any, *, freeform: bool = False) -> Revision:
    if isinstance(result, dict):
        data = dict(result)
    else:
        data = result.model_dump()  # type: ignore[attr-defined]
    if freeform:
        data["addressed"] = [
            {"claim_id": str(a), "change": ""} if not isinstance(a, dict) else a
            for a in data.get("addressed", [])
        ]
        data["contested"] = [
            {"claim_id": str(a), "reason": ""} if not isinstance(a, dict) else a
            for a in data.get("contested", [])
        ]
    rev = Revision.model_validate(data)
    if not rev.code or not rev.code.strip():
        raise ValueError(f"reviser returned no usable code field: {result!r}")
    return rev


def revise_code(client: Any, spec: str, code: str, proven_claims: list[Any], *,
                run_id: str | None = None, model: str | None = None,
                effort: str | None = None, max_tokens: int = REVISER_MAX_TOKENS) -> Revision:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    prompt = (template.replace("{spec}", spec).replace("{code}", code)
              .replace("{claims}", _claim_text(proven_claims)))
    extra: dict[str, Any] = {}
    if model is not None:
        extra["model"] = model
    if effort is not None:
        extra["effort"] = effort
    result = client.complete("reviser", [{"role": "user", "content": prompt}],
                             schema=REVISER_SCHEMA, run_id=run_id, max_tokens=max_tokens,
                             metadata={"origin": "bench"}, **extra)
    return _coerce(result)


def revise_from_freeform(client: Any, spec: str, code: str, feedback: str, *,
                         run_id: str | None = None, model: str | None = None,
                         effort: str | None = None, max_tokens: int = REVISER_MAX_TOKENS) -> Revision:
    prompt = (
        "You are the reviser for Matrix Globe. Fix the code below using the "
        "reviewer's free-text feedback. Return the complete revised solution.py.\n\n"
        f"## Task spec\n\n{spec}\n\n## Current code (solution.py)\n\n```python\n{code}\n```\n\n"
        f"## Reviewer feedback (free text, unverified)\n\n{feedback}\n"
    )
    extra: dict[str, Any] = {}
    if model is not None:
        extra["model"] = model
    if effort is not None:
        extra["effort"] = effort
    result = client.complete("reviser", [{"role": "user", "content": prompt}],
                             schema=FREEFORM_REVISION_SCHEMA, run_id=run_id,
                             max_tokens=max_tokens, metadata={"origin": "bench"}, **extra)
    return _coerce(result, freeform=True)
