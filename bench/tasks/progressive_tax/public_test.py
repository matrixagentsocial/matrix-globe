from decimal import Decimal

import pytest

from solution import effective_rate_percent, income_tax, tax_breakdown


def test_public_tax_below_first_threshold():
    assert income_tax("10000") == Decimal("1900.00")


def test_public_tax_at_first_threshold():
    assert income_tax("12450") == Decimal("2365.50")


def test_public_tax_at_second_threshold():
    assert income_tax("20200") == Decimal("4225.50")


def test_public_tax_mid_bracket_and_breakdown():
    assert income_tax("50000") == Decimal("14201.50")
    rows = tax_breakdown("50000")
    assert [r["tax"] for r in rows] == [
        Decimal("2365.50"),
        Decimal("1860.00"),
        Decimal("4500.00"),
        Decimal("5476.00"),
    ]


def test_public_effective_rate():
    assert effective_rate_percent("50000") == Decimal("28.4030")
    assert effective_rate_percent("0") == Decimal("0.0000")
