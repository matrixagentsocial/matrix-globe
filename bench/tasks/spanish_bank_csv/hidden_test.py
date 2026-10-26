from decimal import Decimal

import pytest

from solution import parse_bank_csv, summarize_transactions

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
