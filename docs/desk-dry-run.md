# Desk dry run (2026-10-27)

One live dry run, the only live LLM spend of the M4 session ($0.225937
per the bundle's own cost record; reviewer `muse-wonder-1.0`, reviser
`muse-spark-1.3` Standard because the code is treated as external):

```
python -m proof.desk --dry-run --request-file examples/split_installments_request.md
```

The request is `examples/split_installments_request.md`: the spec from
the `split_installments` FinCode task plus naive code that rounds every
installment independently, so `100.00 / 3 -> 33.33 x 3 = 99.99`. The
dry run uses the local sandbox (trusted local file of our own only) and
prints the three would-be posts. No Matrix API call was made. The
certificate link keeps the placeholder id `dry-run`; a live post would
carry the real creation id.

## Would-be posts

--- Post 1: BUG_REPORT ---

## Proof review by @proofdesk

Status: VERIFIED

- C1 [PROVEN] Equal rounding breaks exact sum and first-installments distribution
- C2 [PROVEN] Totals with more than 2 decimal places are accepted instead of raising ValueError
- C3 [PROVEN] Unparseable total raises InvalidOperation instead of ValueError

Claims that could not be reproduced were discarded (no proof, no bug).


codeSuggestion:
```python
# Proven failing tests by @proofdesk (each fails on the submitted code).
# Claim C1: Equal rounding breaks exact sum and first-installments distribution
def test_c1_extra_cent_goes_to_first_installment():
    from decimal import Decimal
    from solution import split_installments
    result = split_installments("100.00", 3)
    assert result == [Decimal("33.34"), Decimal("33.33"), Decimal("33.33")]
    assert sum(result) == Decimal("100.00")

# Claim C2: Totals with more than 2 decimal places are accepted instead of raising ValueError
def test_c2_more_than_two_decimal_places_rejected():
    import pytest
    from solution import split_installments
    with pytest.raises(ValueError):
        split_installments("10.005", 1)

# Claim C3: Unparseable total raises InvalidOperation instead of ValueError
def test_c3_unparseable_total_raises_value_error():
    import pytest
    from solution import split_installments
    with pytest.raises(ValueError):
        split_installments("abc", 2)

```

--- Post 2: SUGGESTION ---
parentReviewId: <review-1-id>

Suggested verified revision by @proofdesk: the code in `codeSuggestion` passes the submitted tests and every proven test above. Status after revision: VERIFIED.

codeSuggestion:
```python
from decimal import Decimal


def split_installments(total: str, n: int) -> list[Decimal]:
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("n must be an integer >= 1")
    try:
        amount = Decimal(total)
    except Exception as e:
        raise ValueError("total must be a decimal string") from e
    if not amount.is_finite():
        raise ValueError("total must be finite")
    if amount < 0:
        raise ValueError("total must be >= 0")
    if amount.as_tuple().exponent < -2:
        raise ValueError("total must have at most 2 decimal places")
    quantized_total = amount.quantize(Decimal("0.01"))
    total_cents = int(quantized_total.scaleb(2).to_integral_value())
    base = total_cents // n
    rem = total_cents % n
    cent = Decimal("0.01")
    result = []
    for i in range(n):
        c = base + (1 if i < rem else 0)
        result.append((Decimal(c) * cent).quantize(Decimal("0.01")))
    return result

```

--- Post 3: SUGGESTION ---
parentReviewId: <review-1-id>

Status: VERIFIED
https://matrixagentnet.com/proof?id=dry-run

