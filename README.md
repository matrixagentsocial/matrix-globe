# Matrix Globe

**AI-written code that ships with a receipt. No proof, no bug.**

Matrix Globe is a code-review loop for agent-written code. The reviewer may
report a defect **only if it also writes a test that fails on the code in an
isolated sandbox**. Claims it cannot reproduce are thrown away. A builder then
revises until every proven test passes, and the whole run (claims, test
hashes, results, costs, final code) is sealed in a SHA-256 certificate that
anyone can recompute in a browser.

- **Proof viewer (judges start here):** https://matrixagentsocial.github.io/matrix-globe/
  holds the results tables and all 902 committed proof bundles. Open any row
  and the page recomputes its SHA-256 in your browser.
- **Built for:** Meta Global AI Developer Hackathon, Indie Dev track
  (Oct 26 – Nov 4, 2026). Everything in this repository was built during the event.
- **Built with:** Muse Code (the code), Muse Wonder (the reviewer), Muse Spark 1.3
  (builder and reviser) and Muse Spark Open on Baseten (the open-weights stack).

## Why

I work in finance. Agents write money code that passes its tests and is still
off by a cent: rounding at the wrong step, an inclusive boundary, a tie broken
the wrong way. A free-text reviewer can say "this looks wrong" a hundred times
and be right twice. Matrix Globe makes the reviewer pay for every claim with an
executable test. You can check that, and the next agent can re-run it.

## How it works

```
spec + code ──► reviewer (Muse Wonder or Spark Open)
                  │  for each claim: title, severity, the spec sentence it relies on, a pytest
                  ▼
               sandbox runs each test against the code
                  │  fails  → PROVEN    passes → UNPROVEN (discarded)    does not run → INVALID
                  ▼
               reviser (Muse Spark) fixes the proven defects, or contests a claim quoting the spec
                  │  up to 2 rounds; rollback if a revision breaks a passing test
                  ▼
               ProofBundle (canonical JSON) ──► sha256 certificate
```

Guards are in code, not in prompts: per-run and total dollar caps checked
before every call (`proof/ledger.py`), a call cap, a wall-clock cap, a sandbox
timeout and rollback to the best version (`proof/loop.py`). Benchmark code (our
own) runs in a trusted local sandbox. External code only runs in Docker with
`--network none`, a read-only root, 512 MB and no secrets (`proof/sandbox/docker.py`).

## FinCode-30: a review benchmark for finance code

There are 30 finance tasks (`bench/tasks/`): split installments, IBAN, Spanish
NIF and CIF, XIRR, ACT/ACT day counts, FX triangulation, FIFO lots, progressive
tax, a 17:00 Madrid cut-off across DST, an idempotent ledger and more. Each has
a spec of 8 to 15 interacting rules, a reference solution, public tests and
hidden tests. 10 tasks are for development and 20 are held out for testing.

The pilots showed that a cheap builder writes these from scratch without
trouble. The real problem is **code that already exists, passes its tests and
is still wrong**. So every task has 3 **mutants**: plausible one-line bugs
that pass every public test and fail at least one hidden test. Each task also
has its **clean** reference, which no reviewer may break. On top of that come
6 **PR packages** of three modules each, with one bug hidden in one module.

The held-out test split ran with prompts frozen before the run. Full tables
are in [`results/final/`](results/final/) and [`results/final_open/`](results/final_open/),
and they are rendered on the viewer.

| models | scope | condition | bugs fixed | correct code damaged | $ / target |
|---|---|---|---|---|---|
| **Open weights** (Spark Open, every role) | single | free-text review | 41/60 (68%) | 0/20 | $0.027 |
| | single | self-check (own tests) | 54/60 (90%) | 0/20 | $0.071 |
| | single | **Matrix Globe (proof-gated)** | **57/60 (95%)** | 0/20 | $0.063 |
| | PR | free-text review | 12/18 (67%) | 0/6 | $0.143 |
| | PR | **Matrix Globe (proof-gated)** | **17/18 (94%)** | 0/6 | $0.086 |
| **Hosted Meta** (Wonder reviewer, Spark reviser) | single | self-check | 119/120 | 0/40 | $0.005 |
| | single | free-text review | 60/60 | 0/20 | $0.101 |
| | single | Matrix Globe (10-task subset) | 28/30 | 0/10 | $0.182 |
| | PR | free-text review | 17/18 | 0/6 | $0.196 |
| | PR | Matrix Globe | 17/18 | 0/6 | $0.312 |

What this shows:

1. **The proof rule turns a cheap open model into a reliable reviewer.** With
   the same open-weights model, proof-gated review fixed 57/60 bugs where
   free-text review fixed 41/60 (PR packages: 17/18 against 12/18), with no
   damage to correct code, for 6 to 9 cents per target.
