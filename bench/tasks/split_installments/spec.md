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
