# Weighted average cost inventory

Implement in `solution.py`:

```python
def process_inventory(movements: list[dict]) -> dict
```

Rules (all explicit; the traps are in these details):

1. `movements` must be a `list`; anything else raises `ValueError`.
   Movements are processed strictly in list order. Each movement must be
   a `dict`, otherwise `ValueError` is raised. Extra keys in a movement
   are ignored.
2. Each movement has `"type"` exactly one of `"PURCHASE"`, `"SALE"`,
   `"CUSTOMER_RETURN"`, `"PURCHASE_RETURN"` (case-sensitive). A missing
   or any other type raises `ValueError`.
3. Each movement has `"quantity"` which must be an `int` (not `bool`)
   and `> 0`. Zero, negative, non-integer, missing quantities raise
   `ValueError`.
4. `"unit_cost"` is required only for `PURCHASE`: it must be present and
   be a string parseable by `Decimal`, finite and `>= 0` (`"0"` is
   allowed). A missing, non-string, unparseable, non-finite or negative
   `unit_cost` on a `PURCHASE` raises `ValueError`. There is no limit on
   its decimal places. For every other movement type a present
   `"unit_cost"` is ignored entirely and is not validated.
5. All money uses `Decimal` (precision 50 for divisions) and never
   `float`. Amounts denoted D2 are quantized to `Decimal("0.01")` with
   `ROUND_HALF_UP`. The tracked inventory value is re-quantized to cents
   after every movement (each addition/removal below is already in
   cents, so the stored value always has exponent `-2`).
6. `PURCHASE`: the added value is `(quantity * unit_cost)` quantized to
   cents D2; inventory value increases by it and quantity on hand
   increases by `quantity`.
7. The average cost before a removal or valued return is
   `inventory_value / quantity_on_hand` computed exactly with `Decimal`
   division at precision 50 at that moment, with no prior rounding.
8. `SALE`: if `quantity > quantity_on_hand`, `ValueError` is raised.
   Otherwise `cogs = (average_cost * quantity)` quantized D2; inventory
   value decreases by `cogs`, quantity on hand decreases by `quantity`,
   and `cogs` is added to `total_cogs`.
9. `CUSTOMER_RETURN`: if `quantity_on_hand == 0`, `ValueError` is raised
   because there is no current average cost. Otherwise the returned
   goods are valued at the current average cost (rule 7):
   `added = (average_cost * quantity)` quantized D2; inventory value
   increases by `added` and quantity on hand increases by `quantity`.
   It does not change `total_cogs`.
10. `PURCHASE_RETURN`: if `quantity > quantity_on_hand`, `ValueError` is
    raised. Otherwise it removes goods at the current average cost like
    a sale: `removed = (average_cost * quantity)` quantized D2;
    inventory value decreases by `removed` and quantity on hand
    decreases by `quantity`, but `removed` is added to
    `total_purchase_returns`, not to `total_cogs`.
11. When quantity on hand reaches 0, inventory value is whatever the
    cent-quantized removals leave (it is exactly `Decimal("0.00")` when
    the removal was valued at the full remaining average, which is
    always the case for a removal of the entire on-hand quantity).
12. Return exactly
    `{"quantity_on_hand": int, "inventory_value": D2,
    "average_cost": Decimal quantized to 4 decimal places with
    ROUND_HALF_UP, or Decimal("0.0000") if none on hand,
    "total_cogs": D2, "total_purchase_returns": D2}`.
    No other keys. `average_cost` when stock is held is
    `(inventory_value / quantity_on_hand)` at precision 50, then
    quantized to `Decimal("0.0001")` with `ROUND_HALF_UP`.
13. An empty movement list returns quantity 0, `inventory_value`
    `Decimal("0.00")`, `average_cost` `Decimal("0.0000")`,
    `total_cogs` `Decimal("0.00")` and `total_purchase_returns`
    `Decimal("0.00")`.
14. Worked example: buy 10 @ `"10.00"`, buy 10 @ `"20.00"` (value
    300.00, average 15), sell 5 (cogs 75.00, value 225.00, qty 15),
    customer return 2 (value +30.00 = 255.00, qty 17), purchase return
    3 (removed 45.00, value 210.00, qty 14). Result:
    `{"quantity_on_hand": 14, "inventory_value": Decimal("210.00"),
    "average_cost": Decimal("15.0000"), "total_cogs": Decimal("75.00"),
    "total_purchase_returns": Decimal("45.00")}`.
15. Only the stdlib may be used.
