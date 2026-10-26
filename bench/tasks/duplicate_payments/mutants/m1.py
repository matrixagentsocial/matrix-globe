from datetime import date
from decimal import Decimal, InvalidOperation

_PUNCT = set(".,;:'\"()/-")
_LEGAL = {"SA", "SL", "SLU", "LTD", "LIMITED", "INC", "LLC", "GMBH", "BV", "NV", "SAS"}
_CENT = Decimal("0.01")


def _normalize_vendor(vendor):
    text = vendor.upper()
    text = "".join(ch for ch in text if ch not in _PUNCT)
    tokens = text.split()
    if tokens and tokens[-1] in _LEGAL:
        tokens.pop()
    return " ".join(tokens)


def find_duplicate_payments(payments: list[dict], window_days: int = 7) -> list[dict]:
    if isinstance(window_days, bool) or not isinstance(window_days, int):
        raise ValueError("window_days must be an integer")
    if window_days < 0 or window_days > 365:
        raise ValueError("window_days must be between 0 and 365")
    if not isinstance(payments, list):
        raise ValueError("payments must be a list")
    records = []
    seen_ids = set()
    for entry in payments:
        if not isinstance(entry, dict):
            raise ValueError("each payment must be a dict")
        for key in ("id", "date", "vendor", "amount", "currency"):
            if key not in entry:
                raise ValueError(f"missing key: {key}")
        pid, raw_date, vendor, raw_amount, currency = (entry["id"], entry["date"], entry["vendor"], entry["amount"], entry["currency"])
        if not all(isinstance(v, str) for v in (pid, raw_date, vendor, raw_amount, currency)):
            raise ValueError("payment fields must be strings")
        if pid == "":
            raise ValueError("id must be non-empty")
        if pid in seen_ids:
            raise ValueError(f"duplicate payment id: {pid}")
        seen_ids.add(pid)
        parts = raw_date.split("-")
        if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
            raise ValueError(f"invalid date: {raw_date!r}")
        try:
            parsed_date = date.fromisoformat(raw_date)
        except ValueError:
            raise ValueError(f"invalid date: {raw_date!r}") from None
        try:
            amount = Decimal(raw_amount)
        except (InvalidOperation, ValueError):
            raise ValueError(f"invalid amount: {raw_amount!r}") from None
        if not amount.is_finite():
            raise ValueError("amount must be finite")
        if amount != amount.quantize(_CENT):
            raise ValueError("amount must have at most 2 decimal places")
        norm_vendor = _normalize_vendor(vendor)
        if norm_vendor == "":
            raise ValueError("vendor normalizes to empty")
        norm_currency = currency.strip().upper()
        if norm_currency == "":
            raise ValueError("currency must be non-empty")
        records.append({"id": pid, "date": parsed_date, "vendor": norm_vendor, "amount": amount, "currency": norm_currency})
    n = len(records)
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    for i in range(n):
        for j in range(i + 1, n):
            a, b = records[i], records[j]
            if a["vendor"] == b["vendor"] and a["currency"] == b["currency"] and a["amount"] == b["amount"] and abs((a["date"] - b["date"]).days) <= window_days:
                union(i, j)
    components = {}
    for i in range(n):
        components.setdefault(find(i), []).append(records[i])
    groups = []
    for members in components.values():
        if len(members) < 2:
            continue
        ordered = sorted(members, key=lambda r: (r["date"], r["id"]))
        groups.append((ordered[0]["date"], ordered[0]["id"], {
            "payment_ids": [r["id"] for r in ordered],
            "vendor": ordered[0]["vendor"],
            "amount": ordered[0]["amount"].quantize(_CENT),
            "currency": ordered[0]["currency"],
        }))
    groups.sort(key=lambda item: (item[0], item[1]))
    return [g for _, _, g in groups]
