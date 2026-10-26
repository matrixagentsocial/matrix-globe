"""JUnit parsing and pytest_runner behaviour (M1)."""
import sys

from proof.pytest_runner import parse_junit_xml, run_pytest
from proof.sandbox.local import LocalSandbox

SAMPLE_XML = """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest" tests="4" failures="1" errors="1" skipped="1">
    <testcase classname="public_test" name="test_ok" time="0.01"/>
    <testcase classname="public_test" name="test_bad" time="0.01">
      <failure message="assert 1 == 2">details</failure>
    </testcase>
    <testcase classname="public_test" name="test_err" time="0.01">
      <error message="boom">trace</error>
    </testcase>
    <testcase classname="public_test" name="test_skip" time="0.0">
      <skipped message="not today"/>
    </testcase>
  </testsuite>
</testsuites>
"""


def test_parse_junit_outcomes():
    tests, collection_errors = parse_junit_xml(SAMPLE_XML)
    by_name = {t.name: t.outcome for t in tests}
    assert by_name["public_test::test_ok"] == "passed"
    assert by_name["public_test::test_bad"] == "failed"
    assert by_name["public_test::test_err"] == "error"
    assert by_name["public_test::test_skip"] == "skipped"
    assert collection_errors == []


def test_parse_junit_empty():
    assert parse_junit_xml("") == ([], [])


def test_run_pytest_pass_and_fail():
    sandbox = LocalSandbox()
    solution = "def add(a, b):\n    return a + b\n"
    tests = {
        "public_test.py": (
            "from solution import add\n\n"
            "def test_add_ok():\n    assert add(1, 2) == 3\n\n"
            "def test_add_bad():\n    assert add(1, 2) == 4\n"
        )
    }
    result = run_pytest(sandbox, solution, tests)
    assert result.total == 2
    assert result.passed == 1
    assert result.all_passed is False
    outcomes = {t.name: t.outcome for t in result.tests}
    assert outcomes["public_test::test_add_ok"] == "passed"
    assert outcomes["public_test::test_add_bad"] == "failed"


def test_run_pytest_collection_error():
    sandbox = LocalSandbox()
    result = run_pytest(
        sandbox,
        "def broken(:\n",
        {"public_test.py": "from solution import broken\n\ndef test_x():\n    assert True\n"},
    )
    assert result.all_passed is False
    assert result.collection_errors or any(t.outcome == "error" for t in result.tests)


def test_run_pytest_timeout():
    sandbox = LocalSandbox()
    result = run_pytest(
        sandbox,
        "import time\ntime.sleep(30)\ndef f():\n    pass\n",
        {"public_test.py": "from solution import f\n\ndef test_x():\n    f()\n"},
        timeout_s=2,
    )
    assert result.timed_out is True
    assert result.all_passed is False
