# --- hidden tests for day_count (module task_a.py) ---
from decimal import Decimal

import pytest

from task_a import accrued_interest, day_count_fraction


def test_hidden_us_start_feb_last_adjusts_both():
    # 2023-02-28 is last day of Feb (non-leap): d1 -> 30, and Mar 31 -> 30.
    assert day_count_fraction("2023-02-28", "2023-03-31", "30/360_US") == Decimal("0.0833333333")
    assert day_count_fraction("2023-02-28", "2023-03-30", "30/360_US") == Decimal("0.0833333333")


def test_hidden_us_end_feb_last_only_when_start_feb_last():
    # Start Jan 31 is not Feb-last, so Feb 28/29 keep their real day: 28/360 and 29/360.
    assert day_count_fraction("2023-01-31", "2023-02-28", "30/360_US") == Decimal("0.0777777778")
    assert day_count_fraction("2024-01-31", "2024-02-29", "30/360_US") == Decimal("0.0805555556")


def test_hidden_us_start_feb_last_leap():
    assert day_count_fraction("2024-02-29", "2024-03-31", "30/360_US") == Decimal("0.0833333333")
    assert day_count_fraction("2024-02-29", "2024-03-29", "30/360_US") == Decimal("0.0805555556")


def test_hidden_us_end_31_kept_when_d1_below_30():
    # d1 = 1, so Dec 31 stays 31: 30*11 + 30 = 360 days.
    assert day_count_fraction("2024-01-01", "2024-12-31", "30/360_US") == Decimal("1.0000000000")
    assert day_count_fraction("2024-03-31", "2024-04-30", "30/360_US") == Decimal("0.0833333333")


def test_hidden_30e_caps_days_without_feb_rule():
    # 30E: d1 = 28 (not capped up), d2 = 30 -> 32/360, unlike US 30/360.
    assert day_count_fraction("2023-02-28", "2023-03-31", "30E/360") == Decimal("0.0888888889")
    # 30E caps Dec 31 to 30: 359/360, unlike US above.
    assert day_count_fraction("2024-01-01", "2024-12-31", "30E/360") == Decimal("0.9972222222")


def test_hidden_30e_and_us_agree_on_plain_half_year():
    assert day_count_fraction("2024-01-15", "2024-07-15", "30E/360") == Decimal("0.5000000000")
    assert day_count_fraction("2024-01-15", "2024-07-15", "30/360_US") == Decimal("0.5000000000")
    assert day_count_fraction("2024-01-31", "2024-02-01", "30/360_US") == Decimal("0.0027777778")


def test_hidden_act365f_counts_leap_day_but_denominator_365():
    # 2023-06-15 to 2024-06-15 is 366 actual days / 365.
    assert day_count_fraction("2023-06-15", "2024-06-15", "ACT/365F") == Decimal("1.0027397260")
    assert day_count_fraction("2024-01-01", "2024-01-02", "ACT/365F") == Decimal("0.0027397260")


def test_hidden_act_act_leap_and_multi_year():
    assert day_count_fraction("2024-01-01", "2025-01-01", "ACT/ACT_ISDA") == Decimal("1.0000000000")
    assert day_count_fraction("2023-01-01", "2025-01-01", "ACT/ACT_ISDA") == Decimal("2.0000000000")
    assert day_count_fraction("2023-01-01", "2023-12-31", "ACT/ACT_ISDA") == Decimal("0.9972602740")


def test_hidden_act_act_year_boundary_denominators():
    # 1 day in leap 2024 portion before 2025, and 1 day in non-leap 2023 before 2024.
    assert day_count_fraction("2024-12-31", "2025-01-01", "ACT/ACT_ISDA") == Decimal("0.0027322404")
    assert day_count_fraction("2023-12-31", "2024-01-01", "ACT/ACT_ISDA") == Decimal("0.0027397260")


def test_hidden_act_act_february_leap_vs_nonleap():
    # Feb 2020: 29/366; Feb 2019: 28/365.
    assert day_count_fraction("2020-02-01", "2020-03-01", "ACT/ACT_ISDA") == Decimal("0.0792349727")
    assert day_count_fraction("2019-02-01", "2019-03-01", "ACT/ACT_ISDA") == Decimal("0.0767123288")


def test_hidden_equal_dates_zero_all_conventions():
    for convention in ("30/360_US", "30E/360", "ACT/365F", "ACT/ACT_ISDA"):
        result = day_count_fraction("2024-02-29", "2024-02-29", convention)
        assert result == Decimal("0.0000000000")
        assert result.as_tuple().exponent == -10


def test_hidden_fraction_exponent_ten_places():
    result = day_count_fraction("2024-01-01", "2024-04-01", "ACT/365F")
    assert result.as_tuple().exponent == -10
    assert day_count_fraction("2024-02-28", "2024-02-29", "ACT/ACT_ISDA") == Decimal("0.0027322404")


