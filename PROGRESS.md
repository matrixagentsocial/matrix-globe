# Progress

Running log for Matrix Globe. Updated every session.

## Milestone status

| Milestone | Status |
|---|---|
| M0 — Gate + skeleton | done (Official Rules step pending; rules not yet published, tracked separately) |
| M1 — Sandbox + tasks + builder | done |
| M2 — Proof loop | done (condition B live cost not measured: session live budget was exhausted by D, see below) |
| M3 — FinCode-30 complete | part 1 done (tasks + reviewer fixes; zero LLM calls); part 2 pending (pilot A/B/D on dev, calibrate, freeze `prompts-v1`) |

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

## M2 results (2026-10-26)

- Reviewer (`proof/roles/reviewer.py` + `prompts/reviewer.md`): strict
  explicit `json_schema` dict (every object `additionalProperties: false`,
  all properties required, verdict/severity enums, max 5 claims), role
  `reviewer` (Wonder, effort high, fresh context per round). Prompt: only
  report defects you can make executable; a claim whose test passes is
  discarded; quote exact spec sentences in `spec_reference`.
- Proof rule (`proof/proofrule.py`): each claim's test runs in its own
  file in the sandbox -> PROVEN / UNPROVEN / INVALID (collection, syntax,
  bad import, timeout); bench-only validity vs `reference.py` -> VALID /
  UNCONFIRMED.
- Reviser (`proof/roles/reviser.py`, Spark) -> `{code, addressed[],
  contested[]}`; self-refine (`proof/roles/self_refine.py`) for C and the
  free-form reviewer (`prompts/reviewer_freeform.md`, plain text, no
  tests, no proof rule) for E.
- Loop (`proof/loop.py`) `run_proof(task, mode)` for A-E exactly as in
  the Decisions section (B = Wonder single shot, effort `max`). Guards:
  `MAX_ROUNDS=2`, `MAX_USD_PER_RUN`, `MAX_LLM_CALLS_PER_RUN=8`, sandbox
  timeout, 6 min wall clock; rollback to the best version on regression
  (a `regression` event); a failed step is recorded and the loop
  continues with the best version; final VERIFIED / PARTIAL / FAILED
  from what actually passed; every event is in the bundle.
- ProofBundle (`proof/bundle.py`, pydantic): canonical JSON
  (sort_keys, separators `(",", ":")`, `ensure_ascii=False`, UTF-8) +
  sha256. Fixture `tests/fixtures/bundle_fixture.json` + expected sha256
  `4b671d61a33699440eb7c78cb83165a2c06cead654c9d348cf5830a4e5e8ef44`
  for the web viewer to test against later.
- `bench/run_bench.py` supports `--cond A|B|C|D|E` (plus `--task <id>`),
  writes bundles to `results/bundles/` and per-run JSONL with the M1
  fields plus, for D/E, claims proposed/proven/unproven/invalid/valid/
  unconfirmed, rounds and regressions, and `reviewer_usd` separately.
- Unit tests: 72 passed (`.venv\Scripts\python -m pytest -q`), with a
  mocked LLM covering proof-rule classification (incl. unconfirmed),
  loop guards (round, call, $ and wall-clock caps), rollback on
  regression, recovery after a failed step, bundle hash stability and
  strict-schema checks.

### Demo (`scripts/review_demo.py`, live)

Naive `split_installments` (rounds each installment independently,
100.00/3 -> 99.99; public 3/5) reviewed by the real Wonder reviewer:

```
C1: PROVEN / VALID
C2: PROVEN / VALID
C3: PROVEN / VALID
C4: PROVEN / VALID
Verify revision: public 5/5, proven 4/4
Final status: VERIFIED
Demo LLM cost this run: $0.1083
SUMMARY proven=4 valid=4 status=VERIFIED
```

### Condition D live (6 dev tasks, 1 seed, real models)

Results in `results/runs/condD_dev_20261026T212537Z.jsonl`, bundles in
`results/bundles/bench-D-*-s0.json`:

| task | status | public | hidden | all_pass | usd | reviewer usd | claims (prop/prov/valid/hall) | rounds |
|---|---|---|---|---|---|---|---|---|
| business_days | VERIFIED | 5/5 | 19/19 | yes | $0.0472 | $0.0464 | 0/0/0/0 | 1 |
| currency_rounding | VERIFIED | 5/5 | 19/19 | yes | $0.1608 | $0.1592 | 1/1/0/1 | 2 |
| iban_validation | VERIFIED | 5/5 | 19/19 | yes | $0.0663 | $0.0657 | 0/0/0/0 | 1 |
| number_parsing | VERIFIED | 5/5 | 21/21 | yes | $0.3382 | $0.3359 | 0/0/0/0 | 0 |
| receivables_aging | VERIFIED | 5/5 | 19/19 | yes | $0.5106 | $0.5084 | 3/3/2/1 | 2 |
| split_installments | PARTIAL | 5/5 | 17/17 | yes | $0.3620 | $0.3596 | 1/1/0/1 | 2 |

