# Amortization schedule with level payments

Implement in `solution.py`:

```python
def amortize(principal: str, annual_rate_percent: str, months: int, start_date: str) -> list[dict]
def total_interest(schedule) -> Decimal
```

Rules (all explicit; the traps are in these details):

1. `principal` must be a `str` parsed with `decimal.Decimal`. It must be finite, `> 0`, and have at most 2 decimal places (cents). A non-string, `"abc"`, `""`, `"NaN"`, `"Infinity"`, `"0.00"`, a negative value, or a value with more than 2 decimal places such as `"10.005"` raises `ValueError`. `"100"`, `"100.5"` and `"100.00"` are valid forms.
2. `annual_rate_percent` must be a `str` parsed with `decimal.Decimal`. It must be finite and satisfy `0 <= rate <= 100`. A non-string, an unparseable or non-finite string, a negative rate, or a rate above `100` raises `ValueError`. `"0"` and `"100"` are valid.
3. `months` must be an `int` with `1 <= months <= 360`. `bool` values, non-integers such as `2.5` or `"3"`, `0`, negative values, and values above `360` raise `ValueError`.
4. `start_date` must be a `str` in exactly `YYYY-MM-DD` format naming a valid calendar date. Any other type, format, or an impossible date such as `"2024-02-30"` or `"2024-13-01"` raises `ValueError`. `start_date` is the disbursement date; it is not itself a payment date.
5. The monthly rate is `r = annual_rate_percent / 1200` computed as an exact `Decimal` division (never `float`). The level-payment formula in rule 6 is evaluated under a `decimal.localcontext` with precision `50`.
6. The level payment is `P * r / (1 - (1 + r) ** -months)` when `r > 0`, quantized to cents (`Decimal("0.01")`) with `ROUND_HALF_UP`. When `r == 0` the level payment is `principal / months` quantized to cents with `ROUND_HALF_UP`.
7. The schedule has exactly `months` rows, in chronological order, numbered `n = 1, 2, ..., months`. Each row is a dict with exactly the keys `"n"` (int), `"date"` (`"YYYY-MM-DD"` string), `"payment"`, `"interest"`, `"principal"` and `"balance"` (all `Decimal`). Every money value is quantized to exactly 2 decimal places (exponent `-2`).
8. Payment dates are monthly, starting one month after `start_date`. The anchor day is the day-of-month of `start_date`. Each payment day is the anchor day clamped to the last day of the target month, and the original anchor day is restored in the next month. Example: start `2024-01-31` gives payment dates `2024-02-29`, `2024-03-31`, `2024-04-30`. Start `2024-01-15` gives `2024-02-15`, `2024-03-15`, and so on, rolling into the next year as needed.
9. For each month, `interest` is the opening balance multiplied by the monthly rate `r`, quantized to cents with `ROUND_HALF_UP`. The opening balance of month 1 is `principal` (quantized to cents); the opening balance of each later month is the previous row's `balance`.
10. For every month except the final month, `payment` equals the level payment from rule 6 and the principal part is `principal = payment - interest`. The new balance is `opening balance - principal`.
11. In the final month, `principal` equals the whole opening balance and `payment = opening balance + interest`, so the final `balance` is exactly `Decimal("0.00")` regardless of rounding drift in the level payment. The final payment may therefore differ from the level payment by a few cents.
12. `total_interest(schedule)` returns the sum of the `"interest"` values of the rows as a `Decimal` quantized to exactly 2 decimal places. For an empty schedule it returns `Decimal("0.00")`. It does not recompute anything from rates or dates.
13. Use only the stdlib. Never use `float` for money or rate maths.

Worked examples:

- `amortize("100.00", "12", 3, "2024-01-15")` returns rows with payments `34.00, 34.00, 34.01`, interest `1.00, 0.67, 0.34`, principal parts `33.00, 33.33, 33.67`, balances `67.00, 33.67, 0.00`, on dates `2024-02-15, 2024-03-15, 2024-04-15`. `total_interest` of that schedule is `Decimal("2.01")`.
- `amortize("100.00", "0", 3, "2024-01-15")` has payments `33.33, 33.33, 33.34`, all interest `0.00`, and final balance `0.00`.
- Single month: `amortize("100.00", "12", 1, "2024-01-15")` returns one row dated `2024-02-15` with payment `101.00`, interest `1.00`, principal `100.00`, balance `0.00`.
