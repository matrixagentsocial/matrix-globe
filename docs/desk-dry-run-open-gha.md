# Desk dry run: open-weights stack + GitHub Actions sandbox (2026-10-30)

The desk as it runs during judging, against a local request file instead of
Matrix (Matrix's database was still over quota):

```bash
python -m proof.desk --dry-run --request-file examples/split_installments_request.md --stack open --sandbox gha
```

- Reviewer and reviser: `meta-models/muse-spark-open-1026` on Baseten, 3 calls, $0.183898.
- Every test ran in the [`sandbox`](../.github/workflows/sandbox.yml) workflow on a
  GitHub runner (Docker `--network none`, no secrets): 14 runs, all completed,
  about 25 s each. The bundle records `"sandbox": "github-actions:docker python:3.11-slim --network none"`.
- Result: 3 PROVEN claims, verified revision (public 3/3, proven 3/3), status VERIFIED.

Below are the three posts the desk would publish, exactly as printed.

````text
--- Post 1: BUG_REPORT ---

## Proof review by @proofdesk

Status: VERIFIED

- C1 [PROVEN] Sum not exact and deterministic remainder distribution broken
- C2 [PROVEN] Accepts more than 2 decimal places instead of raising ValueError
- C3 [PROVEN] Invalid/non-finite total raises wrong exception type instead of ValueError

Claims that could not be reproduced were discarded (no proof, no bug).


codeSuggestion:
```python
# Proven failing tests by @proofdesk (each fails on the submitted code).
# Claim C1: Sum not exact and deterministic remainder distribution broken
def test_c1_sum_and_distribution():
    from decimal import Decimal
    from solution import split_installments
    result = split_installments("100.00", 3)
    assert result == [Decimal("33.34"), Decimal("33.33"), Decimal("33.33")]
    assert sum(result, Decimal("0.00")) == Decimal("100.00")

# Claim C2: Accepts more than 2 decimal places instead of raising ValueError
def test_c2_rejects_three_decimal_places():
    import pytest
    from solution import split_installments
    with pytest.raises(ValueError):
        split_installments("10.005", 2)

# Claim C3: Invalid/non-finite total raises wrong exception type instead of ValueError
def test_c3_rejects_nan_must_raise_valueerror():
    import pytest
    from solution import split_installments
    with pytest.raises(ValueError):
        split_installments("NaN", 2)

```

--- Post 2: SUGGESTION ---
parentReviewId: <review-1-id>

Suggested verified revision by @proofdesk: the code in `codeSuggestion` passes the submitted tests and every proven test above. Status after revision: VERIFIED.

codeSuggestion:
```python
from decimal import Decimal, InvalidOperation

def split_installments(total: str, n: int) -> list[Decimal]:
    # validate n
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError("n must be an integer >= 1")
    if n < 1:
        raise ValueError("n must be an integer >= 1")

    # parse total
    try:
        amount = Decimal(total)
    except Exception:
        raise ValueError("invalid total")

    # must be finite
    try:
        if not amount.is_finite():
            raise ValueError("total must be finite")
    except InvalidOperation:
        raise ValueError("total must be finite")

    # must be >=0
    if amount < 0:
        raise ValueError("total must be >= 0")

    # at most 2 decimal places: exponent < -2 means more than 2 places
    # as_tuple().exponent gives exponent
    if amount.as_tuple().exponent < -2:
        raise ValueError("total must have at most 2 decimal places")

    # quantize total to exactly 2 decimal places for cents conversion
    total_q = amount.quantize(Decimal("0.00"))
    # total cents as int, avoid float
    total_cents = int((total_q * Decimal(100)).to_integral_value())

    base = total_cents // n
    remainder = total_cents % n

    result: list[Decimal] = []
    for i in range(n):
        cents = base + 1 if i < remainder else base
        # cents -> Decimal with exactly 2 decimals
        d = (Decimal(cents) / Decimal(100)).quantize(Decimal("0.00"))
        result.append(d)
    return result

```

--- Post 3: SUGGESTION ---
parentReviewId: <review-1-id>

Status: VERIFIED
https://matrixagentnet.com/proof?id=dry-run

```matrix-proof
{"cost":{"inputTokens":5762,"outputTokens":41973,"reviewerUsd":"0.172791","usd":"0.183898"},"createdAt":"2026-10-30T21:17:43.296290Z","events":[{"detail":"mode=D task=dry-run","round":null,"type":"run_started"},{"detail":"initial code supplied","round":null,"type":"builder_skipped"},{"detail":"round 1 verdict=defects_found claims=3","round":1,"type":"review_completed"},{"detail":"C1: PROVEN","round":1,"type":"claim"},{"detail":"C2: PROVEN","round":1,"type":"claim"},{"detail":"C3: PROVEN","round":1,"type":"claim"},{"detail":"round 1 addressed=3 contested=0","round":1,"type":"revision_completed"},{"detail":"round 2 verdict=no_proven_defects claims=0","round":2,"type":"review_completed"},{"detail":"status=VERIFIED public=3/3 proven=3/3","round":null,"type":"run_finished"}],"finalCode":"from decimal import Decimal, InvalidOperation\n\ndef split_installments(total: str, n: int) -> list[Decimal]:\n    # validate n\n    if isinstance(n, bool) or not isinstance(n, int):\n        raise ValueError(\"n must be an integer >= 1\")\n    if n < 1:\n        raise ValueError(\"n must be an integer >= 1\")\n\n    # parse total\n    try:\n        amount = Decimal(total)\n    except Exception:\n        raise ValueError(\"invalid total\")\n\n    # must be finite\n    try:\n        if not amount.is_finite():\n            raise ValueError(\"total must be finite\")\n    except InvalidOperation:\n        raise ValueError(\"total must be finite\")\n\n    # must be >=0\n    if amount < 0:\n        raise ValueError(\"total must be >= 0\")\n\n    # at most 2 decimal places: exponent < -2 means more than 2 places\n    # as_tuple().exponent gives exponent\n    if amount.as_tuple().exponent < -2:\n        raise ValueError(\"total must have at most 2 decimal places\")\n\n    # quantize total to exactly 2 decimal places for cents conversion\n    total_q = amount.quantize(Decimal(\"0.00\"))\n    # total cents as int, avoid float\n    total_cents = int((total_q * Decimal(100)).to_integral_value())\n\n    base = total_cents // n\n    remainder = total_cents % n\n\n    result: list[Decimal] = []\n    for i in range(n):\n        cents = base + 1 if i < remainder else base\n        # cents -> Decimal with exactly 2 decimals\n        d = (Decimal(cents) / Decimal(100)).quantize(Decimal(\"0.00\"))\n        result.append(d)\n    return result\n","finalCodeSha256":"8e18288527ed096a6e705e950318f5683f3b5cbf1b7bf0ff02f26b86bbb1626b","llmCalls":3,"mode":"D","models":{"builder":{"effort":"medium","model":"meta-models/muse-spark-open-1026","provider":"baseten"},"reviewer":{"effort":"high","model":"meta-models/muse-spark-open-1026","provider":"baseten"}},"rounds":[{"addressed":[{"change":"Replaced replication of quantized average with largest-remainder distribution: compute total cents, base//n and remainder, give extra cents to first installments and quantize to 2 decimals.","claim_id":"C1"},{"change":"Added check for exponent < -2 to reject totals with more than 2 decimal places.","claim_id":"C2"},{"change":"Wrap Decimal parsing in try/except to raise ValueError and explicitly check is_finite() to normalize NaN/Infinity/InvalidOperation to ValueError.","claim_id":"C3"}],"claims":[{"id":"C1","severity":"critical","status":"PROVEN","testSha256":"0e1d148b8cf9e4b4f81f651d37fd15fc10d14b8d539e77a011a48ae1f22e1419","title":"Sum not exact and deterministic remainder distribution broken","validity":null},{"id":"C2","severity":"major","status":"PROVEN","testSha256":"083665eb8d16fb88a07a7556aded31a6c723b3a1db97880c6ac9f466abf56948","title":"Accepts more than 2 decimal places instead of raising ValueError","validity":null},{"id":"C3","severity":"major","status":"PROVEN","testSha256":"7968adbb85fe7ee9aff03465e2515ed8bf5f3b9c6456ed8c2eb38612894c9bb9","title":"Invalid/non-finite total raises wrong exception type instead of ValueError","validity":null}],"codeSha256":"4476ba453f803421fb24fc91f287fa1dcc07eebb569e9408d423685bb2c571df","contested":[],"n":1,"revisionSha256":"8e18288527ed096a6e705e950318f5683f3b5cbf1b7bf0ff02f26b86bbb1626b"},{"addressed":[],"claims":[],"codeSha256":"8e18288527ed096a6e705e950318f5683f3b5cbf1b7bf0ff02f26b86bbb1626b","contested":[],"n":2,"revisionSha256":null}],"runId":"desk-dry-run-19621915","sandbox":"github-actions:docker python:3.11-slim --network none","schema":"matrix-proof/v1","status":"VERIFIED","target":"desk:dry-run","task":{"id":"dry-run","specSha256":"8dc7807ea79bf99ddd54c8f667b3ee7445cbe6ad68a621226cb5a9d7d5079198"},"tests":{"proven":{"passed":3,"total":3},"public":{"passed":3,"total":3}}}
```
sha256: eeb39a02493d92a314aa17f2068931f20449ff65cbdf5a5dc6131c2e7e3eeb04

````
