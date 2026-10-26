# Idempotent payment ledger

Implement in `solution.py`:

```python
def process_payments(requests: list[dict]) -> dict
```

Rules:

1. `requests` must be a list of dicts, processed strictly in the given order. A non-list argument raises `ValueError`. An empty list returns `{"applied": [], "duplicates": [], "conflicts": [], "balances": {}}`.
2. Each request is a dict with fields `"key"`, `"account"`, `"currency"`, `"amount"` and `"reference"`. A missing field, or a request that is not a dict, raises `ValueError`.
3. Every request is validated before it is processed, including a repeat of an earlier key: an invalid repeat raises `ValueError` rather than being recorded as a duplicate or conflict (see rule 8).
4. Validation: `"key"` must be a non-empty string; `"account"` must be a non-empty string; `"currency"` must be a string of exactly 3 letters (A-Z, case-insensitive) and is normalized to upper case (so `"eur"` becomes `"EUR"`); `"amount"` must be a string parseable as `Decimal`, finite, strictly `> 0`, with at most 2 decimal places; `"reference"` must be a string (it may be empty). Any violation raises `ValueError`. Examples of invalid amounts: `"0.00"`, `"-1.00"`, `"10.005"`, `"abc"`, `""`, `"NaN"`.
5. Balances are kept per `(account, currency)` pair, starting at `Decimal("0.00")`. Account names are case-sensitive and are used exactly as given; only the currency is normalized.
6. The first occurrence of a key is applied: the amount is added to that `(account, currency)` balance, and an entry `{"key": key, "account": account, "currency": normalized_currency, "amount": D2, "balance_after": D2}` is appended to `"applied"` in processing order. `D2` means a `Decimal` quantized to exactly 2 decimal places (so `"10"` is recorded as `Decimal("10.00")` and `"10.5"` as `Decimal("10.50")`).
7. A later request whose key was already seen is compared with the first occurrence's payload: account (exactly as given), normalized currency, amount as a `Decimal` (so `"10.0"` and `"10.00"` are identical), and reference. If all four are identical, it is a duplicate: it is not applied, and its key is appended to `"duplicates"`. Each duplicate occurrence appends one entry, in the order the repeats occur.
8. If a later request with an already-seen key differs in any of those four payload fields, it is a conflict: it is not applied, and `{"key": key, "reason": "payload differs from first occurrence"}` (exactly that reason string) is appended to `"conflicts"`, one entry per conflict occurrence, in occurrence order. Later repeats are always compared against the first occurrence, never against a duplicate or conflict.
9. Duplicates and conflicts never change any balance, never add to `"applied"` and never create a balance entry.
10. The return value is `{"applied": [...], "duplicates": [...], "conflicts": [...], "balances": {...}}`. `"balances"` maps `"ACCOUNT:CCY"` (account exactly as given, then a colon, then the normalized currency) to the final `D2` balance, and contains an entry for every `(account, currency)` pair that had at least one applied payment. The `"balances"` dict is ordered by its keys sorted ascending (lexicographic).
11. All money values are `Decimal`, never `float`.
12. Worked example: requests `[{"key": "k1", "account": "A", "currency": "eur", "amount": "10.00", "reference": "r1"}, {"key": "k2", "account": "A", "currency": "EUR", "amount": "5.50", "reference": ""}, {"key": "k1", "account": "A", "currency": "EUR", "amount": "10.0", "reference": "r1"}]` give two applied entries with `balance_after` `Decimal("10.00")` and `Decimal("15.50")`, `duplicates == ["k1"]`, no conflicts, and `balances == {"A:EUR": Decimal("15.50")}`. Changing the third request's amount to `"11.00"` instead makes it a conflict with the exact reason above.
13. Use only the Python standard library.
