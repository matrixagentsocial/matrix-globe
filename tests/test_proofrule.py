"""Proof-rule classification with the local sandbox (no LLM)."""
from proof.proofrule import UNCONFIRMED, INVALID, PROVEN, UNPROVEN, VALID, prove_claim, prove_claims
from proof.sandbox.local import LocalSandbox

GOOD = "def add(a, b):\n    return a + b\n"
BAD = "def add(a, b):\n    return a - b\n"


def claim(cid, test):
    return {"id": cid, "severity": "major", "title": "t", "spec_reference": "s",
            "explanation": "e", "failing_test": test}


def test_proven_when_test_fails_on_code():
    p = prove_claim(claim("C1", "from solution import add\n\ndef test_c1():\n    assert add(1, 2) == 3\n"), BAD, LocalSandbox())
    assert p.status == PROVEN


def test_unproven_when_test_passes():
    p = prove_claim(claim("C1", "from solution import add\n\ndef test_c1():\n    assert add(1, 2) == 3\n"), GOOD, LocalSandbox())
    assert p.status == UNPROVEN


def test_invalid_syntax_error():
    p = prove_claim(claim("C1", "def test_c1(:\n    pass\n"), GOOD, LocalSandbox())
    assert p.status == INVALID


def test_invalid_bad_import():
    p = prove_claim(claim("C1", "from solution import nonexistent\n\ndef test_c1():\n    assert True\n"), GOOD, LocalSandbox())
    assert p.status == INVALID


def test_invalid_timeout():
    p = prove_claim(claim("C1", "import time\nfrom solution import add\n\ndef test_c1():\n    time.sleep(5)\n    assert add(1, 2) == 3\n"),
                    GOOD, LocalSandbox(), timeout_s=1.0)
    assert p.status == INVALID


def test_valid_when_reference_passes_proven_test():
    p = prove_claim(claim("C1", "from solution import add\n\ndef test_c1():\n    assert add(1, 2) == 3\n"),
                    BAD, LocalSandbox(), reference_code=GOOD)
    assert p.status == PROVEN and p.validity == VALID


def test_unconfirmed_when_reference_also_fails():
    p = prove_claim(claim("C1", "from solution import add\n\ndef test_c1():\n    assert add(1, 2) == 99\n"),
                    GOOD, LocalSandbox(), reference_code=GOOD)
    assert p.status == PROVEN and p.validity == UNCONFIRMED


def test_one_bad_test_cannot_hide_others():
    claims = [
        claim("C1", "def test_bad(:\n    pass\n"),
        claim("C2", "from solution import add\n\ndef test_c2():\n    assert add(1, 2) == 3\n"),
    ]
    proofs = prove_claims(claims, BAD, LocalSandbox(), reference_code=GOOD)
    assert [p.status for p in proofs] == [INVALID, PROVEN]
    assert proofs[1].validity == VALID
