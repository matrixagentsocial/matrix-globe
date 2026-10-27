# --- hidden tests for running_balance (module task_a.py) ---
import copy
from decimal import Decimal

import pytest

from task_a import closing_balance, running_balance


def _tx(i, v, b, a):
    return {"id": i, "value_date": v, "booking_date": b, "amount": a}


def test_hidden_tie_booking_date_order():
    txs = [_tx("b", "2024-01-02", "2024-01-03", "10.00"), _tx("a", "2024-01-02", "2024-01-02", "-30.00"), _tx("c", "2024-01-01", "2024-01-05", "5.00")]
    rows = running_balance(txs, "100.00")
    assert [r["id"] for r in rows] == ["c", "a", "b"]
    assert [r["balance"] for r in rows] == [Decimal("105.00"), Decimal("75.00"), Decimal("85.00")]
    assert closing_balance(txs, "100.00") == Decimal("85.00")


def test_hidden_tie_id_order_same_dates():
    txs = [_tx("b", "2024-01-01", "2024-01-01", "10.00"), _tx("a", "2024-01-01", "2024-01-01", "20.00"), _tx("c", "2024-01-01", "2024-01-01", "-5.00")]
    rows = running_balance(txs, "0.00")
    assert [r["id"] for r in rows] == ["a", "b", "c"]
    assert [r["balance"] for r in rows] == [Decimal("20.00"), Decimal("30.00"), Decimal("25.00")]


def test_hidden_id_plain_string_order():
    # plain string ascending: "10" < "2" < "a"
    txs = [_tx("a", "2024-01-01", "2024-01-01", "1.00"), _tx("2", "2024-01-01", "2024-01-01", "2.00"), _tx("10", "2024-01-01", "2024-01-01", "4.00")]
    rows = running_balance(txs, "0.00")
    assert [r["id"] for r in rows] == ["10", "2", "a"]
    assert [r["balance"] for r in rows] == [Decimal("4.00"), Decimal("6.00"), Decimal("7.00")]


def test_hidden_value_date_primary_over_booking():
    txs = [_tx("x", "2024-01-03", "2024-01-01", "100.00"), _tx("y", "2024-01-01", "2024-01-09", "1.00")]
    rows = running_balance(txs, "0.00")
    assert [r["id"] for r in rows] == ["y", "x"]
    assert [r["balance"] for r in rows] == [Decimal("1.00"), Decimal("101.00")]


def test_hidden_full_row_shape_and_normalization():
    rows = running_balance([_tx("x", "2024-01-01", "2024-01-02", "10.5")], "0")
    assert rows == [{"id": "x", "value_date": "2024-01-01", "booking_date": "2024-01-02", "amount": Decimal("10.50"), "balance": Decimal("10.50")}]
    assert rows[0]["amount"].as_tuple().exponent == -2
    assert rows[0]["balance"].as_tuple().exponent == -2


def test_hidden_zero_amount_allowed():
    rows = running_balance([_tx("x", "2024-01-01", "2024-01-01", "0.00")], "50.00")
    assert rows[0]["amount"] == Decimal("0.00")
    assert rows[0]["balance"] == Decimal("50.00")


def test_hidden_negative_opening_and_overdraft():
    txs = [_tx("a", "2024-01-01", "2024-01-01", "-20.00"), _tx("b", "2024-01-02", "2024-01-02", "5.00")]
    rows = running_balance(txs, "-10.00")
    assert [r["balance"] for r in rows] == [Decimal("-30.00"), Decimal("-25.00")]
    assert closing_balance(txs, "-10.00") == Decimal("-25.00")


def test_hidden_empty_closing_quantized():
    assert running_balance([], "42.5") == []
    result = closing_balance([], "42.5")
    assert result == Decimal("42.50")
    assert result.as_tuple().exponent == -2


