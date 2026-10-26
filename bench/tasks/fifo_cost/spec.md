# FIFO cost basis and realized gains

Implement in `solution.py`:

```python
def fifo_report(trades: list[dict]) -> dict
```

Rules (all explicit; the traps are in these details):

1. `trades` must be a `list`. Each item must be a `dict` with keys
   `"date"`, `"side"`, `"quantity"` and `"price"`, plus optional `"fee"`.
   A non-list `trades`, a non-dict trade, or a trade missing a required
   key raises `ValueError`. Extra keys are ignored.
2. Trades are processed strictly in the order given. They are **not**
   sorted by date or by any other field.
3. `date` must be a string in exactly `YYYY-MM-DD` form (4-digit year,
   2-digit month, 2-digit day, hyphen separators) naming a real calendar
   date. `"2024-02-30"`, `"2024-13-01"`, `"2024-1-01"`, `"01/01/2024"`,
   `""`, and non-strings raise `ValueError`. The sale's `date` in the
   output is the original string.
4. `side` must be exactly `"BUY"` or `"SELL"` (case-sensitive). Any other
   value raises `ValueError`.
5. `quantity` must be an `int` greater than `0`. `bool`, non-`int` values
   (for example `2.5` or `"2"`), `0` and negative values raise `ValueError`.
6. `price` must be a string parseable by `decimal.Decimal`. It must be
   finite, `> 0`, and have at most 4 decimal places. `"0"`, `"-1.00"`,
   `"10.12345"`, `"abc"`, `""`, `"NaN"`, `"Infinity"` and non-strings
   raise `ValueError`.
7. `fee` is optional and defaults to `"0.00"` when absent. When present it
   must be a string parseable by `decimal.Decimal`, finite, `>= 0`, and
   have at most 2 decimal places. A negative fee, `"abc"`, a non-string,
   or more than 2 decimal places (for example `"1.234"`) raises
   `ValueError`.
8. All money is `Decimal`, never `float`. Intermediate lot costs, cost
   consumed and proceeds are kept exact (unrounded); only the output
   fields described in rules 11-13 are quantized.
9. A `BUY` creates a new lot at the back of the inventory queue whose
   exact total cost is `quantity * price + fee` and whose remaining
   quantity is `quantity`.
10. A `SELL` first checks that the total remaining inventory quantity at
    that moment is at least the sale quantity; if not, it raises
    `ValueError` (even if a later `BUY` would cover it). It consumes lots
    oldest first (FIFO), partially if needed. For each lot touched, with
    `taken` units taken from a lot having remaining quantity `q` and
    remaining exact total cost `c`, the exact cost consumed from that lot
    is `c * taken / q`, and the lot's remaining total cost and quantity
    are reduced by that amount and `taken`. Exact proceeds are
    `quantity * price - fee`. No exception is raised merely because
    proceeds are negative.
11. For each sale, in processing order, append
    `{"date": <original date string>, "quantity": <int>,
    "proceeds": D, "cost": D, "realized": D}` to `sales`, where
    `proceeds` is the exact proceeds quantized to 2 decimal places
    (`ROUND_HALF_UP`), `cost` is the exact total cost consumed quantized
    to 2 decimal places, and `realized` is `(exact proceeds - exact cost
    consumed)` quantized to 2 decimal places. Each is quantized
    independently, so `realized` may differ by a cent from
    `proceeds - cost` as displayed.
12. `total_realized` is the sum of the per-sale quantized `realized`
    values, quantized to 2 decimal places. With no sales it is
    `Decimal("0.00")`.
13. `remaining` lists, oldest first, every lot with remaining quantity
    `> 0` as `{"quantity": <int>, "unit_cost": D, "total_cost": D}`,
    where `total_cost` is the lot's exact remaining total cost quantized
    to 2 decimal places and `unit_cost` is
    `exact remaining total cost / remaining quantity` quantized to
    exactly 4 decimal places (`ROUND_HALF_UP`). `inventory_quantity` is
    the sum of the remaining quantities (`int`).
14. Empty `trades` (`[]`) returns `{"sales": [], "total_realized":
    Decimal("0.00"), "remaining": [], "inventory_quantity": 0}`.
    Worked example: buy 10 at `"10"` (fee `"0.00"`), buy 10 at `"20"`,
    then sell 15 at `"30"`. The sale consumes all 10 at cost 10 and 5 at
    cost 20: `cost` is `200.00`, `proceeds` is `450.00`, `realized` is
    `250.00`. `total_realized` is `250.00`; `remaining` is
    `[{"quantity": 5, "unit_cost": Decimal("20.0000"),
    "total_cost": Decimal("100.00")}]` and `inventory_quantity` is `5`.
15. Use only the stdlib. Never use `float` for the money maths.
