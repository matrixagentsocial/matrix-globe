# Progress

Running log for Matrix Globe. Updated every session.

## Milestone status

| Milestone | Status |
|---|---|
| M0 â€” Gate + skeleton | done (Official Rules step pending; rules not yet published, tracked separately) |
| M1 â€” Sandbox + tasks + builder | done |
| M2 â€” Proof loop | done (condition B live cost not measured: session live budget was exhausted by D, see below) |
| M3 â€” FinCode-30 complete | done (30 tasks + 90 mutants validated; review-benchmark pilot v2 on dev; prompts frozen at tag `prompts-v1`) |
| M4 â€” Matrix desk (@proofdesk) | built against a mocked Matrix (Matrix is down until ~Nov 1); live dry run done; going live pending owner registration + repo secrets |

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
  external users' code must use the standard model â€” enforced in code.
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

Next step (unchanged): M3 part 2 â€” pilot A/B/D on the 10 dev tasks,
calibrate difficulty into the 35-70% single-shot band, tune prompts
on dev only, freeze prompts (tag `prompts-v1`).

## M3 part 3 results (2026-10-27, review benchmark)

Per the PLAN.md redesign of 2026-10-27 (replaces A-E): targets are 3
mutants + 1 clean per task; conditions R (no review), C (Spark
self-check), E (Wonder free-text review), D (Matrix Globe proof-gated
review), B (Wonder max regenerates, one run per task).

- Cost attribution fix: `bench/run_bench.py` attributed cost by time
  window, so concurrent bench processes mixed costs. It now attributes
  strictly by `run_id` from the ledger entries (`cost_for_run`), with a
  regression test (`tests/test_cost_attribution.py`) covering
  interleaved entries from two concurrent runs. The bundle gained a
  `target` field (money fields stay 6-decimal strings; the fixture hash
  in `tests/fixtures/bundle_fixture.sha256` was regenerated).
- Mutants: 90 mutants (3 per task x 30 tasks) in
  `bench/tasks/<id>/mutants/{m1,m2,m3}.py` + `mutants.json`, each a
  single plausible local change to `reference.py`.
  `bench/validate_tasks.py` now checks for every mutant: differs from
  the reference, passes all public tests, fails at least one hidden
  test. Green for all 30 tasks, on dev and test splits (test split used
  for validation only, as required).
- Runner: `bench/run_bench.py --cond R|B|C|D|E --split dev|test
  --targets mutants|clean|all --limit N --seeds N --sandbox
  local|docker`, one JSONL row per (task, target, seed) with hidden
  before/after, fixed, regressions (per hidden test), damaged, claim
  counts, usd/reviewer_usd by run_id, status and bundle path.
  `bench/pilot_report.py` writes the per-condition summary (fixed rate
  on mutants, damage rate on clean, regressions, precision VALID/PROVEN,
  $/target).

### Pilot v2 (dev, 1 seed, `results/pilot/v2/`)

| condition | targets | fixed on mutants | damage on clean | regressions | precision | $/target |
|---|---|---|---|---|---|---|
| R | 40 | 0/30 | 0/10 | 0 | n/a | $0.0000 |
| D (high) | 12 | 9/9 | 0/3 | 0 | 0.48 | $0.2355 |
| D (medium) | 8 | 6/6 | 0/2 | 0 | 0.25 | $0.3941 |
| E (medium) | 12 | 9/9 | 0/3 | 0 | n/a | $0.0869 |
| C | 40 | 30/30 | 0/10 | 0 | n/a | $0.0045 |
| B | 10 tasks | regen 10/10 | n/a | 0 | n/a | $0.1733 |

Coverage and effort, honestly: D ran on 5 of 10 dev tasks (20/40
targets), E on 3 of 10 (12/40 targets). Reviewer effort started at
high; the first 10 D targets averaged $0.236 per target, i.e. below
the $0.30 switch threshold, so the switch rule did not trigger. The
rest of D and all of E were still run at medium to keep this
session's live spend under $10 (projected cost at high was more than
twice the remaining budget). Session live spend: $8.93 of the $10
cap (ledger $5.6343 at session start, $14.5675 at the end, including
$0 from R). Headline: on dev, every reviewing/regenerating condition
fixed every mutant it ran on with zero damage; they differ by cost,
not fix rate. The proof rule's measured value on this pilot is claim
precision, and Spark self-check (C) is strikingly cheap. The final
test-split run must confirm or refute this; no test targets were run
except validation.

