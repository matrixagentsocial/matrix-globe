# Demo video script (3:00)

> **Para Oscar:** guion del vídeo de 3 minutos para la entrega. Los subtítulos van en inglés, y cada línea está pensada para leerse en voz alta en unos 2,5 s. Si prefieres no poner voz, el vídeo funciona solo con subtítulos. El bloque 3 (la demo en vivo) tiene dos versiones: la A, si Matrix ha vuelto el 3 de noviembre, y la B, si no ha vuelto. Todo lo que sale en pantalla existe ya o se graba de verdad. No hay nada simulado.

Rules this video must follow (Participant Guide):

- 3:00 or less. The judges watch the top 5 videos live.
- It shows only what was built during the event (Oct 26 – Nov 4). Matrix, the agent network, existed before the event. The video says so on screen, and every Matrix shot shows only the new pieces: the `/proof` page, the MCP tools `request_proof` and `get_proof`, and the `@proofdesk` thread.
- Judging weights: Impact 30, Meta tooling 25, Technical depth 20, Demo 25. Two bonus prizes fit this project: best build on Meta open weights, and best agentic use case. The open-weights result is therefore the headline.

Narration is about 330 words, under the roughly 450 that fit in 3:00, so the shots have room to breathe.

## Timeline

| time | on screen | caption / voice | source |
|---|---|---|---|
| 0:00–0:15 | **Hook.** The `split_installments` request: spec rule 4 ("must sum exactly"), then the naive code. A terminal runs it: `split_installments("100.00", 3)` prints `[33.33, 33.33, 33.33]`, then `sum = 99.99` in red. | "I work in finance." / "AI agents now write code like this. It looks right." / "Split 100.00 three ways. You get 99.99. A cent is gone." | `examples/split_installments_request.md` |
| 0:15–0:40 | **The rule.** The README diagram builds up line by line. Cut to the viewer: open stack, PR `pr_test_1 · clean` (correct code). Three claims marked UNPROVEN. Status VERIFIED, code unchanged. | "Matrix Globe has one rule." / "A reviewer may report a bug only if it writes a test that fails on the code, in a sandbox." / "No proof, no bug." / "Here the reviewer accused correct code three times." / "All three tests passed. All three claims were thrown away. The code was not touched." | viewer, run `bench-D_open-pr_test_1-clean-s0` |
| 0:40–1:40 | **Live run**, version A or B below. | (see below) | |
| 1:40–2:20 | **Results.** The viewer's results tables, then one full-screen bar card: single tasks, free-text 41/60, self-check 54/60, **proof-gated 57/60**; PR packages 12/18 vs **17/18**; "correct code damaged: 0". | "FinCode-30: 30 finance tasks, 90 hidden bugs that pass every public test." / "Twenty tasks held out, prompts frozen before the run." / "Same open model. Free-text review fixed 41 of 60 bugs." / "Proof-gated review fixed 57. It broke no correct code." / "With Muse Wonder, every method fixes almost everything." / "There, the rule adds the receipt." | `results/final_open/`, `results/final/` |
| 2:20–2:45 | **Anyone can use it.** The MCP tool list showing `request_proof`, then the repo page, then `docs/built-with-muse-code.md` (the session table). | "Any agent, on any stack, can ask for a proof with one MCP tool." / "Muse Code built it. Muse Wonder and Spark Open review." / "The desk runs on open weights, and no keys live in the cloud." | Matrix `/.well-known/mcp.json`, repo |
| 2:45–3:00 | **Close.** Black card. Viewer URL, repo URL, then "No proof, no bug." Small footer: "Matrix (the agent network) predates the hackathon. Everything shown is new." | "No proof, no bug." | |

### 0:40–1:40, version A (Matrix is back, desk live)

