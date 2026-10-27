# --- hidden tests for progressive_tax (module task_a.py) ---
from decimal import Decimal

import pytest

from task_a import effective_rate_percent, income_tax, tax_breakdown


def test_hidden_zero_income():
    assert income_tax("0") == Decimal("0.00")
    assert income_tax("0.00") == Decimal("0.00")
    assert tax_breakdown("0") == []


def test_hidden_one_cent_tax_rounds_to_zero_but_row_present():
    rows = tax_breakdown("0.01")
    assert rows == [
        {
            "from": Decimal("0.00"),
            "to": Decimal("12450.00"),
            "rate_percent": 19,
            "taxable": Decimal("0.01"),
            "tax": Decimal("0.00"),
        }
    ]
    assert income_tax("0.01") == Decimal("0.00")


def test_hidden_first_bracket_full_row():
    assert tax_breakdown("12450") == [
        {
            "from": Decimal("0.00"),
            "to": Decimal("12450.00"),
            "rate_percent": 19,
            "taxable": Decimal("12450.00"),
            "tax": Decimal("2365.50"),
        }
    ]


def test_hidden_one_euro_into_second_bracket():
    rows = tax_breakdown("12451")
    assert len(rows) == 2
    assert rows[1] == {
        "from": Decimal("12450.00"),
        "to": Decimal("20200.00"),
        "rate_percent": 24,
        "taxable": Decimal("1.00"),
        "tax": Decimal("0.24"),
    }
    assert income_tax("12451") == Decimal("2365.74")


def test_hidden_tax_at_35200():
    assert income_tax("35200") == Decimal("8725.50")


def test_hidden_tax_at_60000():
    assert income_tax("60000") == Decimal("17901.50")


def test_hidden_tax_at_300000():
    assert income_tax("300000") == Decimal("125901.50")


def test_hidden_tax_above_top_bracket():
    assert income_tax("400000") == Decimal("172901.50")
    top = tax_breakdown("400000")[-1]
    assert top["from"] == Decimal("300000.00")
    assert top["to"] is None
    assert top["rate_percent"] == 47
    assert top["taxable"] == Decimal("100000.00")
    assert top["tax"] == Decimal("47000.00")


def test_hidden_breakdown_50000_full():
    rows = tax_breakdown("50000")
    assert [(str(r["from"]), str(r["to"]), r["rate_percent"]) for r in rows] == [
        ("0.00", "12450.00", 19),
        ("12450.00", "20200.00", 24),
        ("20200.00", "35200.00", 30),
        ("35200.00", "60000.00", 37),
    ]
    assert [r["taxable"] for r in rows] == [
        Decimal("12450.00"),
        Decimal("7750.00"),
        Decimal("15000.00"),
        Decimal("14800.00"),
    ]


def test_hidden_tax_breakdown_sum_agrees():
    for value in ["1.00", "30000", "100000", "300001", "123456.78"]:
        rows = tax_breakdown(value)
        assert sum((r["tax"] for r in rows), Decimal("0.00")) == income_tax(value)


def test_hidden_effective_rate_first_bracket():
    assert effective_rate_percent("10000") == Decimal("19.0000")
    assert effective_rate_percent("12450") == Decimal("19.0000")


def test_hidden_effective_rate_second_bracket():
    # 4225.50 / 20200 * 100 = 20.918316... -> 20.9183
    assert effective_rate_percent("20200") == Decimal("20.9183")


def test_hidden_effective_rate_top():
    # 172901.50 / 400000 * 100 = 43.225375 -> 43.2254
    assert effective_rate_percent("400000") == Decimal("43.2254")


def test_hidden_negative_raises():
    with pytest.raises(ValueError):
        income_tax("-1.00")


def test_hidden_three_decimals_raises():
    with pytest.raises(ValueError):
        tax_breakdown("10.005")


def test_hidden_non_numeric_raises():
    with pytest.raises(ValueError):
        income_tax("abc")


def test_hidden_empty_and_nan_raise():
    with pytest.raises(ValueError):
        income_tax("")
    with pytest.raises(ValueError):
        effective_rate_percent("NaN")
    with pytest.raises(ValueError):
        income_tax("Infinity")


def test_hidden_non_string_raises():
    with pytest.raises(ValueError):
        income_tax(10000)

# --- hidden tests for prorata_billing (module task_b.py) ---
from decimal import Decimal

import pytest

from task_b import prorate_period


def test_hidden_leap_feb_with_change():
    result = prorate_period(
        "2024-02-01", "2024-03-01",
        [{"date": "2024-02-01", "monthly_price": "29.00"}, {"date": "2024-02-15", "monthly_price": "58.00"}],
    )
    assert result["period_days"] == 29
    assert [(s["from"], s["to"], s["days"], str(s["amount"])) for s in result["segments"]] == [
        ("2024-02-01", "2024-02-15", 14, "14.00"),
        ("2024-02-15", "2024-03-01", 15, "30.00"),
    ]
    assert result["total"] == Decimal("44.00")


