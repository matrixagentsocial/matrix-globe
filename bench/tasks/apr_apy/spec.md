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
