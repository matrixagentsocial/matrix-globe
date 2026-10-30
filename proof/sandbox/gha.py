"""GitHub Actions sandbox: untrusted code runs on a GitHub runner, never on this PC.

PLAN.md section 9. The desk runs on the owner's PC, where the API keys
live, and the PC has no Docker. Each run goes to the ``sandbox`` workflow
of the public repository through ``workflow_dispatch``:

1. the files, command and timeout are packed into one compressed input,
2. the job, which holds no secrets, runs them with :class:`DockerSandbox`
   (``--network none``, read-only root, 512 MB, unprivileged user),
3. the job uploads the :class:`RunResult` as the ``sandbox-result`` artifact,
4. this class downloads it.

All GitHub calls go through the ``gh`` CLI, so no token passes through
this code. A GitHub failure (dispatch refused, no run found, run failed
without a result) raises :class:`SandboxInfraError`; the desk then posts
nothing and retries on its next poll. A timeout of the code itself comes
back as an ordinary ``timed_out`` result.
"""
from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
import tempfile
import time
import uuid
import zlib
from pathlib import Path
from typing import Any, Callable

from proof.sandbox.base import RunResult, Sandbox, validate_relative_path

DEFAULT_REPO = "matrixagentsocial/matrix-globe"
DEFAULT_WORKFLOW = "sandbox.yml"
ARTIFACT_NAME = "sandbox-result"
PAYLOAD_VERSION = 1
# GitHub caps all workflow_dispatch inputs together at 65,535 characters.
MAX_PAYLOAD_CHARS = 60_000
MAX_TIMEOUT_S = 60.0
MAX_OUTPUT_CHARS = 100_000
NONCE_RE = re.compile(r"^[0-9a-f]{16,32}$")
# Only pytest runs in the remote sandbox; the job refuses anything else.
ALLOWED_CMD_PREFIX = ["python", "-m", "pytest"]


class SandboxInfraError(RuntimeError):
    """GitHub could not run the job; no result for the code exists."""


# ------------------------------------------------------------- payloads
def encode_payload(files: dict[str, str], cmd: list[str], timeout_s: float) -> str:
    """Pack a run into one base64 string; raise if GitHub would refuse its size."""
    body = {
        "v": PAYLOAD_VERSION,
        "files": {validate_relative_path(k): str(v) for k, v in files.items()},
        "cmd": [str(c) for c in cmd],
        "timeout_s": float(timeout_s),
    }
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    encoded = base64.b64encode(zlib.compress(raw.encode("utf-8"), 9)).decode("ascii")
    if len(encoded) > MAX_PAYLOAD_CHARS:
        raise ValueError(
            f"sandbox payload is {len(encoded)} characters after compression; "
            f"the GitHub limit used here is {MAX_PAYLOAD_CHARS}"
        )
    return encoded


def decode_payload(encoded: str) -> dict[str, Any]:
    """Unpack and validate a payload (the job side). Raises ValueError."""
    if len(encoded) > MAX_PAYLOAD_CHARS:
        raise ValueError("payload too large")
    try:
        raw = zlib.decompress(base64.b64decode(encoded, validate=True), bufsize=1 << 20)
        body = json.loads(raw.decode("utf-8"))
    except (ValueError, zlib.error) as exc:
        raise ValueError(f"payload is not valid: {type(exc).__name__}") from None
    if not isinstance(body, dict) or body.get("v") != PAYLOAD_VERSION:
        raise ValueError("unsupported payload version")
    files = body.get("files")
    cmd = body.get("cmd")
    timeout_s = body.get("timeout_s")
    if not isinstance(files, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in files.items()
    ):
        raise ValueError("files must map relative paths to text")
    files = {validate_relative_path(k): v for k, v in files.items()}
    if not isinstance(cmd, list) or not all(isinstance(c, str) for c in cmd):
        raise ValueError("cmd must be a list of strings")
    if cmd[: len(ALLOWED_CMD_PREFIX)] != ALLOWED_CMD_PREFIX:
        raise ValueError("only 'python -m pytest ...' may run in this sandbox")
    if not isinstance(timeout_s, (int, float)) or not 0 < timeout_s <= MAX_TIMEOUT_S:
        raise ValueError(f"timeout_s must be in (0, {MAX_TIMEOUT_S}]")
    return {"files": files, "cmd": cmd, "timeout_s": float(timeout_s)}


def _clip(text: str) -> str:
    return text if len(text) <= MAX_OUTPUT_CHARS else text[:MAX_OUTPUT_CHARS] + "\n[truncated]"


def result_to_json(result: RunResult) -> str:
    return json.dumps({
        "exit": result.exit,
        "stdout": _clip(result.stdout),
        "stderr": _clip(result.stderr),
        "duration": result.duration,
        "timed_out": result.timed_out,
        "output_files": {k: _clip(v) for k, v in result.output_files.items()},
    }, sort_keys=True, ensure_ascii=False)