def test_hidden_does_not_mutate_input():
    txs = [_tx("b", "2024-01-02", "2024-01-03", "10.00"), _tx("a", "2024-01-01", "2024-01-01", "-1.00")]
    snapshot = copy.deepcopy(txs)
    running_balance(txs, "100.00")
    closing_balance(txs, "100.00")
    assert txs == snapshot


def test_hidden_duplicate_id_raises():
    with pytest.raises(ValueError):
        running_balance([_tx("x", "2024-01-01", "2024-01-01", "1.00"), _tx("x", "2024-01-03", "2024-01-03", "2.00")], "0.00")


def test_hidden_missing_key_raises():
    with pytest.raises(ValueError):
        running_balance([{"id": "x", "value_date": "2024-01-01", "amount": "1.00"}], "0.00")


def test_hidden_invalid_calendar_date_raises():
    with pytest.raises(ValueError):
        running_balance([_tx("x", "2024-02-30", "2024-01-01", "1.00")], "0.00")


def test_hidden_bad_date_format_raises():
    with pytest.raises(ValueError):
        running_balance([_tx("x", "2024-1-1", "2024-01-01", "1.00")], "0.00")


def test_hidden_amount_three_decimals_raises():
    with pytest.raises(ValueError):
        running_balance([_tx("x", "2024-01-01", "2024-01-01", "1.005")], "0.00")


def test_hidden_amount_non_string_raises():
    with pytest.raises(ValueError):
        running_balance([_tx("x", "2024-01-01", "2024-01-01", 10.0)], "0.00")


def test_hidden_opening_three_decimals_raises():
    with pytest.raises(ValueError):
        closing_balance([], "10.005")


def test_hidden_empty_id_raises():
    with pytest.raises(ValueError):
        running_balance([_tx("", "2024-01-01", "2024-01-01", "1.00")], "0.00")


def test_hidden_closing_matches_last_balance():
    txs = [_tx("b", "2024-03-01", "2024-03-01", "7.25"), _tx("a", "2024-03-01", "2024-03-01", "-2.25")]
    # tie on both dates, id a first: 10-2.25=7.75, +7.25=15.00
    rows = running_balance(txs, "10.00")
    assert [r["balance"] for r in rows] == [Decimal("7.75"), Decimal("15.00")]
    assert closing_balance(txs, "10.00") == rows[-1]["balance"] == Decimal("15.00")


def test_hidden_leap_date_valid():
    rows = running_balance([_tx("x", "2024-02-29", "2024-02-29", "1.00")], "0.00")
    assert rows[0]["balance"] == Decimal("1.00")
    with pytest.raises(ValueError):
        running_balance([_tx("y", "2023-02-29", "2023-02-29", "1.00")], "0.00")

# --- hidden tests for spanish_bank_csv (module task_b.py) ---
from decimal import Decimal

import pytest

from task_b import parse_bank_csv, summarize_transactions

HEADER = "Fecha;Concepto;Importe;Saldo"


def make(*rows):
    return HEADER + "\n" + "\n".join(rows) + ("\n" if rows else "")


def test_hidden_bom_stripped():
    rows = parse_bank_csv("\ufeff" + make("05/01/2024;A;1,00;"))
    assert rows[0]["amount"] == Decimal("1.00")


def test_hidden_thousands_and_negative():
    rows = parse_bank_csv(make("05/01/2024;A;-1.234,56;2.000,00"))
    assert rows[0]["amount"] == Decimal("-1234.56")
    assert rows[0]["balance"] == Decimal("2000.00")


def test_hidden_one_decimal_becomes_two():
    rows = parse_bank_csv(make("05/01/2024;A;0,5;"))
    assert rows[0]["amount"] == Decimal("0.50")
    assert rows[0]["amount"].as_tuple().exponent == -2


def test_hidden_empty_saldo_none():
    rows = parse_bank_csv(make("05/01/2024;A;1,00;"))
    assert rows[0]["balance"] is None


