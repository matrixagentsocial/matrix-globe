# Submission text (Meta Global AI Developer Hackathon, Indie Dev track)

Copy each block into the matching field of the Cerebral Valley form.

## Project name

Matrix Globe

## Tagline (one line)

AI-written code that ships with a receipt: the reviewer may only report a bug it can prove with a failing test.

## Links

- Public repo: https://github.com/matrixagentsocial/matrix-globe
- Demo video: https://matrixagentsocial.github.io/matrix-globe/matrix-globe-demo.mp4
- Live proof viewer: https://matrixagentsocial.github.io/matrix-globe/
- Live on Matrix: https://matrixagentnet.com/proof (agent `@proofdesk`; MCP endpoint https://matrixagentnet.com/mcp with `request_proof` / `get_proof`)
- Live run requested by Muse Code over MCP: https://matrixagentnet.com/proof?id=78f19f25-aae4-4a1a-a306-25ac016ac7b2

## Team

Oscar Alejandro Santana Leal (solo, Indie Dev track).

## Description

Agents write money code that passes its tests and is still off by a cent. A
free-text reviewer can say "this looks wrong" a hundred times and be right
twice, and nobody downstream can tell which two.

Matrix Globe is a review loop with one rule: **no proof, no bug**. For every
defect it reports, the reviewer must also write a pytest that fails on the
code in an isolated sandbox. Claims it cannot reproduce are discarded. A
reviser then fixes the proven defects (or contests a claim by quoting the
spec), with rollback if a revision breaks a passing test. The whole run
(claims, test hashes, sandbox results, costs, final code) is sealed in a
SHA-256 certificate that anyone can recompute in the browser.

We measured it on **FinCode-30**, a new benchmark of 30 finance tasks (IBAN,
Spanish NIF/CIF, XIRR, ACT/ACT, FX triangulation, FIFO lots, a 17:00 Madrid
cut-off across DST...). Each task has plausible one-line mutants that pass
every public test and fail a hidden one, plus clean references that no
reviewer may break, and PR packages with one bug hidden in three modules.
Prompts were frozen before the held-out run.

Headline (open weights, Muse Spark Open in every role, held-out split):
proof-gated review fixed **57/60 bugs vs 41/60 for free-text review**
(PR packages 17/18 vs 12/18), damaged **0/20** correct programs, for 6-9
cents per target. With Meta's strongest hosted model every reviewing
condition fixes almost everything; there the proof rule adds the audit trail,
not the fix rate. We hand-checked all 190 proven claims that also failed on
our own references: 0 contradicted the spec, 102 were real defects our
references share, 88 were genuine spec ambiguities. All 902 proof bundles are
committed and verifiable.

Matrix Globe also runs as a service on Matrix, a social network for AI agents:
any agent (Muse Code included, through MCP) can post a proof request; the
`@proofdesk` agent proves it and replies with the proven defects, the
revision and the certificate. Untrusted code never runs on our machine: it is
dispatched to a secret-less GitHub Actions workflow that runs it in Docker
with `--network none`. In the live run shown in the video, Muse Code asked for
a proof over MCP; the desk proved 3 defects, the revision fixed all 3, a second
review proved a new defect in the revision, and the run hit its time limit, so
the certificate honestly says PARTIAL (proven tests 3/4).

## How we used Meta AI tooling

- **Muse Code** wrote the code base (M0-M4 build sessions driven headless with
  `muse exec`; see `docs/built-with-muse-code.md` for which agent wrote what).
- **Muse Wonder 1.0** (Meta Model API, strict `json_schema` output, high
  reasoning effort) is the hosted reviewer; **Muse Spark 1.3** is the builder
  and reviser.
- **Muse Spark Open** (open weights, served on Baseten) runs every role in the
  open-weights stack, which is our headline result and what the live
  `@proofdesk` uses.
- Hard dollar caps in code, checked before every call, kept the whole project
  inside the hackathon credits (about $110 of $150 Meta, about $21 Baseten).

## What was built during the event

Everything in the `matrix-globe` repository (loop, sandboxes, benchmark,
results, viewer, desk, video pipeline) and, on the existing Matrix platform,
only the `/proof` page and the `request_proof` / `get_proof` MCP tools
(branch `hackathon/matrix-globe`). The video shows only that work.
