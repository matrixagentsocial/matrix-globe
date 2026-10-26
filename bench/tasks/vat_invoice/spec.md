# VAT invoice breakdown by rate

Implement in `solution.py`:

```python
def vat_breakdown(lines: list[dict], mode: str) -> dict
```

Rules (all explicit; the traps are in these details):

1. `lines` must be a `list`. Each item must be a `dict` with keys
   `"quantity"`, `"unit_net"` and `"vat_rate"`. A non-list `lines`, a
   non-dict line, or a line missing any of these keys raises `ValueError`.
   Extra keys in a line are ignored.
2. `mode` must be exactly `"PER_LINE"` or `"PER_INVOICE"` (case-sensitive).
   Any other value, including a non-string, raises `ValueError`.
3. `quantity` must be an `int` greater than `0`. `bool`, non-`int` values
   (for example `2.5` or `"2"`), `0` and negative values raise `ValueError`.
4. `unit_net` must be a string parseable by `decimal.Decimal`. It must be
   finite, `>= 0`, and have at most 4 decimal places. `"abc"`, `""`,
   `"NaN"`, `"Infinity"`, a non-string, a negative value, or a value with
   more than 4 decimal places (for example `"1.12345"`) raises `ValueError`.
   Amounts such as `"0.99"`, `"10"` and `"0.3333"` are valid.
5. `vat_rate` must be a string parseable by `decimal.Decimal`, finite, and
   equal as a `Decimal` to one of `0`, `4`, `10` or `21`. So `"21"`,
   `"21.0"` and `"21.00"` are all the rate `21`; `"5"`, `"21.5"`, `"abc"`,
   a non-string or a negative rate raises `ValueError`.
6. The key for a rate in `by_rate` is the canonical string of the rate with
   no trailing zeros and no exponent: `"21"` (not `"21.0"`), `"4"`, `"10"`,
   `"0"`. `by_rate` contains only rates that occur in `lines`.
7. All money is `Decimal`, never `float`. Quantizing to cents means
   quantizing to exactly 2 decimal places with `ROUND_HALF_UP`.
8. `"PER_LINE"` mode: for each line, line net is
   `quantity * unit_net` (exact) quantized to cents; line VAT is
   `line_net * vat_rate / 100` using the quantized line net, quantized to
   cents. A rate group's net and VAT are the sums of its lines' quantized
   nets and VATs.
9. `"PER_INVOICE"` mode: for each rate, group net exact is the sum of the
   exact (unrounded) `quantity * unit_net` over that rate's lines, then
   quantized to cents; group VAT is `group_net * vat_rate / 100` using the
   quantized group net, quantized to cents. Lines are not rounded
   individually in this mode.
10. Return `{"net": D, "vat": D, "gross": D, "by_rate": {...}}` where each
    rate maps to `{"net": D, "vat": D, "gross": D}`. Every `gross` is
    `net + vat` for that scope. Total `net`/`vat` are the sums of the
    `by_rate` group nets/VATs (equivalently the sums described in rules
    8-9), and total `gross` is total `net + vat`. Every returned `Decimal`
    is quantized to exactly 2 decimal places.
11. Empty `lines` (`[]`) returns `{"net": Decimal("0.00"),
    "vat": Decimal("0.00"), "gross": Decimal("0.00"), "by_rate": {}}`
    for either valid mode. An invalid `mode` still raises `ValueError`
    even when `lines` is empty.
12. Worked example: three lines each `{"quantity": 1, "unit_net": "0.99",
    "vat_rate": "21"}`. `"PER_LINE"`: each line VAT is
    `0.99 * 21 / 100 = 0.2079 -> 0.21`, so `net` is `2.97`, `vat` is
    `0.63`, `gross` is `3.60`, and `by_rate` is
    `{"21": {"net": 2.97, "vat": 0.63, "gross": 3.60}}` (as Decimals).
    `"PER_INVOICE"`: group VAT is `2.97 * 21 / 100 = 0.6237 -> 0.62`, so
    `vat` is `0.62` and `gross` is `3.59`.
13. Mixed-rate example: `[{"quantity": 2, "unit_net": "10.00",
    "vat_rate": "21"}, {"quantity": 1, "unit_net": "5.00",
    "vat_rate": "10"}]` in either mode gives `net` `25.00`, `vat` `4.70`,
    `gross` `29.70`, with `by_rate` `{"21": {"net": 20.00, "vat": 4.20,
    "gross": 24.20}, "10": {"net": 5.00, "vat": 0.50, "gross": 5.50}}`
    (as Decimals).
14. Use only the stdlib. Never use `float` for the money maths.
