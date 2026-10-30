// Matrix Globe static proof viewer. No framework, no build step.
// canonicalJson mirrors Python json.dumps(sort_keys=True, separators=(",", ":"),
// ensure_ascii=False), the rule the desk uses to hash certificates.

export function canonicalJson(value) {
  const sort = (v) => {
    if (Array.isArray(v)) return v.map(sort);
    if (v && typeof v === "object") {
      const out = {};
      for (const key of Object.keys(v).sort()) out[key] = sort(v[key]);
      return out;
    }
    return v;
  };
  return JSON.stringify(sort(value));
}

export async function sha256Hex(text) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, "0")).join("");
}

const MODES = {
  A: "Spark builder, single shot",
  B: "Muse Wonder regenerates from the spec, max effort",
  C: "Self-check: Spark writes its own tests and revises",
  D: "Matrix Globe: proof-gated review",
  E: "Ablation: free-text review, no proof rule",
  R: "No review (ship as is)",
  C_open: "Self-check, Muse Spark Open",
  D_open: "Matrix Globe, Muse Spark Open for every role",
  E_open: "Free-text review, Muse Spark Open",
};

const STACK_SHORT = { meta: "Hosted Meta", open: "Open weights", dev: "Dev demo" };
const SCOPE_LABEL = { pr: "PR packages (3 modules, one hidden bug each, plus a clean control)", single: "Single tasks (3 mutants + 1 clean per task)" };
const MAX_ROWS = 200;

const el = (tag, attrs = {}, ...children) => {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else node.setAttribute(key, value);
  }
  for (const child of children) node.append(child);
  return node;
};

const badge = (status) => el("span", { class: `badge ${String(status || "").toLowerCase()}`, text: status || "?" });

async function loadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  return response.json();
}

const frac = (a, b) => (b ? `${a}/${b} (${Math.round((a / b) * 100)}%)` : "–");
const usd = (v) => (typeof v === "number" ? `$${v.toFixed(4)}` : "–");

async function renderResults(target) {
  let summary = null;
  try {
    summary = await loadJson("data/summary.json");
  } catch {
    summary = null;
  }
  if (!summary || summary.status !== "final" || !Array.isArray(summary.tables)) {
    target.append(el("p", { class: "muted", text: "Final FinCode-30 results appear here after the final run." }));
    return;
  }
  if (summary.headline) target.append(el("p", { class: "headline", text: summary.headline }));
  for (const table of summary.tables) {
    const head = ["Condition", "Targets", "Bugs fixed", "Correct code damaged", "Regressions", "Precision", "$ / target"];
    const t = el("table", { class: "table results" });
    t.append(el("thead", {}, el("tr", {}, ...head.map((h) => el("th", { text: h })))));
    const body = el("tbody");
    for (const c of table.conditions) {
      const fixed = c.regen ? `regenerated ${c.regenPassed}/${c.regen} pass` : frac(c.fixed, c.buggy);
      const max = Math.max(...table.conditions.map((x) => (x.buggy ? x.fixed / x.buggy : 0)));
      const best = c.buggy && c.fixed / c.buggy === max && max > 0;
      body.append(
        el(
          "tr",
          { class: c.id === "D" ? "ours" : "" },
          el("td", { text: `${c.id} · ${c.label}` }),
          el("td", { text: `${c.targets}${c.seeds > 1 ? ` (${c.seeds} seeds)` : ""}${c.id === "D" && table.stack === "meta" && table.scope === "single" ? ", 10-task subset" : ""}` }),
          el("td", { class: best ? "ok" : "", text: fixed }),
          el("td", { text: c.clean ? `${c.damaged}/${c.clean}` : "–" }),
          el("td", { text: String(c.regressions) }),
          el("td", { text: c.precision == null ? "–" : `${c.precision} (${c.claims.valid}/${c.claims.proven})` }),
          el("td", { text: usd(c.usdPerTarget) }),
        ),
      );
    }
    t.append(body);
    target.append(el("h3", { text: `${table.stackLabel} · ${SCOPE_LABEL[table.scope] || table.scope}` }), t);
  }
  target.append(
    el("p", {
      class: "muted small",
      text: "Held-out test split, prompts frozen before the run. Bugs fixed: hidden tests all pass after review. Precision: proven claims whose test the reference solution passes (VALID) over all proven claims; the rest are UNCONFIRMED (spec ambiguity, a defect the reference shares, or a reviewer error; see the repo). Computed from the committed JSONL rows.",
    }),
  );
}

