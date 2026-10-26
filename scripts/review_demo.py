"""Demo: review -> prove -> revise -> verify on split_installments.

Uses a deliberately naive solution that rounds each installment
independently (100.00/3 -> 33.33 x3 = 99.99). Runs the real reviewer
(Wonder), the proof rule in the sandbox, the reviser (Spark), then
verifies public + proven tests on the revision. Prints each claim with
its proof/validity status and the final status. Run from the repo root:

    .venv\\Scripts\\python scripts\\review_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bench.task_loader import load_task
from proof.config import load_settings
from proof.ledger import Ledger
from proof.llm import LLMClient
from proof.proofrule import prove_claims
from proof.pytest_runner import run_pytest
from proof.roles.reviewer import review_code
from proof.roles.reviser import revise_code
from proof.loop import format_public_results

NAIVE_SOLUTION = '''
from decimal import Decimal, ROUND_HALF_UP

def split_installments(total, n):
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("n must be an integer >= 1")
    amount = Decimal(total)
    if not amount.is_finite() or amount < 0 or amount != amount.quantize(Decimal("0.01")):
        raise ValueError("invalid total")
    each = (amount / n).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return [each] * n
'''


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    task = load_task(repo / "bench" / "tasks" / "split_installments")
    settings = load_settings()
    ledger = Ledger(Path("state/ledger.jsonl"), settings=settings)
    client = LLMClient(ledger=ledger, settings=settings)
    from proof.sandbox.local import LocalSandbox

    sandbox = LocalSandbox()
    run_id = "review-demo-split_installments"
    before = ledger.total_usd()

    print("=== Naive solution (rounds each installment independently) ===")
    print(NAIVE_SOLUTION.strip())
    pub = run_pytest(sandbox, NAIVE_SOLUTION, {"public_test.py": task.public_test})
    print(f"\nPublic tests on naive code: {pub.passed}/{pub.total} passed")

    print("\n=== Review (Wonder reviewer) ===")
    report = review_code(client, task.spec, NAIVE_SOLUTION, format_public_results(pub), run_id=run_id)
    print(f"verdict: {report.verdict}; claims: {len(report.claims)}")
    for c in report.claims:
        print(f"- {c.id} [{c.severity}] {c.title}")

    print("\n=== Proof rule (sandbox, bench validity vs reference) ===")
    proofs = prove_claims(list(report.claims), NAIVE_SOLUTION, sandbox, reference_code=task.reference)
    for p in proofs:
        print(f"{p.id}: {p.status}" + (f" / {p.validity}" if p.validity else ""))
    proven = [p for p in proofs if p.status == "PROVEN"]

    status = "FAILED"
    final_code = NAIVE_SOLUTION
    if proven:
        print("\n=== Revise (Spark reviser, proven claims only) ===")
        revision = revise_code(client, task.spec, NAIVE_SOLUTION,
                               [p.to_claim_dict() for p in proven], run_id=run_id)
        final_code = revision.code
        print(f"addressed: {[a.claim_id for a in revision.addressed]}")
        print(f"contested: {[c.claim_id for c in revision.contested]}")
        pub2 = run_pytest(sandbox, final_code, {"public_test.py": task.public_test})
        proven_total = len(proven)
        proven_passed = 0
        for p in proven:
            r = run_pytest(sandbox, final_code, {f"test_proven_{p.id}.py": p.failing_test})
            if r.all_passed:
                proven_passed += 1
        print(f"\nVerify revision: public {pub2.passed}/{pub2.total}, proven {proven_passed}/{proven_total}")
        if pub2.total and pub2.passed == pub2.total and proven_passed == proven_total:
            status = "VERIFIED"
        elif pub2.passed < pub2.total:
            status = "FAILED"
        else:
            status = "PARTIAL"
    else:
        status = "VERIFIED" if pub.all_passed else "FAILED"

    print(f"\nFinal status: {status}")
    print(f"Demo LLM cost this run: ${ledger.total_usd() - before:.4f}")
    # Machine-readable summary line for PROGRESS.md / checks.
    proven_valid = sum(1 for p in proofs if p.status == "PROVEN" and p.validity == "VALID")
    print(f"SUMMARY proven={len(proven)} valid={proven_valid} status={status}")
    return 0 if proven_valid >= 1 else 2


if __name__ == "__main__":
    raise SystemExit(main())
