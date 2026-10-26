# Progress

Running log for Matrix Globe. Updated every session.

## Milestone status

| Milestone | Status |
|---|---|
| M0 — Gate + skeleton | done (Official Rules step pending; rules not yet published, tracked separately) |

## Verified facts (M0)

- Base URL `https://api.meta.ai/v1`, OpenAI-compatible Chat Completions.
- Models (from `.env`): `MODEL_BUILDER=muse-spark-1.3-contributor`,
  `MODEL_REVIEWER=muse-wonder-1.0`. Live smoke confirmed both answer.
- `response_format: json_schema` (strict) works on both roles; parsed
  `{"ok": true, "who": ...}` on the first attempt.
- `reasoning_effort` works (`medium` builder, `high` reviewer); reasoning
  tokens are reported separately and count inside `max_tokens`.
- Pricing per PLAN.md Decisions of 2026-10-26 (source: Meta docs
  `dev.meta.ai/docs/models` + `/docs/pricing-rate-limits`): Wonder
  $4.00/$0.20/$20.00, Spark 1.3 $1.25/$0.15/$4.25, Spark 1.3 contributor
  $0.10/$0.002/$0.20 per 1M input/cached/output.

## Decisions

- Per PLAN.md "Decisions of 2026-10-26" (overrides older text).
- Builder/reviser default to the contributor model (own benchmark code);
  external users' code must use the standard model — enforced in code.
- Product ledger caps: `MAX_USD_TOTAL=100`, `MAX_USD_PER_RUN=0.60`,
  enforced before every call.

## Dollars spent

$0.004831 total (smoke run `run_id=smoke`, 2 calls in `state/ledger.jsonl`).

## Next step

M1 — Sandbox + tasks + builder (PLAN.md section 6, row D2).
