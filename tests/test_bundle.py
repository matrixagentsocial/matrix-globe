"""ProofBundle canonical JSON + sha256 stability (M2)."""
import hashlib
import json
from pathlib import Path

from proof.bundle import ProofBundle, canonical_json, sha256_of

FIXTURE = Path("tests/fixtures/bundle_fixture.json")
EXPECTED = Path("tests/fixtures/bundle_fixture.sha256")


def test_fixture_hash_matches_expected():
    raw = FIXTURE.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    expected = EXPECTED.read_text(encoding="utf-8").strip()
    # canonical form of the parsed fixture hashes to the expected value
    assert hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest() == expected
    assert sha256_of(data) == expected
    # fixture file itself is stored in canonical form
    assert raw.decode("utf-8") == canonical_json(data)


def test_bundle_model_roundtrip_hash_stable():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    bundle = ProofBundle.model_validate(data)
    assert bundle.canonical_json() == canonical_json(data)
    assert bundle.sha256() == EXPECTED.read_text(encoding="utf-8").strip()
    # re-validating the dumped model yields the same hash
    again = ProofBundle.model_validate(bundle.model_dump(by_alias=True))
    assert again.sha256() == bundle.sha256()


def _assert_no_float(value, path="$"):
    assert not isinstance(value, float), f"float at {path}: {value!r}"
    if isinstance(value, dict):
        for key, item in value.items():
            _assert_no_float(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_float(item, f"{path}[{index}]")


def test_canonical_bundle_dump_contains_no_float():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    bundle = ProofBundle.model_validate(data)
    dumped = json.loads(bundle.canonical_json())
    _assert_no_float(dumped)
    # money fields are 6-decimal strings
    assert dumped["cost"]["usd"] == "0.010000"
    assert dumped["cost"]["reviewerUsd"] == "0.008000"


def test_canonical_json_sorted_no_spaces_unicode():
    s = canonical_json({"b": "café", "a": 1})
    assert s == '{"a":1,"b":"café"}'
