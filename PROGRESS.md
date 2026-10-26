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

Product ledger: $0.004831 total (smoke run `run_id=smoke`, 2 calls in `state/ledger.jsonl`).

Muse Code build sessions (outside the product ledger; budget $25), from `muse exec --json` `run.usage`:

| Session | Model | Input (cached) | Output (reasoning) | Calls | USD |
|---|---|---|---|---|---|
| M0 (2026-10-26) | muse-wonder-1.0, effort high | 2,259,393 (2,175,592) | 26,362 (9,025) | 35 | ~1.30 |

## Review notes (Claude Code, supervisor)

- M0 reviewed: tests pass (25), no secrets tracked, cost maths correct (cached tokens at the cached rate, reasoning not double-billed).
- Fixed: the ledger default path is now anchored to the repo root instead of the cwd.
- For M2: pydantic `model_json_schema()` does not emit `additionalProperties: false`; strict json_schema needs it on every object, so build the reviewer schema explicitly (or post-process) and test it live once.
- For M6: parallel Actions jobs each see only their own ledger; the total cap must be enforced per job budget (split `MAX_USD_TOTAL` across jobs) and the ledgers merged into `results/`.

## Next step

M1 — Sandbox + tasks + builder (PLAN.md section 6, row D2).
