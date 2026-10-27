"""Pilot report writer: UTF-8 output and R shown as UNREVIEWED."""
import json

from bench.pilot_report import display_status, write_report


def test_write_report_utf8_and_r_unreviewed(tmp_path):
    row = {"task_id": "pr_dev_1", "target_id": "clean", "condition": "R",
           "fixed": True, "all_pass": True, "hidden_before_passed": 3,
           "hidden_before_total": 3, "hidden_after_passed": 3,
           "hidden_after_total": 3, "regressions": 0, "damaged": False,
           "usd": 0.0, "reviewer_usd": 0.0, "status": "VERIFIED Café"}
    jsonl = tmp_path / "condR.jsonl"
    jsonl.write_text(json.dumps(row) + "\n", encoding="utf-8")
    out = write_report([str(jsonl)], tmp_path / "summary.md", title="T")
    raw = out.read_bytes()
    assert not raw.startswith(b"\xff\xfe")
    text = raw.decode("utf-8")
    assert "UNREVIEWED" in text
    assert display_status(row) == "UNREVIEWED"
    assert display_status({"condition": "D", "status": "VERIFIED"}) == "VERIFIED"
