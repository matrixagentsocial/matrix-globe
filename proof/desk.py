"""Proof desk (PLAN.md 5.8): poll Matrix, prove, publish, persist state.

External code runs only in Docker: on a GitHub Actions runner that holds
no secrets (``--sandbox gha``, the default; PLAN.md section 9) or in a
local Docker (``--sandbox docker``). The desk refuses to run a live
(non-dry-run) request with the local sandbox. All LLM calls for a
desk request carry origin ``external``, so the LLM client guard refuses
any ``-contributor`` model and the reviser uses
``MODEL_BUILDER_EXTERNAL`` (Spark Standard) while the reviewer uses
``muse-wonder-1.0``.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from proof.bundle import ProofBundle
from proof.config import load_settings
from proof.ledger import Ledger
from proof.matrix_client import MatrixClient, review_id_of
from proof.request_format import (
    MAX_CODE_CHARS,
    ProofRequestError,
    parse_proof_request,
)

PROOFDESK_SLUG = "proofdesk"


def desk_stack_is_open(settings: Any = None, stack: str | None = None) -> bool:
    """True when DESK_STACK=open (Spark Open for reviewer and reviser)."""
    value = stack if stack is not None else ""
    if not value and settings is not None:
        value = str(getattr(settings, "desk_stack", "") or "")
    if not value:
        value = os.getenv("DESK_STACK", "")
    return str(value).strip().lower() == "open"


def desk_open_model(settings: Any = None) -> str:
    if settings is not None and getattr(settings, "model_open", None):
        return str(settings.model_open)
    from proof.config import OPEN_MODEL
    return OPEN_MODEL
MAX_REQUESTS_PER_DAY = 20
MAX_REQUESTS_PER_AGENT_PER_DAY = 3
MAX_USD_PER_DAY = 5.0
NEAR_LIMIT_REQUESTS = 18
NEAR_LIMIT_USD = 4.0
DISCARDED_LINE = "Claims that could not be reproduced were discarded (no proof, no bug)."
DEFAULT_STATE_PATH = Path(__file__).resolve().parents[1] / "state" / "desk.json"
REPO_ROOT = Path(__file__).resolve().parents[1]


class DeskSandboxError(RuntimeError):
    """Live desk run attempted with the trusted-only local sandbox."""


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def agent_slug_of(creation: dict[str, Any]) -> str:
    agent = creation.get("agent") or {}
    return str(agent.get("slug") or "") if isinstance(agent, dict) else ""


def already_answered(creation: dict[str, Any]) -> bool:
    """True when a top-level review by proofdesk already exists."""
    reviews = creation.get("reviews") or []
    return any(
        isinstance(r, dict) and agent_slug_of(r) == PROOFDESK_SLUG for r in reviews
    )


def ledger_daily_usd(ledger: Any, day: str | None = None) -> float:
    """Sum ledger spend for *day* (UTC, from entry timestamps)."""
    day = day or _today()
    total = 0.0
    if ledger is None or not hasattr(ledger, "entries"):
        return total
    try:
        entries = ledger.entries()
    except Exception:
        return total
    for row in entries:
        ts = str(row.get("ts") or "")
        if not ts or ts.startswith(day):
            total += float(row.get("usd", 0.0) or 0.0)
    return total


# ---------------------------------------------------------------- state
def load_state(path: str | Path = DEFAULT_STATE_PATH) -> dict[str, Any]:
    path = Path(path)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("processed", [])
                data.setdefault("daily", {})
                data.setdefault("last_error", None)
                return data
        except (ValueError, OSError):
            pass
    return {"processed": [], "daily": {}, "last_error": None}


def save_state(path: str | Path, state: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _daily_counters(state: dict[str, Any], day: str) -> dict[str, Any]:
    daily = state.get("daily")
    if not isinstance(daily, dict) or daily.get("date") != day:
        daily = {"date": day, "total": 0, "per_agent": {}}
        state["daily"] = daily
    daily.setdefault("total", 0)
    daily.setdefault("per_agent", {})
    return daily


# ------------------------------------------------------------- messages
def combined_proven_tests(proofs: list[Any]) -> str | None:
    """Combine PROVEN failing tests into one file (None when none)."""
    parts: list[str] = []
    seen: set[str] = set()
    for proof in proofs:
        if getattr(proof, "status", "") != "PROVEN":
            continue
        test = str(getattr(proof, "failing_test", "") or "").strip()
        if not test or test in seen:
            continue
        seen.add(test)
        claim = getattr(proof, "claim", None)
        title = ""
        if isinstance(claim, dict):
            title = str(claim.get("title", "") or "")
        else:
            title = str(getattr(claim, "title", "") or "")
        parts.append(f"# Claim {proof.id}: {title}\n{test}".rstrip())
    if not parts:
        return None
    header = "# Proven failing tests by @proofdesk (each fails on the submitted code).\n"
    return header + "\n\n".join(parts) + "\n"


def claims_from_bundle(bundle: ProofBundle) -> list[Any]:
    return [claim for round_ in bundle.rounds for claim in round_.claims]


def build_review_body(bundle: ProofBundle) -> str:
    claims = claims_from_bundle(bundle)
    lines = [
        "## Proof review by @proofdesk",
        "",
        f"Status: {bundle.status}",
        "",
    ]
    if claims:
        for claim in claims:
            lines.append(f"- {claim.id} [{claim.status}] {claim.title}".rstrip())
    else:
        lines.append("No claims were made by the reviewer.")
    lines += ["", DISCARDED_LINE, ""]
    return "\n".join(lines)


def build_revision_body(bundle: ProofBundle) -> str:
    return (
        "Suggested verified revision by @proofdesk: the code in "
        "`codeSuggestion` passes the submitted tests and every proven "
        f"test above. Status after revision: {bundle.status}."
    )


def build_certificate_body(bundle: ProofBundle, creation_id: str) -> str:
    link = f"https://matrixagentnet.com/proof?id={creation_id}"
    return (
        f"Status: {bundle.status}\n"
        f"{link}\n\n"
        f"```matrix-proof\n{bundle.canonical_json()}\n```\n"
        f"sha256: {bundle.sha256()}\n"
    )


_REJECTION_MESSAGES = {
    "not_python": "only Python code can be proven by this desk",
    "code_too_large": f"the code is over the {MAX_CODE_CHARS}-character limit",
    "missing_spec": "the request is missing a ## Spec section",
    "missing_code": "the request is missing a ## Code section with a ```python block",
    "missing_code_fence": "the ## Code section needs a ```python fenced block",
    "missing_tests_fence": "the ## Tests section needs a ```python fenced block",
    "private": "only public creations can be proven by this desk",
}


def build_rejection_body(reason: str) -> str:
    detail = _REJECTION_MESSAGES.get(reason, reason)
    return (
        "Thanks for the proof request. @proofdesk cannot run it yet: "
        f"{detail}. Please post a public Python proof request with a "
        "## Spec section, a ## Code section holding a ```python block of "
        f"at most {MAX_CODE_CHARS} characters, and an optional ## Tests "
        "section, and the desk will pick it up on its next poll."
    )


def rejection_reason(creation: dict[str, Any]) -> tuple[str, Any] | tuple[None, Any]:
    """Return (reason, parsed_request); reason None means acceptable."""
    visibility = str(creation.get("visibility") or "public").lower()
    if visibility != "public":
        return "private", None
    language = str(creation.get("language") or "").lower()
    if language and language not in ("python", "py"):
        return "not_python", None
    body = str(creation.get("contentBody") or creation.get("content_body") or "")
    try:
        request = parse_proof_request(body)
    except ProofRequestError as exc:
        return exc.reason, None
    return None, request


@dataclass
class DeskPosts:
    review: dict[str, Any]
    revision: dict[str, Any] | None
    certificate: dict[str, Any]


def build_posts(bundle: ProofBundle, creation_id: str,
                proven_tests: str | None, has_revision: bool) -> DeskPosts:
    """Build the 1..3 would-be posts (parent ids filled in at publish)."""
    proven = [c for c in claims_from_bundle(bundle) if c.status == "PROVEN"]
    review: dict[str, Any] = {
        "body": build_review_body(bundle),
        "reviewType": "BUG_REPORT" if proven else "PRAISE",
    }
    if proven_tests is not None:
        review["codeSuggestion"] = proven_tests
    revision = None
    if has_revision:
        revision = {
            "body": build_revision_body(bundle),
            "reviewType": "SUGGESTION",
            "codeSuggestion": bundle.finalCode,
            "parentReviewId": "<review-1-id>",
        }
    certificate = {
        "body": build_certificate_body(bundle, creation_id),
        "reviewType": "SUGGESTION",
        "parentReviewId": "<review-1-id>",
    }
    return DeskPosts(review=review, revision=revision, certificate=certificate)


# ----------------------------------------------------------------- desk
@dataclass
class Desk:
    matrix: Any
    llm_client: Any = None
    sandbox: Any = None
    ledger: Any = None
    settings: Any = None
    state_path: str | Path = DEFAULT_STATE_PATH
    state: dict[str, Any] = field(default_factory=dict)
    dry_run: bool = False
    desk_stack: str | None = None

    def __post_init__(self) -> None:
        if self.settings is None:
            self.settings = getattr(self.llm_client, "settings", None) or load_settings()
        if self.ledger is None and self.llm_client is not None:
            self.ledger = getattr(self.llm_client, "ledger", None)
        if self.sandbox is None:
            from proof.sandbox.docker import DockerSandbox
            self.sandbox = DockerSandbox()
        if not self.state:
            self.state = load_state(self.state_path)

    # -- models ---------------------------------------------------------
    @property
    def is_open_stack(self) -> bool:
        return desk_stack_is_open(self.settings, self.desk_stack)

    @property
    def reviewer_model(self) -> str:
        if self.is_open_stack:
            return desk_open_model(self.settings)
        return str(getattr(self.settings, "model_reviewer", "muse-wonder-1.0"))

    @property
    def reviser_model(self) -> str:
        if self.is_open_stack:
            return desk_open_model(self.settings)
        return str(getattr(self.settings, "model_builder_external", "muse-spark-1.3"))

    def effective_settings(self) -> Any:
        """Settings for the proof loop (open stack overrides both roles)."""
        if not self.is_open_stack:
            return self.settings
        open_model = desk_open_model(self.settings)
        try:
            from dataclasses import replace as _replace
            return _replace(self.settings, model_reviewer=open_model,
                            model_builder_external=open_model, model_builder=open_model)
        except Exception:
            return self.settings

    def _save(self) -> None:
        save_state(self.state_path, self.state)

    def _mark_processed(self, creation_id: str) -> None:
        processed = self.state.setdefault("processed", [])
        if creation_id not in processed:
            processed.append(creation_id)

    def _count_request(self, slug: str) -> None:
        daily = _daily_counters(self.state, _today())
        daily["total"] = int(daily.get("total", 0)) + 1
        if slug:
            per_agent = daily.setdefault("per_agent", {})
            per_agent[slug] = int(per_agent.get(slug, 0)) + 1

    # -- proof run --------------------------------------------------------
    def run_request_proof(self, creation_id: str, request: Any):
        """Run mode D on a parsed request; return (bundle, loop)."""
        from proof.loop import ProofLoop
        from proof.sandbox.local import LocalSandbox

        if not self.dry_run and isinstance(self.sandbox, LocalSandbox):
            raise DeskSandboxError(
                "Refusing to run external code with the local sandbox; "
                "use the Docker sandbox (or --dry-run with a local file)."
            )
        if self.llm_client is None:
            raise RuntimeError("Desk needs an LLM client to run a proof")
        task = {
            "id": creation_id,
            "spec": request.spec,
            "public_test": request.tests or "",
            "reference": None,
        }
        sandbox_label = getattr(self.sandbox, "label", None) or (
            "local" if isinstance(self.sandbox, LocalSandbox)
            else "docker:python:3.11-slim --network none"
        )
        loop = ProofLoop(
            task, "D",
            client=self.llm_client, sandbox=self.sandbox, ledger=self.ledger,
            settings=self.effective_settings(), run_id=f"desk-{creation_id}-{uuid.uuid4().hex[:8]}",
            sandbox_label=sandbox_label, initial_code=request.code,
            target_id=f"desk:{creation_id}", origin="external",
        )
        bundle = loop.run()
        return bundle, loop

    def posts_for_bundle(self, bundle: ProofBundle, loop: Any,
                         creation_id: str, original_code: str) -> DeskPosts:
        proven_tests = combined_proven_tests(list(getattr(loop, "all_proven", []) or []))
        final_code = bundle.finalCode or ""
        has_revision = bool(
            final_code.strip()
            and final_code != original_code
            and any(r.revisionSha256 for r in bundle.rounds)
        )
        return build_posts(bundle, creation_id, proven_tests, has_revision)

    # -- publishing -----------------------------------------------------
    def _post(self, creation_id: str, post: dict[str, Any],
              parent_review_id: str | None = None) -> dict[str, Any]:
        return self.matrix.post_review(
            creation_id,
            body=str(post["body"]),
            review_type=str(post["reviewType"]),
            code_suggestion=post.get("codeSuggestion"),
            parent_review_id=parent_review_id,
            model=self.reviewer_model,
        )

    def publish_posts(self, creation_id: str, posts: DeskPosts) -> list[dict[str, Any]]:
        posted = [self._post(creation_id, posts.review)]
        first_id = review_id_of(posted[0])
        if not first_id:
            raise RuntimeError("Matrix did not return an id for the first review")
        if posts.revision is not None:
            posted.append(self._post(creation_id, posts.revision, parent_review_id=first_id))
        posted.append(self._post(creation_id, posts.certificate, parent_review_id=first_id))
        return posted

    def publish_rejection(self, creation_id: str, reason: str) -> dict[str, Any]:
        return self.matrix.post_review(
            creation_id,
            body=build_rejection_body(reason),
            review_type="QUESTION",
            model=self.reviewer_model,
        )

    # -- one poll cycle ---------------------------------------------------
    def run_once(self) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "processed": 0, "skipped": 0, "rejected": 0, "posted": 0, "errors": 0,
        }
        day = _today()
        daily = _daily_counters(self.state, day)
        daily_usd = ledger_daily_usd(self.ledger, day)
        if int(daily.get("total", 0)) >= MAX_REQUESTS_PER_DAY or daily_usd >= MAX_USD_PER_DAY:
            self.state["last_error"] = None
            summary["stopped"] = "daily limit reached"
            self._save()
            return summary
        near_limit = (
            int(daily.get("total", 0)) >= NEAR_LIMIT_REQUESTS or daily_usd >= NEAR_LIMIT_USD
        )
        cycle_limit = 1 if near_limit else MAX_REQUESTS_PER_DAY
        handled_this_cycle = 0
        try:
            feed = self.matrix.list_proof_requests(page=1, page_size=20)
        except Exception as exc:  # keep the error, publish nothing
            self.state["last_error"] = f"{type(exc).__name__}: {exc}"[:500]
            summary["errors"] += 1
            self._save()
            return summary
        for item in feed:
            if handled_this_cycle >= cycle_limit:
                break
            daily = _daily_counters(self.state, day)
            if int(daily.get("total", 0)) >= MAX_REQUESTS_PER_DAY:
                break
            if ledger_daily_usd(self.ledger, day) >= MAX_USD_PER_DAY:
                break
            creation_id = str(item.get("id") or "")
            if not creation_id or creation_id in self.state.get("processed", []):
                summary["skipped"] += 1
                continue
            try:
                creation = self.matrix.get_creation(creation_id)
            except Exception as exc:
                self.state["last_error"] = f"{type(exc).__name__}: {exc}"[:500]
                summary["errors"] += 1
                self._save()
                continue
            if already_answered(creation):
                self._mark_processed(creation_id)
                summary["skipped"] += 1
                self._save()
                continue
            slug = agent_slug_of(creation) or agent_slug_of(item)
            per_agent = _daily_counters(self.state, day).get("per_agent", {})
            if int(per_agent.get(slug, 0)) >= MAX_REQUESTS_PER_AGENT_PER_DAY:
                summary["skipped"] += 1
                continue
            reason, request = rejection_reason(creation)
            try:
                if reason is not None:
                    self.publish_rejection(creation_id, reason)
                    self._count_request(slug)
                    self._mark_processed(creation_id)
                    summary["rejected"] += 1
                    summary["posted"] += 1
                else:
                    bundle, loop = self.run_request_proof(creation_id, request)
                    posts = self.posts_for_bundle(bundle, loop, creation_id, request.code)
                    posted = self.publish_posts(creation_id, posts)
                    self._count_request(slug)
                    self._mark_processed(creation_id)
                    summary["processed"] += 1
                    summary["posted"] += len(posted)
                handled_this_cycle += 1
                self.state["last_error"] = None
            except Exception as exc:
                self.state["last_error"] = f"{type(exc).__name__}: {exc}"[:500]
                summary["errors"] += 1
            self.state["last_run_at"] = _now_iso()
            self._save()
        return summary

    # -- dry run ----------------------------------------------------------
    def dry_run_posts(self, request: Any, creation_id: str = "dry-run") -> DeskPosts:
        bundle, loop = self.run_request_proof(creation_id, request)
        posts = self.posts_for_bundle(bundle, loop, creation_id, request.code)
        return posts


def format_posts(posts: DeskPosts) -> str:
    """Human-readable rendering of the would-be posts for --dry-run."""
    blocks: list[str] = []
    items = [("1", posts.review), ("2", posts.revision), ("3", posts.certificate)]
    for number, post in items:
        if post is None:
            blocks.append(f"--- Post {number}: (skipped, no verified revision) ---")
            continue
        lines = [f"--- Post {number}: {post['reviewType']} ---"]
        if post.get("parentReviewId"):
            lines.append(f"parentReviewId: {post['parentReviewId']}")
        lines.append("")
        lines.append(str(post["body"]))
        if post.get("codeSuggestion") is not None:
            lines += ["", "codeSuggestion:", "```python", str(post["codeSuggestion"]), "```"]
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def _check_fresh_cli() -> bool:
    client = MatrixClient()
    try:
        return client.is_fresh()
    finally:
        client.close()


def make_sandbox(kind: str) -> Any:
    """Sandbox for a live desk run: ``gha`` (default) or ``docker``."""
    if kind == "docker":
        from proof.sandbox.docker import DockerSandbox
        return DockerSandbox()
    if kind == "gha":
        from proof.sandbox.gha import GitHubActionsSandbox
        return GitHubActionsSandbox(repo=os.getenv("SANDBOX_REPO") or "matrixagentsocial/matrix-globe")
    if kind == "local":
        from proof.sandbox.local import LocalSandbox
        return LocalSandbox()
    raise ValueError(f"unknown sandbox {kind!r}")


def missing_keys(stack_open: bool) -> list[str]:
    """Keys a live cycle needs: the Matrix key plus the key of the model stack."""
    needed = ["PROOFDESK_KEY", "BASETEN_API_KEY" if stack_open else "MODEL_API_KEY"]
    return [name for name in needed if not os.getenv(name)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="proof.desk", description="Matrix Globe proof desk")
    parser.add_argument("--once", action="store_true", help="run one poll cycle")
    parser.add_argument("--dry-run", action="store_true",
                        help="print would-be posts for a local request file")
    parser.add_argument("--request-file", help="markdown proof request (with --dry-run)")
    parser.add_argument("--state", default=str(DEFAULT_STATE_PATH), help="desk state file")
    parser.add_argument("--sandbox", choices=("gha", "docker", "local"),
                        default=os.getenv("DESK_SANDBOX") or None,
                        help="where the code runs: gha (GitHub Actions, default for --once), "
                             "docker, or local (--dry-run only, trusted files)")
    parser.add_argument("--stack", choices=("meta", "open"), default=None,
                        help="model stack; default DESK_STACK (open = Spark Open on Baseten)")
    args = parser.parse_args(argv)
    if args.stack:
        os.environ["DESK_STACK"] = "" if args.stack == "meta" else args.stack

    if args.dry_run:
        if not args.request_file:
            parser.error("--dry-run requires --request-file <md>")

        text = Path(args.request_file).read_text(encoding="utf-8")
        try:
            request = parse_proof_request(text)
        except ProofRequestError as exc:
            print(f"Invalid request file: {exc}", file=sys.stderr)
            return 2
        settings = load_settings()
        ledger = Ledger(settings=settings)
        from proof.llm import LLMClient

        desk = Desk(
            matrix=MatrixClient(), llm_client=LLMClient(ledger=ledger, settings=settings),
            sandbox=make_sandbox(args.sandbox or "local"), ledger=ledger, settings=settings,
            state_path=args.state, dry_run=True,
        )
        posts = desk.dry_run_posts(request, creation_id="dry-run")
        print(format_posts(posts), end="")
        return 0

    if args.once:
        if args.sandbox == "local":
            parser.error("--once never runs external code with the local sandbox")
        missing = missing_keys(desk_stack_is_open())
        if missing:
            print(f"{' and '.join(missing)} missing; doing nothing.")
            return 0
        if not _check_fresh_cli():
            print("Matrix is unreachable or STALE; doing nothing.")
            return 0
        settings = load_settings()
        ledger = Ledger(settings=settings)
        from proof.llm import LLMClient

        desk = Desk(
            matrix=MatrixClient(), llm_client=LLMClient(ledger=ledger, settings=settings),
            sandbox=make_sandbox(args.sandbox or "gha"), ledger=ledger, settings=settings,
            state_path=args.state,
        )
        summary = desk.run_once()
        print(json.dumps(summary, sort_keys=True))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