def test_hidden_accrued_act_act_split():
    # 5000 * 0.06 * (31/365 + 31/366) = 50.8892... -> 50.89
    assert accrued_interest("5000.00", "6", "2023-12-01", "2024-02-01", "ACT/ACT_ISDA") == Decimal("50.89")


def test_hidden_accrued_act365f_exact():
    # 10000 * 0.05 * 91/365 = 124.6575... -> 124.66
    assert accrued_interest("10000.00", "5", "2024-01-01", "2024-04-01", "ACT/365F") == Decimal("124.66")
    assert accrued_interest("1000.00", "10", "2023-01-01", "2024-01-01", "ACT/ACT_ISDA") == Decimal("100.00")
    assert accrued_interest("12000.00", "4", "2024-01-15", "2024-07-15", "30E/360") == Decimal("240.00")


def test_hidden_accrued_uses_unrounded_fraction():
    # Unrounded: 10000000 * 1.00 * 91/365 = 2493150.6849... -> 2493150.68.
    # Using the 10dp fraction 0.2493150685 would give 2493150.69.
    assert accrued_interest("10000000.00", "100", "2024-01-01", "2024-04-01", "ACT/365F") == Decimal("2493150.68")


def test_hidden_accrued_equal_dates_and_zero_rate():
    assert accrued_interest("10000.00", "5", "2024-01-15", "2024-01-15", "ACT/365F") == Decimal("0.00")
    assert accrued_interest("10000.00", "0", "2024-01-01", "2024-12-31", "30/360_US") == Decimal("0.00")
    assert accrued_interest("0.00", "5", "2024-01-01", "2024-07-01", "ACT/365F") == Decimal("0.00")


def test_hidden_end_before_start_raises():
    with pytest.raises(ValueError):
        day_count_fraction("2024-07-01", "2024-01-01", "ACT/365F")
    with pytest.raises(ValueError):
        accrued_interest("1000.00", "5", "2024-07-01", "2024-01-01", "30/360_US")


def test_hidden_unknown_convention_raises():
    with pytest.raises(ValueError):
        day_count_fraction("2024-01-01", "2024-07-01", "ACT/360")
    with pytest.raises(ValueError):
        day_count_fraction("2024-01-01", "2024-07-01", "act/365f")
    with pytest.raises(ValueError):
        day_count_fraction("2024-01-01", "2024-07-01", None)


def test_hidden_bad_date_raises():
    with pytest.raises(ValueError):
        day_count_fraction("2024-02-30", "2024-07-01", "ACT/365F")
    with pytest.raises(ValueError):
        day_count_fraction("2024-01-01", "01/07/2024", "30E/360")


def test_hidden_accrued_invalid_money_raises():
    with pytest.raises(ValueError):
        accrued_interest("10.005", "5", "2024-01-01", "2024-07-01", "ACT/365F")
    with pytest.raises(ValueError):
        accrued_interest("-100.00", "5", "2024-01-01", "2024-07-01", "ACT/365F")
    with pytest.raises(ValueError):
        accrued_interest("100.00", "101", "2024-01-01", "2024-07-01", "ACT/365F")
    with pytest.raises(ValueError):
        accrued_interest("100.00", "-1", "2024-01-01", "2024-07-01", "ACT/365F")

# --- hidden tests for fifo_cost (module task_b.py) ---
from decimal import Decimal

import pytest

from task_b import fifo_report


def _buy(date, qty, price, fee="0.00"):
    return {"date": date, "side": "BUY", "quantity": qty, "price": price, "fee": fee}


def _sell(date, qty, price, fee="0.00"):
    return {"date": date, "side": "SELL", "quantity": qty, "price": price, "fee": fee}


def test_hidden_buy_only_fee_in_lot_cost():
    result = fifo_report([_buy("2024-01-01", 10, "10.00", "5.00")])
    assert result["sales"] == []
    assert result["total_realized"] == Decimal("0.00")
    assert result["remaining"] == [
        {"quantity": 10, "unit_cost": Decimal("10.5000"), "total_cost": Decimal("105.00")}
    ]
    assert result["inventory_quantity"] == 10


def test_hidden_buy_and_sell_fees():
    result = fifo_report(
        [
            _buy("2024-01-01", 10, "10.00", "10.00"),
            _sell("2024-01-02", 5, "20.00", "5.00"),
        ]
    )
    # Lot total 110; half consumed = 55; proceeds 100-5=95; realized 40.
    assert result["sales"][0]["proceeds"] == Decimal("95.00")
    assert result["sales"][0]["cost"] == Decimal("55.00")
    assert result["sales"][0]["realized"] == Decimal("40.00")
    assert result["remaining"] == [
        {"quantity": 5, "unit_cost": Decimal("11.0000"), "total_cost": Decimal("55.00")}
    ]