def test_hidden_same_price_mid_cycle_merges():
    result = prorate_period(
        "2024-03-01", "2024-04-01",
        [{"date": "2024-03-01", "monthly_price": "31.00"}, {"date": "2024-03-16", "monthly_price": "31.00"}],
    )
    assert len(result["segments"]) == 1
    assert result["segments"][0]["days"] == 31
    assert result["total"] == Decimal("31.00")


def test_hidden_per_segment_rounding():
    # 30-day period: 10*10/30=3.33, 20*20/30=13.33
    result = prorate_period(
        "2024-04-01", "2024-05-01",
        [{"date": "2024-04-01", "monthly_price": "10.00"}, {"date": "2024-04-11", "monthly_price": "20.00"}],
    )
    assert [s["amount"] for s in result["segments"]] == [Decimal("3.33"), Decimal("13.33")]
    assert result["total"] == Decimal("16.66")


def test_hidden_entry_after_end_ignored():
    result = prorate_period(
        "2024-03-01", "2024-04-01",
        [{"date": "2024-03-01", "monthly_price": "31.00"}, {"date": "2024-05-01", "monthly_price": "999.00"}],
    )
    assert len(result["segments"]) == 1
    assert result["total"] == Decimal("31.00")


def test_hidden_entry_exactly_at_end_ignored():
    result = prorate_period(
        "2024-03-01", "2024-04-01",
        [{"date": "2024-03-01", "monthly_price": "31.00"}, {"date": "2024-04-01", "monthly_price": "62.00"}],
    )
    assert len(result["segments"]) == 1
    assert result["segments"][0]["to"] == "2024-04-01"


def test_hidden_entry_after_end_still_validated():
    with pytest.raises(ValueError):
        prorate_period(
            "2024-03-01", "2024-04-01",
            [{"date": "2024-03-01", "monthly_price": "31.00"}, {"date": "2024-05-01", "monthly_price": "-5.00"}],
        )


def test_hidden_plan_before_start_applies():
    result = prorate_period(
        "2024-03-01", "2024-04-01",
        [{"date": "2024-02-15", "monthly_price": "31.00"}],
    )
    assert len(result["segments"]) == 1
    assert result["segments"][0]["from"] == "2024-03-01"
    assert result["total"] == Decimal("31.00")


def test_hidden_latest_before_start_wins():
    result = prorate_period(
        "2024-03-01", "2024-04-01",
        [{"date": "2024-01-01", "monthly_price": "10.00"}, {"date": "2024-02-01", "monthly_price": "31.00"}],
    )
    assert len(result["segments"]) == 1
    assert result["segments"][0]["monthly_price"] == Decimal("31.00")


def test_hidden_zero_price():
    result = prorate_period("2024-01-01", "2024-02-01", [{"date": "2024-01-01", "monthly_price": "0.00"}])
    assert result["total"] == Decimal("0.00")
    assert result["segments"][0]["amount"] == Decimal("0.00")


def test_hidden_segment_days_sum_and_coverage():
    result = prorate_period(
        "2024-01-15", "2024-03-15",
        [
            {"date": "2024-01-01", "monthly_price": "60.00"},
            {"date": "2024-02-01", "monthly_price": "30.00"},
            {"date": "2024-03-01", "monthly_price": "90.00"},
        ],
    )
    assert sum(s["days"] for s in result["segments"]) == result["period_days"]
    assert result["segments"][0]["from"] == "2024-01-15"
    assert result["segments"][-1]["to"] == "2024-03-15"
    for a, b in zip(result["segments"], result["segments"][1:]):
        assert a["to"] == b["from"]
    assert result["total"] == sum((s["amount"] for s in result["segments"]), Decimal("0.00"))


def test_hidden_end_not_after_start_raises():
    with pytest.raises(ValueError):
        prorate_period("2024-04-01", "2024-04-01", [{"date": "2024-03-01", "monthly_price": "1.00"}])
    with pytest.raises(ValueError):
        prorate_period("2024-04-01", "2024-03-01", [{"date": "2024-03-01", "monthly_price": "1.00"}])


def test_hidden_no_plan_at_start_raises():
    with pytest.raises(ValueError):
        prorate_period("2024-03-01", "2024-04-01", [{"date": "2024-03-05", "monthly_price": "31.00"}])


def test_hidden_duplicate_date_raises():
    with pytest.raises(ValueError):
        prorate_period(
            "2024-03-01", "2024-04-01",
            [{"date": "2024-03-01", "monthly_price": "31.00"}, {"date": "2024-03-01", "monthly_price": "32.00"}],
        )


def test_hidden_empty_changes_raises():
    with pytest.raises(ValueError):
        prorate_period("2024-03-01", "2024-04-01", [])


