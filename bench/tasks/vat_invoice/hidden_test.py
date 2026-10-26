from decimal import Decimal

import pytest

from solution import vat_breakdown

LINES_099 = [{"quantity": 1, "unit_net": "0.99", "vat_rate": "21"} for _ in range(3)]


def test_hidden_per_line_key_example_by_rate():
    result = vat_breakdown(LINES_099, "PER_LINE")
    assert result["by_rate"] == {
        "21": {"net": Decimal("2.97"), "vat": Decimal("0.63"), "gross": Decimal("3.60")}
    }


def test_hidden_per_invoice_key_example_by_rate():
    result = vat_breakdown(LINES_099, "PER_INVOICE")
    assert result == {
        "net": Decimal("2.97"),
        "vat": Decimal("0.62"),
        "gross": Decimal("3.59"),
        "by_rate": {
            "21": {"net": Decimal("2.97"), "vat": Decimal("0.62"), "gross": Decimal("3.59")}
        },
    }


def test_hidden_mixed_rates_per_invoice():
    lines = [
        {"quantity": 2, "unit_net": "10.00", "vat_rate": "21"},
        {"quantity": 1, "unit_net": "5.00", "vat_rate": "10"},
    ]
    result = vat_breakdown(lines, "PER_INVOICE")
    assert result["by_rate"] == {
        "21": {"net": Decimal("20.00"), "vat": Decimal("4.20"), "gross": Decimal("24.20")},
        "10": {"net": Decimal("5.00"), "vat": Decimal("0.50"), "gross": Decimal("5.50")},
    }
    assert result["gross"] == Decimal("29.70")


def test_hidden_canonical_rate_keys():
    lines = [
        {"quantity": 1, "unit_net": "10.00", "vat_rate": "21.0"},
        {"quantity": 1, "unit_net": "10.00", "vat_rate": "4.00"},
        {"quantity": 1, "unit_net": "10.00", "vat_rate": "0"},
    ]
    result = vat_breakdown(lines, "PER_LINE")
    assert set(result["by_rate"].keys()) == {"21", "4", "0"}
    assert result["by_rate"]["4"] == {
        "net": Decimal("10.00"),
        "vat": Decimal("0.40"),
        "gross": Decimal("10.40"),
    }
    assert result["by_rate"]["0"]["vat"] == Decimal("0.00")
    assert result["net"] == Decimal("30.00")
    assert result["vat"] == Decimal("2.50")


def test_hidden_same_rate_spelled_differently_grouped():
    lines = [
        {"quantity": 1, "unit_net": "0.99", "vat_rate": "21.0"},
        {"quantity": 1, "unit_net": "0.99", "vat_rate": "21"},
        {"quantity": 1, "unit_net": "0.99", "vat_rate": "21.00"},
    ]
    result = vat_breakdown(lines, "PER_INVOICE")
    assert list(result["by_rate"].keys()) == ["21"]
    assert result["vat"] == Decimal("0.62")


def test_hidden_per_line_subcent_unit_net():
    lines = [{"quantity": 1, "unit_net": "0.005", "vat_rate": "21"} for _ in range(2)]
    result = vat_breakdown(lines, "PER_LINE")
    # Each line net 0.005 -> 0.01; each VAT 0.01*0.21=0.0021 -> 0.00.
    assert result == {
        "net": Decimal("0.02"),
        "vat": Decimal("0.00"),
        "gross": Decimal("0.02"),
        "by_rate": {
            "21": {"net": Decimal("0.02"), "vat": Decimal("0.00"), "gross": Decimal("0.02")}
        },
    }


def test_hidden_per_invoice_subcent_unit_net():
    lines = [{"quantity": 1, "unit_net": "0.005", "vat_rate": "21"} for _ in range(2)]
    result = vat_breakdown(lines, "PER_INVOICE")
    # Group exact net 0.010 -> 0.01; VAT 0.0021 -> 0.00.
    assert result["net"] == Decimal("0.01")
    assert result["vat"] == Decimal("0.00")
    assert result["gross"] == Decimal("0.01")