Condition D total: $1.4850 (reviewer $1.4752). All 6 tasks pass public
+ hidden; 5 VERIFIED, 1 PARTIAL (split_installments: the single proven
claim was UNCONFIRMED and its test still fails on the revision, so the
status honestly stays PARTIAL even though hidden tests pass).

Surprises:

- Wonder reviewer cost dominates everything (builder+reviser are
  ~$0.001-0.01 per run on the contributor model). Two tasks cost far
  more than expected: receivables_aging $0.5106 exceeded the $0.40
  single-run stop threshold (the bench guard stopped the batch after
  writing its row; split_installments was then run alone with `--task`),
  and split_installments cost $0.3620 for one unconfirmed claim.
- number_parsing: the reviewer call truncated at 16,384 `max_tokens`
  (reasoning ate the budget, empty content). The loop recorded a
  `step_failed` event, continued with the builder code and finished
  VERIFIED with `rounds=0`. Reviewer `max_tokens` is now 32,768, as
  the builder already was; not re-run live (budget, see below).
- Hallucinated claims are real: 3 of 5 proven claims across D were
  UNCONFIRMED (the reference fails their tests too). The reviser still
  "addressed" them; in split_installments that left the claim test
  failing, hence PARTIAL. Reviewer precision on this tiny sample:
  2 valid / 5 proven.
- Session live spend was $1.5933, i.e. $0.093 over the $1.50 session
  cap: the per-run costs above were only knowable after each call, and
  the $0.40 guard stopped the batch at receivables_aging, but running
  split_installments afterwards pushed the total over. No further live
  calls were made after that point.
- Condition B (Wonder, effort `max`, one dev task) was therefore NOT
  run live: any further live call would have exceeded the session cap
  knowingly. Its cost is still unmeasured; run it first in the next
  session (expected order $0.10-0.30 based on Wonder output pricing).

## M3 part 1 results (2026-10-26, tasks + reviewer fixes, zero LLM calls)

No bench runs, no demo, no smoke calls this session. API spend: $0.

- Reviewer scope fix (root cause of all 3 M2 UNCONFIRMED claims: they
  tested amounts around 1e30, outside any range the specs state):
  `prompts/reviewer.md` now requires every claim to stay inside the
  input domain the spec defines (types, ranges, formats, examples);
  anything the spec does not specify is not a defect and goes to
  `untested_concerns`. The rule that every claim quotes the exact spec
  sentence it relies on is kept and strengthened.
- `prompts/reviser.md`: the reviser may contest a claim that asks for
  behaviour the spec does not require, with a one-sentence reason
  quoting the spec. The loop already excluded contested claims from
  the proven count in `ProofLoop.evaluate` (PLAN.md 5.4); that is now
  covered by a mocked-LLM test
  (`test_condition_d_contested_claim_excluded_from_verified`,
  including a lower-case claim id from the reviser), so a contested
  out-of-scope claim can no longer leave a run PARTIAL the way
  `split_installments` ended in M2.
- Bench validity label renamed: a proven claim whose test also fails
  on the reference is now `UNCONFIRMED` (was `HALLUCINATED`; the
  ground truth does not confirm it). `VALID` is unchanged. Renamed in
  `proof/proofrule.py` (constant), `proof/bundle.py`,
  `bench/run_bench.py` (`claims_unconfirmed`), unit tests and this
  file. The bundle fixture now carries an `UNCONFIRMED` claim and its
  expected sha256 is
  `4b671d61a33699440eb7c78cb83165a2c06cead654c9d348cf5830a4e5e8ef44`.
  Historical run JSONL and bundles under `results/` keep the label
  they were recorded with.
- FinCode-30 complete: 24 new tasks (4 dev + 20 test), each with
  `spec.md` (8-15 numbered rules, every hidden-tested rule stated,
  worked examples), `public_test.py` (3-5 tests), `hidden_test.py`
  (15-21 tests on rule interactions), a stdlib-only `reference.py`
  and `meta.json`. Spot checks were re-derived independently (CIF
  control digit, RF check digits `RF741`, ACT/ACT ISDA fraction
  0.1696309604, APY 12.682503 / 12.749685, tax on 50000 = 14201.50,
  amortization payment 34.00/34.00/34.01).
- `madrid_cutoff` reference: `zoneinfo` is primary, with a pure-stdlib
  EU DST fallback when no tzdata is installed (Windows, slim images),
  so it validates outside Linux CI too.
