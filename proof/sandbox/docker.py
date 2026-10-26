"""Docker sandbox (PLAN.md section 4).

Runs code with no network, capped memory/CPU/PIDs, a read-only
container filesystem and an unprivileged user. The image is built from
``docker/Dockerfile`` (python:3.11-slim + pinned pytest).

Docker is not installed on the dev PC, so :func:`build_docker_command`
is unit-tested directly; :meth:`DockerSandbox.run` raises a clear error
when the ``docker`` binary is missing.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from proof.sandbox.base import RunResult, Sandbox, validate_relative_path
from proof.sandbox.local import _collect_output_files, _decode

DEFAULT_IMAGE = "matrix-globe-runner:py311"


def build_docker_command(
    workdir: str | Path,
    cmd: list[str],
    image: str = DEFAULT_IMAGE,
) -> list[str]:
    """Build the exact docker run command from PLAN.md section 4."""
    if not cmd:
        raise ValueError("cmd must not be empty")
    return [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--memory",
        "512m",
        "--cpus",
        "1",
        "--pids-limit",
        "128",
        "--read-only",
        "--tmpfs",
        "/tmp",
        "--user",
        "1000:1000",
        "-v",
        f"{workdir}:/work:ro",
        image,
        *cmd,
    ]


class DockerSandbox(Sandbox):
    """Docker sandbox for untrusted code (GitHub Actions / desk)."""

    def __init__(self, image: str = DEFAULT_IMAGE) -> None:
        self.image = image
        self.python_cmd = "python"

    def build_command(self, workdir: str | Path, cmd: list[str]) -> list[str]:
        return build_docker_command(workdir, cmd, image=self.image)

    def run(
        self,
        files: dict[str, str],
        cmd: list[str],
        timeout_s: float = 10.0,
        *,
        origin: str | None = None,
    ) -> RunResult:
        if shutil.which("docker") is None:
            raise RuntimeError(
                "docker is not available on this machine; the Docker "
                "sandbox runs in GitHub Actions. Use the local sandbox "
                "for trusted bench code only."
            )
        start = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="matrix-globe-") as tmp:
            workdir = Path(tmp)
            for name, content in files.items():
                rel = validate_relative_path(name)
                target = workdir.joinpath(*rel.split("/"))
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            docker_cmd = self.build_command(workdir, list(cmd))
            try:
                proc = subprocess.run(
                    docker_cmd,
                    cwd=str(workdir),
                    capture_output=True,
                    timeout=timeout_s,
                    check=False,
                )
                return RunResult(
                    exit=proc.returncode,
                    stdout=_decode(proc.stdout),
                    stderr=_decode(proc.stderr),
                    duration=time.monotonic() - start,
                    timed_out=False,
                    output_files=_collect_output_files(workdir),
                )
            except subprocess.TimeoutExpired as exc:
                return RunResult(
                    exit=None,
                    stdout=_decode(exc.stdout),
                    stderr=_decode(exc.stderr),
                    duration=time.monotonic() - start,
                    timed_out=True,
                    output_files=_collect_output_files(workdir),
                )
