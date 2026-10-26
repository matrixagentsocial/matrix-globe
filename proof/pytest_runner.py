"""Run pytest inside a sandbox and parse per-test outcomes.

Writes ``solution.py`` plus the given test files into the sandbox,
runs ``python -m pytest -q -p no:cacheprovider --junitxml=report.xml``
and parses the JUnit XML with the stdlib. Per-test outcomes are
``passed`` / ``failed`` / ``error`` / ``skipped``; collection errors
and timeouts are reported separately (PLAN.md sections 4 and 5.2).
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from proof.sandbox.base import RunResult, Sandbox

PYTEST_TIMEOUT_S = 10.0


@dataclass
class TestOutcome:
    name: str
    outcome: str  # passed | failed | error | skipped
    message: str = ""


@dataclass
class PytestRunResult:
    tests: list[TestOutcome] = field(default_factory=list)
    collection_errors: list[str] = field(default_factory=list)
    timed_out: bool = False
    run: RunResult | None = None

    @property
    def passed(self) -> int:
        return sum(1 for t in self.tests if t.outcome == "passed")

    @property
    def total(self) -> int:
        return len(self.tests)

    @property
    def all_passed(self) -> bool:
        return (
            not self.timed_out
            and not self.collection_errors
            and self.total > 0
            and self.passed == self.total
        )

    def counts(self) -> dict[str, int]:
        result = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}
        for t in self.tests:
            result[t.outcome] = result.get(t.outcome, 0) + 1
        return result


def _is_collection_error(testcase: ET.Element, error_el: ET.Element) -> bool:
    classname = testcase.get("classname", "")
    name = testcase.get("name", "")
    text = (error_el.get("message", "") + " " + (error_el.text or "")).lower()
    if not classname:
        return True
    if name.startswith("collection") or classname in ("", "collection"):
        return True
    markers = (
        "collection error",
        "collecterror",
        "modulenotfounderror",
        "importerror",
        "syntaxerror",
        "indentationerror",
    )
    # A module-level import/syntax failure surfaces as a collection error:
    # pytest reports it on a testcase whose name is the module, not a test.
    if not name.startswith("test"):
        return True
    return any(m in text.replace(" ", "") for m in ("importerror", "syntaxerror")) and not classname


def parse_junit_xml(xml_text: str) -> tuple[list[TestOutcome], list[str]]:
    """Parse JUnit XML into (per-test outcomes, collection errors)."""
    tests: list[TestOutcome] = []
    collection_errors: list[str] = []
    if not xml_text or not xml_text.strip():
        return tests, collection_errors
    root = ET.fromstring(xml_text)
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    for suite in suites:
        # Suite-level errors with no testcase children are collection errors.
        suite_testcases = suite.findall("testcase")
        for err in suite.findall("error"):
            msg = err.get("message", "") or (err.text or "")
            if msg.strip():
                collection_errors.append(msg.strip())
        for case in suite_testcases:
            classname = case.get("classname", "")
            name = case.get("name", "")
            full_name = f"{classname}::{name}" if classname else name
            failure = case.find("failure")
            error = case.find("error")
            skipped = case.find("skipped")
            if error is not None and _is_collection_error(case, error):
                msg = error.get("message", "") or (error.text or "") or full_name
                collection_errors.append(msg.strip())
                tests.append(TestOutcome(name=full_name, outcome="error", message=msg.strip()))
            elif error is not None:
                msg = error.get("message", "") or (error.text or "")
                tests.append(TestOutcome(name=full_name, outcome="error", message=msg.strip()))
            elif failure is not None:
                msg = failure.get("message", "") or (failure.text or "")
                tests.append(TestOutcome(name=full_name, outcome="failed", message=msg.strip()))
            elif skipped is not None:
                msg = skipped.get("message", "") or ""
                tests.append(TestOutcome(name=full_name, outcome="skipped", message=msg.strip()))
            else:
                tests.append(TestOutcome(name=full_name, outcome="passed"))
    return tests, collection_errors


def run_pytest(
    sandbox: Sandbox,
    solution_code: str,
    test_files: dict[str, str],
    timeout_s: float = PYTEST_TIMEOUT_S,
    *,
    origin: str = "bench",
) -> PytestRunResult:
    """Run *test_files* against *solution_code* in *sandbox*.

    ``test_files`` maps file name (e.g. ``"public_test.py"``) to source.
    The sandbox receives ``solution.py`` plus those files and runs
    pytest with a 10 s default timeout per run.
    """
    files: dict[str, str] = {"solution.py": solution_code}
    files.update(test_files)
    test_names = sorted(test_files)
    cmd = [
        sandbox.python_cmd,
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        "--junitxml=report.xml",
        *test_names,
    ]
    run = sandbox.run(files, cmd, timeout_s=timeout_s, origin=origin)
    result = PytestRunResult(timed_out=run.timed_out, run=run)
    xml_text = run.output_files.get("report.xml", "")
    if xml_text.strip():
        try:
            tests, collection_errors = parse_junit_xml(xml_text)
            result.tests = tests
            result.collection_errors = collection_errors
        except ET.ParseError as exc:
            result.collection_errors.append(f"could not parse report.xml: {exc}")
    if run.timed_out:
        if not result.collection_errors and not result.tests:
            result.collection_errors.append("pytest run timed out")
    elif not xml_text.strip():
        detail = (run.stderr or run.stdout or "").strip()
        result.collection_errors.append(
            f"pytest produced no report.xml (exit={run.exit})"
            + (f": {detail[:500]}" if detail else "")
        )
    return result
