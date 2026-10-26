# Bank reconciliation matching

Implement in `solution.py`:

```python
def reconcile(book: list[dict], bank: list[dict], tolerance_days: int = 3) -> dict
```

Rules (all explicit; the traps are in these details):

1. `book` and `bank` must each be a `list` of `dict` entries, otherwise
   `ValueError` is raised. Extra keys in an entry are ignored.
2. Each entry has `"id"`, `"date"` and `"amount"`. `id` must be a
   non-empty string. Ids must be unique within each side: a duplicate id
   inside `book`, or inside `bank`, raises `ValueError`. The same id may
   appear on both sides.
3. `date` must be a string in exactly `YYYY-MM-DD` form (4-digit year,
   2-digit month and day) naming a real calendar date. Anything else
   raises `ValueError`.
4. `amount` must be a string parseable by `Decimal`, finite, with at
   most 2 decimal places (its value equals its quantization to cents).
   Anything else raises `ValueError`. Amounts are signed: matching uses
   the signed amount, so `Decimal("10.00")` never matches
   `Decimal("-10.00")`, and subset sums in rule 7 are signed sums.
5. `tolerance_days` must be an `int` (not `bool`) with
   `0 <= tolerance_days <= 31`, otherwise `ValueError` is raised. The
   date difference is the absolute difference in calendar days.
6. Phase 1 (one-to-one): a bank entry can match a book entry when their
   amounts are exactly equal (to the cent) and their date difference is
   `<= tolerance_days`. Consider every such candidate pair. Sort
   candidate pairs by: smallest date difference, then earliest bank
   date, then bank `id`, then book `id`. Walk the sorted pairs greedily,
   taking a pair only if both entries are still unused. Each entry is
   used at most once across both phases.
7. Phase 2 (one-to-many): for each remaining bank entry, considered in
   `(date, id)` order, look for a subset of 2 or 3 still-remaining book
   entries such that every book entry's date differs from the bank
   entry's date by `<= tolerance_days` and the book amounts sum exactly
   to the bank amount. Among all such subsets for that bank entry prefer:
   subset size 2 over size 3; then the smallest maximum date difference
   within the subset; then the lexicographically smallest tuple of the
   subset's sorted book ids. If a preferred subset exists, match it
   (marking those book entries used); otherwise the bank entry stays
   unmatched. Book entries consumed by an earlier bank entry in this
   phase are unavailable to later bank entries.
8. Return exactly `{"matches": [...], "unmatched_book": [...],
   "unmatched_bank": [...]}`. Each match is
   `{"bank_id": <bank id>, "book_ids": <sorted list of book ids>}`
   (a phase 1 match has a one-element `book_ids` list). `matches` is
   ordered by the matched bank entry's `(date, id)`, merging phase 1 and
   phase 2 matches into that single order.
9. `unmatched_book` is the list of unmatched book ids ordered by their
   entries' `(date, id)`; `unmatched_bank` is the same for bank entries.
10. Empty inputs are valid: two empty lists return
    `{"matches": [], "unmatched_book": [], "unmatched_bank": []}`.
11. Example (one-to-one): book `[{"id": "b1", "date": "2024-01-05",
    "amount": "100.00"}]`, bank `[{"id": "k1", "date": "2024-01-06",
    "amount": "100.00"}]` with tolerance 3 returns matches
    `[{"bank_id": "k1", "book_ids": ["b1"]}]` and no unmatched ids.
12. Example (one-to-many): one bank entry of `"100.00"` and remaining
    book entries of `"60.00"` and `"40.00"` (all dates within tolerance)
    match as one match whose `book_ids` are both book ids sorted.
13. Example (greedy order): if one book entry could match two bank
    entries with date differences 1 and 2, it matches the difference-1
    bank entry, and the other bank entry is unmatched (unless phase 2
    later matches it).
14. Only the stdlib may be used. Money uses `Decimal`, never `float`.
