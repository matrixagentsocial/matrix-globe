"""Job side of the GitHub Actions sandbox (run by ``.github/workflows/sandbox.yml``).

Usage: python -m proof.sandbox.gha_job --out sandbox-result/result.json

Reads the run from the ``SANDBOX_PAYLOAD`` environment variable (never from
the command line, so the workflow never pastes untrusted text into a shell),
validates it, runs it with :class:`DockerSandbox` and writes the result.
The job has no secrets. The log shows only the exit code and duration.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from proof.sandbox.docker import DockerSandbox
from proof.sandbox.gha import NONCE_RE, decode_payload, result_to_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="proof.sandbox.gha_job")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    if not NONCE_RE.match(os.environ.get("SANDBOX_NONCE", "")):
        print("invalid SANDBOX_NONCE", file=sys.stderr)
        return 2
    try:
        run = decode_payload(os.environ.get("SANDBOX_PAYLOAD", ""))
    except ValueError as exc:
        print(f"rejected payload: {exc}", file=sys.stderr)
        return 2
    result = DockerSandbox().run(run["files"], run["cmd"], timeout_s=run["timeout_s"])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(result_to_json(result), encoding="utf-8")
    print(f"exit={result.exit} timed_out={result.timed_out} duration={result.duration:.1f}s "
          f"files={len(run['files'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
