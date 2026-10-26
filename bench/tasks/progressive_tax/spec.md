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
