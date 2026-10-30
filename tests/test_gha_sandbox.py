"""GitHub Actions sandbox with a fake `gh` (no network, no GitHub calls)."""
import json
import subprocess
from pathlib import Path

import pytest

from proof import desk
from proof.sandbox import gha, gha_job
from proof.sandbox.base import RunResult
from proof.sandbox.gha import (
    GitHubActionsSandbox,
    SandboxInfraError,
    decode_payload,
    encode_payload,
    result_from_json,
    result_to_json,
)

CMD = ["python", "-m", "pytest", "-q", "--junitxml=/out/report.xml", "test_a.py"]
FILES = {"solution.py": "def f():\n    return 1\n", "test_a.py": "from solution import f\n"}


class FakeGh:
    """Answers the four gh calls the sandbox makes, like GitHub would."""

    def __init__(self, result=None, *, appear_after=0, conclusion="success", artifact=True):
        self.calls = []
        self.dispatched = None
        self.result = result or RunResult(exit=1, stdout="1 failed", stderr="", duration=2.0,
                                          timed_out=False, output_files={"report.xml": "<testsuites/>"})
        self.appear_after = appear_after
        self.conclusion = conclusion
        self.artifact = artifact

    def __call__(self, args):
        self.calls.append(args)
        sub = args[1:]
        if sub[:3] == ["api", "-X", "POST"]:
            self.dispatched = json.loads(Path(sub[sub.index("--input") + 1]).read_text(encoding="utf-8"))
            return self._ok("")
        if sub[0] == "api" and "/runs?" in sub[1]:
            runs = [{"id": 7, "display_title": "sandbox someone-else"}]
            if self.appear_after <= 0 and self.dispatched:
                runs.append({"id": 42, "display_title": f"sandbox {self.dispatched['inputs']['nonce']}"})
            self.appear_after -= 1
            return self._ok(json.dumps({"workflow_runs": runs}))
        if sub[0] == "api" and sub[1].endswith("/runs/42"):
            return self._ok(json.dumps({"status": "completed", "conclusion": self.conclusion}))
        if sub[:2] == ["run", "download"]:
            if self.artifact:
                out = Path(sub[sub.index("-D") + 1])
                (out / "result.json").write_text(result_to_json(self.result), encoding="utf-8")
                return self._ok("")
            return subprocess.CompletedProcess(args, 1, "", "no artifact matches any of the names")
        raise AssertionError(args)

    @staticmethod
    def _ok(out):
        return subprocess.CompletedProcess([], 0, out, "")


def sandbox(fake, **kw):
    return GitHubActionsSandbox(runner=fake, sleep=lambda _: None, **kw)


def test_payload_round_trip_and_validation():
    run = decode_payload(encode_payload(FILES, CMD, 10))
    assert run == {"files": FILES, "cmd": CMD, "timeout_s": 10.0}


@pytest.mark.parametrize("files,cmd,timeout,msg", [
    ({"../x.py": ""}, CMD, 10, "escape"),
    ({"/etc/x.py": ""}, CMD, 10, "relative"),
    (FILES, ["bash", "-c", "curl evil"], 10, "pytest"),
    (FILES, CMD, 600, "timeout"),
])
def test_job_rejects_bad_payloads(files, cmd, timeout, msg):
    import base64
    import zlib
    raw = json.dumps({"v": 1, "files": files, "cmd": cmd, "timeout_s": timeout})
    encoded = base64.b64encode(zlib.compress(raw.encode())).decode()
    with pytest.raises(ValueError, match=msg):
        decode_payload(encoded)


def test_payload_too_large_is_refused_before_dispatch():
    fake = FakeGh()
    big = {"solution.py": "".join(f"x{i} = {i * 7919}\n" for i in range(40_000))}
    with pytest.raises(ValueError, match="GitHub limit"):
        sandbox(fake).run(big, CMD)
    assert fake.calls == []


