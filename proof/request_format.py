"""Proof-request markdown format (PLAN.md 5.8, mirror of web proof.ts).

A request body has ``## Spec``, ``## Code`` with a ```python fenced
block, and an optional ``## Tests`` / ``## Tests (optional)`` section
with a ```python fenced block. ``format_proof_request`` mirrors
``formatProofRequest`` in ``apps/web/src/lib/proof.ts`` byte for byte so
parse/format round-trips.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

MAX_CODE_CHARS = 20000

_HEADING_RE = re.compile(r"^##\s+(Spec|Code|Tests(?:\s*\(optional\))?)\s*$")
_FENCE_RE = re.compile(r"```([A-Za-z0-9_+.-]*)\s*\n(.*?)```", re.DOTALL)


class ProofRequestError(ValueError):
    """Malformed request; ``reason`` is a stable machine-readable code."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


@dataclass
class ProofRequest:
    spec: str
    code: str
    tests: str | None = None


def format_proof_request(spec: str, code: str, tests: str | None = None) -> str:
    """Format a request body exactly like the web ``formatProofRequest``."""
    parts = ["## Spec", spec.strip(), "", "## Code", "```python",
             code.rstrip(), "```"]
    if tests and tests.strip():
        parts += ["", "## Tests (optional)", "```python", tests.rstrip(), "```"]
    return "\n".join(parts) + "\n"


# Friendly alias matching the web name.
formatProofRequest = format_proof_request


def _sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []
    for line in (body or "").splitlines():
        match = _HEADING_RE.match(line.strip())
        if match:
            if current is not None:
                sections[current] = "\n".join(buf)
            heading = match.group(1)
            current = "Tests" if heading.startswith("Tests") else heading
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf)
    return sections


def _fenced_python(section: str, *, section_name: str) -> str:
    match = _FENCE_RE.search(section)
    if match is None:
        raise ProofRequestError(
            "missing_code_fence" if section_name == "Code" else "missing_tests_fence",
            f"The ## {section_name} section needs a ```python fenced block.",
        )
    language = (match.group(1) or "").lower()
    if language not in ("python", "py"):
        raise ProofRequestError(
            "not_python",
            f"The ## {section_name} section must use a ```python fence, "
            f"got {language or '(no language)'!r}.",
        )
    return match.group(2).rstrip()


def parse_proof_request(body: str) -> ProofRequest:
    """Parse a request body; raise ProofRequestError when malformed."""
    sections = _sections(body or "")
    if "Spec" not in sections or not sections["Spec"].strip():
        raise ProofRequestError("missing_spec", "The request needs a non-empty ## Spec section.")
    if "Code" not in sections:
        raise ProofRequestError("missing_code", "The request needs a ## Code section.")
    code = _fenced_python(sections["Code"], section_name="Code")
    if not code.strip():
        raise ProofRequestError("missing_code", "The ## Code fenced block is empty.")
    if len(code) > MAX_CODE_CHARS:
        raise ProofRequestError(
            "code_too_large",
            f"The code is {len(code)} characters; the limit is {MAX_CODE_CHARS}.",
        )
    tests: str | None = None
    if "Tests" in sections and sections["Tests"].strip():
        tests = _fenced_python(sections["Tests"], section_name="Tests")
        if not tests.strip():
            tests = None
    return ProofRequest(spec=sections["Spec"].strip(), code=code, tests=tests)


# Friendly alias matching the web naming style.
parseProofRequest = parse_proof_request
