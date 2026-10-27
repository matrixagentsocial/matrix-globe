# Pull request pr_test_1

This package contains three modules: `task_a.py`, `task_b.py`, `task_c.py`. Each section below is the spec for one module. Where a section says `solution.py`, it means that section's module file. Implement and review the package as a whole; a defect may be in any module.


## Module `task_a.py` — task `allocate_ratios`

# Allocate an amount by ratios

Implement in `solution.py`:

```python
def allocate_by_ratios(total: str, ratios: list) -> list[Decimal]
```

Rules (all explicit; the traps are in these details):

1. `total` is a money string parsed with `Decimal`. It must be finite and have at most 2 decimal places, otherwise `ValueError` (e.g. `"abc"`, `""`, `"NaN"`, `"Infinity"`, `"10.005"`). It may be negative, zero, or positive.
2. `ratios` must be a non-empty list, otherwise `ValueError`. Each entry is either an `int` (not `bool`) or a decimal string parseable by `Decimal` (a `Decimal` instance is also accepted). `float` entries, `bool` entries, non-numeric strings and any other types raise `ValueError`.
3. Every weight must be finite and `>= 0`, and at least one weight must be `> 0`, otherwise `ValueError`. Weights may have any number of decimal places when given as strings (e.g. `"1.5"`).
4. Negative totals: allocate the absolute value of `total` by the rules below, then negate every resulting part. Example: `"-0.01"` by `[1, 1]` -> `[Decimal("-0.01"), Decimal("0.00")]` (the negated zero part is `Decimal("0.00")`, which equals `Decimal("-0.00")`); the parts still sum exactly to `total`. A total of `"0.00"` returns one `Decimal("0.00")` per ratio.
5. Method (on the absolute total, in cents): each entry's exact share is `total_cents * weight / total_weight`. Give each entry the floor (truncation toward zero, all values non-negative here) of its exact share in whole cents.
6. Distribute the remaining cents one each in order of largest fractional remainder. Ties in fractional remainder are broken by larger weight, then by lower index. Each entry receives at most one remainder cent per pass; the number of remaining cents is always less than the number of positive-weight entries, so one pass suffices.
7. Entries with weight `0` always get `Decimal("0.00")` and never receive a remainder cent: remainder cents go only to entries with weight `> 0`, even when a zero-weight entry's fractional remainder would be considered (it is exactly `0` and it is explicitly skipped).
8. Return a list of `Decimal` values in the original input order, each quantized to exactly 2 decimal places (exponent `-2`), summing exactly to `total`.
9. Examples: `"100.00"` by `[1, 1, 1]` -> `[Decimal("33.34"), Decimal("33.33"), Decimal("33.33")]` (equal remainders and equal weights tie-break to the lower index first); `"10.00"` by `[2, 1, 1]` -> `[Decimal("5.00"), Decimal("2.50"), Decimal("2.50")]`; `"0.05"` by `[1, 1]` -> `[Decimal("0.03"), Decimal("0.02")]`; `"100.00"` by `[0, 1, 0]` -> `[Decimal("0.00"), Decimal("100.00"), Decimal("0.00")]`.
10. Further example (weight tie-break): `"0.03"` by `[1, 2]` -> exact shares `1` cent and `2` cents with no remainder, giving `[Decimal("0.01"), Decimal("0.02")]`. And `"0.05"` by `[1, 2]`: exact shares are `1.666...` and `3.333...` cents, floors `1` and `3`, one remaining cent goes to the larger fractional remainder (`0.666...`, index 0), giving `[Decimal("0.02"), Decimal("0.03")]`.
11. Use only the stdlib. Never use `float` for the money maths.


## Module `task_b.py` — task `apr_apy`

# Convert between APR and APY

Implement in `solution.py`:

```python
def apr_to_apy(apr_percent: str, frequency: str) -> Decimal
def apy_to_apr(apy_percent: str, frequency: str) -> Decimal
```

Rules (all explicit; the traps are in these details):

1. `apr_percent` (for `apr_to_apy`) and `apy_percent` (for `apy_to_apr`) are decimal strings parsed with `decimal.Decimal`. Each must be a string, finite, and satisfy `value > Decimal("-100")`. Otherwise raise `ValueError` (including `"abc"`, `""`, `"NaN"`, `"Infinity"`, `"-100"`, values `< -100`, and non-string inputs). There is no upper bound and no limit on decimal places in the input.
2. `frequency` must be a string. It is matched case-insensitively (after stripping surrounding whitespace) against exactly these keys: `"annually"` (m=1), `"semiannually"` (m=2), `"quarterly"` (m=4), `"monthly"` (m=12), `"weekly"` (m=52), `"daily"` (m=365), `"continuous"` (continuous compounding). Any other value, or a non-string, raises `ValueError`.
3. Inputs and outputs are percents, not fractions: an input of `"12"` means 12%. Let `r = apr_percent / 100` and `y = apy_percent / 100` for the fraction forms.
4. For a periodic frequency with `m` periods per year, `apr_to_apy` computes `APY_percent = ((1 + r/m)**m - 1) * 100`.
5. For `"continuous"`, `apr_to_apy` computes `APY_percent = (exp(r) - 1) * 100`, using `Decimal.exp`.
6. For a periodic frequency, `apy_to_apr` is the exact inverse of Rule 4: `APR_percent = m * ((1 + y)**(1/m) - 1) * 100`.
7. For `"continuous"`, `apy_to_apr` computes `APR_percent = ln(1 + y) * 100`, using `Decimal.ln` (equivalently `ln(1 + APY/100) * 100`).
8. All internal arithmetic uses `Decimal` with precision 50 (for example via `localcontext`). Never use `float`.
9. Both functions return a `Decimal` quantized to exactly 6 decimal places with `ROUND_HALF_UP` (exponent `-6`, so for example `Decimal("12.682503")` and `Decimal("12.000000")`).
10. An input of `"0"` (or `"0.000000"`) returns `Decimal("0.000000")` for every valid frequency, in both directions.
11. Use only the stdlib.

