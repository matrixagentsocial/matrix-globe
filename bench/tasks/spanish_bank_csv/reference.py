import csv
import io
import re
from datetime import date
from decimal import Decimal

_HEADER = "Fecha;Concepto;Importe;Saldo"
_DATE_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
_AMOUNT_RE = re.compile(r"^-?(?:\d{1,3}(?:\.\d{3})+|\d+),\d{1,2}$")
_CENT = Decimal("0.01")


def _parse_amount(raw, lineno):
    s = raw.strip()
    if not _AMOUNT_RE.match(s):
        raise ValueError(f"line {lineno}: invalid amount {raw!r}")
    return Decimal(s.replace(".", "").replace(",", ".")).quantize(_CENT)


def parse_bank_csv(text: str) -> list[dict]:
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    if text.startswith("\ufeff"):
        text = text[1:]
    lines = text.splitlines()
    rows = []
    header_seen = False
    for lineno, line in enumerate(lines, start=1):
        if line.strip() == "":
            continue
        if not header_seen:
            if line != _HEADER:
                raise ValueError(f"line {lineno}: invalid header")
            header_seen = True
            continue
        try:
            fields = next(csv.reader(io.StringIO(line), delimiter=";", quotechar='"', doublequote=True, strict=True))
        except Exception:
            raise ValueError(f"line {lineno}: malformed CSV row") from None
        if len(fields) != 4:
            raise ValueError(f"line {lineno}: expected 4 fields, got {len(fields)}")
        raw_date, concept, raw_importe, raw_saldo = fields
        m = _DATE_RE.match(raw_date.strip())
        if not m:
            raise ValueError(f"line {lineno}: invalid date {raw_date!r}")
        try:
            d = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            raise ValueError(f"line {lineno}: invalid date {raw_date!r}") from None
        if raw_importe.strip() == "":
            raise ValueError(f"line {lineno}: missing Importe")
        amount = _parse_amount(raw_importe, lineno)
        balance = None if raw_saldo.strip() == "" else _parse_amount(raw_saldo, lineno)
        rows.append({"date": d.isoformat(), "concept": concept, "amount": amount, "balance": balance})
    if not header_seen:
        raise ValueError("missing header")
    return rows


def summarize_transactions(transactions: list[dict]) -> dict:
    if not isinstance(transactions, list):
        raise ValueError("transactions must be a list")
    credits = Decimal("0.00")
    debits = Decimal("0.00")
    for t in transactions:
        if not isinstance(t, dict) or "amount" not in t or "date" not in t:
            raise ValueError("invalid transaction")
        amt = t["amount"]
        if not isinstance(amt, Decimal) or not amt.is_finite():
            raise ValueError("invalid transaction amount")
        if not isinstance(t["date"], str):
            raise ValueError("invalid transaction date")
        if amt > 0:
            credits += amt
        elif amt < 0:
            debits += amt
    return {
        "count": len(transactions),
        "credits": credits.quantize(_CENT),
        "debits": debits.quantize(_CENT),
        "net": (credits + debits).quantize(_CENT),
        "first_date": transactions[0]["date"] if transactions else None,
        "last_date": transactions[-1]["date"] if transactions else None,
    }