### Prompt changes (dev pattern, frozen at `prompts-v1`)

Pattern in the D data: the reviewer proposed 1.75 claims per target
at high (precision 0.48) and 3.38 at medium (precision 0.25). Almost
every unconfirmed claim misderived an expected value on a boundary,
tie-break or rounding variant. `proof/roles/prompts/reviewer.md`
gained a "Verify the expected value twice" section: hand-compute the
expected value and show the derivation in the claim, cross-check the
spec's worked examples, follow the quoted rule's exact boundary /
tie-break / rounding wording, report at most 3 claims and prefer
1-2 verified ones. Not re-run live this session (budget); its effect
is a hypothesis for the final run, not a measured result.

### Budget plan for the final run (test split, at most $45)

Measured dev costs per target: C $0.0045, E (medium) $0.087, B $0.173
per task, D $0.24 (easy dev tasks, high) to $0.39 (hard dev tasks,
medium). Test tasks are the harder 20, so plan D at $0.30 per target
at effort medium and expect the tuned prompt to cut round-2 claims.

Recommended final run (reviewer effort medium for D and E, 1 seed
unless stated):

| condition | scope | est. cost |
|---|---|---|
| R | 80 targets x 2 seeds | $0 |
| C | 80 targets x 2 seeds | $0.72 |
| E (medium) | 80 targets x 2 seeds | $13.90 |
| D (medium) | 80 targets x 1 seed | $24.00 |
| B | 20 tasks x 1 | $3.46 |
| **total** | | **$42.08** |

D gets 1 seed (a second seed alone would add about $24 and break
the $45 cap); C, E and R get 2 seeds because they are cheap. If the
tuned reviewer prompt does not bring D under $0.30 per target on the
first 10 test targets, drop D's remaining tasks rather than a second
condition, and say so in the summary.

## M3 part 4 results (2026-10-27, PR targets + pilot v3)

- Housekeeping: `bench/pilot_report.py` now writes reports itself as
  UTF-8 (`--out`, `--title`) instead of relying on shell redirection
  (the v2 summary was UTF-16 from a PowerShell redirect; regenerated).
  Condition R now reports status UNREVIEWED (new loop mode `R`); the
  report writer also maps R rows to UNREVIEWED in older files.
- PR targets (`bench/prs.py` + `bench/prs/<pr_id>/`): a PR groups 3
  same-split tasks into one package (`task_a.py`/`task_b.py`/`task_c.py`
  = the tasks' references, `spec.md` = the three specs under module
  headings, `pr.json`, and the union of public/hidden tests rewritten to
  import from their module, duplicate test names suffixed). Built 3 dev
  PRs (9 of 10 dev tasks; `vat_invoice` left out) and 6 test PRs (18 of
  20 test tasks; `weighted_average_cost`, `xirr` left out). Per PR:
  3 buggy variants (each replaces a different module with that task's
  first validated mutant) + 1 clean. All 9 PRs validate like the
  mutants: buggy passes every public test and fails at least one hidden
  test, clean passes everything (`.venv\Scripts\python bench\prs.py
  --build --validate`). Building/validating test PRs used no LLM calls.
- Loop + bench: every condition works on a PR package. The reviewer and
  reviser see the whole package and the concatenated spec; claim tests
  may import from any module and are proven against all modules
  (`proof/proofrule.py: prove_claims_modules`); fixes may touch any
  module; condition B regenerates all three modules. `run_bench.py`
  gains `--targets prs` (plus `--prs`, `--pr-target`). Single-task
  targets keep working. Mocked-LLM unit tests cover R/C/D/E/B on a real
  dev PR (88 passed, 4 skipped overall).
- Effort bug found by v3 (important): `--reviewer-effort` never reached
  the reviewer call, so the reviewer always ran at effort `high`. The
  ledger proves the same bug affected pilot v2: rows labelled
  D (medium) / E (medium) record reviewer effort `high`, so v2's
  high-vs-medium rows are not an effort comparison and their costs are
  high-effort costs. Fixed (`proof/loop.py` now passes the settings
  effort to every reviewer call, with a mocked test); all v3 E/D rows
  record reviewer effort `medium` in the ledger. The aborted first v3
  E attempt at the wrong effort and its polluted rerun wasted about
  $1.66 of this session's $6 cap; the published v3 rows are clean
  reruns with unique run ids.

### Pilot v3 (dev PRs only, 1 seed, `results/pilot/v3/`)

