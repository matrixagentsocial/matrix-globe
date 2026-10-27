"""Proof-request parsing/formatting (mirror of web proof.ts)."""
import pytest

from proof.request_format import (
    MAX_CODE_CHARS,
    ProofRequestError,
    format_proof_request,
    parse_proof_request,
)

SPEC = "Implement add(a, b) returning a+b."
CODE = "def add(a, b):\n    return a + b\n"
TESTS = "from solution import add\n\ndef test_add():\n    assert add(1, 2) == 3\n"


def test_parse_full_request():
    req = parse_proof_request(format_proof_request(SPEC, CODE, TESTS))
    assert req.spec == SPEC
    assert req.code == CODE.rstrip()
    assert req.tests == TESTS.rstrip()


def test_parse_without_tests():
    req = parse_proof_request(format_proof_request(SPEC, CODE))
    assert req.tests is None


def test_parse_tests_heading_without_optional_suffix():
    body = format_proof_request(SPEC, CODE, TESTS).replace("## Tests (optional)", "## Tests")
    req = parse_proof_request(body)
    assert req.tests == TESTS.rstrip()


def test_format_round_trip_is_stable():
    body = format_proof_request(SPEC, CODE, TESTS)
    req = parse_proof_request(body)
    assert format_proof_request(req.spec, req.code, req.tests) == body


def test_missing_spec_rejected():
    with pytest.raises(ProofRequestError) as exc:
        parse_proof_request("## Code\n```python\nx = 1\n```\n")
    assert exc.value.reason == "missing_spec"


def test_missing_code_rejected():
    with pytest.raises(ProofRequestError) as exc:
        parse_proof_request("## Spec\ndo things\n")
    assert exc.value.reason == "missing_code"


def test_non_python_fence_rejected():
    body = "## Spec\ndo things\n\n## Code\n```java\nint x;\n```\n"
    with pytest.raises(ProofRequestError) as exc:
        parse_proof_request(body)
    assert exc.value.reason == "not_python"


def test_code_too_large_rejected():
    big = "x = '" + "a" * MAX_CODE_CHARS + "'\n"
    assert len(big) > MAX_CODE_CHARS
    with pytest.raises(ProofRequestError) as exc:
        parse_proof_request(format_proof_request(SPEC, big))
    assert exc.value.reason == "code_too_large"
