"""Cost maths, including cached tokens and reasoning-in-completion."""
import pytest

from proof.config import (
    PRICING,
    UnknownModelError,
    compute_cost,
    compute_cost_from_usage,
    get_pricing,
)


def test_pricing_table_matches_decisions():
    assert PRICING["muse-wonder-1.0"].input == 4.00
    assert PRICING["muse-wonder-1.0"].cached_input == 0.20
    assert PRICING["muse-wonder-1.0"].output == 20.00
    assert PRICING["muse-spark-1.3"].input == 1.25
    assert PRICING["muse-spark-1.3"].cached_input == 0.15
    assert PRICING["muse-spark-1.3"].output == 4.25
    assert PRICING["muse-spark-1.3-contributor"].input == 0.10
    assert PRICING["muse-spark-1.3-contributor"].cached_input == 0.002
    assert PRICING["muse-spark-1.3-contributor"].output == 0.20
    # Family members named in the task are present.
    for model in (
        "muse-spark-1.1",
        "muse-spark-1.2",
        "muse-spark-1.2-contributor",
    ):
        assert model in PRICING


def test_compute_cost_no_cache():
    # 1M input + 1M output on Wonder = 4 + 20.
    assert compute_cost("muse-wonder-1.0", 1_000_000, 1_000_000, 0) == pytest.approx(24.0)


def test_compute_cost_with_cached_tokens():
    # Spark 1.3: 500k cached at 0.15/M, 500k fresh at 1.25/M, 100k out at 4.25/M.
    usd = compute_cost("muse-spark-1.3", 1_000_000, 100_000, cached_tokens=500_000)
    expected = (500_000 * 0.15 + 500_000 * 1.25 + 100_000 * 4.25) / 1_000_000
    assert usd == pytest.approx(expected)


def test_compute_cost_all_cached():
    usd = compute_cost("muse-spark-1.3-contributor", 1_000_000, 0, cached_tokens=1_000_000)
    assert usd == pytest.approx(0.002)


def test_cached_tokens_clamped_to_prompt():
    # Cached larger than prompt must not produce negative fresh tokens.
    usd = compute_cost("muse-spark-1.3", 100, 0, cached_tokens=9999)
    assert usd == pytest.approx(100 * 0.15 / 1_000_000)


def test_reasoning_tokens_not_double_billed():
    # completion_tokens already includes reasoning; usage with reasoning
    # detail must cost the same as the plain completion count.
    usage = {
        "prompt_tokens": 1000,
        "completion_tokens": 500,
        "prompt_tokens_details": {"cached_tokens": 200},
        "completion_tokens_details": {"reasoning_tokens": 300},
    }
    with_reasoning = compute_cost_from_usage("muse-spark-1.3", usage)
    plain = compute_cost("muse-spark-1.3", 1000, 500, cached_tokens=200)
    assert with_reasoning == pytest.approx(plain)


def test_compute_cost_from_usage_object_shape():
    class Details:
        cached_tokens = 200

    class Usage:
        prompt_tokens = 1000
        completion_tokens = 500
        prompt_tokens_details = Details()
        completion_tokens_details = None

    usd = compute_cost_from_usage("muse-wonder-1.0", Usage())
    assert usd == pytest.approx(compute_cost("muse-wonder-1.0", 1000, 500, 200))


def test_unknown_model_refused():
    with pytest.raises(UnknownModelError, match="Unknown model id"):
        get_pricing("no-such-model")
    with pytest.raises(UnknownModelError):
        compute_cost("no-such-model", 10, 10)