def test_run_dispatches_finds_its_run_and_returns_the_result():
    fake = FakeGh(appear_after=2)
    result = sandbox(fake).run(FILES, CMD, timeout_s=10)
    assert result == fake.result
    body = fake.dispatched
    assert body["ref"] == "main"
    assert gha.NONCE_RE.match(body["inputs"]["nonce"])
    assert decode_payload(body["inputs"]["payload"])["files"] == FILES
    assert fake.calls[0][:5] == ["gh", "api", "-X", "POST",
                                 "repos/matrixagentsocial/matrix-globe/actions/workflows/sandbox.yml/dispatches"]
    assert ["gh", "run", "download", "42", "-R", "matrixagentsocial/matrix-globe", "-n", "sandbox-result"] == fake.calls[-1][:8]


def test_code_timeout_comes_back_as_a_result_not_an_error():
    timed = RunResult(exit=None, stdout="", stderr="", duration=10.1, timed_out=True)
    assert sandbox(FakeGh(timed)).run(FILES, CMD).timed_out is True


def test_failed_run_without_artifact_is_an_infra_error():
    with pytest.raises(SandboxInfraError, match="ended 'failure' without a result"):
        sandbox(FakeGh(conclusion="failure", artifact=False)).run(FILES, CMD)


def test_run_that_never_appears_is_an_infra_error():
    clock = iter(range(0, 10_000, 100))
    sb = GitHubActionsSandbox(runner=FakeGh(appear_after=10_000), sleep=lambda _: None,
                              clock=lambda: next(clock), queue_timeout_s=300)
    with pytest.raises(SandboxInfraError, match="never appeared"):
        sb.run(FILES, CMD)


def test_result_json_round_trip_clips_huge_output():
    r = RunResult(exit=0, stdout="x" * (gha.MAX_OUTPUT_CHARS * 2), stderr="", duration=1.0, timed_out=False)
    back = result_from_json(result_to_json(r))
    assert back.stdout.endswith("[truncated]") and len(back.stdout) < len(r.stdout)


def test_job_main_runs_payload_in_docker_and_writes_result(monkeypatch, tmp_path):
    seen = {}

    class FakeDocker:
        def run(self, files, cmd, timeout_s):
            seen.update(files=files, cmd=cmd, timeout_s=timeout_s)
            return RunResult(exit=0, stdout="ok", stderr="", duration=1.5, timed_out=False)

    monkeypatch.setattr(gha_job, "DockerSandbox", FakeDocker)
    monkeypatch.setenv("SANDBOX_NONCE", "0123456789abcdef")
    monkeypatch.setenv("SANDBOX_PAYLOAD", encode_payload(FILES, CMD, 10))
    out = tmp_path / "r" / "result.json"
    assert gha_job.main(["--out", str(out)]) == 0
    assert seen == {"files": FILES, "cmd": CMD, "timeout_s": 10.0}
    assert result_from_json(out.read_text(encoding="utf-8")).stdout == "ok"


def test_job_main_refuses_bad_nonce(monkeypatch, tmp_path):
    monkeypatch.setenv("SANDBOX_NONCE", "$(id)")
    monkeypatch.setenv("SANDBOX_PAYLOAD", encode_payload(FILES, CMD, 10))
    assert gha_job.main(["--out", str(tmp_path / "r.json")]) == 2


def test_desk_defaults_to_the_github_sandbox_and_needs_the_stack_key(monkeypatch):
    assert isinstance(desk.make_sandbox("gha"), GitHubActionsSandbox)
    for name in ("PROOFDESK_KEY", "MODEL_API_KEY", "BASETEN_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("PROOFDESK_KEY", "k")
    assert desk.missing_keys(stack_open=True) == ["BASETEN_API_KEY"]
    assert desk.missing_keys(stack_open=False) == ["MODEL_API_KEY"]


def test_desk_once_refuses_the_local_sandbox():
    with pytest.raises(SystemExit):
        desk.main(["--once", "--sandbox", "local"])
