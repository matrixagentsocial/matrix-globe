# Pull request pr_test_2

This package contains three modules: `task_a.py`, `task_b.py`, `task_c.py`. Each section below is the spec for one module. Where a section says `solution.py`, it means that section's module file. Implement and review the package as a whole; a defect may be in any module.


## Module `task_a.py` — task `budget_variance`

# Budget variance report

Implement in `solution.py`:

```python
def variance_report(lines: list[dict]) -> list[dict]
def variance_summary(lines: list[dict]) -> dict
```

Rules (all explicit; the traps are in these details):

1. Each line is a dict `{"name": str, "kind": "revenue" | "cost", "budget": str, "actual": str}`. Missing keys, non-dict entries, a non-string `name`, or a `kind` other than exactly `"revenue"` or `"cost"` raise `ValueError`. Both functions apply the same validation; `variance_summary` must raise on the same bad input as `variance_report`.
2. `budget` and `actual` are money strings parsed with `Decimal`. They may have any sign (negative revenue and negative cost are allowed), must be finite, and must have at most 2 decimal places. Inputs such as `"abc"`, `""`, `"NaN"`, `"Infinity"` or `"10.005"` raise `ValueError`.
3. `variance_report` returns one dict per input line, in input order (no sorting, no grouping). Each dict is exactly `{"name", "kind", "budget", "actual", "variance", "variance_percent", "favourable", "status"}` with the line's original `name` and `kind`.
4. `budget` and `actual` in the output are `Decimal` quantized to exactly 2 decimal places. `variance` is `actual - budget` (signed, in that order for both kinds), quantized to exactly 2 decimal places.
5. `favourable` is `True` when `variance > 0` for a `revenue` line, or when `variance < 0` for a `cost` line. When `variance == 0`, `favourable` is `False` for both kinds. Otherwise `favourable` is `False`.
6. `status` is `"favourable"` when `favourable` is `True`, `"on_budget"` when `variance == 0`, and `"unfavourable"` otherwise. So a zero-variance line is always `{"favourable": False, "status": "on_budget"}`.
7. `variance_percent` is `(variance / budget * 100)` computed from the signed variance and the signed budget, quantized to 2 decimal places with `ROUND_HALF_UP`. If `budget == 0`, `variance_percent` is `None` (even when `variance` is also `0`). Example: revenue budget `"100.00"`, actual `"110.00"` -> variance `10.00`, percent `10.00`. Cost budget `"100.00"`, actual `"110.00"` -> variance `10.00`, percent `10.00` (the percent keeps the sign of the variance; favourability is reported separately).
8. `variance_summary` returns exactly `{"total_budget_revenue", "total_actual_revenue", "total_budget_cost", "total_actual_cost", "net_budget", "net_actual", "net_variance", "favourable_count", "unfavourable_count", "on_budget_count"}`. All money values are `Decimal` quantized to exactly 2 decimal places; the counts are `int`.
9. The four totals are the plain sums of the respective `budget`/`actual` values over lines of that kind only. A kind with no lines totals `Decimal("0.00")`.
10. `net_budget` is `total_budget_revenue - total_budget_cost`. `net_actual` is `total_actual_revenue - total_actual_cost`. `net_variance` is `net_actual - net_budget`.
11. `favourable_count`, `unfavourable_count` and `on_budget_count` count lines by their `status` as defined in rule 6, over all lines of both kinds. The three counts sum to `len(lines)`.
12. Empty `lines` returns `[]` from `variance_report`, and a summary whose money values are all `Decimal("0.00")` and whose counts are all `0`.
13. Worked example: lines `[{"name":"Sales","kind":"revenue","budget":"100.00","actual":"110.00"}, {"name":"Rent","kind":"cost","budget":"50.00","actual":"40.00"}]` -> report variances `10.00` (favourable) and `-10.00` (favourable, because cost fell); summary `net_budget 50.00`, `net_actual 70.00`, `net_variance 20.00`, `favourable_count 2`.
14. Use only the stdlib. Never use `float` for the money maths.