2. **With Meta's strongest model, every reviewing condition fixes almost
   everything.** Requiring proof does not raise the fix rate there; Spark's
   self-check is as good and about 40x cheaper. What the proof rule adds is
   the audit trail: every reported defect comes with a test that fails.
3. **The reviewer never contradicted the spec.** 190 proven claims also failed
   on our own reference solution. We read every one of them against the spec
   ([`results/unconfirmed_classification.md`](results/unconfirmed_classification.md),
   rules in [`bench/classify_unconfirmed.py`](bench/classify_unconfirmed.py)).
   0 contradicted it. 102 were **real defects that our references share**:
   dates with a trailing newline, a 2-character code that `upper()` turns into
   3 characters, valid 29-digit amounts that crash the default Decimal context.
   The other 88 were genuine ambiguities in our specs, mostly whether `"1.500"`
   has "at most 2 decimal places". Counting VALID plus shared defects, 82% of
   Wonder's proven claims and 68% of Spark Open's point at real defects.
4. **Honest misses.** Hosted D broke two passing hidden tests on one PR (the
   bundle records it). Single-task D on the hosted stack ran on a 10-task
   subset, declared before it ran, to save credits.

## Verify a proof yourself

1. Open any row on the [viewer](https://matrixagentsocial.github.io/matrix-globe/).
   The page fetches the bundle, rebuilds its canonical JSON (sorted keys, no
   whitespace, UTF-8) and shows `✓ verified in your browser`.
2. Or offline:

```bash
python -c "import json,sys; from proof.bundle import canonical_json, sha256_text; print(sha256_text(canonical_json(json.load(open(sys.argv[1], encoding='utf-8')))))" results/final/bundles_pr_D/bench-D-pr_test_1-buggy_a-s0final-pr_D.json
```

That hash equals `bundle_sha256` in `results/final/pr_D.jsonl`. A test checks
this for every final-run row (`tests/test_site_index.py`).

## Run it

Python 3.11. Keys go in `.env` (see `.env.example`). The benchmark caps
spend at `MAX_USD_TOTAL` and `MAX_USD_PER_RUN`.

```bash
python -m venv .venv && .venv/Scripts/pip install -e .        # or .venv/bin/pip
python -m pytest -q                                           # 130 tests, mocked LLM, no spend
python bench/validate_tasks.py                                # every mutant passes public, fails hidden
python scripts/review_demo.py                                 # live: naive split_installments, ~$0.11
python bench/run_bench.py --cond D_open --split test --targets mutants --task allocate_ratios
python -m proof.desk --dry-run --request-file examples/split_installments_request.md
```

## Matrix integration (`@proofdesk`)

[Matrix](https://matrixagentnet.com) is a social network for AI agents.
`proof/desk.py` polls Matrix for proof requests (spec plus code), proves them,
and posts the thread: the proven defects, the revision and a certificate link.
On the Matrix side, a `/proof` page and the MCP tools `request_proof` and
`get_proof` let any agent, Muse Code included, ask for a proof. They are
built on the Matrix branch `hackathon/matrix-globe`. The desk was
built and dry-run against a mocked Matrix
([`docs/desk-dry-run.md`](docs/desk-dry-run.md)), because Matrix's free database
was over quota during the event. It goes live when the database is back. The
proof viewer above never depends on Matrix.

## Repository map

| path | what |
|---|---|
| `proof/loop.py` | the loop: conditions R, B, C, D, E and the open variants, guards, rollback |
| `proof/proofrule.py` | one claim's test, one sandbox run: PROVEN, UNPROVEN or INVALID; VALID or UNCONFIRMED against the reference |
| `proof/roles/` | builder, reviewer (strict JSON schema), reviser, self-refine, prompts |
| `proof/bundle.py` | ProofBundle, canonical JSON, sha256 |
| `proof/sandbox/` | trusted local sandbox, Docker `--network none` sandbox |
| `proof/llm.py`, `proof/ledger.py` | OpenAI-compatible client for the Meta Model API and Baseten, cost ledger with hard caps |
| `proof/desk.py`, `proof/matrix_client.py` | the `@proofdesk` desk |
| `bench/` | FinCode-30, mutants, PR packages, runner, validation, claim classification |
| `results/` | every committed run: JSONL rows and proof bundles |
| `site/` | static proof viewer (GitHub Pages) |
| `PROGRESS.md` | day-by-day log with every decision, cost and incident |
| [`docs/built-with-muse-code.md`](docs/built-with-muse-code.md) | which agent wrote what |

## Cost

About $110 of the $150 Meta credits, Muse Code build sessions included, and
about $21 of Baseten credits. The final hosted run cost $30.60. The open-weights
run cost $21.38. Every call is in the ledger with its model, tokens and dollars.

MIT licensed.
