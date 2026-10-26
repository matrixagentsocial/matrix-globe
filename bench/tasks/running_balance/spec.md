# Running balance over sorted transactions

Implement in `solution.py`:

```python
def running_balance(transactions: list[dict], opening_balance: str) -> list[dict]
def closing_balance(transactions: list[dict], opening_balance: str) -> Decimal
```

Rules (all explicit; the traps are in these details):

1. `opening_balance` is a decimal string parsed with `decimal.Decimal`. It must be a string, finite, and have at most 2 decimal places (it may be negative, zero, or positive). Otherwise raise `ValueError` (including `"abc"`, `""`, `"NaN"`, `"Infinity"`, `"10.005"`, and non-string inputs). It is treated as quantized to exactly 2 decimal places.
2. `transactions` must be a `list`. A non-list raises `ValueError`. Each element must be a `dict` containing at least the keys `"id"`, `"value_date"`, `"booking_date"` and `"amount"`; a missing key or a non-dict element raises `ValueError`. Extra keys are ignored and do not appear in the output.
3. `"id"` must be a non-empty string, else `ValueError`. Ids must be unique across the whole list (exact string comparison); a duplicate id raises `ValueError`.
4. `"value_date"` and `"booking_date"` must each be strings in exactly `YYYY-MM-DD` format (4-digit year, 2-digit month, 2-digit day, hyphen separators) naming a valid calendar date. Anything else (for example `"2024-13-01"`, `"2024-02-30"`, `"01/02/2024"`, `"2024-1-1"`, or a non-string) raises `ValueError`.
5. `"amount"` must be a string parsed with `Decimal`, finite, with at most 2 decimal places. It is signed: credits are positive and debits are negative. Zero (`"0"`, `"0.00"`, `"-0.00"`) is allowed. Anything else (for example `"10.005"`, `"abc"`, `""`, `"NaN"`, a non-string such as a float or int) raises `ValueError`. Amounts are normalized to exactly 2 decimal places in the output (so `"-0.00"` becomes `Decimal("0.00")`).
6. Neither function mutates its input: the input list and its dicts are unchanged after the call.
7. Transactions are sorted by `value_date` ascending, then `booking_date` ascending, then `id` ascending using plain string comparison. The date strings sort the same lexicographically as chronologically because of the fixed format in Rule 4.
8. `running_balance` returns one output row per input transaction, in the sorted order of Rule 7. Each row is exactly `{"id": str, "value_date": str, "booking_date": str, "amount": Decimal, "balance": Decimal}`, where `value_date` and `booking_date` are the original strings, `amount` is the normalized amount (Rule 5), and `balance` is the running balance after applying that transaction: `opening_balance + sum of amounts of all rows up to and including this one`, in sorted order.
9. Every `amount` and `balance` in the output is a `Decimal` quantized to exactly 2 decimal places. Never use `float`.
10. If `transactions` is empty, `running_balance` returns `[]` and `closing_balance` returns the opening balance quantized to 2 decimal places.
11. `closing_balance` returns a single `Decimal` quantized to exactly 2 decimal places: the `balance` of the last row of `running_balance`, or the quantized opening balance when the list is empty. It applies exactly the same validation and sorting as `running_balance`.
12. Use only the stdlib.

Worked example: with opening `"100.00"` and transactions
`{"id": "b", "value_date": "2024-01-02", "booking_date": "2024-01-03", "amount": "10.00"}`,
`{"id": "a", "value_date": "2024-01-02", "booking_date": "2024-01-02", "amount": "-30.00"}`,
`{"id": "c", "value_date": "2024-01-01", "booking_date": "2024-01-05", "amount": "5.00"}`,
the sorted order is `c` (earliest value_date), then `a` (same value_date as `b` but earlier booking_date), then `b`. Balances are `105.00`, `75.00`, `85.00`, and `closing_balance` is `Decimal("85.00")`.