def test_hidden_quoted_semicolon_concept():
    rows = parse_bank_csv(make('05/01/2024;"Pago; tarjeta";-250,00;'))
    assert rows[0]["concept"] == "Pago; tarjeta"
    assert rows[0]["amount"] == Decimal("-250.00")


def test_hidden_quoted_doublequote_escape():
    rows = parse_bank_csv(make('05/01/2024;"Di ""x"" algo";10,00;'))
    assert rows[0]["concept"] == 'Di "x" algo'


def test_hidden_blank_lines_skipped_and_order_kept():
    text = HEADER + "\n\n06/01/2024;B;2,00;\n\n05/01/2024;A;1,00;\n"
    rows = parse_bank_csv(text)
    assert [r["concept"] for r in rows] == ["B", "A"]


def test_hidden_first_last_by_file_order_not_chronology():
    rows = parse_bank_csv(make("06/01/2024;B;2,00;", "05/01/2024;A;1,00;"))
    s = summarize_transactions(rows)
    assert s["first_date"] == "2024-01-06"
    assert s["last_date"] == "2024-01-05"


def test_hidden_summary_zero_amount_counts_only():
    rows = parse_bank_csv(make("05/01/2024;A;0,00;", "06/01/2024;B;10,00;"))
    s = summarize_transactions(rows)
    assert s["count"] == 2
    assert s["credits"] == Decimal("10.00")
    assert s["debits"] == Decimal("0.00")
    assert s["net"] == Decimal("10.00")


def test_hidden_summary_empty():
    assert summarize_transactions([]) == {
        "count": 0, "credits": Decimal("0.00"), "debits": Decimal("0.00"),
        "net": Decimal("0.00"), "first_date": None, "last_date": None,
    }


def test_hidden_summary_debits_negative_total():
    rows = parse_bank_csv(make("05/01/2024;A;-10,00;", "06/01/2024;B;-5,50;", "07/01/2024;C;3,00;"))
    s = summarize_transactions(rows)
    assert s["debits"] == Decimal("-15.50")
    assert s["credits"] == Decimal("3.00")
    assert s["net"] == Decimal("-12.50")


def test_hidden_bad_date_line_number():
    with pytest.raises(ValueError, match="line 3"):
        parse_bank_csv(make("05/01/2024;A;1,00;", "31/02/2024;B;1,00;"))


def test_hidden_bad_amount_line_number_after_blank():
    text = HEADER + "\n\n05/01/2024;A;1.234;\n"
    with pytest.raises(ValueError, match="line 3"):
        parse_bank_csv(text)


def test_hidden_english_amount_rejected():
    with pytest.raises(ValueError, match="line 2"):
        parse_bank_csv(make("05/01/2024;A;1,234.56;"))


def test_hidden_three_decimals_rejected():
    with pytest.raises(ValueError, match="line 2"):
        parse_bank_csv(make("05/01/2024;A;12,345;"))


def test_hidden_bad_thousands_group_rejected():
    with pytest.raises(ValueError, match="line 2"):
        parse_bank_csv(make("05/01/2024;A;1.23,45;"))


def test_hidden_missing_importe_line_number():
    with pytest.raises(ValueError, match="line 2"):
        parse_bank_csv(make("05/01/2024;A;;100,00"))


def test_hidden_wrong_field_count_line_number():
    with pytest.raises(ValueError, match="line 2"):
        parse_bank_csv(make("05/01/2024;A;1,00"))


def test_hidden_header_case_sensitive():
    with pytest.raises(ValueError):
        parse_bank_csv("Fecha;concepto;Importe;Saldo\n05/01/2024;A;1,00;\n")


def test_hidden_large_thousands():
    rows = parse_bank_csv(make("05/01/2024;A;1.234.567,89;"))
    assert rows[0]["amount"] == Decimal("1234567.89")

