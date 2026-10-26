# Receivables aging buckets

Implement in `solution.py`:

```python
def aging_buckets(invoices: list[dict], as_of: date) -> dict[str, Decimal]
```

Each invoice is a dict with keys:

- `"due_date"`: a `datetime.date` **or** an ISO string `"YYYY-MM-DD"`.
- `"amount"`: the outstanding amount as a decimal string such as
  `"100.00"` (a `Decimal` or `int` amount is also accepted; a `float`
  amount raises `ValueError`). Negative amounts (credit notes) are
  allowed and reduce their bucket.

Rules (all explicit; the traps are in these details):

1. `days_overdue = (as_of - due_date).days` using calendar days.
2. Buckets, by `days_overdue` (boundaries are part of the spec):
   - `"current"`: `days_overdue <= 0` (not yet due; due **today** is current)
   - `"1-30"`: `1 <= days_overdue <= 30` (day 30 is in this bucket)
   - `"31-60"`: `31 <= days_overdue <= 60`
   - `"61-90"`: `61 <= days_overdue <= 90` (day 90 is in this bucket)
   - `"90+"`: `days_overdue >= 91` (day 91, not day 90)
3. The returned dict always has exactly these five keys, in this
   order: `"current"`, `"1-30"`, `"31-60"`, `"61-90"`, `"90+"`, even
   when a bucket is empty or `invoices` is empty.
4. Each bucket value is the exact sum of its invoice amounts as a
   `Decimal` quantized to exactly 2 decimal places (exponent `-2`).
   An empty bucket is `Decimal("0.00")`.
5. A missing `"due_date"` or `"amount"` key, an unparseable date
   string, or an unparseable/non-finite amount raises `ValueError`.
   `as_of` may be a `date` or an ISO `"YYYY-MM-DD"` string; anything
   else raises `ValueError`.
6. Use only the stdlib. Never use `float` for the money maths.