| condition | targets | fixed on buggy | damage on clean | regressions | precision | $/target |
|---|---|---|---|---|---|---|
| R | 12 | 0/9 | 0/3 | 0 | n/a | $0.0000 |
| C | 12 | 9/9 | 0/3 | 0 | n/a | $0.0085 |
| E (Wonder medium) | 12 | 9/9 | 0/3 | 0 | n/a | $0.1570 |
| D (Wonder medium) | 7 of 12 | 5/5 | 0/2 | 0 | 0.28 | $0.3189 |

D claims on its 7 targets: proposed 19, PROVEN 18, UNPROVEN discarded 1,
INVALID 0, UNCONFIRMED 13, VALID 5 (precision 5/18 = 0.28). The reviser
contested 0 of the 13 UNCONFIRMED claims and accepted all 13; two D
targets end PARTIAL because accepted UNCONFIRMED claim tests still fail
on code that passes every hidden test. D stopped at 7 of 12 targets
when the session spend reached $5.8784 of the $6 cap (missing:
pr_dev_2 clean/buggy_b/buggy_c, pr_dev_3 buggy_b/buggy_c). Total live
spend this session: $5.8784; product ledger now $20.4459. No LLM call
touched a test-split task (pilot ran `--split dev` only).

### Honest reading of v2 + v3

In v2 (single-function mutants) and again in v3 (PR-sized packages,
where each bug hides in one of three modules among ~56 hidden tests),
every reviewing condition fixed every buggy target it ran on, with zero
damage to clean code and zero regressions. Making the target bigger did
not separate the conditions on fix rate. What separates them is cost
(C is 18x cheaper than E and 37x cheaper than D per PR target) and,
for D, claim quality: the proof rule does not raise the fix rate here,
and D's claim precision got worse on packages (0.28 in v3 versus 0.48
in v2, with the reviser contesting none of the 13 unconfirmed claims,
so the proof gate's filtering value is currently spent on claims the
reviser waves through anyway). Nothing yet shows that proof-gated
review beats Spark self-check or free-text review on correctness; the
only measured D-specific outputs are an auditable claim trail and its
precision number. Separately, v2's effort labels were wrong (see the
effort bug above), so no high-versus-medium conclusion can be drawn
from v2 at all.

### Recommended design for the final run (within $45)

Run both, with PR targets as the headline (they are the realistic
setting and the demo story) and single-task targets for breadth.
Reviewer effort medium (now actually delivered) for D and E, 1 seed
for the Wonder conditions, 2 seeds for the cheap ones. Estimates use
v3 PR costs and v2 single-task costs marked up for harder test tasks;
v2's D/E figures were measured at effort high, so medium should not
exceed them.

| scope | condition | targets x seeds | est. cost |
|---|---|---|---|
| PR test (6 PRs) | R | 24 x 2 | $0 |
| PR test | C | 24 x 2 | $0.58 |
| PR test | E (medium) | 24 x 1 | $5.28 |
| PR test | D (medium) | 24 x 1 | $10.80 |
| PR test | B (regen, per PR) | 6 x 1 | $3.00 |
| single-task test (20 tasks) | R | 80 x 2 | $0 |
| single-task test | C | 80 x 2 | $0.96 |
| single-task test | E (medium) | 80 x 1 | $7.20 |
| single-task test | D (medium) | 80 x 1 | $16.00 |
| **total** | | | **$43.82** |

Cut rule: measure D's real $/target on the first 2 test PRs; if it
exceeds $0.45 per PR target, drop single-task D (saves $16) rather
than any PR condition, and say so in the summary. If even PR D
overruns, finish D's remaining PRs and drop single-task E next.

## M4 results (2026-10-27, desk against a mocked Matrix)

Matrix is down until its Neon quota resets (~Nov 1), so no Matrix API
call was made this session; everything is tested with an
`httpx.MockTransport` mock and a mocked LLM.

- `proof/request_format.py`: parse/format the proof-request markdown
  (`## Spec`, `## Code` with a ```python fence, `## Tests` with or
  without the `(optional)` suffix), mirroring `formatProofRequest` in
  the web `proof.ts`; round-trip tested. Limits enforced at parse:
  Python only, code <= 20,000 chars.
- `proof/matrix_client.py`: httpx client; anonymous feed/creation
  reads, authenticated `proofdesk` review posts with attribution
  headers (`X-Matrix-Provider: meta`, `X-Matrix-Model: <reviewer
  model>`, `X-Matrix-Agent: Matrix Globe`); retries on 429/5xx with
  backoff; the key is never logged and never appears in errors.
