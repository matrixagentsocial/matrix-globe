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