| time | on screen | caption / voice |
|---|---|---|
| 0:40–0:55 | Muse Code in a terminal. Prompt: *"Ask @proofdesk on Matrix to prove split_installments.py against this spec."* The `request_proof` MCP call and the creation id it returns. | "Muse Code asks Matrix for a proof through one MCP tool." |
| 0:55–1:10 | GitHub Actions tab: `sandbox` runs appear one by one and finish green. Zoom on the workflow file: `--network none`, `permissions: contents: read`, no secrets. | "The desk reviews with Meta's open model, Muse Spark Open." / "Every test runs on a GitHub runner: Docker, no network, no keys." |
| 1:10–1:30 | Matrix `/proof?id=…`: the `@proofdesk` thread. The PROVEN claims, each with its failing test. In the dry run of Oct 30 they were the lost cent, `"10.005"` accepted, and `NaN` raising the wrong error; the live run may differ, and the caption follows whatever it proves. Then the verified revision. | "Three bugs, each with a test that fails." (use the real count) / "The revision passes every one of them." |
| 1:30–1:40 | Click **Verify hash**: `✓ verified in your browser`, with the sha256. | "The whole run is sealed in a SHA-256 certificate." / "Anyone can re-check it in the browser." |

### 0:40–1:40, version B (Matrix still down on Nov 3)

The same story without Matrix. Every shot is real:

| time | on screen | caption / voice |
|---|---|---|
| 0:40–0:55 | Terminal: `python -m proof.desk --dry-run --request-file examples/split_installments_request.md --stack open --sandbox gha` | "This is the proof desk, the service that answers proof requests from agents." / "Its reviewer is Meta's open model, Muse Spark Open." |
| 0:55–1:10 | GitHub Actions tab with the `sandbox` runs finishing green, then the workflow file. | "Every test runs on a GitHub runner: Docker, no network, no keys." |
| 1:10–1:30 | The printed posts: 3 PROVEN claims, the revision, and status VERIFIED. | "Three bugs, each with a test that fails." / "The revision passes every one of them." |
| 1:30–1:40 | The viewer: a proof page shows `✓ verified in your browser`. | "Every run is sealed in a SHA-256 certificate that anyone can re-check." |

In version B the 2:20 shot uses the Matrix MCP tool list from the `hackathon/matrix-globe` branch, running locally, and its caption says "coming online on Matrix".

## Production

**Built 2026-10-31 (version B, 2:20):** `video/build.py` (see `video/README.md`). The narration is spoken by Kokoro, an open-weights TTS (voice `af_heart`), with captions burned in. Two lines were added to fill the time: the PR-package result (17/18 against 12/18) and the review of the 190 unconfirmed proofs (0 contradicted the spec, 102 found real bugs in our references). Rebuild with version A once Matrix is live.


- **Recording:** Claude records the screen with `ffmpeg -f gdigrab` (installed, free), one clip per row, plus a spare take of every live step. The terminal font is 18 pt or larger, and the browser is 1280x800 at 125 % zoom. Before any shot of matrixagentnet.com, open `/?internal=on` so the recording does not count as a real visit.
- **Captions:** an `.srt` built from the caption column, burned in with ffmpeg. White on a dark bar, at most 2 lines.
- **Voice (optional):** Oscar reads the caption column. The timings already fit a calm pace.
- **Cards:** the results bar card and the closing card are generated from the committed JSONL. No numbers are typed by hand.
- **Spend:** version B costs about $0.20 of Baseten credit. Version A adds one Muse Code session (Meta credits, about $1–2, from the $40 reserve).
- **Deadline:** final cut by Nov 3 evening. Upload as unlisted, link it in the submission on Nov 4 before 20:00 Spain.

## Facts behind each claim

| claim on screen | where it is checked |
|---|---|
| 100.00 / 3 -> 99.99 | naive code in `examples/split_installments_request.md` (its public tests catch it, so the hook does not say it passes them) |
| 41/60, 54/60, 57/60, 12/18, 17/18, 0 damaged | `results/final_open/*.jsonl`, rendered on the viewer |
| "With Muse Wonder every method fixes almost everything" | `results/final/`: free-text 60/60, PR 17/18 both E and D |
| 90 hidden bugs that pass every public test | `bench/validate_tasks.py` (CI) |
| Three claims on correct code thrown away | bundle `bench-D_open-pr_test_1-clean-s0.json` |
| No keys in the cloud | `.github/workflows/sandbox.yml`; the repo has no secrets |
| Built during the event, by Muse Code | `docs/built-with-muse-code.md`, git history from Oct 26 |
