# Pull request pr_dev_3

This package contains three modules: `task_a.py`, `task_b.py`, `task_c.py`. Each section below is the spec for one module. Where a section says `solution.py`, it means that section's module file. Implement and review the package as a whole; a defect may be in any module.


## Module `task_a.py` — task `number_parsing`

# Parse European / US number formats

Implement in `solution.py`:

```python
def parse_number(text: str) -> Decimal
```

Parse a human-written number and return a `decimal.Decimal`.
Invalid input raises `ValueError`. Rules (all explicit; the traps are
in these details):

1. Strip leading/trailing whitespace (space, tab, non-breaking space
   `"\u00a0"`). Empty after stripping raises `ValueError`.
2. Parentheses: if the stripped text starts with `(` and ends with
   `)`, the number is negative and the parentheses are removed. A
   leading `+`/`-` sign **inside** or outside the parentheses combined
   with parentheses raises `ValueError` (so `"-(1,5)"` and `"(-1,5)"`
   are invalid). Unbalanced parentheses raise `ValueError`.
3. Without parentheses, one optional leading `+` or `-` sign is allowed.
   A sign anywhere else, or two signs, raises `ValueError`.
4. Interior spaces (space and `"\u00a0"`) are thousands separators:
   remove them. Example: `"-1 234,56"` -> `Decimal("-1234.56")`.
   After removal the remaining characters must be digits, `.` or `,`
   only; anything else raises `ValueError`. There must be at least
   one digit.
5. Decimal / thousands separator decision (after sign, parentheses
   and spaces are handled):
   - Both `.` and `,` present: the **rightmost** of the two is the
     decimal separator, the other is the thousands separator.
     `"1.234,56"` -> `1234.56`; `"1,234.56"` -> `1234.56`;
     `"1.234.567,89"` -> `1234567.89`.
   - Only `,` present: if there is more than one `,`, they are
     thousands separators (`"1,234,567"` -> `1234567`). If there is
     exactly one `,`, it is the decimal separator
     (`"1,234"` -> `Decimal("1.234")`, `"12,5"` -> `12.5`).
   - Only `.` present: if there is more than one `.`, they are
     thousands separators (`"1.234.567"` -> `1234567`). If there is
     exactly one `.`, it is the decimal separator
     (`"1.234"` -> `Decimal("1.234")`, `"12.5"` -> `12.5`).
   - Neither present: a plain integer.
6. Thousands grouping is validated whenever a thousands separator is
   used: the first group has 1-3 digits and every later group has
   exactly 3 digits, and the decimal part (if any) has at least 1
   digit. `"12,34,56"`, `"1.23.456"`, `"1,2345.6"` (bad grouping of
   the thousands part) and `"1,234."` raise `ValueError`. A trailing
   or leading decimal separator with no digits on one side (`".5"`
   is allowed only as a decimal with an empty integer part? No:)
   `".5"`, `"5."`, `",5"` and `"5,"` all raise `ValueError`; the
   integer part and the decimal part must both be non-empty.
7. Never use `float`. Use only the stdlib.


## Module `task_b.py` — task `receivables_aging`

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


## Module `task_c.py` — task `split_installments`

# Split an amount into N installments that sum exactly

Implement in `solution.py`:

```python
def split_installments(total: str, n: int) -> list[Decimal]
```

Rules (all explicit; the traps are in these details):

1. `total` is a decimal string such as `"100.00"`. Parse it with
   `decimal.Decimal`. It must be finite, must be `>= 0`, and must have
   at most 2 decimal places (cents). Inputs such as `"10.005"`,
   `"-1.00"`, `"abc"`, `""`, `"NaN"` or `"Infinity"` raise `ValueError`.
2. `n` must be an integer `>= 1`. `n == 0`, negative `n` and non-integer
   `n` (for example `2.5` or `"3"`) raise `ValueError`. (`bool` is not
   accepted as an integer.)
3. Return a list of exactly `n` `Decimal` values, each quantized to
   exactly 2 decimal places (exponent `-2`, so `str()` shows cents).
4. The installments must sum **exactly** to `total`. Each installment
   differs from any other by at most `Decimal("0.01")`.
5. Distribution is by largest remainder with deterministic order: the
   unavoidable extra cents go one each to the **first** installments.
   Example: `"100.00"` in 3 -> `[33.34, 33.33, 33.33]`;
   `"0.05"` in 2 -> `[0.03, 0.02]`; `"0.01"` in 3 -> `[0.01, 0.00, 0.00]`.
6. `"0.00"` in any valid `n` returns `n` copies of `Decimal("0.00")`.
   `n == 1` returns `[Decimal(total)]` quantized to cents.
7. Use only the stdlib. Never use `float` for the money maths.