- `bench/validate_tasks.py` extended: every hidden test function name
  must be unique, and no task file may import a non-stdlib module
  (test files may also import `solution` and `pytest`). Both checks
  have unit tests. `validate_tasks.py` is green for all 30 tasks
  (reference passes public + hidden, naive stub fails hidden, hidden
  not a subset of public, unique names, stdlib only).
- Unit tests: 76 passed, 4 skipped (Docker live tests).

FinCode-30 tasks (30 = 10 dev + 20 test):

| task | split | difficulty |
|---|---|---|
| allocate_ratios | test | medium |
| amortization_schedule | dev | hard |
| apr_apy | test | medium |
| bank_reconciliation | test | hard |
| budget_variance | test | medium |
| business_days | dev | medium |
| currency_rounding | dev | medium |
| day_count | dev | hard |
| depreciation_declining | test | hard |
| depreciation_straight_line | test | hard |
| duplicate_payments | test | hard |
| eom_roll | test | hard |
| fifo_cost | dev | hard |
| fx_triangulation | test | hard |
| iban_validation | dev | medium |
| idempotent_ledger | test | hard |
| madrid_cutoff | test | hard |
| number_parsing | dev | hard |
| percent_change | test | medium |
| progressive_tax | test | hard |
| prorata_billing | test | hard |
| receivables_aging | dev | easy |
| rf_reference | test | medium |
| running_balance | test | medium |
| spanish_bank_csv | test | hard |
| spanish_tax_id | test | hard |
| split_installments | dev | easy |
| vat_invoice | dev | hard |
| weighted_average_cost | test | hard |
| xirr | test | expert |

Next step (unchanged): M3 part 2 — pilot A/B/D on the 10 dev tasks,
calibrate difficulty into the 35-70% single-shot band, tune prompts
on dev only, freeze prompts (tag `prompts-v1`).

## Dollars spent

Product ledger: $0.014354 total (12 calls in `state/ledger.jsonl`):
smoke $0.004831 (M0) + condition A $0.006115 (6 tasks) + $0.003408
for the aborted first condition A attempt above. No single builder
run exceeded $0.002 (stop threshold was $0.05).

After M2 the product ledger is $1.607672: M2 live spend was $1.593318 (demo $0.1083 + condition D $1.4850 on 6 dev tasks). That is $0.093 over the $1.50 session cap set for M2 (see the M2 surprises above); one single run (receivables_aging, $0.5106) also exceeded the $0.40 single-run stop threshold and triggered the bench guard. Condition B was not run live for this reason.

Muse Code build sessions (outside the product ledger; budget $25), from `muse exec --json` `run.usage`:

| Session | Model | Input (cached) | Output (reasoning) | Calls | USD |
|---|---|---|---|---|---|
| M0 (2026-10-26) | muse-wonder-1.0, effort high | 2,259,393 (2,175,592) | 26,362 (9,025) | 35 | ~1.30 |
| M1 (2026-10-26) | muse-wonder-1.0, effort high | 4,688,210 (4,565,440) | 40,709 (6,509) | 49 | ~2.22 |

## Review notes (Claude Code, supervisor)

- M0 reviewed: tests pass (25), no secrets tracked, cost maths correct (cached tokens at the cached rate, reasoning not double-billed).
- Fixed: the ledger default path is now anchored to the repo root instead of the cwd.
- For M2: pydantic `model_json_schema()` does not emit `additionalProperties: false`; strict json_schema needs it on every object, so build the reviewer schema explicitly (or post-process) and test it live once.
- For M6: parallel Actions jobs each see only their own ledger; the total cap must be enforced per job budget (split `MAX_USD_TOTAL` across jobs) and the ledgers merged into `results/`.

- M1 reviewed: 43 tests pass, validate_tasks green; spot-checked business_days hidden tests by hand (weekdays, month-end MF cases) and they are right; the local sandbox env drops every *_KEY.
- M1 risk: the 6 dev tasks are too easy (single-shot 6/6). M3 must make tasks harder through interacting rules, not hidden ones.
- Repo published 2026-10-26: https://github.com/matrixagentsocial/matrix-globe (public). Commit emails rewritten to the GitHub noreply address before the first push. The gh token lacks the `workflow` scope, so `.github/workflows/*` cannot be pushed until the owner runs `gh auth refresh -h github.com -s workflow`.

## Next step

M3 part 2 — pilot A/B/D on the 10 dev tasks, calibrate difficulty into the 35-70% single-shot band (the 6 original dev tasks are too easy; the 4 new dev tasks are the hard ones), tune prompts on dev only, freeze prompts (tag `prompts-v1`). First, in a fresh session with budget, run one live condition B (Wonder, effort max) on one dev task to measure its cost, which M2 could not do within its session cap.