- `proof/desk.py`: poll -> already-answered filter (`proofdesk` has a
  top-level review) -> rejection (one polite `QUESTION` review for
  private / non-Python / missing sections / oversized code) -> limits
  (<= 20/day total, <= 3/day per requesting agent, <= $5/day from the
  ledger, 1 per cycle when near a limit) -> `run_proof` mode D with
  `initial_code` and origin `external` -> publish review (BUG_REPORT
  with the combined proven-test file, or PRAISE), verified-revision
  reply, and certificate reply (status line, `/proof?id=` link,
  ```matrix-proof bundle + `sha256:`), exactly what the web
  `readProofThread()` / `extractCertificate()` parse (covered by a
  Python port of `extractCertificate` in the tests). State in
  `state/desk.json` (processed ids, daily counters, last error).
  External code runs only in the Docker sandbox; the desk refuses the
  local sandbox unless `--dry-run` with a local file of our own. The
  reviewer is `muse-wonder-1.0` and the reviser
  `MODEL_BUILDER_EXTERNAL` (`muse-spark-1.3` Standard): desk LLM calls
  carry origin `external`, so the contributor guard fires on any
  `-contributor` model (tested through the real `LLMClient`).
- `.github/workflows/desk.yml`: every 15 min + manual dispatch;
  concurrency group so runs never overlap; exits successfully doing
  nothing when `MODEL_API_KEY`/`PROOFDESK_KEY` is missing or Matrix is
  unreachable/STALE (`GET /v1/agents?pageSize=1` must be 200 without
  `X-Matrix-Cache: STALE`); builds the runner image; runs
  `python -m proof.desk --once`; commits `state/desk.json` to the
  `desk-state` branch (created if missing).
- Unit tests: 119 passed, 4 skipped (Docker live). New coverage:
  parsing, limits, skip-already-answered, the three posts and their
  exact shapes, certificate parse-back, contributor guard for external
  code, STALE/down early exit.
- Live dry run (the session's only live spend, $0.225937 of the $2
  cap; ledger $20.445912 -> $20.671849):
  `examples/split_installments_request.md` (the `100.00 / 3 -> 99.99`
  bug) produced 3 PROVEN claims, a verified revision (public 3/3,
  proven 3/3, VERIFIED) and a certificate whose `sha256` re-verifies
  from the pasted text. Would-be posts are in `docs/desk-dry-run.md`.

### What remains for going live (when Matrix is back, ~Nov 1)

1. Owner registers the Matrix agents `proofdesk`, `proof-builder` and
   `muse-demo` (email codes), and classifies them `seeded` right after
   registration so they never count as external adoption.
2. Owner sets the repo secrets `MODEL_API_KEY` and `PROOFDESK_KEY`
   (and `BUILDER_KEY` for showcase posts) with `gh secret set`.
3. Enable/run the `desk` workflow once by hand, check the first real
   thread (proven defect -> revision -> certificate), then let the
   15-minute schedule run; publish the curated showcase proofs and keep
   an eye on the desk's $5/day and product budget caps.

## Open weights (Baseten) (2026-10-27, branch open-weights)

Verified facts (live probes, 2026-10-27, this session):

- Base URL `https://inference.baseten.co/v1`, OpenAI-compatible. Model id
  exactly `meta-models/muse-spark-open-1026`; the key only works with it.
- `response_format: json_schema` (strict) **works**: returned
  `{"answer": "hi", "n": 3}` for a strict schema on the first attempt, so
  the existing strict-schema path is used unchanged (no tool/JSON-mode
  fallback was needed; both were also probed and work: `json_object` mode
  and a single required function tool both returned correct results).
- `reasoning_effort` **is accepted** (`medium` and `high` both answered;
  the model always reasons and `usage` reports `reasoning_tokens` and
  `cached_tokens`, which the existing usage parsing already handles).
  The benchmark and desk use effort `medium` for the reviewer.
- Price (Baseten model library, baseten.co/library/muse-spark-open,
  verified 2026-10-27): **$1.25 input / $0.15 cached input / $4.25 output
  per 1M tokens** - the same list price as Muse Spark 1.3 Standard, taken
  from Baseten's published page (not estimated). Recorded in
  `proof/config.py` PRICING for the open model.
- Provider routing: model ids starting with `meta-models/` go to Baseten
  (`BASETEN_API_KEY`, never logged); everything else stays on the Meta
  Model API. The ledger records `provider` per call. Baseten spend has
  its own cap `BASETEN_MAX_USD` (default 90) enforced before every call,
  separate from `MAX_USD_TOTAL`. The proof loop now passes its model
  explicitly to every role call, so loop-level model overrides (the open
  conditions, the desk open stack) cannot silently fall back to the
  client's default models - a mocked regression test covers this.
- Incident, honestly: the first launch of this run resolved models from
  the client's (Meta) settings, so ~$0.09 of calls went to the Meta
  contributor model. It was stopped as soon as the ledger showed it,
  all affected rows and bundles were discarded (never used), the root
  cause was fixed (`proof/loop.py`, commit e9a8e52), routing was
  re-verified live (ledger: provider baseten on every call), and only
  then was the run restarted. All reported results below are Baseten-only.

Conditions (test split, 1 seed, reviewer effort medium; bundles record
provider `baseten` and the exact model id; `results/final_open/`):

| scope | condition | provider | targets | fixed | damage | regressions | precision | $/target |
|---|---|---|---|---|---|---|---|---|
| PR | C_open | baseten | 24 | 17/18 (94%) | 0/6 | 0 | n/a | $0.1246 |
| PR | E_open | baseten | 24 | 12/18 (67%) | 0/6 | 0 | n/a | $0.1425 |
| PR | D_open | baseten | 24 | 17/18 (94%) | 0/6 | 0 | 0.40 | $0.0858 |
| single | C_open | baseten | 80 | 54/60 (90%) | 0/20 | 0 | n/a | $0.0708 |
| single | E_open | baseten | 80 | 41/60 (68%) | 0/20 | 0 | n/a | $0.0272 |
| single | D_open | baseten | 80 | 57/60 (95%) | 0/20 | 0 | 0.64 | $0.0634 |

Total Baseten spend for the run: $21.38 (955 ledger calls, all provider
baseten; session live Baseten total including verification probes stays
well under the $60 session cap and the $100 partner credit).

Desk: `DESK_STACK=open` makes `proof/desk.py` use Spark Open for both
reviewer and reviser (external code is fine on Baseten; it is not a
training "contributor" mode). Default stack stays Wonder + Spark.
Unit-tested (mocked) both ways.

Honest comparison with the Wonder-based conditions (read-only from
`C:\MatrixGlobe\results\final\` while that run was still in progress,
plus the finished dev pilots in this file):

- Wonder PR C (Spark self-check, 2 seeds): fixed 36/36, $0.0069/target -
  the contributor-priced self-check remains far cheaper than any open
  condition (C_open $0.1246/PR target) and, on PRs, just as effective.
- Wonder PR E (free-text, 1 seed): fixed 17/18 (94%), $0.1957/target.
  Spark Open free-text review is much weaker (67-68% fixed) though
  cheaper per target; free text is where the open model loses most.
- Wonder PR D (partial at read time, 12/24 rows): fixed 8/9, precision
  0.27, $0.3362/target. D_open is cheaper ($0.0858/PR target) with
  precision 0.40 (PR) / 0.64 (single) and a 94-95% fix rate. On dev
  pilots Wonder D fixed everything it ran on; no finished Wonder
  single-task final numbers existed yet at comparison time, so the
  single-task comparison rests on the dev pilots (all conditions 100%).
- Headline: a fully open-weights Matrix Globe works. Proof-gated review
  is the strongest open condition and beats open free-text review by
  ~27 points of fix rate; it does not beat Wonder on raw fix rate in
  the pilots, and Wonder + contributor pricing still wins on cost for
  self-check. The open stack's value is openness and price
  predictability at a modest quality cost, not a new fix-rate record.

Unit tests: 127 passed, 4 skipped (Docker live) with the
`C:\MatrixGlobe` venv run from `C:\MatrixGlobe-open` (run after the
routing fix; the open-conditions mocked tests assert every role call
carries the open model id).

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

The final test-split benchmark run follows the recommended design in
the M3 part 4 section above (PR targets headline + single-task breadth,
reviewer effort medium now actually delivered, D 1 seed, about $43.82
of the $45 cap, with its cut rule); do not start it without a fresh
session budget. No LLM call may touch test-split tasks outside that
run. M4 is built against a mocked Matrix (see the M4 section above); going live waits for Matrix to return (~Nov 1) and the owner tasks listed there.
