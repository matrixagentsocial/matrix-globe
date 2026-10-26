"""Local subprocess sandbox: TRUSTED ONLY (PLAN.md section 4).

Runs code in a fresh temp dir with a scrubbed environment. It refuses to
run anything whose origin is not ``"bench"``: benchmark code our own
builder wrote may run locally (dev only); external users' code must go
to the Docker sandbox in GitHub Actions (PLAN.md ground rule 3).

The scrubbed environment keeps only OS essentials (``PATH``,
``SYSTEMROOT``, ``TEMP``/``TMP`` and similar). No ``*_KEY`` variable,
``MODEL_API_KEY`` included, ever reaches the child process.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from proof.sandbox.base import RunResult, Sandbox, validate_relative_path

# OS essentials only. Anything not listed here is dropped, which by
# construction excludes MODEL_API_KEY and every other *_KEY secret.
ALLOWED_ENV_KEYS = {
    "PATH",
    "SYSTEMROOT",
    "WINDIR",
    "TEMP",
    "TMP",
    "TMPDIR",
    "COMSPEC",
    "PATHEXT",
    "NUMBER_OF_PROCESSORS",
    "PROCESSOR_ARCHITECTURE",
    "LANG",
    "LC_ALL",
    "TZ",
}


def scrubbed_env(workdir: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    for key, value in os.environ.items():
        if key.upper() in ALLOWED_ENV_KEYS:
            env[key] = value
    # Defence in depth: never forward anything that looks like a secret.
    env = {
        k: v
        for k, v in env.items()
        if not k.upper().endswith("_KEY") and k.upper() != "MODEL_API_KEY"
    }
    env["TEMP"] = str(workdir)
    env["TMP"] = str(workdir)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _decode(data: bytes | str | None) -> str:
    if data is None:
        return ""
    if isinstance(data, bytes):
        return data.decode("utf-8", errors="replace")
    return data


def _collect_output_files(workdir: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(workdir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(workdir).as_posix()
        if "__pycache__" in rel or rel.endswith((".pyc", ".pyo")):
            continue
        try:
            out[rel] = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return out


class LocalSandbox(Sandbox):
    """Temp-dir subprocess sandbox for trusted benchmark code only."""

    def __init__(self, origin: str = "bench") -> None:
        self.origin = origin
        self.python_cmd = sys.executable

    def run(
        self,
        files: dict[str, str],
        cmd: list[str],
        timeout_s: float = 10.0,
        *,
        origin: str | None = None,
    ) -> RunResult:
        effective_origin = self.origin if origin is None else origin
        if effective_origin != "bench":
            raise PermissionError(
                "LocalSandbox is TRUSTED ONLY: refusing to run code with "
                f"origin={effective_origin!r} (expected 'bench'). "
                "External code must run in the Docker sandbox."
            )
        if not cmd:
            raise ValueError("cmd must not be empty")

        start = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="matrix-globe-") as tmp:
            workdir = Path(tmp)
            for name, content in files.items():
                rel = validate_relative_path(name)
                target = workdir.joinpath(*rel.split("/"))
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            try:
                proc = subprocess.run(
                    list(cmd),
                    cwd=str(workdir),
                    env=scrubbed_env(workdir),
                    capture_output=True,
                    timeout=timeout_s,
                    check=False,
                )
                duration = time.monotonic() - start
                return RunResult(
                    exit=proc.returncode,
                    stdout=_decode(proc.stdout),
                    stderr=_decode(proc.stderr),
                    duration=duration,
                    timed_out=False,
                    output_files=_collect_output_files(workdir),
                )
            except subprocess.TimeoutExpired as exc:
                duration = time.monotonic() - start
                return RunResult(
                    exit=None,
                    stdout=_decode(exc.stdout),
                    stderr=_decode(exc.stderr),
                    duration=duration,
                    timed_out=True,
                    output_files=_collect_output_files(workdir),
                )