def test_hidden_invalid_dates_raise():
    with pytest.raises(ValueError):
        prorate_period("2024-02-30", "2024-04-01", [{"date": "2024-02-01", "monthly_price": "1.00"}])
    with pytest.raises(ValueError):
        prorate_period("2024-03-01", "2024-04-01", [{"date": "not-a-date", "monthly_price": "1.00"}])


def test_hidden_invalid_price_raises():
    with pytest.raises(ValueError):
        prorate_period("2024-03-01", "2024-04-01", [{"date": "2024-03-01", "monthly_price": "10.005"}])
    with pytest.raises(ValueError):
        prorate_period("2024-03-01", "2024-04-01", [{"date": "2024-03-01", "monthly_price": "-1.00"}])
    with pytest.raises(ValueError):
        prorate_period("2024-03-01", "2024-04-01", [{"date": "2024-03-01", "monthly_price": "abc"}])


def test_hidden_missing_key_raises():
    with pytest.raises(ValueError):
        prorate_period("2024-03-01", "2024-04-01", [{"date": "2024-03-01"}])


def test_hidden_non_leap_feb_days():
    result = prorate_period("2023-02-01", "2023-03-01", [{"date": "2023-02-01", "monthly_price": "28.00"}])
    assert result["period_days"] == 28
    assert result["total"] == Decimal("28.00")

# --- hidden tests for rf_reference (module task_c.py) ---
import pytest

from task_c import is_valid_rf_reference, rf_reference


def test_hidden_generate_zero_padded_check():
    # Base "7": numeric "7271500"; 7271500 % 97 = 89; 98 - 89 = 9 -> "09".
    assert rf_reference("7") == "RF097"
    assert is_valid_rf_reference("RF097") is True


def test_hidden_generate_letter_base():
    # Base "A": numeric "10271500"; mod 97 = 73; 98 - 73 = 25.
    assert rf_reference("A") == "RF25A"


def test_hidden_generate_mixed_base():
    # Base "ABC": numeric "101112271500" -> check digits 45.
    assert rf_reference("ABC") == "RF45ABC"
    assert is_valid_rf_reference("RF45ABC") is True


def test_hidden_generate_normalizes_spaces_and_case():
    assert rf_reference(" 5390 0754 7034 ") == "RF18539007547034"
    assert rf_reference("abc") == "RF45ABC"


def test_hidden_generate_max_length_base():
    result = rf_reference("A" * 21)
    assert len(result) == 25
    assert result.startswith("RF")
    assert is_valid_rf_reference(result) is True


def test_hidden_generate_too_long_raises():
    with pytest.raises(ValueError):
        rf_reference("A" * 22)


def test_hidden_generate_bad_characters_raise():
    with pytest.raises(ValueError):
        rf_reference("AB-CD")
    with pytest.raises(ValueError):
        rf_reference("AB!CD")
    with pytest.raises(ValueError):
        rf_reference("   ")


def test_hidden_generate_non_string_raises():
    with pytest.raises(ValueError):
        rf_reference(123)
    with pytest.raises(ValueError):
        rf_reference(None)


def test_hidden_validate_normalizes_spaces_and_case():
    assert is_valid_rf_reference("rf741") is True
    assert is_valid_rf_reference("RF74 1") is True
    assert is_valid_rf_reference("rf18 5390 0754 7034") is True


def test_hidden_validate_wrong_check_digit_variants():
    # Correct check digits for base "1" are 74.
    assert is_valid_rf_reference("RF741") is True
    assert is_valid_rf_reference("RF751") is False
    assert is_valid_rf_reference("RF731") is False


def test_hidden_validate_too_short_and_too_long():
    assert is_valid_rf_reference("RF74") is False
    assert is_valid_rf_reference("RF") is False
    assert is_valid_rf_reference("") is False
    assert is_valid_rf_reference("RF18" + "A" * 22) is False


def test_hidden_validate_wrong_prefix():
    assert is_valid_rf_reference("XX741") is False
    assert is_valid_rf_reference("FR741") is False


def test_hidden_validate_check_positions_must_be_digits():
    assert is_valid_rf_reference("RF7A1") is False
    assert is_valid_rf_reference("RFA41") is False


def test_hidden_validate_non_alphanumeric():
    assert is_valid_rf_reference("RF74-1") is False
    assert is_valid_rf_reference("RF74!") is False


def test_hidden_validate_non_string():
    assert is_valid_rf_reference(None) is False
    assert is_valid_rf_reference(741) is False


def test_hidden_roundtrip_various_bases():
    for base in ("HELLO123", "X9", "42", "539007547034", "Z"):
        generated = rf_reference(base)
        assert generated == "RF" + generated[2:4] + base
        assert is_valid_rf_reference(generated) is True
        # Flipping the last character breaks the checksum.
        replacement = "0" if generated[-1] != "0" else "1"
        assert is_valid_rf_reference(generated[:-1] + replacement) is False
