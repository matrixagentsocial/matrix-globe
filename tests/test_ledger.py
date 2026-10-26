"""Ledger totals and hard-cap enforcement (caps checked BEFORE a call)."""
import pytest

from proof.config import Settings
from proof.ledger import HardCapExceeded, Ledger


def _settings(total: float = 100.0, per_run: float = 0.60) -> Settings:
    return Settings(
        base_url="https://api.meta.ai/v1",
        api_key="",
        model_builder="muse-spark-1.3-contributor",
        model_builder_external="muse-spark-1.3",
        model_reviewer="muse-wonder-1.0",
        max_usd_total=total,
        max_usd_per_run=per_run,
    )


def _entry(run_id: str, usd: float) -> dict:
    return {
        "run_id": run_id,
        "role": "builder",
        "model": "muse-spark-1.3",
        "effort": "medium",
        "input_tokens": 100,
        "cached_tokens": 10,
        "output_tokens": 50,
        "reasoning_tokens": 5,
        "usd": usd,
    }


def test_append_and_totals(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl", settings=_settings())
    ledger.append(_entry("run-1", 0.10))
    ledger.append(_entry("run-1", 0.05))
    ledger.append(_entry("run-2", 0.20))

    assert ledger.total_usd() == pytest.approx(0.35)
    assert ledger.run_usd("run-1") == pytest.approx(0.15)
    assert ledger.run_usd("run-2") == pytest.approx(0.20)
    assert ledger.run_usd("missing") == 0.0

    totals = ledger.totals()
    assert totals["total"] == pytest.approx(0.35)
    assert totals["run-1"] == pytest.approx(0.15)
    assert totals["run-2"] == pytest.approx(0.20)

    rows = ledger.entries()
    assert len(rows) == 3
    assert rows[0]["input_tokens"] == 100
    assert rows[0]["cached_tokens"] == 10
    assert rows[0]["reasoning_tokens"] == 5
    assert rows[0]["ts"]


def test_empty_ledger_totals(tmp_path):
    ledger = Ledger(tmp_path / "nope.jsonl", settings=_settings())
    assert ledger.entries() == []
    assert ledger.total_usd() == 0.0


def test_total_cap_raises_at_cap(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl", settings=_settings(total=0.30))
    ledger.append(_entry("run-1", 0.30))
    # Exactly at the cap counts as reached: no further call allowed.
    with pytest.raises(HardCapExceeded, match="MAX_USD_TOTAL"):
        ledger.check_caps("run-1")


def test_total_cap_raises_over_cap(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl", settings=_settings(total=0.30))
    ledger.append(_entry("run-1", 0.50))
    with pytest.raises(HardCapExceeded):
        ledger.check_caps("run-2")


def test_per_run_cap_raises(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl", settings=_settings(per_run=0.10))
    ledger.append(_entry("run-1", 0.10))
    with pytest.raises(HardCapExceeded, match="MAX_USD_PER_RUN"):
        ledger.check_caps("run-1")
    # A different, fresh run is still allowed.
    ledger.check_caps("run-2")


def test_under_caps_passes(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl", settings=_settings(total=1.0, per_run=0.5))
    ledger.append(_entry("run-1", 0.10))
    ledger.check_caps("run-1")  # must not raise
    ledger.check_caps(None)
