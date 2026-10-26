import re
from datetime import date
from decimal import Decimal, InvalidOperation
from itertools import combinations

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _entries(side, name):
    if not isinstance(side, list):
        raise ValueError(f"{name} must be a list")
    seen = set()
    out = []
    for e in side:
        if not isinstance(e, dict):
            raise ValueError("entry must be a dict")
        eid = e.get("id")
        if not isinstance(eid, str) or eid == "":
            raise ValueError("id must be a non-empty string")
        if eid in seen:
            raise ValueError(f"duplicate id: {eid}")
        seen.add(eid)
        raw_date = e.get("date")
        if not isinstance(raw_date, str) or not _DATE_RE.match(raw_date):
            raise ValueError(f"invalid date: {raw_date!r}")
        try:
            d = date(int(raw_date[0:4]), int(raw_date[5:7]), int(raw_date[8:10]))
        except ValueError:
            raise ValueError(f"invalid date: {raw_date!r}") from None
        raw_amt = e.get("amount")
        if not isinstance(raw_amt, str):
            raise ValueError("amount must be a string")
        try:
            amt = Decimal(raw_amt)
        except (InvalidOperation, ValueError):
            raise ValueError(f"invalid amount: {raw_amt!r}") from None
        if not amt.is_finite() or amt != amt.quantize(Decimal("0.01")):
            raise ValueError(f"invalid amount: {raw_amt!r}")
        out.append({"id": eid, "date": d, "amount": amt})
    return out


def reconcile(book: list[dict], bank: list[dict], tolerance_days: int = 3) -> dict:
    if isinstance(tolerance_days, bool) or not isinstance(tolerance_days, int) or not (0 <= tolerance_days <= 31):
        raise ValueError("tolerance_days must be an int in [0, 31]")
    books = _entries(book, "book")
    banks = _entries(bank, "bank")
    book_by_id = {b["id"]: b for b in books}
    bank_by_id = {b["id"]: b for b in banks}
    used_book = set()
    used_bank = set()
    matches = {}  # bank_id -> list book_ids

    candidates = []
    for bk in banks:
        for bo in books:
            if bk["amount"] == bo["amount"]:
                diff = abs((bk["date"] - bo["date"]).days)
                if diff <= tolerance_days:
                    candidates.append((diff, bk["date"], bk["id"], bo["id"]))
    candidates.sort(key=lambda c: (c[3], c[2]))
    for diff, _bd, bank_id, book_id in candidates:
        if bank_id not in used_bank and book_id not in used_book:
            used_bank.add(bank_id)
            used_book.add(book_id)
            matches[bank_id] = [book_id]

    remaining_banks = sorted((b for b in banks if b["id"] not in used_bank), key=lambda b: (b["date"], b["id"]))
    for bk in remaining_banks:
        remaining_books = [b for b in books if b["id"] not in used_book]
        eligible = [b for b in remaining_books if abs((bk["date"] - b["date"]).days) <= tolerance_days]
        best = None  # key: (size, maxdiff, tuple sorted ids)
        for size in (2, 3):
            for combo in combinations(eligible, size):
                if sum((c["amount"] for c in combo), Decimal("0")) == bk["amount"]:
                    maxdiff = max(abs((bk["date"] - c["date"]).days) for c in combo)
                    ids = tuple(sorted(c["id"] for c in combo))
                    key = (size, maxdiff, ids)
                    if best is None or key < best[0]:
                        best = (key, ids)
            # size preference: if any size-2 found, don't need size3? But key ordering handles it;
            # still must consider all size2 before deciding, combinations loop above covers all size2.
            if best is not None and size == 2:
                break
        if best is not None:
            ids = list(best[1])
            matches[bk["id"]] = ids
            used_bank.add(bk["id"])
            for i in ids:
                used_book.add(i)

    ordered_matches = [
        {"bank_id": bid, "book_ids": sorted(matches[bid])}
        for bid in sorted(matches, key=lambda bid: (bank_by_id[bid]["date"], bid))
    ]
    unmatched_book = [b["id"] for b in sorted((b for b in books if b["id"] not in used_book), key=lambda b: (b["date"], b["id"]))]
    unmatched_bank = [b["id"] for b in sorted((b for b in banks if b["id"] not in used_bank), key=lambda b: (b["date"], b["id"]))]
    return {"matches": ordered_matches, "unmatched_book": unmatched_book, "unmatched_bank": unmatched_bank}
