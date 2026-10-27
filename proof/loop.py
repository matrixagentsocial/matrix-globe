"""Proof loop (PLAN.md 5.4 + Decisions of 2026-10-26 conditions A-E).

A: Spark builder single shot, effort medium.
B: Wonder single shot, effort max (model = reviewer model).
C: Spark self-refine (builder writes its own tests, then revises).
D: Spark builder + Wonder reviewer under the proof rule + Spark reviser.
E: like D, but Wonder gives free-text review with no proof rule.

Guards: MAX_ROUNDS=2, MAX_USD_PER_RUN (settings), MAX_LLM_CALLS_PER_RUN=8,
sandbox timeout, wall clock 6 min. A revision that breaks previously
passing tests rolls back to the best version (``regression`` event). A
failed LLM/tool step is recorded as an event and the loop continues with
the best version so far. Every event goes into the bundle.
"""
from __future__ import annotations

import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from proof.bundle import (
    BundleClaim, BundleCost, BundleEvent, BundleRound, BundleTests,
    ModelRef, ModelsRef, ProofBundle, TaskRef, TestCounts, format_usd, sha256_text,
)
from proof.package import format_package, parse_package
from proof.proofrule import prove_claims, prove_claims_modules
from proof.pytest_runner import run_pytest, run_pytest_files

MAX_ROUNDS = 2
MAX_LLM_CALLS_PER_RUN = 8
MAX_WALL_CLOCK_S = 360.0
SANDBOX_TIMEOUT_S = 10.0

_MODE_ALIASES = {
    "R": "R", "no_review": "R",
    "A": "A", "single": "A",
    "B": "B", "single_xhigh": "B", "single_max": "B",
    "C": "C", "self_refine": "C",
    "D": "D", "matrix_proof": "D",
    "E": "E", "review_freeform": "E",
}


def normalise_mode(mode: str) -> str:
    key = str(mode).strip()
    if key in _MODE_ALIASES:
        return _MODE_ALIASES[key]
    if key.upper() in _MODE_ALIASES:
        return _MODE_ALIASES[key.upper()]
    raise ValueError(f"unknown mode {mode!r}; expected R|A|B|C|D|E")


def _field(task: Any, name: str, default: Any = "") -> Any:
    if isinstance(task, dict):
        return task.get(name, default)
    return getattr(task, name, default)


def format_public_results(result: Any) -> str:
    lines = [f"public tests: {result.passed}/{result.total} passed"]
    if result.timed_out:
        lines.append("run timed out")
    for err in result.collection_errors:
        lines.append(f"collection error: {err}")
    for t in result.tests:
        if t.outcome != "passed":
            lines.append(f"{t.name}: {t.outcome} {t.message}".strip()[:500])
    return "\n".join(lines)