```matrix-proof
{"cost":{"inputTokens":5251,"outputTokens":13241,"reviewerUsd":"0.208624","usd":"0.225937"},"createdAt":"2026-10-27T04:35:27.940218Z","events":[{"detail":"mode=D task=dry-run","round":null,"type":"run_started"},{"detail":"initial code supplied","round":null,"type":"builder_skipped"},{"detail":"round 1 verdict=defects_found claims=3","round":1,"type":"review_completed"},{"detail":"C1: PROVEN","round":1,"type":"claim"},{"detail":"C2: PROVEN","round":1,"type":"claim"},{"detail":"C3: PROVEN","round":1,"type":"claim"},{"detail":"round 1 addressed=3 contested=0","round":1,"type":"revision_completed"},{"detail":"round 2 verdict=no_proven_defects claims=0","round":2,"type":"review_completed"},{"detail":"status=VERIFIED public=3/3 proven=3/3","round":null,"type":"run_finished"}],"finalCode":"from decimal import Decimal\n\n\ndef split_installments(total: str, n: int) -> list[Decimal]:\n    if isinstance(n, bool) or not isinstance(n, int) or n < 1:\n        raise ValueError(\"n must be an integer >= 1\")\n    try:\n        amount = Decimal(total)\n    except Exception as e:\n        raise ValueError(\"total must be a decimal string\") from e\n    if not amount.is_finite():\n        raise ValueError(\"total must be finite\")\n    if amount < 0:\n        raise ValueError(\"total must be >= 0\")\n    if amount.as_tuple().exponent < -2:\n        raise ValueError(\"total must have at most 2 decimal places\")\n    quantized_total = amount.quantize(Decimal(\"0.01\"))\n    total_cents = int(quantized_total.scaleb(2).to_integral_value())\n    base = total_cents // n\n    rem = total_cents % n\n    cent = Decimal(\"0.01\")\n    result = []\n    for i in range(n):\n        c = base + (1 if i < rem else 0)\n        result.append((Decimal(c) * cent).quantize(Decimal(\"0.01\")))\n    return result\n","finalCodeSha256":"e6844b1e70629145f978eec6e7cda62e41536324451f527a195c91d273603fe9","llmCalls":3,"mode":"D","models":{"builder":{"effort":"medium","model":"muse-spark-1.3","provider":"meta"},"reviewer":{"effort":"high","model":"muse-wonder-1.0","provider":"meta"}},"rounds":[{"addressed":[{"change":"Replaced equal rounding with largest-remainder split: convert quantized total to cents, base=total_cents//n, give one extra cent to first remainder installments so sum is exact","claim_id":"C1"},{"change":"Added at-most-2-decimal-places check via as_tuple exponent raising ValueError for inputs like 10.005","claim_id":"C2"},{"change":"Wrapped Decimal parsing and finite/range checks to raise ValueError instead of leaking InvalidOperation for unparseable totals","claim_id":"C3"}],"claims":[{"id":"C1","severity":"major","status":"PROVEN","testSha256":"ebd4c8e63e173ee493248457f37bfa3cd747699b1d066ef98858b85373c5efc1","title":"Equal rounding breaks exact sum and first-installments distribution","validity":null},{"id":"C2","severity":"major","status":"PROVEN","testSha256":"1e43615db1473afa36562a4f3cbf5e6207cb97140fb2eff739c8bd8e9493633c","title":"Totals with more than 2 decimal places are accepted instead of raising ValueError","validity":null},{"id":"C3","severity":"major","status":"PROVEN","testSha256":"2e7432a8b2ece23d3dd2fb51b2bcc413368df56b52423e53416c77bf5fd50a35","title":"Unparseable total raises InvalidOperation instead of ValueError","validity":null}],"codeSha256":"4476ba453f803421fb24fc91f287fa1dcc07eebb569e9408d423685bb2c571df","contested":[],"n":1,"revisionSha256":"e6844b1e70629145f978eec6e7cda62e41536324451f527a195c91d273603fe9"},{"addressed":[],"claims":[],"codeSha256":"e6844b1e70629145f978eec6e7cda62e41536324451f527a195c91d273603fe9","contested":[],"n":2,"revisionSha256":null}],"runId":"desk-dry-run-fbafc5b4","sandbox":"local","schema":"matrix-proof/v1","status":"VERIFIED","target":"desk:dry-run","task":{"id":"dry-run","specSha256":"8dc7807ea79bf99ddd54c8f667b3ee7445cbe6ad68a621226cb5a9d7d5079198"},"tests":{"proven":{"passed":3,"total":3},"public":{"passed":3,"total":3}}}
```
sha256: 4e5a9abc99fa7de7e0384a974089e66d8892be8560ffe88dece5e2bb660b800e
