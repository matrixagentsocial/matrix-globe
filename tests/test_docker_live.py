"""Live Docker sandbox checks (GitHub Actions only).

Skipped unless ``MATRIX_GLOBE_DOCKER=1`` and the runner image exists. The CI
job builds ``docker/Dockerfile`` first. These are the guarantees the desk
relies on for external code: tests run, there is no network, a runaway
process is stopped, and no secret reaches the container.
"""
from __future__ import annotations

import os

import pytest

from proof.pytest_runner import run_pytest
from proof.sandbox.docker import DockerSandbox

pytestmark = pytest.mark.skipif(
    os.getenv("MATRIX_GLOBE_DOCKER") != "1",
    reason="live Docker checks run in CI only (MATRIX_GLOBE_DOCKER=1)",
)

SOLUTION = "def add(a, b):\n    return a + b\n"


def _outcomes(result):
    return {t.name.split("::")[-1]: t.outcome for t in result.tests}


def test_docker_runs_pytest_and_reports_outcomes():
    tests = {
        "test_add.py": (
            "from solution import add\n\n"
            "def test_ok():\n    assert add(2, 2) == 4\n\n"
            "def test_bad():\n    assert add(2, 2) == 5\n"
        )
    }
    result = run_pytest(DockerSandbox(), SOLUTION, tests, timeout_s=60, origin="external")
    outcomes = _outcomes(result)
    assert outcomes.get("test_ok") == "passed", result
    assert outcomes.get("test_bad") == "failed", result


def test_docker_has_no_network():
    tests = {
        "test_net.py": (
            "import socket\nimport pytest\n\n"
            "def test_no_network():\n"
            "    with pytest.raises(OSError):\n"
            "        socket.create_connection(('1.1.1.1', 53), timeout=3)\n"
        )
    }
    result = run_pytest(DockerSandbox(), SOLUTION, tests, timeout_s=60, origin="external")
    assert _outcomes(result).get("test_no_network") == "passed", result


def test_docker_sees_no_secrets(monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "should-never-leak")
    tests = {
        "test_env.py": (
            "import os\n\n"
            "def test_no_secret():\n"
            "    assert 'MODEL_API_KEY' not in os.environ\n"
            "    assert not any(k.endswith('_KEY') for k in os.environ)\n"
        )
    }
    result = run_pytest(DockerSandbox(), SOLUTION, tests, timeout_s=60, origin="external")
    assert _outcomes(result).get("test_no_secret") == "passed", result


def test_docker_timeout_kills_runaway_code():
    tests = {"test_loop.py": "def test_forever():\n    while True:\n        pass\n"}
    result = run_pytest(DockerSandbox(), SOLUTION, tests, timeout_s=8, origin="external")
    assert result.timed_out