def result_from_json(text: str) -> RunResult:
    data = json.loads(text)
    return RunResult(
        exit=data.get("exit"),
        stdout=str(data.get("stdout", "")),
        stderr=str(data.get("stderr", "")),
        duration=float(data.get("duration", 0.0)),
        timed_out=bool(data.get("timed_out", False)),
        output_files={str(k): str(v) for k, v in (data.get("output_files") or {}).items()},
    )


# -------------------------------------------------------------- sandbox
Runner = Callable[[list[str]], subprocess.CompletedProcess]


def _default_runner(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", check=False, timeout=120)


class GitHubActionsSandbox(Sandbox):
    """Runs each request in the secret-less ``sandbox`` workflow on GitHub."""

    python_cmd = "python"
    report_path = "/out/report.xml"
    label = "github-actions:docker python:3.11-slim --network none"

    def __init__(
        self,
        repo: str = DEFAULT_REPO,
        workflow: str = DEFAULT_WORKFLOW,
        ref: str = "main",
        *,
        gh: str = "gh",
        runner: Runner | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        poll_s: float = 5.0,
        queue_timeout_s: float = 600.0,
    ) -> None:
        self.repo = repo
        self.workflow = workflow
        self.ref = ref
        self.gh = gh
        self._runner = runner or _default_runner
        self._sleep = sleep
        self._clock = clock
        self.poll_s = poll_s
        self.queue_timeout_s = queue_timeout_s

    # -- gh calls -----------------------------------------------------
    def _gh(self, *args: str) -> str:
        if self._runner is _default_runner and shutil.which(self.gh) is None:
            raise SandboxInfraError("the GitHub CLI (gh) is not installed")
        proc = self._runner([self.gh, *args])
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip().splitlines()
            raise SandboxInfraError(f"gh {args[0]} failed: {detail[-1][:300] if detail else proc.returncode}")
        return proc.stdout or ""

    def _gh_json(self, *args: str) -> Any:
        try:
            return json.loads(self._gh(*args) or "null")
        except ValueError:
            raise SandboxInfraError(f"gh {args[0]} returned invalid JSON") from None

    def dispatch(self, nonce: str, payload: str) -> None:
        body = {"ref": self.ref, "inputs": {"nonce": nonce, "payload": payload}}
        with tempfile.TemporaryDirectory(prefix="matrix-globe-gha-") as tmp:
            path = Path(tmp) / "dispatch.json"
            path.write_text(json.dumps(body), encoding="utf-8")
            self._gh("api", "-X", "POST",
                     f"repos/{self.repo}/actions/workflows/{self.workflow}/dispatches",
                     "--input", str(path))

    def find_run(self, nonce: str, deadline: float) -> int:
        title = f"sandbox {nonce}"
        while True:
            data = self._gh_json(
                "api", f"repos/{self.repo}/actions/workflows/{self.workflow}/runs"
                "?event=workflow_dispatch&per_page=30")
            for run in (data or {}).get("workflow_runs", []):
                if run.get("display_title") == title:
                    return int(run["id"])
            if self._clock() >= deadline:
                raise SandboxInfraError("the dispatched sandbox run never appeared")
            self._sleep(self.poll_s)

    def wait_run(self, run_id: int, deadline: float) -> str:
        while True:
            run = self._gh_json("api", f"repos/{self.repo}/actions/runs/{run_id}") or {}
            if run.get("status") == "completed":
                return str(run.get("conclusion") or "")
            if self._clock() >= deadline:
                raise SandboxInfraError(f"sandbox run {run_id} did not finish in time")
            self._sleep(self.poll_s)

    def download_result(self, run_id: int) -> RunResult:
        with tempfile.TemporaryDirectory(prefix="matrix-globe-gha-") as tmp:
            self._gh("run", "download", str(run_id), "-R", self.repo,
                     "-n", ARTIFACT_NAME, "-D", tmp)
            path = Path(tmp) / "result.json"
            if not path.exists():
                raise SandboxInfraError(f"sandbox run {run_id} has no result.json")
            return result_from_json(path.read_text(encoding="utf-8"))

    # -- Sandbox API ----------------------------------------------------
    def run(
        self,
        files: dict[str, str],
        cmd: list[str],
        timeout_s: float = 10.0,
        *,
        origin: str | None = None,
    ) -> RunResult:
        if not cmd:
            raise ValueError("cmd must not be empty")
        payload = encode_payload(files, list(cmd), min(float(timeout_s), MAX_TIMEOUT_S))
        nonce = uuid.uuid4().hex[:16]
        deadline = self._clock() + self.queue_timeout_s + timeout_s
        self.dispatch(nonce, payload)
        run_id = self.find_run(nonce, deadline)
        conclusion = self.wait_run(run_id, deadline)
        try:
            return self.download_result(run_id)
        except SandboxInfraError:
            raise SandboxInfraError(
                f"sandbox run {run_id} ended '{conclusion}' without a result") from None