function proofFilters(rows, onChange) {
  const options = (key, labels) => ["all", ...[...new Set(rows.map((r) => r[key]).filter(Boolean))].sort()].map((v) => [v, v === "all" ? "all" : labels?.[v] || v]);
  const make = (key, label, values, initial) => {
    const select = el("select", { "aria-label": label, "data-key": key });
    for (const [value, text] of values) {
      const option = el("option", { value, text });
      if (value === initial) option.selected = true;
      select.append(option);
    }
    select.addEventListener("change", onChange);
    return el("label", { class: "small muted" }, `${label} `, select);
  };
  return el(
    "div",
    { class: "filters" },
    make("stack", "Models", options("stack", STACK_SHORT), "all"),
    make("scope", "Scope", options("scope", { pr: "PR", single: "single task" }), "all"),
    make("mode", "Condition", options("mode"), rows.some((r) => r.mode === "D") ? "D" : "all"),
    make("status", "Status", options("status"), "all"),
  );
}

async function renderIndex() {
  await renderResults(document.getElementById("results"));
  const table = document.getElementById("proofs");
  let index;
  try {
    index = await loadJson("data/index.json");
  } catch (error) {
    table.replaceWith(el("p", { class: "error", text: `Could not load the proof index (${error.message}).` }));
    return;
  }
  const rows = index.bundles || [];
  if (rows.length === 0) {
    table.replaceWith(el("p", { class: "muted", text: "No proofs published yet." }));
    return;
  }
  const tbody = table.querySelector("tbody");
  const count = el("p", { class: "muted small" });
  const draw = () => {
    const wanted = Object.fromEntries([...filters.querySelectorAll("select")].map((s) => [s.dataset.key, s.value]));
    const shown = rows.filter((r) => Object.entries(wanted).every(([key, value]) => value === "all" || r[key] === value));
    tbody.replaceChildren();
    for (const row of shown.slice(0, MAX_ROWS)) {
      const link = el("a", { href: `proof.html?run=${encodeURIComponent(row.runId)}`, text: `${row.task || row.runId}${row.target ? ` · ${row.target}` : ""}` });
      tbody.append(
        el(
          "tr",
          {},
          el("td", {}, link),
          el("td", { text: STACK_SHORT[row.stack] || "–" }),
          el("td", { text: row.mode || "–", title: MODES[row.mode] || "" }),
          el("td", {}, badge(row.status)),
          el("td", { text: `${row.claims.proven}/${row.claims.proposed}` }),
          el("td", { text: `${row.claims.valid}` }),
          el("td", { text: row.usd ? `$${row.usd}` : "–" }),
          el("td", { class: "mono small", text: (row.sha256 || "").slice(0, 12) + "…" }),
        ),
      );
    }
    count.textContent = `${shown.length} of ${rows.length} proof bundles${shown.length > MAX_ROWS ? `, first ${MAX_ROWS} shown` : ""}. Open any row to recompute its SHA-256 in your browser.`;
  };
  const filters = proofFilters(rows, draw);
  table.before(filters, count);
  draw();
}

