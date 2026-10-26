"""ProofBundle (PLAN.md 5.5): canonical JSON + SHA-256.

Canonical JSON: keys sorted, separators (",", ":"), ``ensure_ascii=False``,
UTF-8. ``sha256`` is the hex digest of that canonical string. The web
viewer recomputes it with ``crypto.subtle`` using the same rules; both
sides are tested against ``tests/fixtures/bundle_fixture.json``.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, Field, field_validator


def canonical_json(data: Any) -> str:
    """Canonical JSON string for a dict / pydantic model / plain value."""
    if isinstance(data, BaseModel):
        data = data.model_dump(mode="json")
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_of(data: Any) -> str:
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class TaskRef(BaseModel):
    id: str
    specSha256: str


class ModelRef(BaseModel):
    provider: str = "meta"
    model: str
    effort: str


class ModelsRef(BaseModel):
    builder: ModelRef
    reviewer: ModelRef


class BundleClaim(BaseModel):
    id: str
    title: str = ""
    severity: str = ""
    status: str = ""  # PROVEN | UNPROVEN | INVALID (or final pass/fail)
    validity: str | None = None  # VALID | UNCONFIRMED | None
    testSha256: str = ""


class BundleRound(BaseModel):
    n: int
    codeSha256: str = ""
    claims: list[BundleClaim] = Field(default_factory=list)
    revisionSha256: str | None = None
    addressed: list[dict[str, Any]] = Field(default_factory=list)
    contested: list[dict[str, Any]] = Field(default_factory=list)


class TestCounts(BaseModel):
    passed: int = 0
    total: int = 0


class BundleTests(BaseModel):
    public: TestCounts = Field(default_factory=TestCounts)
    proven: TestCounts = Field(default_factory=TestCounts)


def format_usd(value: float | int | str | None) -> str:
    """Format a USD amount as a string with exactly 6 decimals.

    Bundles are re-serialised in JavaScript by the web viewer; floats
    such as 7.48e-05 format differently in JS and Python and break the
    hash check, so money in the bundle is always this string form.
    """
    if value is None or value == "":
        return "0.000000"
    return f"{float(value):.6f}"


class BundleCost(BaseModel):
    inputTokens: int = 0
    outputTokens: int = 0
    usd: str = "0.000000"
    reviewerUsd: str = "0.000000"

    @field_validator("usd", "reviewerUsd", mode="before")
    @classmethod
    def _coerce_usd(cls, value: Any) -> str:
        return format_usd(value)


class BundleEvent(BaseModel):
    type: str
    round: int | None = None
    detail: str = ""


class ProofBundle(BaseModel):
    schema_: str = Field(default="matrix-proof/v1", alias="schema")
    runId: str
    createdAt: str
    task: TaskRef
    models: ModelsRef
    mode: str = "D"
    target: str = ""
    rounds: list[BundleRound] = Field(default_factory=list)
    events: list[BundleEvent] = Field(default_factory=list)
    finalCodeSha256: str = ""
    finalCode: str = ""
    tests: BundleTests = Field(default_factory=BundleTests)
    status: str = "FAILED"  # VERIFIED | PARTIAL | FAILED
    cost: BundleCost = Field(default_factory=BundleCost)
    sandbox: str = "local"
    llmCalls: int = 0

    model_config = {"populate_by_name": True}

    def model_dump_canonical(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=True)

    def canonical_json(self) -> str:
        return canonical_json(self.model_dump_canonical())

    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    # Convenience alias used by callers.
    def compute_sha256(self) -> str:
        return self.sha256()
