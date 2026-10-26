from decimal import Decimal

import pytest

from solution import apr_to_apy, apy_to_apr


def test_public_apr_monthly():
    assert apr_to_apy("12", "monthly") == Decimal("12.682503")


def test_public_apr_continuous():
    assert apr_to_apy("12", "continuous") == Decimal("12.749685")


def test_public_apy_to_apr_monthly():
    assert apy_to_apr("12.682503", "monthly") == Decimal("12.000000")


def test_public_zero():
    assert apr_to_apy("0", "monthly") == Decimal("0.000000")
    assert apy_to_apr("0", "daily") == Decimal("0.000000")


def test_public_bad_frequency():
    with pytest.raises(ValueError):
        apr_to_apy("12", "hourly")
