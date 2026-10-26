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