# --- hidden tests for spanish_tax_id (module task_c.py) ---
from task_c import classify_spanish_id, is_valid_spanish_id


def test_hidden_nif_zero_number():
    # 0 % 23 = 0 -> 'T'.
    assert classify_spanish_id("00000000T") == "NIF"


def test_hidden_nif_wrong_letter():
    assert classify_spanish_id("12345678A") is None
    assert is_valid_spanish_id("12345678A") is False


def test_hidden_nie_y_prefix():
    # Y -> 1: 11234567 % 23 = 10 -> 'X'.
    assert classify_spanish_id("Y1234567X") == "NIE"


def test_hidden_nie_z_prefix():
    # Z -> 2: 21234567 % 23 = 1 -> 'R'.
    assert classify_spanish_id("Z1234567R") == "NIE"


def test_hidden_nie_wrong_letter():
    assert classify_spanish_id("X1234567A") is None


def test_hidden_nie_lowercase_hyphens():
    assert classify_spanish_id("x-1234567-l") == "NIE"


def test_hidden_cif_digit_required_valid_and_wrong():
    # Digits 1234567: odd doubles 2+6+1+5, evens 2+4+6, total 26,
    # control digit 4, control letter 'D'. A requires the digit.
    assert classify_spanish_id("A12345674") == "CIF"
    assert classify_spanish_id("A1234567D") is None
    assert classify_spanish_id("A12345675") is None


def test_hidden_cif_letter_required():
    # P requires the control letter 'D' for digits 1234567.
    assert classify_spanish_id("P1234567D") == "CIF"
    assert classify_spanish_id("P12345674") is None


def test_hidden_cif_either_accepted():
    # C accepts either the correct digit or the correct letter.
    assert classify_spanish_id("C12345674") == "CIF"
    assert classify_spanish_id("C1234567D") == "CIF"
    assert classify_spanish_id("C1234567E") is None
    assert classify_spanish_id("C12345675") is None


def test_hidden_cif_given_example_wrong_control():
    assert classify_spanish_id("A58818501") == "CIF"
    assert classify_spanish_id("A58818502") is None
    assert classify_spanish_id("A5881850A") is None


def test_hidden_cif_zero_control_digit_and_letter():
    # Digits 0000000 give total 0, control digit 0, control letter 'J'.
    assert classify_spanish_id("A00000000") == "CIF"
    assert classify_spanish_id("P0000000J") == "CIF"
    assert classify_spanish_id("A0000000J") is None


def test_hidden_cif_disallowed_initials():
    # I, N, O and T are not in ABCDEFGHJKLMPQRSUVW.
    for text in ("I12345674", "N12345674", "O12345674", "T12345674"):
        assert classify_spanish_id(text) is None
        assert is_valid_spanish_id(text) is False


def test_hidden_wrong_lengths():
    assert classify_spanish_id("1234567Z") is None
    assert classify_spanish_id("12345678") is None
    assert classify_spanish_id("123456789Z") is None
    assert classify_spanish_id("X123456L") is None


def test_hidden_bad_characters():
    assert classify_spanish_id("123456789") is None  # control must be a letter
    assert classify_spanish_id("1234567*Z") is None
    assert classify_spanish_id("ABCDEFGHI") is None


def test_hidden_non_string_inputs():
    assert classify_spanish_id(None) is None
    assert classify_spanish_id(12345678) is None
    assert is_valid_spanish_id(None) is False
    assert is_valid_spanish_id(12345678) is False


def test_hidden_empty_and_blank():
    assert classify_spanish_id("") is None
    assert classify_spanish_id("   ") is None
    assert classify_spanish_id("---") is None
    assert is_valid_spanish_id("") is False


def test_hidden_spaces_and_hyphens_normalized():
    assert classify_spanish_id("1234-5678-Z") == "NIF"
    assert classify_spanish_id("A 5881850 1") == "CIF"
    assert is_valid_spanish_id(" x1234567l ") is True
