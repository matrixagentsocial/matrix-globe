# Net present value and XIRR for irregular cashflows

Implement in `solution.py`:

```python
def npv(rate_percent: str, cashflows: list[tuple[str, str]]) -> Decimal
def xirr(cashflows: list[tuple[str, str]]) -> Decimal
```

Rules (all explicit; the traps are in these details):

1. `cashflows` is a list of `(date, amount)` pairs. Each `date` is a string in
   exactly `YYYY-MM-DD` format naming a valid calendar date, and each `amount`
   is a decimal string parseable by `decimal.Decimal` (it may be negative,
   e.g. `"-1000"`, `"550.25"`). A non-list `cashflows`, an entry that is not a
   pair, a non-string or malformed date, a non-string, unparseable or
   non-finite amount (`"NaN"`, `"Infinity"`), or an empty list raises
   `ValueError` in both functions.
2. Entries sharing the same date are combined by summing their amounts.
   Combined entries are then sorted by date ascending. All validation in
   rules 3-4 applies to the combined, sorted flows.
3. There must be at least 2 distinct dates after combining, otherwise
   `ValueError`.
4. After combining there must be at least one strictly positive amount and
   at least one strictly negative amount, otherwise `ValueError`. (All-zero
   flows therefore raise.)
5. The year fraction of a flow is `days / 365` exactly, where `days` is the
   number of calendar days between the earliest (combined) date and that
   flow's date (so the earliest flow has fraction 0). Leap years do not
   change the 365 denominator: 2023-01-01 to 2024-01-01 is 365 days, i.e.
   fraction 1.
6. `npv(rate_percent, cashflows)` computes
   `sum(amount / (1 + r) ** (days / 365))` over the combined flows, where
   `r = Decimal(rate_percent) / 100`. All arithmetic is done with
   `decimal.Decimal` in a `localcontext` with `prec = 50`; never use
   `float`.
7. `rate_percent` must be a string parseable as a finite `Decimal` and must
   satisfy `rate_percent > -100` (so a rate of exactly `"-100"` or below
   raises `ValueError`, as do `"abc"`, `""` and non-strings).
8. `npv` returns the sum quantized to 2 decimal places (`Decimal("0.01")`)
   with `ROUND_HALF_UP`.
9. `xirr(cashflows)` returns the rate, expressed **as a percent** (so 10%
   is `Decimal("10.000000")`), for which the net present value in rule 6 is
   zero. It applies the same cashflow validation as `npv` (rules 1-4).
10. The returned rate is quantized to 6 decimal places
    (`Decimal("0.000001")`) with `ROUND_HALF_UP`. A result that rounds to
    zero is returned as `Decimal("0.000000")`.
11. If no rate makes the NPV zero (no sign change over the searchable range
    `-99.99%` to `10000%`, or the computation cannot converge), `xirr`
    raises `ValueError`. Any root-finding method is acceptable (e.g.
    Newton from 10% with a bisection fallback on that bracket); only the
    returned rate / raised error is checked.
12. Worked examples: `npv("10", [("2023-01-01", "-1000"),
    ("2024-01-01", "1100")]) == Decimal("0.00")` and
    `xirr([("2023-01-01", "-1000"), ("2024-01-01", "1100")])
    == Decimal("10.000000")`; `xirr([("2021-01-01", "-1000"),
    ("2023-01-01", "1210")]) == Decimal("10.000000")` (730 days, 2 years);
    `xirr([("2023-01-01", "-1000"), ("2024-01-01", "1000")])
    == Decimal("0.000000")`; `npv("0", [("2023-01-01", "-1000"),
    ("2024-01-01", "1100")]) == Decimal("100.00")`.
13. Use only the stdlib. Never use `float` for the money/rate maths.
