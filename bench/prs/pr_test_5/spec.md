# Pull request pr_test_5

This package contains three modules: `task_a.py`, `task_b.py`, `task_c.py`. Each section below is the spec for one module. Where a section says `solution.py`, it means that section's module file. Implement and review the package as a whole; a defect may be in any module.


## Module `task_a.py` — task `progressive_tax`

# Progressive income tax with bracket breakdown

Implement in `solution.py`:

```python
def income_tax(income: str) -> Decimal
def tax_breakdown(income: str) -> list[dict]
def effective_rate_percent(income: str) -> Decimal
```

Rules:

1. `income` must be a string parseable as `decimal.Decimal`. It must be finite, `>= 0`, and have at most 2 decimal places (cents). Inputs such as `"10.005"`, `"-1.00"`, `"abc"`, `""`, `"NaN"`, `"Infinity"`, or a non-string raise `ValueError`.
2. Tax brackets (taxable income, EUR, fixed): `0-12450` at 19%; `12450-20200` at 24%; `20200-35200` at 30%; `35200-60000` at 37%; `60000-300000` at 45%; above `300000` at 47%.
3. Each bracket taxes the part of income above its lower bound up to its upper bound. The lower bound is exclusive and the upper bound is inclusive. For example, income `12450.00` is taxed entirely in the first bracket, and income `12450.01` has `0.01` in the second bracket.
4. `tax_breakdown` returns one row per bracket that taxes an amount `> 0`, in bracket order. Each row is `{"from": D2, "to": D2 or None, "rate_percent": int, "taxable": D2, "tax": D2}` where `D2` means a `Decimal` quantized to exactly 2 decimal places. `"to"` is the bracket upper bound, or `None` only for the top (open-ended) bracket. `"from"` is the bracket lower bound.
5. Each row's `tax` is `taxable * rate_percent / 100`, quantized to cents (2dp) with `ROUND_HALF_UP`.
6. `income_tax` is the sum of the rounded row taxes from rule 5, quantized to cents. Hence `income_tax(x)` always equals the sum of `row["tax"]` in `tax_breakdown(x)`. For income `0`, `tax_breakdown` returns `[]` and `income_tax` returns `Decimal("0.00")`.
7. `effective_rate_percent(income)` returns `income_tax(income) / income * 100`, quantized to exactly 4 decimal places with `ROUND_HALF_UP`. For income `0` (in any valid representation, e.g. `"0"` or `"0.00"`) it returns `Decimal("0.0000")`. The same validation as rule 1 applies.
8. All money values are `Decimal`, never `float`. `Decimal` return values from `income_tax` are quantized to 2dp; `effective_rate_percent` to 4dp.
9. Worked examples: `income_tax("10000")` is `Decimal("1900.00")`; `income_tax("12450")` is `Decimal("2365.50")`; `income_tax("20200")` is `2365.50 + 7750 * 0.24 = Decimal("4225.50")`; `income_tax("50000")` is `2365.50 + 1860.00 + 4500.00 + 5476.00 = Decimal("14201.50")`, because the brackets tax `12450`, `7750`, `15000` and `14800` respectively.
10. For `income_tax("50000")`, `effective_rate_percent("50000")` is `Decimal("28.4030")` (`14201.50 / 50000 * 100`).
11. Use only the Python standard library.


## Module `task_b.py` — task `prorata_billing`

# Pro-rata billing for a period with mid-cycle price changes

Implement in `solution.py`:

```python
def prorate_period(period_start: str, period_end: str, changes: list[dict]) -> dict
```

Rules:

1. `period_start` and `period_end` are ISO date strings `"YYYY-MM-DD"` naming valid calendar dates. The billing period is `[period_start, period_end)`: `period_start` is included and `period_end` is exclusive. `period_end` must be strictly after `period_start`, otherwise `ValueError`. Invalid date strings (bad format, or a non-existent date such as `"2024-02-30"`) raise `ValueError`.
2. `changes` must be a non-empty list of dicts. Each entry is `{"date": "YYYY-MM-DD", "monthly_price": str}`. Any missing key, invalid date, or invalid entry shape raises `ValueError`. Entries may be given in any order and are applied in date order.
3. Each `monthly_price` must be a string parseable as `Decimal`, finite, `>= 0`, with at most 2 decimal places. Values such as `"-1.00"`, `"10.005"`, `"abc"`, `""`, `"NaN"` raise `ValueError`.
4. Duplicate effective dates are forbidden: two entries with the same `"date"` raise `ValueError`, even if that date lies outside the period.
5. The entry with the earliest date must have a date `<= period_start`, otherwise `ValueError` (no plan covers the start of the period). That earliest applicable plan applies from `period_start`. More precisely, the plan in force at `period_start` is the entry with the greatest date `<= period_start`; earlier entries are superseded (but still validated). Entries with a date `>= period_end` are ignored for segmentation (including an entry exactly on `period_end`), but they are still validated under rules 2-4.
6. Segments are consecutive `[seg_start, seg_end)` intervals covering the whole period, split at each change date strictly inside the period. Adjacent segments with the same `monthly_price` are merged into a single segment. Therefore a mid-period change to the same price produces a single segment for the whole period.
7. `period_days` is the number of actual calendar days in `[period_start, period_end)` (so a period spanning a leap-day February counts 29 days for that month). Each segment's `days` is its actual number of days, and the segment days sum to `period_days`.
8. Each segment amount is `monthly_price * segment_days / period_days`, computed with `Decimal` (never `float`) and quantized to cents (2dp) with `ROUND_HALF_UP`, per segment.
9. The return value is `{"period_days": int, "segments": [...], "total": D2}`. Each segment is `{"from": iso_date_str, "to": iso_date_str, "days": int, "monthly_price": D2, "amount": D2}`, where `"from"` is the inclusive segment start, `"to"` is the exclusive segment end (for the last segment this is exactly `period_end`), and `D2` means a `Decimal` quantized to exactly 2 decimal places. `"total"` is the sum of the (rounded) segment amounts, quantized to cents.
10. Worked example: period `"2024-03-01"` to `"2024-04-01"` (31 days) with changes `[{"date": "2024-03-01", "monthly_price": "31.00"}, {"date": "2024-03-16", "monthly_price": "62.00"}]` gives segment 1 from `2024-03-01` to `2024-03-16`, 15 days, amount `31.00 * 15 / 31 = Decimal("15.00")`; segment 2 from `2024-03-16` to `2024-04-01`, 16 days, amount `62.00 * 16 / 31 = Decimal("32.00")`; `total` is `Decimal("47.00")`.
11. Leap-year example: period `"2024-02-01"` to `"2024-03-01"` has `period_days == 29`. A single plan at `"29.00"` from `2024-02-01` gives one segment of 29 days with amount `Decimal("29.00")`.
12. Use only the Python standard library.


## Module `task_c.py` — task `rf_reference`

# ISO 11649 RF creditor references

Implement in `solution.py`:

```python
def rf_reference(base: str) -> str
def is_valid_rf_reference(text: str) -> bool
```

Rules (all explicit; the traps are in these details):

1. Generation — normalization: `base` must be a `str`; remove every
   ASCII space `" "` and uppercase the rest (hyphens and other
   characters are **not** removed). A non-string `base` raises
   `ValueError`.
2. Generation — validity: the normalized base must be 1-21 characters
   long and entirely alphanumeric (`A`-`Z`, `0`-`9`). An empty base, a
   base longer than 21 characters, or one containing any other
   character raises `ValueError`.
3. Generation — result: `"RF"` + the 2 check digits + the normalized
   base, so the total length is at most 25. Example:
   `rf_reference("539007547034") == "RF18539007547034"`.
4. Check digits: form the string `base + "RF00"`, convert it to a
   numeric string by replacing each letter with its two-digit value
   (`A=10, B=11, ..., Z=35`) and keeping each digit as-is, interpret it
   as an integer, and take it mod 97. The check digits are
   `98 - (value mod 97)`, formatted as exactly two digits with a
   leading zero when needed (e.g. check 9 is `"09"`).
   Hand example: for base `"1"` the numeric string is
   `"1" + "27" + "15" + "00" = "1271500"`; `1271500 mod 97 = 24`, so
   the check digits are `98 - 24 = 74` and
   `rf_reference("1") == "RF741"`. For base `"7"` the check digits are
   `"09"`, so `rf_reference("7") == "RF097"`.
5. Validation — normalization: if `text` is not a `str`,
   `is_valid_rf_reference` returns `False`. Otherwise remove every
   ASCII space and uppercase the rest.
6. Validation — shape: the normalized text must start with `"RF"`, be
   5-25 characters long in total, be entirely alphanumeric, and the two
   characters after `"RF"` (the check digits) must both be digits.
7. Validation — checksum: moving the first 4 characters (`"RF"` plus the
   check digits) to the end and converting letters as in rule 4 must
   give a number with `mod 97 == 1`. Equivalently, the embedded check
   digits must equal the digits recomputed from the remaining base by
   rule 4; both statements describe the same check and both must hold
   (they always agree when the shape in rule 6 holds).
8. Validation returns `True` only when rules 5-7 all hold, and `False`
   otherwise (never raises). Examples: `is_valid_rf_reference("RF741")`
   is `True`, `is_valid_rf_reference("rf 741")` is `True` (spaces and
   case are normalized), `is_valid_rf_reference("RF751")` is `False`
   (wrong check digits), and `is_valid_rf_reference("RF74")` is `False`
   (too short).
9. Use only the stdlib.
