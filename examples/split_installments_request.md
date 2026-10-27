## Spec
Implement in `solution.py`:

```python
def split_installments(total: str, n: int) -> list[Decimal]
```

Rules:
1. `total` is a decimal string such as `"100.00"`. Parse it with `decimal.Decimal`. It must be finite, must be `>= 0`, and must have at most 2 decimal places (cents). Inputs such as `"10.005"`, `"-1.00"`, `"abc"`, `""`, `"NaN"` or `"Infinity"` raise `ValueError`.
2. `n` must be an integer `>= 1`. `n == 0`, negative `n` and non-integer `n` (for example `2.5` or `"3"`) raise `ValueError`. (`bool` is not accepted as an integer.)
3. Return a list of exactly `n` `Decimal` values, each quantized to exactly 2 decimal places (exponent `-2`, so `str()` shows cents).
4. The installments must sum **exactly** to `total`. Each installment differs from any other by at most `Decimal("0.01")`.
5. Distribution is by largest remainder with deterministic order: the unavoidable extra cents go one each to the **first** installments. Example: `"100.00"` in 3 -> `[33.34, 33.33, 33.33]`; `"0.05"` in 2 -> `[0.03, 0.02]`; `"0.01"` in 3 -> `[0.01, 0.00, 0.00]`.
6. `"0.00"` in any valid `n` returns `n` copies of `Decimal("0.00")`. `n == 1` returns `[Decimal(total)]` quantized to cents.
7. Use only the stdlib. Never use `float` for the money maths.

## Code
```python
from decimal import Decimal, ROUND_HALF_UP


def split_installments(total: str, n: int) -> list[Decimal]:
    amount = Decimal(total)
    if amount < 0:
        raise ValueError("total must be >= 0")
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError("n must be an integer >= 1")
    each = (amount / n).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return [each for _ in range(n)]
```

## Tests (optional)
```python
from decimal import Decimal

import pytest

from solution import split_installments


def test_split_remainder_first():
    assert split_installments("100.00", 3) == [
        Decimal("33.34"),
        Decimal("33.33"),
        Decimal("33.33"),
    ]


def test_split_single():
    assert split_installments("42.50", 1) == [Decimal("42.50")]


def test_split_zero_n_raises():
    with pytest.raises(ValueError):
        split_installments("10.00", 0)
```
