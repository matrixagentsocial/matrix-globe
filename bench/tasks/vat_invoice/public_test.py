from decimal import Decimal

import pytest

from solution import vat_breakdown


def test_public_per_line_key_example():
    lines = [{"quantity": 1, "unit_net": "0.99", "vat_rate": "21"} for _ in range(3)]
    result = vat_breakdown(lines, "PER_LINE")
    assert result["net"] == Decimal("2.97")
    assert result["vat"] == Decimal("0.63")
    assert result["gross"] == Decimal("3.60")


def test_public_per_invoice_key_example():
    lines = [{"quantity": 1, "unit_net": "0.99", "vat_rate": "21"} for _ in range(3)]
    result = vat_breakdown(lines, "PER_INVOICE")
    assert result["vat"] == Decimal("0.62")
    assert result["gross"] == Decimal("3.59")


def test_public_mixed_rates():
    lines = [
        {"quantity": 2, "unit_net": "10.00", "vat_rate": "21"},
        {"quantity": 1, "unit_net": "5.00", "vat_rate": "10"},
    ]
    result = vat_breakdown(lines, "PER_LINE")
    assert result["net"] == Decimal("25.00")
    assert result["vat"] == Decimal("4.70")
    assert result["gross"] == Decimal("29.70")
    assert result["by_rate"]["21"] == {
        "net": Decimal("20.00"),
        "vat": Decimal("4.20"),
        "gross": Decimal("24.20"),
    }


def test_public_empty():
    assert vat_breakdown([], "PER_INVOICE") == {
        "net": Decimal("0.00"),
        "vat": Decimal("0.00"),
        "gross": Decimal("0.00"),
        "by_rate": {},
    }


def test_public_bad_mode_raises():
    with pytest.raises(ValueError):
        vat_breakdown([], "TOTAL")