Worked examples (verify these exactly):

- `apr_to_apy("12", "monthly") == Decimal("12.682503")`
- `apr_to_apy("12", "continuous") == Decimal("12.749685")`
- `apr_to_apy("12", "annually") == Decimal("12.000000")`
- `apr_to_apy("12", "quarterly") == Decimal("12.550881")`
- `apy_to_apr("12.682503", "monthly") == Decimal("12.000000")`
- `apy_to_apr("12.749685", "continuous") == Decimal("12.000000")`
- `apy_to_apr("10", "quarterly") == Decimal("9.645476")` and `apy_to_apr("10", "continuous") == Decimal("9.531018")`


## Module `task_c.py` — task `bank_reconciliation`

# Bank reconciliation matching

Implement in `solution.py`:

```python
def reconcile(book: list[dict], bank: list[dict], tolerance_days: int = 3) -> dict
```

Rules (all explicit; the traps are in these details):

1. `book` and `bank` must each be a `list` of `dict` entries, otherwise
   `ValueError` is raised. Extra keys in an entry are ignored.
2. Each entry has `"id"`, `"date"` and `"amount"`. `id` must be a
   non-empty string. Ids must be unique within each side: a duplicate id
   inside `book`, or inside `bank`, raises `ValueError`. The same id may
   appear on both sides.
3. `date` must be a string in exactly `YYYY-MM-DD` form (4-digit year,
   2-digit month and day) naming a real calendar date. Anything else
   raises `ValueError`.
4. `amount` must be a string parseable by `Decimal`, finite, with at
   most 2 decimal places (its value equals its quantization to cents).
   Anything else raises `ValueError`. Amounts are signed: matching uses
   the signed amount, so `Decimal("10.00")` never matches
   `Decimal("-10.00")`, and subset sums in rule 7 are signed sums.
5. `tolerance_days` must be an `int` (not `bool`) with
   `0 <= tolerance_days <= 31`, otherwise `ValueError` is raised. The
   date difference is the absolute difference in calendar days.
6. Phase 1 (one-to-one): a bank entry can match a book entry when their
   amounts are exactly equal (to the cent) and their date difference is
   `<= tolerance_days`. Consider every such candidate pair. Sort
   candidate pairs by: smallest date difference, then earliest bank
   date, then bank `id`, then book `id`. Walk the sorted pairs greedily,
   taking a pair only if both entries are still unused. Each entry is
   used at most once across both phases.
7. Phase 2 (one-to-many): for each remaining bank entry, considered in
   `(date, id)` order, look for a subset of 2 or 3 still-remaining book
   entries such that every book entry's date differs from the bank
   entry's date by `<= tolerance_days` and the book amounts sum exactly
   to the bank amount. Among all such subsets for that bank entry prefer:
   subset size 2 over size 3; then the smallest maximum date difference
   within the subset; then the lexicographically smallest tuple of the
   subset's sorted book ids. If a preferred subset exists, match it
   (marking those book entries used); otherwise the bank entry stays
   unmatched. Book entries consumed by an earlier bank entry in this
   phase are unavailable to later bank entries.
8. Return exactly `{"matches": [...], "unmatched_book": [...],
   "unmatched_bank": [...]}`. Each match is
   `{"bank_id": <bank id>, "book_ids": <sorted list of book ids>}`
   (a phase 1 match has a one-element `book_ids` list). `matches` is
   ordered by the matched bank entry's `(date, id)`, merging phase 1 and
   phase 2 matches into that single order.
9. `unmatched_book` is the list of unmatched book ids ordered by their
   entries' `(date, id)`; `unmatched_bank` is the same for bank entries.
10. Empty inputs are valid: two empty lists return
    `{"matches": [], "unmatched_book": [], "unmatched_bank": []}`.
11. Example (one-to-one): book `[{"id": "b1", "date": "2024-01-05",
    "amount": "100.00"}]`, bank `[{"id": "k1", "date": "2024-01-06",
    "amount": "100.00"}]` with tolerance 3 returns matches
    `[{"bank_id": "k1", "book_ids": ["b1"]}]` and no unmatched ids.
12. Example (one-to-many): one bank entry of `"100.00"` and remaining
    book entries of `"60.00"` and `"40.00"` (all dates within tolerance)
    match as one match whose `book_ids` are both book ids sorted.
13. Example (greedy order): if one book entry could match two bank
    entries with date differences 1 and 2, it matches the difference-1
    bank entry, and the other bank entry is unmatched (unless phase 2
    later matches it).
14. Only the stdlib may be used. Money uses `Decimal`, never `float`.
