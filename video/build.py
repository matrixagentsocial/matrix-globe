"""Build the 3-minute demo video (docs/video-script.md, version B).

Usage (from the repo root, with the video tools installed, see video/README.md):

    python video/build.py --models <dir with kokoro-v1.0.onnx + voices-v1.0.bin> [--only tts|record|assemble]

Steps:
1. tts: every narration line is spoken by Kokoro (open-weights TTS, voice
   af_heart) into build/audio/*.wav; durations set the timeline.
2. record: each shot is recorded at 1920x1080 by Playwright. Cards are
   local HTML pages; "live" shots browse the real public pages (the proof
   viewer on GitHub Pages, the repository and its Actions runs on GitHub).
3. assemble: ffmpeg cuts every shot to its length, joins them, mixes the
   narration and burns in the captions (build/captions.ass).

Every number on a card is read from results/ at build time.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import subprocess
import time
import wave
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILD = REPO / "video" / "build"
VIEWER = "https://matrixagentsocial.github.io/matrix-globe/"
GITHUB = "https://github.com/matrixagentsocial/matrix-globe"
W, H, FPS = 1920, 1080, 30
VOICE, SPEED = "af_heart", 1.0
LEAD, GAP, TAIL = 0.7, 0.45, 1.0


# ------------------------------------------------------------ results
def rows(folder: str, name: str) -> list[dict]:
    path = REPO / "results" / folder / f"{name}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def fixed(folder: str, name: str) -> tuple[int, int, int]:
    """(bugs fixed, buggy targets, clean targets damaged) for one results file."""
    rs = rows(folder, name)
    buggy = [r for r in rs if r["target_id"] != "clean"]
    clean = [r for r in rs if r["target_id"] == "clean"]
    return sum(1 for r in buggy if r["fixed"]), len(buggy), sum(1 for r in clean if r["damaged"])


# -------------------------------------------------------------- shots
# Each line: (spoken text, caption). Captions use digits; speech spells them out.
def shots() -> list[dict]:
    e_fix, e_n, _ = fixed("final_open", "single_E_open")
    c_fix, c_n, _ = fixed("final_open", "single_C_open")
    d_fix, d_n, d_dmg = fixed("final_open", "single_D_open")
    pe_fix, pe_n, _ = fixed("final_open", "pr_E_open")
    pd_fix, pd_n, pd_dmg = fixed("final_open", "pr_D_open")
    assert (e_fix, d_fix, d_n) == (41, 57, 60), "the narration below says 41 and 57 of 60"
    bars = {"single": [("Free-text review", e_fix, e_n), ("Self-check (own tests)", c_fix, c_n),
                       ("Proof-gated (Matrix Globe)", d_fix, d_n)],
            "pr": [("Free-text review", pe_fix, pe_n), ("Proof-gated (Matrix Globe)", pd_fix, pd_n)],
            "damaged": d_dmg + pd_dmg}
    return [
        {"id": "hook", "kind": "card", "html": hook_html, "lines": [
            ("I work in finance.", "I work in finance."),
            ("AI agents now write money code like this. It looks right.",
             "AI agents now write money code like this. It looks right."),
            ("Split one hundred dollars three ways, and you get ninety-nine ninety-nine. A cent is gone.",
             "Split 100.00 three ways and you get 99.99. A cent is gone."),
        ]},
        {"id": "rule", "kind": "card", "html": rule_html, "lines": [
            ("Matrix Globe has one rule.", "Matrix Globe has one rule."),
            ("A reviewer may report a bug only if it writes a test that fails on the code, in a sandbox.",
             "A reviewer may report a bug only if it writes a test that fails on the code, in a sandbox."),
            ("No proof, no bug.", "No proof, no bug."),
        ]},
        {"id": "clean", "kind": "live", "act": act_clean, "lead": 1.0, "tail": 1.8, "lines": [
            ("Here, the reviewer accused correct code three times.",
             "Here the reviewer accused correct code three times."),
            ("All three tests passed. All three claims were thrown away, and the code was not touched.",
             "All three tests passed. All three claims were thrown away, and the code was not touched."),
        ]},
        {"id": "desk", "kind": "card", "html": desk_cmd_html, "lines": [
            ("This is the proof desk, the service that answers proof requests from other agents.",
             "This is the proof desk, the service that answers proof requests from other agents."),
            ("Its reviewer is Meta's open-weights model, Muse Spark Open.",
             "Its reviewer is Meta's open-weights model, Muse Spark Open."),
        ]},
        {"id": "actions", "kind": "live", "act": act_actions, "vp": (1600, 900), "lead": 0.8, "tail": 2.5, "lines": [
            ("Every test runs on a GitHub runner, in Docker, with no network and no keys.",
             "Every test runs on a GitHub runner, in Docker, with no network and no keys."),
        ]},
        {"id": "posts", "kind": "card", "html": desk_posts_html, "lines": [
            ("On this request it proved three bugs, each with a test that fails.",
             "On this request it proved three bugs, each with a test that fails."),
            ("The revision passes every one of them.", "The revision passes every one of them."),
        ]},
        {"id": "verify", "kind": "live", "act": act_verify, "lead": 1.0, "tail": 2.0, "lines": [
            ("Every run is sealed in a SHA-256 certificate that anyone can re-check in the browser.",
             "Every run is sealed in a SHA-256 certificate that anyone can re-check in the browser."),
        ]},
        {"id": "results", "kind": "live", "act": act_results, "lead": 1.0, "tail": 1.5, "lines": [
            ("FinCode-30: thirty finance tasks, with ninety hidden bugs that pass every public test.",
             "FinCode-30: 30 finance tasks, 90 hidden bugs that pass every public test."),
            ("Twenty tasks were held out, and the prompts were frozen before the run.",
             "20 tasks held out. Prompts frozen before the run."),
        ]},
        {"id": "bars", "kind": "card", "html": lambda T: bars_html(T, bars), "lines": [
            ("With the same open model, free-text review fixed forty-one of sixty bugs.",
             "Same open model: free-text review fixed 41 of 60 bugs."),
            ("Proof-gated review fixed fifty-seven, and broke no correct code.",
             "Proof-gated review fixed 57, and broke no correct code."),
            ("On three-module pull requests, it fixed seventeen of eighteen, against twelve.",
             "On 3-module pull requests: 17 of 18, against 12 of 18."),
            ("With Muse Wonder, every method fixes almost everything. There, the rule adds the receipt.",
             "With Muse Wonder every method fixes almost everything. There, the rule adds the receipt."),
        ]},
        {"id": "classify", "kind": "live", "act": act_classify, "vp": (1600, 900), "lead": 1.0, "tail": 1.5, "lines": [
            ("We read all one hundred ninety proofs that also failed our own reference solutions.",
             "We read all 190 proofs that also failed our own reference solutions."),
            ("None contradicted the spec. One hundred two found real bugs in our own code.",
             "None contradicted the spec. 102 found real bugs in our own code."),
        ]},
        {"id": "mcp", "kind": "card", "html": mcp_html, "lines": [
            ("Agents will ask for proofs on Matrix, the agent network, with one MCP tool.",
             "Agents will ask for proofs on Matrix, the agent network, with one MCP tool."),
        ]},
        {"id": "built", "kind": "live", "act": act_built, "vp": (1600, 900), "lead": 1.0, "tail": 1.5, "lines": [
            ("Muse Code built it during the hackathon. Muse Wonder and Spark Open do the reviewing.",
             "Muse Code built it during the hackathon. Muse Wonder and Spark Open do the reviewing."),
            ("The desk runs on open weights, and no keys live in the cloud.",
             "The desk runs on open weights, and no keys live in the cloud."),
        ]},
        {"id": "close", "kind": "card", "html": close_html, "tail": 2.5, "lines": [
            ("No proof, no bug.", "No proof, no bug."),
        ]},
    ]


# --------------------------------------------------------------- cards
CSS = """
:root{--bg:#080808;--card:#0f1410;--border:#1f2e22;--text:#e6ffe9;--muted:#8aa88f;--green:#00ff41;--red:#ff6b6b;--cyan:#4de3ff}
*{box-sizing:border-box}html,body{margin:0;width:1920px;height:1080px;overflow:hidden;background:var(--bg);color:var(--text);
font:34px/1.45 "Segoe UI",system-ui,sans-serif}
.wrap{padding:90px 140px}.eyebrow{font:26px Consolas,monospace;letter-spacing:.2em;text-transform:uppercase;color:var(--green)}
h1{font-size:76px;margin:10px 0 30px;line-height:1.1}.mono{font-family:Consolas,monospace}
.box{background:var(--card);border:2px solid var(--border);border-radius:18px;padding:30px 38px;margin:22px 0}
pre{margin:0;font:30px/1.5 Consolas,monospace;white-space:pre-wrap}.muted{color:var(--muted)}.green{color:var(--green)}.red{color:var(--red)}
[data-at]{opacity:0;transform:translateY(14px);transition:opacity .45s,transform .45s}[data-at].on{opacity:1;transform:none}
.term{background:#000;border:2px solid #222;border-radius:14px;padding:30px 36px;font:28px/1.5 Consolas,monospace}
.term .p{color:var(--green)}
"""

JS = """
let T=__T__;function go(){const s=performance.now();(function f(){const t=(performance.now()-s)/1000;
document.querySelectorAll('[data-at]').forEach(e=>{const k=+e.dataset.at;const at=k<0?0:(T[k]??999)+(+e.dataset.d||0);if(t>=at)e.classList.add('on')});
document.querySelectorAll('[data-type]').forEach(e=>{const at=(T[+e.dataset.type]??0)+(+e.dataset.d||0);const full=e.dataset.text;
const n=Math.max(0,Math.min(full.length,Math.floor((t-at)*40)));e.textContent=full.slice(0,n)});
document.querySelectorAll('[data-bar]').forEach(e=>{const at=T[+e.dataset.bar]??0;const p=Math.max(0,Math.min(1,(t-at)/1.2));
e.style.width=(p*+e.dataset.w)+'%'});requestAnimationFrame(f)})()}
"""


def page(body: str, T: list[float]) -> str:
    return (f"<!doctype html><meta charset=utf-8><style>{CSS}</style><body>{body}"
            f"<script>{JS.replace('__T__', json.dumps(T))}</script></body>")


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def request_blocks() -> tuple[str, str]:
    text = (REPO / "examples" / "split_installments_request.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```python\n(.*?)```", text, re.S)
    rule4 = next(line for line in text.splitlines() if line.startswith("4."))
    return rule4, blocks[1]


def hook_html(T):
    rule4, code = request_blocks()
    rule4 = re.sub(r"\*\*(.+?)\*\*", r"<b class=green>\1</b>", esc(rule4[3:]).replace("`", ""))
    return page(f"""<div class=wrap style="padding:70px 80px"><div class=eyebrow data-at=-1>Matrix Globe · Meta AI Developer Hackathon</div>
<div class=box data-at=0 style="font-size:30px"><span class=muted>Spec, rule 4:</span> {rule4}</div>
<div style="display:flex;gap:28px;align-items:flex-start"><div class=box data-at=1 style="flex:1.45;margin:0"><pre style="font-size:23px">{esc(code.strip())}</pre></div>
<div class=term data-at=2 style="flex:1;font-size:27px"><span class=p>&gt;&gt;&gt; </span><span data-type=2 data-text='split_installments("100.00", 3)'></span><br>
<span data-at=2 data-d=1.3>[Decimal('33.33'), Decimal('33.33'), Decimal('33.33')]</span><br>
<span data-at=2 data-d=1.9><span class=p>&gt;&gt;&gt; </span>sum(_)</span><br>
<span data-at=2 data-d=2.4 class=red style="font-size:40px">Decimal('99.99')</span><br>
<span data-at=2 data-d=2.8 class=red style="font-size:32px">← a cent is gone</span></div></div></div>""", T)


def rule_html(T):
    step = lambda k, d, title, sub: (f"<div class=box data-at={k} data-d={d} style='flex:1'><div class='mono green' "
                                     f"style='font-size:30px'>{title}</div><div class=muted style='font-size:28px'>{sub}</div></div>")
    return page(f"""<div class=wrap><div class=eyebrow data-at=-1>The rule</div><h1 data-at=0>A bug report must come with a failing test.</h1>
<div style="display:flex;gap:28px">{step(1, 0, "1 · Reviewer", "writes one pytest per claimed defect")}
{step(1, 1.4, "2 · Sandbox", "runs it against the code: isolated, no network")}
{step(1, 2.8, "3 · Verdict", "<span class=red>fails → PROVEN</span><br>passes → discarded")}</div>
<div data-at=2 style="text-align:center;margin-top:70px;font:bold 120px Consolas,monospace;color:var(--green)">No proof, no bug.</div></div>""", T)


def desk_output() -> str:
    md = (REPO / "docs" / "desk-dry-run-open-gha.md").read_text(encoding="utf-8")
    return md.split("````text\n", 1)[1].split("\n````", 1)[0]


def desk_cmd_html(T):
    cmd = ("python -m proof.desk --dry-run --request-file examples/split_installments_request.md "
           "--stack open --sandbox gha")
    return page(f"""<div class=wrap><div class=eyebrow data-at=-1>The proof desk · @proofdesk</div>
<h1 data-at=0>Answers proof requests from other agents</h1>
<div class=term data-at=0 data-d=0.4><span class=p>PS C:\\MatrixGlobe&gt; </span><span data-type=0 data-d=0.8 data-text="{esc(cmd)}"></span></div>
<div class=box data-at=1 style="font-size:32px"><span class=muted>reviewer + reviser:</span> <span class=mono>meta-models/muse-spark-open-1026</span>
<span class=muted>(Muse Spark Open, open weights, on Baseten)</span><br><span class=muted>sandbox:</span>
<span class=mono>github-actions · docker --network none · no secrets</span></div>
<div class=muted data-at=1 data-d=1 style="font-size:24px">Replay of the real run of 2026-10-30, docs/desk-dry-run-open-gha.md</div></div>""", T)


def desk_posts_html(T):
    out = desk_output()
    claims = re.findall(r"^- (C\d) \[PROVEN\] (.+)$", out, re.M)
    tests = re.findall(r"^def (test_\w+)", out, re.M)
    status = re.search(r"Status after revision: (\w+)", out).group(1)
    items = "".join(f"<div data-at=0 data-d={0.6 + i * 0.7}><span class=red>✗ {c} PROVEN</span> {esc(t)}<br>"
                    f"<span class='mono muted' style='font-size:26px'>&nbsp;&nbsp;&nbsp;failing test: {tests[i]}</span></div>"
                    for i, (c, t) in enumerate(claims))
    return page(f"""<div class=wrap><div class=eyebrow data-at=-1>Post 1 · BUG_REPORT by @proofdesk</div>
<div class=box data-at=-1 style="font-size:32px">{items}</div>
<div class=eyebrow data-at=1>Post 2 · verified revision</div>
<div class=box data-at=1 style="font-size:34px"><span class=green>✓ public tests 3/3 · proven tests 3/3 · status {status}</span></div>
<div class=muted data-at=1 data-d=0.8 style="font-size:24px">Same run, docs/desk-dry-run-open-gha.md · 14 sandbox runs on GitHub · $0.18</div></div>""", T)


def bars_html(T, bars):
    def bar(label, fix, n, k, hi):
        color = "var(--green)" if hi else "#3a5a40"
        return (f"<div style='display:flex;align-items:center;gap:24px;margin:16px 0'><div style='width:520px;font-size:30px'>{label}</div>"
                f"<div style='flex:1;background:#111;border-radius:10px;height:56px'><div data-bar={k} data-w={100 * fix / n} "
                f"style='height:56px;width:0;background:{color};border-radius:10px'></div></div>"
                f"<div class=mono data-at={k} data-d=1 style='width:170px;font-size:38px'>{fix}/{n}</div></div>")
    single = "".join(bar(lbl, f, n, 0 if i < 2 else 1, i == 2) for i, (lbl, f, n) in enumerate(bars["single"]))
    pr = "".join(bar(lbl, f, n, 1, i == 1) for i, (lbl, f, n) in enumerate(bars["pr"]))
    return page(f"""<div class=wrap style="padding-top:60px"><div class=eyebrow data-at=-1>FinCode-30 · held-out test split · Muse Spark Open in every role</div>
<h2 class=muted style="font-weight:normal;margin:26px 0 0">Bugs fixed, single tasks (60 hidden bugs)</h2>{single}
<h2 class=muted style="font-weight:normal;margin:30px 0 0">Bugs fixed, 3-module PR packages (18 hidden bugs)</h2>{pr}
<div class=box data-at=1 data-d=1.5 style="margin-top:34px"><span class=green>Correct code damaged by proof-gated review: {bars['damaged']}</span></div>
<div class=muted data-at=2 style="font-size:28px">Hosted Muse Wonder reviewer: every method fixes almost everything; the proof rule adds a failing test to every reported bug.</div></div>""", T)


def mcp_html(T):
    return page("""<div class=wrap><div class=eyebrow data-at=-1>Matrix MCP tools · new in this hackathon · coming online on Matrix</div>
<h1 data-at=-1>One tool call to ask for a proof</h1>
<div class=box data-at=0><pre><span class=green>request_proof</span>(spec, code, tests?)   <span class=muted>→ creationId, proofUrl</span>
<span class=green>get_proof</span>(creationId)              <span class=muted>→ claims, proven tests, revision, certificate</span></pre></div>
<div class=muted data-at=0 data-d=1.5 style="font-size:28px">Matrix (matrixagentnet.com, the social network for AI agents) existed before the event.<br>
The /proof page and these two tools were built during it (branch hackathon/matrix-globe).</div></div>""", T)


def close_html(T):
    return page(f"""<div class=wrap style="text-align:center;padding-top:200px">
<div style="font:bold 130px Consolas,monospace;color:var(--green)" data-at=-1>No proof, no bug.</div>
<div class=mono style="font-size:40px;margin-top:60px" data-at=-1>{VIEWER.replace('https://', '')}</div>
<div class=mono style="font-size:40px;margin-top:14px" data-at=-1>{GITHUB.replace('https://', '')}</div>
<div class=muted style="font-size:24px;margin-top:120px" data-at=-1>Matrix Globe · built during the Meta AI Developer Hackathon with Muse Code, Muse Wonder,
Muse Spark and Muse Spark Open.<br>Matrix, the agent network, predates the event; everything shown here was built during it.
Voice: Kokoro (open weights).</div></div>""", T)


# --------------------------------------------------------- live shots
def at(t0: float, t: float) -> None:
    left = t0 + t - time.monotonic()
    if left > 0:
        time.sleep(left)


def scroll_to(page, js_element: str, ms: int = 1400, margin: int = 24) -> None:
    """Smoothly scroll the element found by *js_element* (a JS expression) to the top."""
    page.evaluate(f"(() => {{const e={js_element}; if (e) {{e.style.scrollMarginTop='{margin}px';"
                  f"e.scrollIntoView({{behavior:'smooth', block:'start'}})}}}})()")
    page.wait_for_timeout(ms)


def scroll_by(page, dy: int, ms: int = 1400) -> None:
    page.evaluate(f"window.scrollBy({{top:{dy}, behavior:'smooth'}})")
    page.wait_for_timeout(ms)


def zoom(page, z: float) -> None:
    page.evaluate(f"document.documentElement.style.zoom='{z}'")


def act_clean(page, T, dur, t0):
    page.goto(VIEWER + "proof.html?run=bench-D_open-pr_test_1-clean-s0", wait_until="networkidle")
    zoom(page, 1.5)
    page.wait_for_timeout(800)
    t0[0] = time.monotonic()
    at(t0[0], T[0] - 0.2)
    scroll_to(page, "[...document.querySelectorAll('h2')].find(e => e.textContent.startsWith('Claims')).closest('.card')")
    at(t0[0], dur)


def act_actions(page, T, dur, t0):
    page.goto(GITHUB + "/actions/workflows/sandbox.yml", wait_until="load")
    page.wait_for_timeout(1200)
    t0[0] = time.monotonic()
    at(t0[0], T[0] + 2.2)
    page.goto(GITHUB + "/blob/main/.github/workflows/sandbox.yml", wait_until="domcontentloaded")
    page.wait_for_timeout(1500)
    at(t0[0], dur)


def act_verify(page, T, dur, t0):
    page.goto(VIEWER + "proof.html?run=bench-D_open-pr_test_1-buggy_b-s0", wait_until="networkidle")
    zoom(page, 1.5)
    page.wait_for_timeout(1200)
    t0[0] = time.monotonic()
    at(t0[0], T[0] + 0.8)
    scroll_to(page, "[...document.querySelectorAll('h2')].find(e => e.textContent === 'Certificate').closest('.card')")
    at(t0[0], dur)


def act_results(page, T, dur, t0):
    page.goto(VIEWER, wait_until="networkidle")
    zoom(page, 1.35)
    page.wait_for_timeout(1200)
    t0[0] = time.monotonic()
    at(t0[0], T[0])
    scroll_to(page, "document.querySelector('#results').closest('.card') || document.querySelector('#results')")
    at(t0[0], T[1] + 0.5)
    scroll_by(page, 450)
    at(t0[0], dur)


def act_classify(page, T, dur, t0):
    page.goto(GITHUB + "/blob/main/results/unconfirmed_classification.md", wait_until="load")
    page.wait_for_timeout(1500)
    t0[0] = time.monotonic()
    at(t0[0], T[0] + 1.0)
    scroll_to(page, "document.querySelector('article table')", margin=130)
    at(t0[0], dur)


def act_built(page, T, dur, t0):
    page.goto(GITHUB + "/blob/main/docs/built-with-muse-code.md", wait_until="load")
    page.wait_for_timeout(1500)
    t0[0] = time.monotonic()
    at(t0[0], T[0] + 1.0)
    scroll_to(page, "document.querySelector('article h2')", margin=130)
    at(t0[0], dur)


# ------------------------------------------------------------ pipeline
def wav_seconds(path: Path) -> float:
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def tts(all_shots, models: Path) -> None:
    import soundfile as sf
    from kokoro_onnx import Kokoro
    kokoro = None
    out = BUILD / "audio"
    out.mkdir(parents=True, exist_ok=True)
    for shot in all_shots:
        for say, _ in shot["lines"]:
            path = out / f"{hashlib.sha1(f'{VOICE}|{SPEED}|{say}'.encode()).hexdigest()[:12]}.wav"
            if path.exists():
                continue
            kokoro = kokoro or Kokoro(str(models / "kokoro-v1.0.onnx"), str(models / "voices-v1.0.bin"))
            samples, rate = kokoro.create(say, voice=VOICE, speed=SPEED, lang="en-us")
            sf.write(str(path), samples, rate, subtype="PCM_16")


def timeline(all_shots) -> list[dict]:
    """Shot start/length and every line's absolute start from the wav lengths."""
    t, plan = 0.0, []
    for shot in all_shots:
        offs, cur = [], shot.get("lead", LEAD)
        lines = []
        for say, cap in shot["lines"]:
            wav = BUILD / "audio" / f"{hashlib.sha1(f'{VOICE}|{SPEED}|{say}'.encode()).hexdigest()[:12]}.wav"
            d = wav_seconds(wav)
            offs.append(round(cur, 3))
            lines.append({"wav": wav.name, "start": round(t + cur, 3), "dur": round(d, 3), "cap": cap})
            cur += d + GAP
        dur = round(cur - GAP + shot.get("tail", TAIL), 3)
        plan.append({"id": shot["id"], "start": round(t, 3), "dur": dur, "T": offs, "lines": lines})
        t += dur
    return plan


def record(all_shots, plan, only: set[str] | None = None) -> None:
    from playwright.sync_api import sync_playwright
    raw = BUILD / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    rec_file = BUILD / "recordings.json"
    offsets = json.loads(rec_file.read_text(encoding="utf-8")) if rec_file.exists() else {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for shot, sp in zip(all_shots, plan):
            if only and shot["id"] not in only:
                continue
            vw, vh = shot.get("vp", (W, H))
            ctx = browser.new_context(viewport={"width": vw, "height": vh}, record_video_dir=str(raw / shot["id"]),
                                      record_video_size={"width": vw, "height": vh}, color_scheme="dark", locale="en-US")
            created = time.monotonic()
            pg = ctx.new_page()
            t0 = [0.0]
            if shot["kind"] == "card":
                card = BUILD / "cards" / f"{shot['id']}.html"
                card.parent.mkdir(parents=True, exist_ok=True)
                card.write_text(shot["html"](sp["T"]), encoding="utf-8")
                pg.goto(card.as_uri(), wait_until="load")
                pg.wait_for_timeout(500)
                t0[0] = time.monotonic()
                pg.evaluate("go()")
                at(t0[0], sp["dur"])
            else:
                shot["act"](pg, sp["T"], sp["dur"], t0)
            at(t0[0], sp["dur"] + 0.3)
            video = pg.video
            ctx.close()
            src = Path(video.path())
            offsets[shot["id"]] = {"file": str(src), "offset": round(t0[0] - created, 3)}
            print(f"recorded {shot['id']}: {sp['dur']:.1f}s (offset {offsets[shot['id']]['offset']}s)")
            rec_file.write_text(json.dumps(offsets, indent=1), encoding="utf-8")
        browser.close()


def ff(*args: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True, cwd=BUILD)


def ass_time(t: float) -> str:
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def assemble(plan) -> Path:
    import numpy as np
    import soundfile as sf
    recs = json.loads((BUILD / "recordings.json").read_text(encoding="utf-8"))
    parts = []
    for sp in plan:
        rec = recs[sp["id"]]
        out = f"shot_{sp['id']}.mp4"
        ff("-ss", str(rec["offset"]), "-i", rec["file"],
           "-vf", f"fps={FPS},scale={W}:{H}:flags=lanczos,tpad=stop_mode=clone:stop_duration=2",
           "-t", str(sp["dur"]), "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", out)
        parts.append(out)
    (BUILD / "parts.txt").write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
    ff("-f", "concat", "-safe", "0", "-i", "parts.txt", "-c", "copy", "video_only.mp4")

    total = sum(sp["dur"] for sp in plan)
    rate = 24000
    track = np.zeros(int(total * rate) + rate, dtype=np.float32)
    events = []
    for sp in plan:
        for line in sp["lines"]:
            samples, sr = sf.read(str(BUILD / "audio" / line["wav"]), dtype="float32")
            assert sr == rate
            i = int(line["start"] * rate)
            track[i:i + len(samples)] += samples
            events.append((line["start"], line["start"] + line["dur"] + 0.25, line["cap"]))
    sf.write(str(BUILD / "narration.wav"), track, rate, subtype="PCM_16")

    header = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 0\n\n[V4+ Styles]\n"
              "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
              "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
              "MarginR, MarginV, Encoding\n"
              "Style: Cap,Segoe UI Semibold,50,&H00FFFFFF,&H00FFFFFF,&HC8000000,&HC8000000,0,0,0,0,100,100,0,0,3,14,0,2,"
              "220,220,48,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    body = "".join(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Cap,,0,0,0,,{c}\n" for a, b, c in events)
    (BUILD / "captions.ass").write_text(header + body, encoding="utf-8")

    final = BUILD / "matrix-globe-demo.mp4"
    ff("-i", "video_only.mp4", "-i", "narration.wav", "-vf", "ass=captions.ass", "-c:v", "libx264", "-preset", "slow",
       "-crf", "18", "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest",
       "-movflags", "+faststart", final.name)
    (BUILD / "timeline.json").write_text(json.dumps(plan, indent=1), encoding="utf-8")
    print(f"{final} · {total:.1f}s")
    return final


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--only", choices=("tts", "record", "assemble"))
    parser.add_argument("--shots", help="comma-separated shot ids to (re)record")
    args = parser.parse_args()
    all_shots = shots()
    if args.only in (None, "tts"):
        tts(all_shots, args.models)
    plan = timeline(all_shots)
    total = sum(s["dur"] for s in plan)
    print(f"timeline: {total:.1f}s over {len(plan)} shots")
    if total > 180:
        raise SystemExit("over 3:00: shorten the narration")
    if args.only in (None, "record"):
        record(all_shots, plan, set(args.shots.split(",")) if args.shots else None)
    if args.only in (None, "assemble"):
        assemble(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