class _CountingClient:
    """Wraps a client; counts LLM calls for the call-cap guard."""

    def __init__(self, inner: Any, counter: dict[str, int]) -> None:
        self._inner = inner
        self._counter = counter

    def complete(self, role: str, messages: Any, **kwargs: Any) -> Any:
        self._counter["calls"] += 1
        return self._inner.complete(role, messages, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class ProofLoop:
    def __init__(self, task: Any, mode: str, *, client: Any, sandbox: Any,
                 ledger: Any = None, settings: Any = None, run_id: str | None = None,
                 sandbox_label: str = "local", max_rounds: int = MAX_ROUNDS,
                 max_llm_calls: int = MAX_LLM_CALLS_PER_RUN,
                 max_usd_per_run: float | None = None,
                 max_wall_s: float = MAX_WALL_CLOCK_S,
                 sandbox_timeout_s: float = SANDBOX_TIMEOUT_S,
                 clock: Callable[[], float] = time.monotonic,
                 initial_code: str | None = None,
                 target_id: str = "",
                 initial_modules: dict[str, str] | None = None,
                 reference_modules: dict[str, str] | None = None) -> None:
        self.task = task
        self.mode = normalise_mode(mode)
        self.client_raw = client
        self.counter: dict[str, int] = {"calls": 0}
        self.client = _CountingClient(client, self.counter) if client is not None else None
        self.sandbox = sandbox
        self.ledger = ledger
        self.settings = settings
        if self.settings is None:
            # Prefer the client's settings; fall back to env settings.
            self.settings = getattr(client, "settings", None)
        if self.settings is None:
            from proof.config import load_settings
            self.settings = load_settings()
        self.run_id = run_id or uuid.uuid4().hex
        self.sandbox_label = sandbox_label
        self.max_rounds = int(max_rounds)
        self.max_llm_calls = int(max_llm_calls)
        if max_usd_per_run is not None:
            self.max_usd_per_run = float(max_usd_per_run)
        else:
            self.max_usd_per_run = float(getattr(self.settings, "max_usd_per_run", 0.60))
        self.max_wall_s = float(max_wall_s)
        self.sandbox_timeout_s = float(sandbox_timeout_s)
        self.clock = clock
        self.started = clock()
        self.initial_code = initial_code
        self.initial_modules = dict(initial_modules) if initial_modules is not None else None
        self.reference_modules = dict(reference_modules) if reference_modules is not None else None
        self.is_pr = self.initial_modules is not None or self.reference_modules is not None
        self.module_names: list[str] = sorted(
            (self.initial_modules or self.reference_modules or {}).keys())
        self.target_id = str(target_id or "")
        self.events: list[BundleEvent] = []
        self.rounds: list[BundleRound] = []
        self.all_proven: list[Any] = []  # ClaimProof objects
        self.contested_ids: set[str] = set()
        self.best_code: str = ""
        self.best_public = TestCounts()
        self.best_proven = TestCounts()
        self.best_score = -1
        self.regressions = 0
        self._ledger_before = 0.0
        if ledger is not None and hasattr(ledger, "total_usd"):
            try:
                self._ledger_before = float(ledger.total_usd())
            except Exception:
                self._ledger_before = 0.0

    # -- helpers ------------------------------------------------------
    def event(self, type_: str, detail: str = "", round_: int | None = None) -> None:
        self.events.append(BundleEvent(type=type_, round=round_, detail=str(detail)[:2000]))

    def elapsed(self) -> float:
        return self.clock() - self.started

    def run_usd(self) -> float:
        if self.ledger is None:
            return 0.0
        try:
            if hasattr(self.ledger, "run_usd"):
                v = self.ledger.run_usd(self.run_id)
                if v:
                    return float(v)
            if hasattr(self.ledger, "total_usd"):
                return max(0.0, float(self.ledger.total_usd()) - self._ledger_before)
        except Exception:
            return 0.0
        return 0.0

    def guard_allows(self, step: str) -> bool:
        if self.counter["calls"] >= self.max_llm_calls:
            self.event("guard_call_cap", f"MAX_LLM_CALLS_PER_RUN={self.max_llm_calls} reached before {step}")
            return False
        if self.elapsed() > self.max_wall_s:
            self.event("guard_wall_clock", f"wall clock {self.max_wall_s}s exceeded before {step}")
            return False
        usd = self.run_usd()
        if usd >= self.max_usd_per_run:
            self.event("guard_usd_cap", f"MAX_USD_PER_RUN=${self.max_usd_per_run} reached (${usd:.4f}) before {step}")
            return False
        return True

    def code_files(self, code: str) -> dict[str, str]:
        if self.is_pr:
            return parse_package(code, self.module_names)
        return {"solution.py": code}

    def run_tests(self, code: str, test_files: dict[str, str]):
        if self.is_pr:
            return run_pytest_files(self.sandbox, self.code_files(code), test_files,
                                    timeout_s=self.sandbox_timeout_s)
        return run_pytest(self.sandbox, code, test_files, timeout_s=self.sandbox_timeout_s)

    def run_public(self, code: str):
        return self.run_tests(code, {"public_test.py": str(_field(self.task, "public_test"))})

    def evaluate(self, code: str) -> tuple[TestCounts, TestCounts, int, Any]:
        """Return (public, proven(non-contested), score, public_result)."""
        pub = self.run_public(code)
        public = TestCounts(passed=pub.passed, total=pub.total)
        proven_passed = 0
        proven_total = 0
        for proof in self.all_proven:
            if proof.id.lower() in self.contested_ids:
                continue
            proven_total += 1
            fname = f"test_proven_{proof.id}.py".replace("-", "_")
            r = self.run_tests(code, {fname: proof.failing_test})
            if r.all_passed:
                proven_passed += 1
        proven = TestCounts(passed=proven_passed, total=proven_total)
        return public, proven, public.passed + proven.passed, pub

    def accept_if_best(self, code: str, public: TestCounts, proven: TestCounts, score: int) -> None:
        if score > self.best_score:
            self.best_code, self.best_public, self.best_proven, self.best_score = code, public, proven, score

    # -- main ---------------------------------------------------------
    def run(self) -> ProofBundle:
        from proof.roles.builder import build_solution

        task_id = str(_field(self.task, "id", "task"))
        spec = str(_field(self.task, "spec", ""))
        reference = _field(self.task, "reference", None)
        if reference is not None and not str(reference).strip():
            reference = None

        self.event("run_started", f"mode={self.mode} task={task_id}")

        # ---- build (or use supplied initial code) ----
        current = ""
        if self.initial_modules is not None:
            current = format_package(self.initial_modules)
            self.event("builder_skipped", "initial package supplied")
        elif self.initial_code is not None:
            current = self.initial_code
            self.event("builder_skipped", "initial code supplied")
        else:
            if self.client is None:
                self.event("step_failed", "no LLM client supplied for builder")
            elif self.guard_allows("builder"):
                try:
                    if self.mode == "B" and self.is_pr:
                        from proof.roles.builder import build_modules
                        current = format_package(build_modules(
                            self.client, spec, self.module_names, run_id=self.run_id,
                            model=getattr(self.settings, "model_reviewer", "muse-wonder-1.0"),
                            effort="max"))
                    elif self.mode == "B":
                        current = build_solution(
                            self.client, spec, run_id=self.run_id,
                            model=getattr(self.settings, "model_reviewer", "muse-wonder-1.0"),
                            effort="max")
                    else:
                        current = build_solution(self.client, spec, run_id=self.run_id)
                    self.event("builder_completed", f"code sha {sha256_text(current)[:12]}")
                except Exception as exc:  # recovery: record, continue with best (empty)
                    self.event("step_failed", f"builder failed: {exc}")
            # guard tripped: guard event already recorded

        if current:
            try:
                public, proven, score, _ = self.evaluate(current)
                self.best_code, self.best_public, self.best_proven, self.best_score = current, public, proven, score
            except Exception as exc:
                self.event("step_failed", f"initial evaluation failed: {exc}")
                self.best_code = current

        # ---- mode-specific refinement ----
        if self.mode in ("D",):
            self._run_proof_rounds(spec, reference)
        elif self.mode == "E":
            self._run_freeform_rounds(spec)
        elif self.mode == "C":
            self._run_self_refine_rounds(spec)

        return self._finalise(task_id, spec)

    # -- D ----
    def _run_proof_rounds(self, spec: str, reference: Any) -> None:
        from proof.roles.reviewer import review_code
        from proof.roles.reviser import revise_code

        history = ""
        current = self.best_code
        for n in range(1, self.max_rounds + 1):
            if not current:
                break
            if not self.guard_allows("reviewer"):
                break
            try:
                pub = self.run_public(current)
                report = review_code(self.client, spec, current, format_public_results(pub),
                                     run_id=self.run_id, history=history,
                                     effort=getattr(self.settings, "effort_reviewer", None),
                                     module_names=self.module_names if self.is_pr else None)
            except Exception as exc:
                self.event("step_failed", f"reviewer round {n} failed: {exc}", round_=n)
                break
            self.event("review_completed", f"round {n} verdict={report.verdict} claims={len(report.claims)}", round_=n)
            # prove each claim in its own file
            try:
                if self.is_pr:
                    proofs = prove_claims_modules(
                        list(report.claims), self.code_files(current), self.sandbox,
                        reference_modules=self.reference_modules,
                        timeout_s=self.sandbox_timeout_s)
                else:
                    proofs = prove_claims(list(report.claims), current, self.sandbox,
                                          reference_code=str(reference) if reference else None,
                                          timeout_s=self.sandbox_timeout_s)
            except Exception as exc:
                self.event("step_failed", f"proof rule round {n} failed: {exc}", round_=n)
                break
            bundle_claims: list[BundleClaim] = []
            for p in proofs:
                self.event("claim", f"{p.id}: {p.status}" + (f"/{p.validity}" if p.validity else ""), round_=n)
                bundle_claims.append(BundleClaim(
                    id=p.id, title=str(getattr(p.claim, "title", "") or ""),
                    severity=str(getattr(p.claim, "severity", "") or ""),
                    status=p.status, validity=p.validity, testSha256=p.test_sha256))
            proven = [p for p in proofs if p.status == "PROVEN"]
            history = (f"Round {n}: {len(proofs)} claims, {len(proven)} proven "
                       f"({', '.join(p.id for p in proven) or 'none'}). Code is now v{n}.")
            round_rec = BundleRound(n=n, codeSha256=sha256_text(current), claims=bundle_claims)
            self.rounds.append(round_rec)
            if not proven:
                break
            self.all_proven.extend(proven)
            if not self.guard_allows("reviser"):
                break
            try:
                claims_in = [p.to_claim_dict() for p in proven]
                if self.is_pr:
                    from proof.roles.reviser import revise_code_modules
                    mod_rev = revise_code_modules(self.client, spec, self.code_files(current),
                                                  claims_in, run_id=self.run_id)
                    revision = mod_rev
                    candidate_code = format_package(mod_rev.modules)
                else:
                    revision = revise_code(self.client, spec, current, claims_in, run_id=self.run_id)
                    candidate_code = revision.code
            except Exception as exc:
                self.event("step_failed", f"reviser round {n} failed: {exc}", round_=n)
                break
            self.event("revision_completed", f"round {n} addressed={len(revision.addressed)} contested={len(revision.contested)}", round_=n)
            round_rec.revisionSha256 = sha256_text(candidate_code)
            round_rec.addressed = [a.model_dump() for a in revision.addressed]
            round_rec.contested = [c.model_dump() for c in revision.contested]
            for c in revision.contested:
                self.contested_ids.add(str(c.claim_id).lower())
            # verify candidate; rollback on regression
            try:
                public, proven_c, score, _ = self.evaluate(candidate_code)
            except Exception as exc:
                self.event("step_failed", f"revision evaluation round {n} failed: {exc}", round_=n)
                break
            if score < self.best_score:
                self.regressions += 1
                self.event("regression", f"round {n} revision scored {score} < best {self.best_score}; rolled back", round_=n)
                break
            current = candidate_code
            self.best_code, self.best_public, self.best_proven, self.best_score = current, public, proven_c, score

    # -- E ----
    def _run_freeform_rounds(self, spec: str) -> None:
        from proof.roles.reviewer import review_freeform
        from proof.roles.reviser import revise_from_freeform

        history = ""
        current = self.best_code
        for n in range(1, self.max_rounds + 1):
            if not current:
                break
            if not self.guard_allows("freeform_reviewer"):
                break
            try:
                pub = self.run_public(current)
                feedback = review_freeform(self.client, spec, current, format_public_results(pub),
                                           run_id=self.run_id, history=history,
                                           effort=getattr(self.settings, "effort_reviewer", None),
                                           module_names=self.module_names if self.is_pr else None)
            except Exception as exc:
                self.event("step_failed", f"freeform reviewer round {n} failed: {exc}", round_=n)
                break
            self.event("review_completed", f"round {n} freeform feedback {len(feedback)} chars", round_=n)
            round_rec = BundleRound(n=n, codeSha256=sha256_text(current), claims=[])
            self.rounds.append(round_rec)
            history = f"Round {n} freeform feedback given."
            if feedback.strip().upper().startswith("NO_DEFECTS"):
                break
            if not self.guard_allows("reviser"):
                break
            try:
                if self.is_pr:
                    from proof.roles.reviser import revise_from_freeform_modules
                    mod_rev = revise_from_freeform_modules(self.client, spec, self.code_files(current),
                                                           feedback, run_id=self.run_id)
                    revision = mod_rev
                    candidate_code = format_package(mod_rev.modules)
                else:
                    revision = revise_from_freeform(self.client, spec, current, feedback, run_id=self.run_id)
                    candidate_code = revision.code
            except Exception as exc:
                self.event("step_failed", f"reviser (freeform) round {n} failed: {exc}", round_=n)
                break
            self.event("revision_completed", f"round {n} freeform revision", round_=n)
            round_rec.revisionSha256 = sha256_text(candidate_code)
            round_rec.addressed = [{"claim_id": a.claim_id, "change": a.change} for a in revision.addressed]
            round_rec.contested = [{"claim_id": c.claim_id, "reason": c.reason} for c in revision.contested]
            try:
                public, proven_c, score, _ = self.evaluate(candidate_code)
            except Exception as exc:
                self.event("step_failed", f"revision evaluation round {n} failed: {exc}", round_=n)
                break
            if score < self.best_score:
                self.regressions += 1
                self.event("regression", f"round {n} revision scored {score} < best {self.best_score}; rolled back", round_=n)
                break
            current = candidate_code
            self.best_code, self.best_public, self.best_proven, self.best_score = current, public, proven_c, score

    # -- C ----
    def _run_self_refine_rounds(self, spec: str) -> None:
        from proof.roles import self_refine as sr

        current = self.best_code
        for n in range(1, self.max_rounds + 1):
            if not current:
                break
            if not self.guard_allows("self_refine_tests"):
                break
            try:
                if self.is_pr:
                    tests = sr.generate_self_tests_modules(self.client, spec, self.code_files(current),
                                                           run_id=self.run_id)
                else:
                    tests = sr.generate_self_tests(self.client, spec, current, run_id=self.run_id)
            except Exception as exc:
                self.event("step_failed", f"self-refine tests round {n} failed: {exc}", round_=n)
                break
            self.event("self_tests_generated", f"round {n} self tests {len(tests)} chars", round_=n)
            round_rec = BundleRound(n=n, codeSha256=sha256_text(current), claims=[])
            self.rounds.append(round_rec)
            try:
                self_run = self.run_tests(current, {"self_test.py": tests})
            except Exception as exc:
                self.event("step_failed", f"self tests run round {n} failed: {exc}", round_=n)
                break
            if self_run.all_passed:
                self.event("self_tests_passed", f"round {n}", round_=n)
                break
            if not self.guard_allows("self_refine_revise"):
                break
            try:
                if self.is_pr:
                    candidate = format_package(sr.refine_code_modules(
                        self.client, spec, self.code_files(current), tests,
                        format_public_results(self_run), run_id=self.run_id))
                else:
                    candidate = sr.refine_code(self.client, spec, current, tests,
                                               format_public_results(self_run), run_id=self.run_id)
            except Exception as exc:
                self.event("step_failed", f"self-refine revise round {n} failed: {exc}", round_=n)
                break
            self.event("revision_completed", f"round {n} self-refine revision", round_=n)
            round_rec.revisionSha256 = sha256_text(candidate)
            # score = public + self tests on candidate
            try:
                pub = self.run_public(candidate)
                cand_self = self.run_tests(candidate, {"self_test.py": tests})
                cand_score = pub.passed + cand_self.passed
                cur_self_passed = self_run.passed
                cur_pub = self.run_public(current)
                cur_score = cur_pub.passed + cur_self_passed
            except Exception as exc:
                self.event("step_failed", f"self-refine evaluation round {n} failed: {exc}", round_=n)
                break
            if cand_score < cur_score:
                self.regressions += 1
                self.event("regression", f"round {n} self-refine scored {cand_score} < {cur_score}; rolled back", round_=n)
                break
            current = candidate
            # update best by public evaluate
            public, proven_c, score, _ = self.evaluate(current)
            self.best_code, self.best_public, self.best_proven, self.best_score = current, public, proven_c, score

    # -- finalise ----
    def _finalise(self, task_id: str, spec: str) -> ProofBundle:
        final_code = self.best_code or ""
        # Recompute final counts on the best code for an honest status.
        if final_code:
            try:
                public, proven, score, _ = self.evaluate(final_code)
                self.best_public, self.best_proven, self.best_score = public, proven, score
            except Exception as exc:
                self.event("step_failed", f"final evaluation failed: {exc}")
        public, proven = self.best_public, self.best_proven
        if self.mode == "R":
            status = "UNREVIEWED"
        elif public.total == 0 or public.passed < public.total:
            status = "FAILED"
        elif proven.total > 0 and proven.passed < proven.total:
            status = "PARTIAL"
        else:
            status = "VERIFIED"
        self.event("run_finished", f"status={status} public={public.passed}/{public.total} proven={proven.passed}/{proven.total}")

        # cost from ledger
        in_tok = out_tok = 0
        usd = reviewer_usd = 0.0
        if self.ledger is not None and hasattr(self.ledger, "entries"):
            try:
                for row in self.ledger.entries():
                    if row.get("run_id") != self.run_id:
                        continue
                    in_tok += int(row.get("input_tokens", 0) or 0)
                    out_tok += int(row.get("output_tokens", 0) or 0)
                    usd += float(row.get("usd", 0.0) or 0.0)
                    if row.get("role") in ("reviewer", "freeform_reviewer"):
                        reviewer_usd += float(row.get("usd", 0.0) or 0.0)
            except Exception:
                pass
        if usd == 0.0:
            usd = self.run_usd()

        builder_model = getattr(self.settings, "model_builder", "muse-spark-1.3-contributor")
        builder_effort = getattr(self.settings, "effort_builder", "medium")
        reviewer_model = getattr(self.settings, "model_reviewer", "muse-wonder-1.0")
        reviewer_effort = getattr(self.settings, "effort_reviewer", "high")
        if self.mode == "B":
            builder_model, builder_effort = reviewer_model, "max"
        bundle = ProofBundle(
            runId=self.run_id,
            createdAt=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            task=TaskRef(id=task_id, specSha256=sha256_text(spec)),
            models=ModelsRef(
                builder=ModelRef(model=str(builder_model), effort=str(builder_effort)),
                reviewer=ModelRef(model=str(reviewer_model), effort=str(reviewer_effort)),
            ),
            mode=self.mode,
            target=self.target_id,
            rounds=self.rounds,
            events=self.events,
            finalCodeSha256=sha256_text(final_code) if final_code else "",
            finalCode=final_code,
            tests=BundleTests(public=public, proven=proven),
            status=status,
            cost=BundleCost(inputTokens=in_tok, outputTokens=out_tok, usd=format_usd(usd),
                            reviewerUsd=format_usd(reviewer_usd)),
            sandbox=self.sandbox_label,
            llmCalls=self.counter["calls"],
        )
        return bundle


def run_proof(task: Any, mode: str = "D", **kwargs: Any) -> ProofBundle:
    """Run the proof loop for *task* in *mode* (A|B|C|D|E); see module docstring."""
    return ProofLoop(task, mode, **kwargs).run()