## Module `task_b.py` — task `depreciation_declining`

# Declining-balance depreciation with switch to straight line

Implement in `solution.py`:

```python
def declining_schedule(cost: str, salvage: str, life_years: int, factor: str = "2") -> list[dict]
```

Rules (all explicit; the traps are in these details):

1. `cost` and `salvage` are decimal strings parsed with `decimal.Decimal`. Both must be strings, finite, and have at most 2 decimal places. `cost > salvage >= 0` (so `cost > 0`). Otherwise raise `ValueError` (including `"abc"`, `""`, `"NaN"`, `"Infinity"`, `"10.005"`, negative salvage, `salvage >= cost`, and non-string inputs).
2. `life_years` must be an `int` (not `bool`) with `1 <= life_years <= 50`, else `ValueError`.
3. `factor` is a decimal string (default `"2"`) parsed with `Decimal`. It must be a string, finite, and satisfy `Decimal("1") <= factor <= Decimal("3")`. Otherwise raise `ValueError`. The factor need not have at most 2 decimal places (for example `"1.5"` and `"2.25"` are valid).
4. The schedule has exactly `life_years` rows. Years are 1-based sequence numbers (`1`, `2`, ..., `life_years`), NOT calendar years.
5. Let the opening book value of year 1 be `cost`. For each year, let `remaining_years = life_years - year + 1` (so it is `life_years` in year 1 and `1` in the final year).
6. For every year except the final year, compute two raw amounts from the opening book value: declining amount `= opening_book * (factor / life_years)` and straight-line alternative `= (opening_book - salvage) / remaining_years`. Charge the LARGER of the two (this is the switch-to-straight-line rule).
7. Each non-final year's amount is the larger raw amount from Rule 6, quantized to exactly 2 decimal places with `ROUND_HALF_UP`, but never more than `opening_book - salvage` (so the book value never goes below `salvage`). Use `Decimal` at high precision for the raw amounts; never use `float`.
8. In the final year (`year == life_years`) the amount is exactly `opening_book - salvage`, with no quantization choice (it is already exact cents because all previous amounts were cents). This final rule overrides Rules 6-7 even if the declining amount would exceed `opening_book - salvage`.
9. The total of all `amount` values equals `cost - salvage` exactly, and the final `book_value` equals `salvage` exactly.
10. Each row is a dict `{"year": int, "amount": Decimal, "accumulated": Decimal, "book_value": Decimal}`. `accumulated` is the sum of `amount` up to and including that row. `book_value` is `cost - accumulated` (equivalently the opening book of the next year). `amount`, `accumulated` and `book_value` are all quantized to exactly 2 decimal places.
11. Use only the stdlib. Never use `float` for the money maths.

Worked example A: `declining_schedule("10000", "1000", 4, "2")` has rate `0.5`.

- Year 1: declining `5000.00` vs straight-line `9000/4 = 2250.00` -> charge `5000.00`, book `5000.00`.
- Year 2: declining `2500.00` vs straight-line `4000/3 = 1333.33...` -> charge `2500.00`, book `2500.00`.
- Year 3: declining `1250.00` vs straight-line `1500/2 = 750.00` -> charge `1250.00`, book `1250.00`.
- Year 4 (final): amount `= 1250.00 - 1000.00 = 250.00`, book `1000.00` (even though declining `625.00` would breach salvage).

Total is `9000.00`.

Worked example B (straight line wins mid-schedule): `declining_schedule("10000", "0", 5, "2")`:

- Year 1: `4000.00`, book `6000.00`. Year 2: `2400.00`, book `3600.00`. Year 3: declining `1440.00` vs straight-line `1200.00` -> `1440.00`, book `2160.00`. Year 4: declining `864.00` vs straight-line `1080.00` -> charge straight-line `1080.00`, book `1080.00`. Year 5 (final): `1080.00`, book `0.00`.