def test_hidden_quantity_multiplies_before_rounding():
    lines = [{"quantity": 2, "unit_net": "2.3456", "vat_rate": "4"}]
    result = vat_breakdown(lines, "PER_LINE")
    # Net 4.6912 -> 4.69; VAT 4.69*0.04=0.1876 -> 0.19.
    assert result["by_rate"]["4"] == {
        "net": Decimal("4.69"),
        "vat": Decimal("0.19"),
        "gross": Decimal("4.88"),
    }


def test_hidden_mixed_grouping_interaction_per_invoice():
    lines = [
        {"quantity": 1, "unit_net": "0.99", "vat_rate": "21"},
        {"quantity": 1, "unit_net": "0.99", "vat_rate": "10"},
        {"quantity": 1, "unit_net": "0.99", "vat_rate": "21"},
    ]
    result = vat_breakdown(lines, "PER_INVOICE")
    assert result["by_rate"]["21"] == {
        "net": Decimal("1.98"),
        "vat": Decimal("0.42"),
        "gross": Decimal("2.40"),
    }
    assert result["by_rate"]["10"] == {
        "net": Decimal("0.99"),
        "vat": Decimal("0.10"),
        "gross": Decimal("1.09"),
    }
    assert result["net"] == Decimal("2.97")
    assert result["vat"] == Decimal("0.52")
    assert result["gross"] == Decimal("3.49")


def test_hidden_two_decimal_exponent_everywhere():
    result = vat_breakdown(
        [{"quantity": 3, "unit_net": "1.2345", "vat_rate": "10"}], "PER_LINE"
    )
    assert result["net"] == Decimal("3.70")
    assert result["vat"] == Decimal("0.37")
    for value in (result["net"], result["vat"], result["gross"]):
        assert value.as_tuple().exponent == -2
    for group in result["by_rate"].values():
        for value in group.values():
            assert value.as_tuple().exponent == -2


def test_hidden_zero_quantity_line_net_zero():
    result = vat_breakdown(
        [{"quantity": 2, "unit_net": "0.00", "vat_rate": "21"}], "PER_LINE"
    )
    assert result["net"] == Decimal("0.00")
    assert result["gross"] == Decimal("0.00")
    assert result["by_rate"]["21"]["net"] == Decimal("0.00")


def test_hidden_bad_mode_lowercase_raises():
    with pytest.raises(ValueError):
        vat_breakdown(LINES_099, "per_line")


def test_hidden_bool_quantity_raises():
    with pytest.raises(ValueError):
        vat_breakdown([{"quantity": True, "unit_net": "1.00", "vat_rate": "21"}], "PER_LINE")


def test_hidden_zero_and_float_quantity_raises():
    with pytest.raises(ValueError):
        vat_breakdown([{"quantity": 0, "unit_net": "1.00", "vat_rate": "21"}], "PER_LINE")
    with pytest.raises(ValueError):
        vat_breakdown([{"quantity": 2.5, "unit_net": "1.00", "vat_rate": "21"}], "PER_LINE")


def test_hidden_negative_unit_net_raises():
    with pytest.raises(ValueError):
        vat_breakdown([{"quantity": 1, "unit_net": "-1.00", "vat_rate": "21"}], "PER_LINE")


def test_hidden_unit_net_too_many_places_raises():
    with pytest.raises(ValueError):
        vat_breakdown([{"quantity": 1, "unit_net": "1.12345", "vat_rate": "21"}], "PER_LINE")


def test_hidden_invalid_unit_net_raises():
    with pytest.raises(ValueError):
        vat_breakdown([{"quantity": 1, "unit_net": "abc", "vat_rate": "21"}], "PER_LINE")


def test_hidden_disallowed_rate_raises():
    with pytest.raises(ValueError):
        vat_breakdown([{"quantity": 1, "unit_net": "1.00", "vat_rate": "5"}], "PER_LINE")
    with pytest.raises(ValueError):
        vat_breakdown([{"quantity": 1, "unit_net": "1.00", "vat_rate": "21.5"}], "PER_LINE")


def test_hidden_missing_key_and_non_dict_line_raises():
    with pytest.raises(ValueError):
        vat_breakdown([{"quantity": 1, "unit_net": "1.00"}], "PER_LINE")
    with pytest.raises(ValueError):
        vat_breakdown(["not-a-dict"], "PER_LINE")
