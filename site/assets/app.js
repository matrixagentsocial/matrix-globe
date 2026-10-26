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
  B: "Muse Wonder, single shot, max effort",
  C: "Spark self-refine",
  D: "Matrix Globe: Spark builder + Wonder prover",
  E: "Ablation: free-text review, no proof rule",
};

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

function pct(value) {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "–";
}

async function renderResults(target) {
  let summary = null;
  try {
    summary = await loadJson("data/summary.json");
  } catch {
    summary = null;
  }
  if (!summary || summary.status !== "final" || !Array.isArray(summary.conditions)) {
    target.append(
      el("p", {
        class: "muted",
        text: "Final FinCode-30 results (20 held-out finance tasks, conditions A–E) appear here after the final run.",
      }),
    );
    return;
  }
  if (summary.headline) target.append(el("p", { text: summary.headline }));
  const max = Math.max(0.0001, ...summary.conditions.map((c) => c.allPassRate || 0));
  for (const condition of summary.conditions) {
    const row = el("div", { class: "bar-row" });
    row.append(
      el("div", { class: "bar-label", text: `${condition.id} · ${condition.label || MODES[condition.id] || ""}` }),
      el(
        "div",
        { class: "bar-track" },
        el("div", { class: "bar", style: `width:${Math.max(2, ((condition.allPassRate || 0) / max) * 100)}%` }),
      ),
      el("div", {
        class: "bar-value",
        text: `${pct(condition.allPassRate)} solved · $${(condition.usdPerRun ?? 0).toFixed(4)}/run`,
      }),
    );
    target.append(row);
  }
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
  for (const row of rows) {
    const link = el("a", { href: `proof.html?run=${encodeURIComponent(row.runId)}`, text: row.task || row.runId });
    tbody.append(
      el(
        "tr",
        {},
        el("td", {}, link),
        el("td", { text: row.mode ? `${row.mode}` : "–", title: MODES[row.mode] || "" }),
        el("td", {}, badge(row.status)),
        el("td", { text: `${row.claims.proven}/${row.claims.proposed}` }),
        el("td", { text: `${row.claims.valid}` }),
        el("td", { text: row.usd ? `$${row.usd}` : "–" }),
        el("td", { class: "mono small", text: (row.sha256 || "").slice(0, 12) + "…" }),
      ),
    );
  }
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
    el("p", { class: "muted", text: `Mode ${bundle.mode}: ${MODES[bundle.mode] || ""}` }),
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
