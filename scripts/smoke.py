"""M0 smoke test: one real call to MODEL_BUILDER and one to MODEL_REVIEWER.

Each call asks for a tiny JSON object through a json_schema. Prints model,
tokens, USD and the parsed object. Both calls are written to
``state/ledger.jsonl``. Run from the repo root:

    .venv\\Scripts\\python scripts\\smoke.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import BaseModel

from proof.config import load_settings
from proof.ledger import Ledger
from proof.llm import LLMClient


class SmokeReply(BaseModel):
    ok: bool
    who: str


SCHEMA = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean"},
        "who": {"type": "string"},
    },
    "required": ["ok", "who"],
    "additionalProperties": False,
}


def _report(ledger: Ledger, before: int, label: str, parsed: object) -> float:
    rows = ledger.entries()
    new_rows = rows[before:]
    for row in new_rows:
        print(
            f"{label}: model={row['model']} effort={row['effort']} "
            f"input_tokens={row['input_tokens']} cached_tokens={row['cached_tokens']} "
            f"output_tokens={row['output_tokens']} reasoning_tokens={row['reasoning_tokens']} "
            f"usd=${row['usd']:.6f} parsed={parsed}"
        )
    return sum(float(r["usd"]) for r in new_rows)


def main() -> int:
    settings = load_settings()
    ledger = Ledger(Path("state/ledger.jsonl"), settings=settings)
    client = LLMClient(ledger=ledger, settings=settings)

    total = 0.0

    before = len(ledger.entries())
    builder_result = client.complete(
        "builder",
        [
            {
                "role": "user",
                "content": 'Reply with the JSON object {"ok": true, "who": "builder"} and nothing else.',
            }
        ],
        schema=SCHEMA,
        run_id="smoke",
    )
    total += _report(ledger, before, "MODEL_BUILDER", builder_result)

    before = len(ledger.entries())
    reviewer_result = client.complete(
        "reviewer",
        [
            {
                "role": "user",
                "content": 'Reply with the JSON object {"ok": true, "who": "reviewer"} and nothing else.',
            }
        ],
        effort="high",
        schema=SCHEMA,
        run_id="smoke",
    )
    total += _report(ledger, before, "MODEL_REVIEWER", reviewer_result)

    print(f"Smoke total: ${total:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
