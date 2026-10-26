# Find duplicate payments

Implement in `solution.py`:

```python
def find_duplicate_payments(payments: list[dict], window_days: int = 7) -> list[dict]
```

Rules (all explicit; the traps are in these details):

1. Each payment is a dict `{"id": str, "date": "YYYY-MM-DD", "vendor": str, "amount": str, "currency": str}`. Missing keys, non-dict entries, or wrong types (non-string `id`/`date`/`vendor`/`amount`/`currency`) raise `ValueError`. An empty `payments` list returns `[]`.
2. `id` must be a non-empty string. Two payments with the same `id` raise `ValueError`, even if every other field differs.
3. `date` must be a valid calendar date in exactly `YYYY-MM-DD` format (parsed strictly, e.g. `"2024-02-30"` and `"01/02/2024"` raise `ValueError`). `amount` must be a finite `Decimal` string with at most 2 decimal places (e.g. `"abc"`, `""`, `"NaN"`, `"Infinity"`, `"10.005"` raise `ValueError`). Amounts are signed: `"-50.00"` is allowed.
4. `window_days` must be an `int` (not `bool`) with `0 <= window_days <= 365`, otherwise `ValueError`. The default is `7`.
5. Vendor normalization is applied in exactly this order: (a) uppercase the string; (b) remove every character in the exact set `.,;:'"()/-` (period, comma, semicolon, colon, apostrophe, double quote, left parenthesis, right parenthesis, slash, hyphen); (c) collapse every run of internal whitespace to a single space and trim leading/trailing whitespace; (d) split on single spaces into tokens; (e) repeatedly drop the last token while it is in `{"SA","SL","SLU","LTD","LIMITED","INC","LLC","GMBH","BV","NV","SAS"}`, stopping when the last token is not in that set or no tokens remain. Example: `"ACME, S.L."` -> remove punctuation -> `"ACME SL"` -> drop `SL` -> `"ACME"`. Example: `"Foo-Bar / B.V."` -> `"FOOBAR BV"` -> drop `BV` -> `"FOOBAR"`. Example: `"SA Holdings"` stays `"SA HOLDINGS"` (only trailing tokens are dropped).
6. If the normalized vendor is empty (e.g. vendor `".,-"`, whose characters are all removed, or `"LTD"` alone, whose only token is dropped as a legal-form suffix) raise `ValueError`.
7. Currency is normalized by trimming whitespace and uppercasing (e.g. `" eur "` -> `"EUR"`). An empty currency after trimming raises `ValueError`.
8. Two distinct payments are directly duplicate if all hold: normalized vendors are equal (and non-empty), normalized currencies are equal, amounts are exactly equal as `Decimal` (signed, so `"-50.00"` is never a duplicate of `"50.00"`, while `"50.0"` equals `"50.00"` numerically), and the absolute difference between their dates is `<= window_days` days. Exactly `window_days` days apart counts; `window_days + 1` days does not.
9. Groups are the connected components of the direct-duplicate graph with size `>= 2`. Duplication is transitive through chains: if A-B are within the window and B-C are within the window, A, B and C form one group even if A-C are more than `window_days` apart. Every payment belongs to at most one group. Payments in no group are omitted.
10. Each returned group is `{"payment_ids": [...], "vendor": <normalized vendor>, "amount": <Decimal quantized to 2dp>, "currency": <normalized currency>}`. All payments in a group share the same normalized vendor, amount and currency, so those fields are the common values.
11. Inside a group, `payment_ids` are sorted by `(date, id)` ascending (date first, then the id string). Groups are sorted by `(earliest date in the group, first payment id in the group's sorted payment_ids)` ascending.
12. Worked example: payments `p1 2024-01-01 "Acme Ltd" "100.00" EUR`, `p2 2024-01-05 "ACME, LTD." "100.00" eur`, `p3 2024-01-20 "Other" "100.00" EUR` with the default window `7` return one group `{"payment_ids": ["p1", "p2"], "vendor": "ACME", "amount": Decimal("100.00"), "currency": "EUR"}`; `p3` is excluded (different vendor and too far from `p2`).
13. Use only the stdlib. Never use `float` for the money maths.
