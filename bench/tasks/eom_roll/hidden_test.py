import pytest

from solution import add_months, monthly_schedule


def test_hidden_jan31_plus_two_returns_to_31():
    assert add_months("2024-01-31", 2) == "2024-03-31"


def test_hidden_jan31_plus_one_non_leap():
    assert add_months("2023-01-31", 1) == "2023-02-28"


def test_hidden_leap_day_plus_twelve():
    assert add_months("2024-02-29", 12) == "2025-02-28"


def test_hidden_leap_day_plus_one_sticky():
    assert add_months("2024-02-29", 1) == "2024-03-31"


def test_hidden_mar31_minus_one_leap():
    assert add_months("2024-03-31", -1) == "2024-02-29"


def test_hidden_mar31_minus_one_non_leap():
    assert add_months("2023-03-31", -1) == "2023-02-28"


def test_hidden_apr30_plus_one_sticky_to_31():
    # 2023-04-30 is the last day of April, so it sticks to 2023-05-31.
    assert add_months("2023-04-30", 1) == "2023-05-31"


def test_hidden_apr29_plus_one_not_sticky():
    assert add_months("2023-04-29", 1) == "2023-05-29"


def test_hidden_clamp_without_sticky():
    # May 31 -> April has only 30 days (clamp; also end-of-month).
    assert add_months("2023-05-31", -1) == "2023-04-30"


def test_hidden_year_rollover_forward():
    assert add_months("2024-12-15", 1) == "2025-01-15"
    assert add_months("2024-01-31", -1) == "2023-12-31"


def test_hidden_zero_months_identity():
    assert add_months("2023-06-15", 0) == "2023-06-15"
    assert add_months("2024-02-29", 0) == "2024-02-29"


def test_hidden_months_extreme_bounds():
    assert add_months("2023-06-30", 2400) == "2223-06-30"
    assert add_months("2023-06-15", -2400) == "1823-06-15"


def test_hidden_months_out_of_bounds_raise():
    with pytest.raises(ValueError):
        add_months("2023-06-15", -2401)
    with pytest.raises(ValueError):
        add_months("2023-06-15", 2401)


def test_hidden_months_type_errors():
    with pytest.raises(ValueError):
        add_months("2023-06-15", True)
    with pytest.raises(ValueError):
        add_months("2023-06-15", 1.5)
    with pytest.raises(ValueError):
        add_months("2023-06-15", "2")


def test_hidden_bad_dates_raise():
    with pytest.raises(ValueError):
        add_months("2023-02-29", 1)
    with pytest.raises(ValueError):
        add_months("2023-13-01", 1)
    with pytest.raises(ValueError):
        add_months("not-a-date", 1)
    with pytest.raises(ValueError):
        add_months(20230615, 1)


def test_hidden_schedule_anchor_not_iterative():
    # Anchored: Jan 30 -> Feb 28 (clamp) -> Mar 30 (from Jan 30).
    # Iterative stepping would give Mar 31 because Feb 28 is EOM.
    assert monthly_schedule("2023-01-30", 2) == ["2023-02-28", "2023-03-30"]


def test_hidden_schedule_feb28_anchor():
    assert monthly_schedule("2023-02-28", 2) == ["2023-03-31", "2023-04-30"]


def test_hidden_schedule_mid_month_and_length():
    assert monthly_schedule("2023-01-15", 3) == [
        "2023-02-15",
        "2023-03-15",
        "2023-04-15",
    ]
    schedule = monthly_schedule("2023-06-15", 120)
    assert len(schedule) == 120
    assert schedule[-1] == "2033-06-15"


def test_hidden_schedule_count_bounds():
    assert monthly_schedule("2023-01-15", 1) == ["2023-02-15"]
    with pytest.raises(ValueError):
        monthly_schedule("2023-01-15", 0)
    with pytest.raises(ValueError):
        monthly_schedule("2023-01-15", 121)
    with pytest.raises(ValueError):
        monthly_schedule("2023-01-15", True)


def test_hidden_schedule_bad_start_raises():
    with pytest.raises(ValueError):
        monthly_schedule("2023-02-29", 3)
