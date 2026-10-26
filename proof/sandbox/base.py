"""Sandbox interface (PLAN.md section 4).

``Sandbox.run(files, cmd, timeout_s) -> RunResult`` writes ``files``
(a mapping of relative path -> text content) into an isolated working
directory, runs ``cmd`` there and returns a :class:`RunResult`.
``output_files`` carries back any text files present after the run
(for example ``report.xml`` written by pytest), keyed by relative path.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field


@dataclass
class RunResult:
    exit: int | None
    stdout: str
    stderr: str
    duration: float
    timed_out: bool
    output_files: dict[str, str] = field(default_factory=dict)


def validate_relative_path(name: str) -> str:
    """Return *name* normalised, rejecting absolute or escaping paths."""
    from pathlib import PurePosixPath, PureWindowsPath

    win = PureWindowsPath(name)
    posix = PurePosixPath(name)
    if win.is_absolute() or posix.is_absolute() or win.drive:
        raise ValueError(f"file path must be relative: {name!r}")
    parts = [p for p in posix.parts if p not in ("", ".")]
    if not parts or any(p == ".." for p in parts):
        raise ValueError(f"file path must not escape the work dir: {name!r}")
    return "/".join(parts)


class Sandbox(abc.ABC):
    """Abstract sandbox. ``python_cmd`` is how to invoke Python inside it."""

    python_cmd: str = "python"
    # Path, as seen inside the sandbox, where pytest writes its JUnit report.
    # The report comes back in ``RunResult.output_files["report.xml"]``.
    report_path: str = "report.xml"

    @abc.abstractmethod
    def run(
        self,
        files: dict[str, str],
        cmd: list[str],
        timeout_s: float = 10.0,
        *,
        origin: str | None = None,
    ) -> RunResult:
        raise NotImplementedError
