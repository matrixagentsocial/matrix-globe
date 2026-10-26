import pytest

from solution import add_months, monthly_schedule


def test_public_jan31_plus_one_leap():
    assert add_months("2024-01-31", 1) == "2024-02-29"


def test_public_feb28_sticky():
    assert add_months("2023-02-28", 1) == "2023-03-31"


def test_public_plain_day_kept():
    assert add_months("2023-02-27", 1) == "2023-03-27"


def test_public_schedule_anchored():
    assert monthly_schedule("2024-01-31", 3) == [
        "2024-02-29",
        "2024-03-31",
        "2024-04-30",
    ]


def test_public_months_out_of_range_raises():
    with pytest.raises(ValueError):
        add_months("2024-01-15", 2401)
