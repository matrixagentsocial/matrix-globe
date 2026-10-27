"""Proof rule (PLAN.md 5.2): a claim counts only if its test fails on the code.

Each claim's test runs in its own file in the sandbox, so one bad test
cannot hide the others.

- test fails (assertion or exception from the solution) -> PROVEN
- test passes -> UNPROVEN
- does not collect / syntax error / bad import / timeout -> INVALID
Bench only: a PROVEN test run against ``reference.py`` that passes is
VALID; if the reference also fails it is UNCONFIRMED.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from proof.pytest_runner import run_pytest, run_pytest_files

PROVEN = "PROVEN"
UNPROVEN = "UNPROVEN"
INVALID = "INVALID"
VALID = "VALID"
UNCONFIRMED = "UNCONFIRMED"


def _get(claim: Any, key: str, default: str = "") -> str:
    if isinstance(claim, dict):
        return str(claim.get(key, default) or default)
    return str(getattr(claim, key, default) or default)


def claim_id(claim: Any) -> str:
    return _get(claim, "id", "C?")


def test_filename(claim: Any) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in claim_id(claim)) or "claim"
    return f"test_claim_{safe}.py"


@dataclass
class ClaimProof:
    claim: Any
    status: str  # PROVEN | UNPROVEN | INVALID
    validity: str | None = None  # VALID | UNCONFIRMED | None (bench only)
    output: str = ""
    passed_on_current: bool = False

    @property
    def id(self) -> str:
        return claim_id(self.claim)

    @property
    def failing_test(self) -> str:
        return _get(self.claim, "failing_test")

    @property
    def test_sha256(self) -> str:
        return hashlib.sha256(self.failing_test.encode("utf-8")).hexdigest()

    def to_claim_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": _get(self.claim, "title"),
            "severity": _get(self.claim, "severity"),
            "spec_reference": _get(self.claim, "spec_reference"),
            "explanation": _get(self.claim, "explanation"),
            "failing_test": self.failing_test,
            "output": self.output[:2000],
            "proof_status": self.status,
            "status": self.status,
            "validity": self.validity,
        }


def _summarise(result: Any) -> str:
    parts: list[str] = []
    if result.timed_out:
        parts.append("timed out")
    for err in result.collection_errors:
        parts.append(f"collection: {err}")
    for t in result.tests:
        parts.append(f"{t.name}: {t.outcome} {t.message}".strip())
    if result.run is not None:
        tail = (result.run.stdout or "") + (result.run.stderr or "")
        if tail.strip():
            parts.append(tail.strip()[-1500:])
    return "\n".join(parts)[:4000]


def classify_run(result: Any) -> str:
    """Map one pytest run of a single claim test to PROVEN/UNPROVEN/INVALID."""
    if result.timed_out:
        return INVALID
    if result.collection_errors:
        return INVALID
    if not result.tests:
        return INVALID
    outcomes = [t.outcome for t in result.tests]
    if all(o == "passed" for o in outcomes):
        return UNPROVEN
    if any(o in ("failed", "error") for o in outcomes):
        # A test-level error that is not a collection error means the test
        # collected and then raised (from the solution or its asserts).
        return PROVEN
    return INVALID


def prove_claim(claim: Any, code: str, sandbox: Any, *, reference_code: str | None = None,
                timeout_s: float = 10.0, origin: str = "bench") -> ClaimProof:
    failing_test = _get(claim, "failing_test")
    fname = test_filename(claim)
    result = run_pytest(sandbox, code, {fname: failing_test}, timeout_s=timeout_s, origin=origin)
    status = classify_run(result)
    output = _summarise(result)
    validity: str | None = None
    if status == PROVEN and reference_code is not None:
        ref_result = run_pytest(sandbox, reference_code, {fname: failing_test},
                                timeout_s=timeout_s, origin=origin)
        # Reference passes -> VALID; reference also fails -> UNCONFIRMED.
        validity = VALID if ref_result.all_passed else UNCONFIRMED
        output += f"\n[bench validity vs reference: {validity}]"
    return ClaimProof(claim=claim, status=status, validity=validity, output=output,
                      passed_on_current=(status == UNPROVEN))


def prove_claims(claims: list[Any], code: str, sandbox: Any, *, reference_code: str | None = None,
                 timeout_s: float = 10.0, origin: str = "bench") -> list[ClaimProof]:
    """Prove each claim independently (own file per claim)."""
    return [prove_claim(c, code, sandbox, reference_code=reference_code,
                        timeout_s=timeout_s, origin=origin) for c in claims]


def prove_claim_modules(claim: Any, modules: dict[str, str], sandbox: Any, *,
                        reference_modules: dict[str, str] | None = None,
                        timeout_s: float = 10.0, origin: str = "bench") -> ClaimProof:
    """Proof rule for a PR package: test runs against all modules."""
    failing_test = _get(claim, "failing_test")
    fname = test_filename(claim)
    result = run_pytest_files(sandbox, modules, {fname: failing_test},
                              timeout_s=timeout_s, origin=origin)
    status = classify_run(result)
    output = _summarise(result)
    validity: str | None = None
    if status == PROVEN and reference_modules is not None:
        ref_result = run_pytest_files(sandbox, reference_modules, {fname: failing_test},
                                      timeout_s=timeout_s, origin=origin)
        validity = VALID if ref_result.all_passed else UNCONFIRMED
        output += f"\n[bench validity vs reference: {validity}]"
    return ClaimProof(claim=claim, status=status, validity=validity, output=output,
                      passed_on_current=(status == UNPROVEN))


def prove_claims_modules(claims: list[Any], modules: dict[str, str], sandbox: Any, *,
                         reference_modules: dict[str, str] | None = None,
                         timeout_s: float = 10.0, origin: str = "bench") -> list[ClaimProof]:
    return [prove_claim_modules(c, modules, sandbox, reference_modules=reference_modules,
                                timeout_s=timeout_s, origin=origin) for c in claims]