def test_hidden_fee_default_omitted():
    trades = [
        {"date": "2024-01-01", "side": "BUY", "quantity": 10, "price": "10.00"},
        {"date": "2024-01-02", "side": "SELL", "quantity": 5, "price": "12.00"},
    ]
    result = fifo_report(trades)
    assert result["sales"][0]["proceeds"] == Decimal("60.00")
    assert result["sales"][0]["cost"] == Decimal("50.00")
    assert result["sales"][0]["realized"] == Decimal("10.00")


def test_hidden_proportional_partial_cost_four_dp_price():
    result = fifo_report(
        [_buy("2024-01-01", 3, "3.3333"), _sell("2024-01-02", 1, "10.00")]
    )
    # Lot total 9.9999; 1/3 consumed 3.3333 -> cost 3.33, realized 6.67.
    assert result["sales"][0]["cost"] == Decimal("3.33")
    assert result["sales"][0]["realized"] == Decimal("6.67")
    assert result["remaining"] == [
        {"quantity": 2, "unit_cost": Decimal("3.3333"), "total_cost": Decimal("6.67")}
    ]


def test_hidden_two_sales_total_is_sum_of_realized():
    result = fifo_report(
        [
            _buy("2024-01-01", 10, "10.00"),
            _sell("2024-01-02", 4, "15.00"),
            _sell("2024-01-03", 6, "15.00"),
        ]
    )
    assert [s["realized"] for s in result["sales"]] == [
        Decimal("20.00"),
        Decimal("30.00"),
    ]
    assert result["total_realized"] == Decimal("50.00")
    assert result["remaining"] == []


def test_hidden_interleaved_fifo_across_buys():
    result = fifo_report(
        [
            _buy("2024-01-01", 10, "10.00"),
            _sell("2024-01-02", 5, "30.00"),
            _buy("2024-01-03", 10, "20.00"),
            _sell("2024-01-04", 10, "30.00"),
        ]
    )
    assert result["sales"][0]["realized"] == Decimal("100.00")
    # Second sale: 5 @10 (50) + 5 @20 (100) = 150 cost, 300 proceeds.
    assert result["sales"][1]["cost"] == Decimal("150.00")
    assert result["sales"][1]["realized"] == Decimal("150.00")
    assert result["total_realized"] == Decimal("250.00")
    assert result["remaining"] == [
        {"quantity": 5, "unit_cost": Decimal("20.0000"), "total_cost": Decimal("100.00")}
    ]


def test_hidden_process_in_given_order_not_sorted():
    result = fifo_report(
        [_buy("2024-02-01", 10, "10.00"), _sell("2024-01-01", 5, "20.00")]
    )
    assert result["sales"][0]["date"] == "2024-01-01"
    assert result["sales"][0]["realized"] == Decimal("50.00")
    assert result["inventory_quantity"] == 5


def test_hidden_remaining_multiple_lots_oldest_first():
    result = fifo_report(
        [
            _buy("2024-01-01", 5, "10.00"),
            _buy("2024-01-02", 5, "20.00"),
            _sell("2024-01-03", 3, "15.00"),
        ]
    )
    assert result["sales"][0]["proceeds"] == Decimal("45.00")
    assert result["sales"][0]["cost"] == Decimal("30.00")
    assert result["sales"][0]["realized"] == Decimal("15.00")
    assert result["remaining"] == [
        {"quantity": 2, "unit_cost": Decimal("10.0000"), "total_cost": Decimal("20.00")},
        {"quantity": 5, "unit_cost": Decimal("20.0000"), "total_cost": Decimal("100.00")},
    ]
    assert result["inventory_quantity"] == 7


def test_hidden_four_dp_price_quantization():
    result = fifo_report(
        [_buy("2024-01-01", 10, "10.1234"), _sell("2024-01-02", 3, "20.5555")]
    )
    # Proceeds 61.6665 -> 61.67; cost 101.234*3/10=30.3702 -> 30.37;
    # realized 31.2963 -> 31.30.
    assert result["sales"][0]["proceeds"] == Decimal("61.67")
    assert result["sales"][0]["cost"] == Decimal("30.37")
    assert result["sales"][0]["realized"] == Decimal("31.30")


def test_hidden_exponents_two_and_four_dp():
    result = fifo_report(
        [_buy("2024-01-01", 10, "10.00"), _sell("2024-01-02", 4, "15.00")]
    )
    sale = result["sales"][0]
    for key in ("proceeds", "cost", "realized"):
        assert sale[key].as_tuple().exponent == -2
    assert result["total_realized"].as_tuple().exponent == -2
    assert result["remaining"][0]["unit_cost"].as_tuple().exponent == -4
    assert result["remaining"][0]["total_cost"].as_tuple().exponent == -2


