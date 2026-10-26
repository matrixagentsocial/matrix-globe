"""Local sandbox: trusted-only, scrubbed env, timeout (M1)."""
import os
import sys

import pytest

from proof.sandbox.docker import DEFAULT_IMAGE, build_docker_command
from proof.sandbox.local import LocalSandbox, scrubbed_env


def test_local_runs_trusted_bench_code(tmp_path):
    sandbox = LocalSandbox()
    result = sandbox.run(
        {"hello.py": "print('hello from sandbox')\n"},
        [sys.executable, "hello.py"],
        timeout_s=10,
        origin="bench",
    )
    assert result.timed_out is False
    assert result.exit == 0
    assert "hello from sandbox" in result.stdout


def test_local_refuses_non_bench_origin():
    sandbox = LocalSandbox()
    with pytest.raises(PermissionError):
        sandbox.run(
            {"x.py": "print(1)\n"},
            [sys.executable, "x.py"],
            origin="external",
        )


def test_local_refuses_constructor_origin():
    sandbox = LocalSandbox(origin="desk")
    with pytest.raises(PermissionError):
        sandbox.run({"x.py": "print(1)\n"}, [sys.executable, "x.py"])


def test_local_scrubbed_env_hides_secrets(monkeypatch, tmp_path):
    monkeypatch.setenv("MODEL_API_KEY", "should-never-leak")
    monkeypatch.setenv("SOME_OTHER_KEY", "also-secret")
    sandbox = LocalSandbox()
    code = (
        "import os\n"
        "print('MODEL_API_KEY' in os.environ)\n"
        "print('SOME_OTHER_KEY' in os.environ)\n"
        "print('PATH' in os.environ)\n"
    )
    result = sandbox.run({"probe.py": code}, [sys.executable, "probe.py"], origin="bench")
    assert result.exit == 0
    lines = result.stdout.split()
    assert lines[0] == "False"
    assert lines[1] == "False"
    assert lines[2] == "True"


def test_scrubbed_env_allowlist(tmp_path):
    env = scrubbed_env(tmp_path)
    assert not any(k.upper().endswith("_KEY") for k in env)
    assert "MODEL_API_KEY" not in env


def test_local_timeout():
    sandbox = LocalSandbox()
    result = sandbox.run(
        {"slow.py": "import time\ntime.sleep(30)\n"},
        [sys.executable, "slow.py"],
        timeout_s=1,
        origin="bench",
    )
    assert result.timed_out is True
    assert result.exit is None


def test_local_rejects_path_escape():
    sandbox = LocalSandbox()
    with pytest.raises(ValueError):
        sandbox.run({"../evil.py": "print(1)\n"}, [sys.executable, "evil.py"], origin="bench")


def test_docker_command_construction(tmp_path):
    cmd = build_docker_command(tmp_path, ["python", "-m", "pytest", "-q"])
    assert cmd[:2] == ["docker", "run"]
    assert "--rm" in cmd
    idx = cmd.index("--network")
    assert cmd[idx + 1] == "none"
    assert cmd[cmd.index("--memory") + 1] == "512m"
    assert cmd[cmd.index("--cpus") + 1] == "1"
    assert cmd[cmd.index("--pids-limit") + 1] == "128"
    assert "--read-only" in cmd
    assert cmd[cmd.index("--tmpfs") + 1] == "/tmp"
    assert cmd[cmd.index("--user") + 1] == "1000:1000"
    assert cmd[cmd.index("-v") + 1] == f"{tmp_path}:/work:ro"
    assert cmd[cmd.index("-v") + 2] == DEFAULT_IMAGE
    assert cmd[cmd.index("-w") + 1] == "/work"
    assert cmd[-4:] == ["python", "-m", "pytest", "-q"]


def test_docker_command_with_out_dir_and_name(tmp_path):
    out = tmp_path / "out"
    cmd = build_docker_command(tmp_path, ["python", "-V"], outdir=out, name="mg-test")
    assert cmd[cmd.index("--name") + 1] == "mg-test"
    mounts = [cmd[i + 1] for i, part in enumerate(cmd) if part == "-v"]
    assert mounts == [f"{tmp_path}:/work:ro", f"{out}:/out:rw"]
    assert cmd[cmd.index(f"{out}:/out:rw") + 1] == DEFAULT_IMAGE