## Module `task_c.py` — task `depreciation_straight_line`

# Straight-line depreciation schedule with mid-month convention

Implement in `solution.py`:

```python
def straight_line_schedule(cost: str, salvage: str, life_years: int, placed_year: int, placed_month: int) -> list[dict]
```

Rules (all explicit; the traps are in these details):

1. `cost` and `salvage` are decimal strings parsed with `decimal.Decimal`. Both must be strings, finite, and have at most 2 decimal places. `cost > 0` and `0 <= salvage < cost`. Otherwise raise `ValueError` (including `"abc"`, `""`, `"NaN"`, `"Infinity"`, `"10.005"`, negative values, and non-string inputs).
2. `life_years` must be an `int` (not `bool`) with `1 <= life_years <= 50`. `placed_month` must be an `int` (not `bool`) with `1 <= placed_month <= 12`. `placed_year` must be an `int` (not `bool`) with `1900 <= placed_year <= 2200`. Any violation raises `ValueError`.
3. The depreciable base is `base = cost - salvage` (exact, in cents).
4. The full annual amount is `base / life_years`, computed exactly (do not round it before applying Rule 5; use `Decimal`, never `float`).
5. Mid-month convention: in the placed year the asset is treated as placed mid-month, so the first-year fraction is `(12 - placed_month + 0.5) / 12` of a full year. The first-year raw amount is `(base / life_years) * fraction`. This fraction is always `< 1` (even for `placed_month == 1` it is `11.5/12`).
6. Each following calendar year charges a full annual amount (`base / life_years`) until the remaining base is smaller, subject to Rules 7-8.
7. Each year's amount is quantized to exactly 2 decimal places with `ROUND_HALF_UP`, EXCEPT the final year, whose amount is exactly `base - (sum of all previous amounts)`. The final amount therefore absorbs rounding. All amounts are exact cents.
8. A year's amount never exceeds the remaining base (`base - sum of previous amounts`). Years advance, starting at `placed_year` and increasing by 1 each row, while the remaining base is `> 0`, charging `min(raw_amount_for_that_year, remaining_base)` (with the final such charge being exact per Rule 7).
9. The total of all `amount` values equals `base` exactly, and the final `book_value` equals `salvage` exactly.
10. Each row is a dict `{"year": int, "amount": Decimal, "accumulated": Decimal, "book_value": Decimal}`. `year` is the calendar year of that row (first row `placed_year`). `accumulated` is the sum of `amount` up to and including that row. `book_value` is `cost - accumulated`. `amount`, `accumulated` and `book_value` are all quantized to exactly 2 decimal places.
11. The number of rows is determined by the loop in Rule 8. It is typically `life_years + 1` because the first year is a partial year, but it is shorter if the remaining base reaches zero earlier.
12. Use only the stdlib. Never use `float` for the money maths.

Worked example: `straight_line_schedule("12000", "0", 5, 2024, 7)` has base `12000`, full annual `2400`, first-year fraction `(12-7+0.5)/12 = 5.5/12`, so the rows are:

- `{"year": 2024, "amount": Decimal("1100.00"), "accumulated": Decimal("1100.00"), "book_value": Decimal("10900.00")}`
- `{"year": 2025, "amount": Decimal("2400.00"), "accumulated": Decimal("3500.00"), "book_value": Decimal("8500.00")}`
- `{"year": 2026, "amount": Decimal("2400.00"), "accumulated": Decimal("5900.00"), "book_value": Decimal("6100.00")}`
- `{"year": 2027, "amount": Decimal("2400.00"), "accumulated": Decimal("8300.00"), "book_value": Decimal("3700.00")}`
- `{"year": 2028, "amount": Decimal("2400.00"), "accumulated": Decimal("10700.00"), "book_value": Decimal("1300.00")}`
- `{"year": 2029, "amount": Decimal("1300.00"), "accumulated": Decimal("12000.00"), "book_value": Decimal("0.00")}`

That is 6 rows summing exactly to `12000.00`.