def test_hidden_oversell_despite_later_buy_raises():
    with pytest.raises(ValueError):
        fifo_report(
            [
                _buy("2024-01-01", 5, "10.00"),
                _sell("2024-01-02", 6, "12.00"),
                _buy("2024-01-03", 10, "10.00"),
            ]
        )


def test_hidden_sell_with_no_inventory_raises():
    with pytest.raises(ValueError):
        fifo_report([_sell("2024-01-01", 1, "10.00")])


def test_hidden_invalid_dates_raise():
    with pytest.raises(ValueError):
        fifo_report([_buy("2024-02-30", 1, "10.00")])
    with pytest.raises(ValueError):
        fifo_report([_buy("2024-1-01", 1, "10.00")])
    with pytest.raises(ValueError):
        fifo_report([_buy("01/01/2024", 1, "10.00")])


def test_hidden_bad_side_raises():
    with pytest.raises(ValueError):
        fifo_report(
            [{"date": "2024-01-01", "side": "buy", "quantity": 1, "price": "10.00"}]
        )
    with pytest.raises(ValueError):
        fifo_report(
            [{"date": "2024-01-01", "side": "HOLD", "quantity": 1, "price": "10.00"}]
        )


def test_hidden_bool_and_zero_quantity_raise():
    with pytest.raises(ValueError):
        fifo_report([_buy("2024-01-01", True, "10.00")])
    with pytest.raises(ValueError):
        fifo_report([_buy("2024-01-01", 0, "10.00")])


def test_hidden_price_zero_and_too_many_places_raise():
    with pytest.raises(ValueError):
        fifo_report([_buy("2024-01-01", 1, "0")])
    with pytest.raises(ValueError):
        fifo_report([_buy("2024-01-01", 1, "10.12345")])


def test_hidden_negative_fee_and_missing_key_raise():
    with pytest.raises(ValueError):
        fifo_report([_buy("2024-01-01", 1, "10.00", "-1.00")])
    with pytest.raises(ValueError):
        fifo_report([{"date": "2024-01-01", "side": "BUY", "quantity": 1}])
    with pytest.raises(ValueError):
        fifo_report(["not-a-dict"])

# --- hidden tests for iban_validation (module task_c.py) ---
import pytest

from task_c import normalize_iban, validate_iban


def test_hidden_valid_fr_iban():
    assert validate_iban("FR14 2004 1010 0505 0001 3M02 606") is True


def test_hidden_valid_es_iban():
    assert validate_iban("ES91 2100 0418 4502 0005 1332") is True


def test_hidden_valid_it_iban():
    assert validate_iban("IT60 X054 2811 1010 0000 0123 456") is True


def test_hidden_valid_nl_iban():
    assert validate_iban("NL91 ABNA 0417 1643 00") is True


def test_hidden_valid_be_iban():
    assert validate_iban("BE68 5390 0754 7034") is True


def test_hidden_valid_ch_iban():
    assert validate_iban("CH93 0076 2011 6238 5295 7") is True


def test_hidden_valid_no_iban():
    assert validate_iban("NO93 8601 1117 947") is True


def test_hidden_lowercase_valid():
    assert validate_iban("gb29 nwbk 6016 1331 9268 19") is True


def test_hidden_no_spaces_valid():
    assert validate_iban("DE89370400440532013000") is True


def test_hidden_leading_trailing_spaces():
    assert validate_iban("  GB29 NWBK 6016 1331 9268 19  ") is True


def test_hidden_bad_check_digits():
    assert validate_iban("DE88 3704 0044 0532 0130 00") is False


def test_hidden_unknown_country():
    assert validate_iban("US29 NWBK 6016 1331 9268 19") is False


def test_hidden_dashes_rejected():
    assert validate_iban("GB29-NWBK-6016-1331-9268-19") is False


def test_hidden_empty_rejected():
    assert validate_iban("") is False
    assert validate_iban("   ") is False


def test_hidden_letter_in_check_digits():
    assert validate_iban("GB2A NWBK 6016 1331 9268 19") is False


def test_hidden_gb_too_long():
    assert validate_iban("GB29 NWBK 6016 1331 9268 199") is False


def test_hidden_non_string_returns_false():
    assert validate_iban(None) is False
    assert validate_iban(12345) is False


def test_hidden_normalize_non_string_raises():
    with pytest.raises(ValueError):
        normalize_iban(None)


def test_hidden_swapped_digits_invalid():
    # Valid DE IBAN with two BBAN digits swapped must fail mod-97.
    assert validate_iban("DE89 3704 0044 0532 0130 01") is False
