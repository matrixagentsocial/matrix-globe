# Progress

Running log for Matrix Globe. Updated every session.

## Milestone status

| Milestone | Status |
|---|---|
| M0 — Gate + skeleton | done (Official Rules step pending; rules not yet published, tracked separately) |
| M1 — Sandbox + tasks + builder | done |

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

## M1 results (2026-10-26)

- Sandbox: `proof/sandbox/base.py`, `local.py` (TRUSTED ONLY, refuses
  `origin != "bench"`, temp dir, scrubbed env with OS essentials only,
  timeout, `RunResult(exit, stdout, stderr, duration, timed_out)`),
  `docker.py` (exact `--network none --memory 512m --cpus 1
  --pids-limit 128 --read-only --tmpfs /tmp --user 1000:1000
  -v <tmp>:/work:ro` command; unit-tested only, Docker not installed
  here) and `docker/Dockerfile` (python:3.11-slim + pytest 9.1.1).
- `proof/pytest_runner.py`: writes `solution.py` + tests into the
  sandbox, runs `python -m pytest -q -p no:cacheprovider
  --junitxml=report.xml` (10 s default), parses JUnit XML with the
  stdlib into passed/failed/error/skipped plus collection errors.
- First 6 FinCode dev tasks (all `split: dev`): `split_installments`
  (candidate 2), `currency_rounding` (1, ISO-4217 minor units),
  `business_days` (7, Modified Following), `iban_validation` (9,
  mod-97), `number_parsing` (17, European/US formats),
  `receivables_aging` (19, bucket boundaries). Every rule is stated
  in its `spec.md`; references are stdlib-only.
- `bench/validate_tasks.py` is green for all 6 tasks:

| task | reference | naive fails hidden | hidden not subset |
|---|---|---|---|
| business_days | ok | ok | ok |
| currency_rounding | ok | ok | ok |
| iban_validation | ok | ok | ok |
| number_parsing | ok | ok | ok |
| receivables_aging | ok | ok | ok |
| split_installments | ok | ok | ok |

- Builder role: `proof/roles/prompts/builder.md` +
  `proof/roles/builder.py` (explicit `json_schema` dict, single
  `code` field, `additionalProperties: false`; `LLMClient` role
  `builder`, metadata `origin: bench`).
- Condition A (`bench/run_bench.py --cond A --split dev --limit 6
  --seeds 1 --sandbox local`, model `muse-spark-1.3-contributor`,
  effort `medium`), results in
  `results/runs/condA_dev_20261026T210633Z.jsonl`:

| task | public | hidden | all_pass | usd |
|---|---|---|---|---|
| business_days | 5/5 | 19/19 | yes | $0.0006 |
| currency_rounding | 5/5 | 19/19 | yes | $0.0007 |
| iban_validation | 5/5 | 19/19 | yes | $0.0006 |
| number_parsing | 5/5 | 21/21 | yes | $0.0019 |
| receivables_aging | 5/5 | 19/19 | yes | $0.0011 |
| split_installments | 5/5 | 17/17 | yes | $0.0012 |

Surprising: the cheap Spark builder solved all 6 dev tasks on the
first shot (hidden included), so these 6 are below the 35-70%
single-shot difficulty band of section 5.6; M3 must add harder tasks
and calibrate. Also surprising: at the default 8192 `max_tokens` the
builder's reasoning (8,190 tokens) truncated `number_parsing` to an
empty reply, so the builder now uses 32,768; the aborted first run
cost $0.0034 and its 3 finished rows were lost (run_bench now writes
each row as it completes). Unit tests: 43 passed
(`.venv\Scripts\python -m pytest -q`), including mocked-LLM tests
for builder/run_bench and a validate_tasks fixture.

## Dollars spent

Product ledger: $0.014354 total (12 calls in `state/ledger.jsonl`):
smoke $0.004831 (M0) + condition A $0.006115 (6 tasks) + $0.003408
for the aborted first condition A attempt above. No single builder
run exceeded $0.002 (stop threshold was $0.05).

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

M2 — Proof loop (PLAN.md section 6, row D3): reviewer schema + proof
rule + validity check, reviser, loop guards/rollback/recovery, bundle
+ hash, unit tests with mocked LLM.