async function renderProof() {
  const root = document.getElementById("proof");
  const runId = new URLSearchParams(location.search).get("run");
  let index;
  try {
    index = await loadJson("data/index.json");
  } catch (error) {
    root.append(el("p", { class: "error", text: `Could not load the proof index (${error.message}).` }));
    return;
  }
  const row = (index.bundles || []).find((r) => r.runId === runId);
  if (!row) {
    root.append(el("p", { class: "error", text: `Unknown run ${runId}.` }));
    return;
  }
  const bundleText = await (await fetch(`data/${row.file}`, { cache: "no-store" })).text();
  const bundle = JSON.parse(bundleText);
  document.title = `${row.task} · ${bundle.status} · Matrix Globe`;

  root.append(
    el("p", { class: "eyebrow", text: `${bundle.schema} · run ${bundle.runId}` }),
    el("h1", { text: `${bundle.task?.id ?? "task"} ` }, badge(bundle.status)),
    el("p", { class: "muted", text: `Mode ${bundle.mode}: ${MODES[bundle.mode] || ""}${bundle.target ? ` · target ${bundle.target}` : ""}` }),
  );

  const facts = el("dl", { class: "facts" });
  const fact = (label, value) => facts.append(el("dt", { text: label }), el("dd", { text: value }));
  const models = bundle.models || {};
  fact("Builder", models.builder ? `${models.builder.model} · effort ${models.builder.effort}` : "–");
  fact("Reviewer", models.reviewer ? `${models.reviewer.model} · effort ${models.reviewer.effort}` : "–");
  fact("Public tests", bundle.tests?.public ? `${bundle.tests.public.passed}/${bundle.tests.public.total}` : "–");
  fact("Proven-defect tests", bundle.tests?.proven ? `${bundle.tests.proven.passed}/${bundle.tests.proven.total}` : "–");
  fact("LLM calls", String(bundle.llmCalls ?? "–"));
  fact("Cost", bundle.cost?.usd ? `$${bundle.cost.usd} (reviewer $${bundle.cost.reviewerUsd ?? "–"})` : "–");
  fact("Sandbox", String(bundle.sandbox ?? "–"));
  root.append(el("section", { class: "card" }, el("h2", { text: "Run" }), facts));

  const claimsCard = el("section", { class: "card" }, el("h2", { text: "Claims: no proof, no bug" }));
  const claims = (bundle.rounds || []).flatMap((round) => (round.claims || []).map((claim) => ({ ...claim, round: round.n })));
  if (claims.length === 0) {
    claimsCard.append(el("p", { class: "muted", text: "The reviewer made no claim, or this mode has no reviewer." }));
  } else {
    const list = el("table", { class: "table" });
    list.append(el("thead", {}, el("tr", {}, ...["#", "Round", "Claim", "Severity", "Proof", "Reference"].map((h) => el("th", { text: h })))));
    const body = el("tbody");
    for (const claim of claims) {
      body.append(
        el(
          "tr",
          { class: `claim ${String(claim.status).toLowerCase()}` },
          el("td", { text: claim.id }),
          el("td", { text: String(claim.round) }),
          el("td", { text: claim.title }),
          el("td", { text: claim.severity }),
          el("td", {}, badge(claim.status)),
          el("td", { text: claim.validity || "–" }),
        ),
      );
    }
    list.append(body);
    claimsCard.append(
      list,
      el("p", {
        class: "muted small",
        text: "PROVEN: the reviewer's test fails on the code. UNPROVEN: it passes, so the claim is discarded. INVALID: the test does not run. Reference (benchmark only): VALID when the reference solution passes the test, UNCONFIRMED when it fails it too.",
      }),
    );
  }
  root.append(claimsCard);

  if (Array.isArray(bundle.events) && bundle.events.length) {
    const events = el("ol", { class: "events" });
    for (const event of bundle.events) {
      events.append(el("li", {}, el("span", { class: "mono", text: event.type }), el("span", { class: "muted", text: ` ${event.detail || ""}` })));
    }
    root.append(el("section", { class: "card" }, el("h2", { text: "Timeline" }), events));
  }

  if (bundle.finalCode) {
    root.append(el("section", { class: "card" }, el("h2", { text: "Final code" }), el("pre", { class: "code", text: bundle.finalCode })));
  }

  const status = el("p", { class: "mono small", text: "Computing…" });
  const certificate = el(
    "section",
    { class: "card" },
    el("h2", { text: "Certificate" }),
    el("p", { class: "mono small hash", text: `recorded sha256: ${row.sha256}` }),
    status,
    el("p", {
      class: "muted small",
      text: "SHA-256 of the bundle's canonical JSON (sorted keys, no whitespace, UTF-8), recomputed by this page with crypto.subtle.",
    }),
  );
  root.append(certificate);
  const computed = await sha256Hex(canonicalJson(bundle));
  const matches = computed === row.sha256;
  status.textContent = `${matches ? "✓ verified in your browser" : "✗ mismatch"}: ${computed}`;
  status.className = `mono small ${matches ? "ok" : "error"}`;
}

const page = document.body.dataset.page;
if (page === "index") renderIndex();
if (page === "proof") renderProof();
