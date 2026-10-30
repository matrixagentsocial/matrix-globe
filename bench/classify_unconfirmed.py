"""Classify every PROVEN + UNCONFIRMED claim of the final runs by hand-written rules.

Usage: python bench/classify_unconfirmed.py

A claim is UNCONFIRMED when the reviewer's failing test also fails on our
reference solution. That means one of three things:

- shared_defect: the spec supports the reviewer; our reference has the same
  defect (the hidden tests did not cover it).
- spec_ambiguity: the spec can be read both ways; the reviewer picked the
  reading our reference did not.
- reviewer_error: the spec contradicts the reviewer.

Bundles keep each claim's title and the SHA-256 of its test, not the test
code, so each family below was decided by reading the claim titles against
the task's spec.md and reference.py. The rationale for each rule quotes the
spec. Any claim that matches no rule is reported as `unclassified` and must be
read by hand; the run fails if one exists.

Writes results/unconfirmed_classification.json and .md.
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNS = (("meta", "final"), ("open", "final_open"))
MAGNITUDE = "large values / Decimal context precision"

# (category, family, regex on the lower-cased title, rationale). First match wins.
RULES = [
    ("spec_ambiguity", "trailing-zero decimal places",
     r"(three|3|more than (2|two)|>2|trailing).*(decimal|dp)|decimal places.*trailing|trailing zero|1\.500|1\.0010",
     'Specs say "at most 2 decimal places" with "10.005" as the example. They do not say whether '
     '"1.500" (numerically 2 places, written with 3) is valid; the reference reads it numerically, '
     "the reviewer reads the written form."),
    ("spec_ambiguity", "zero-quantized straight-line year",
     r"zero-quantized|quantized (annual|yearly) amount is zero|rounds to 0\.00|is 0\.00|collapse|loops forever|whole base|entire (remaining )?base",
     "depreciation_straight_line rule 8 loops while the remaining base is > 0 charging min(raw, remaining); "
     "when the yearly amount quantizes to 0.00 the rules never terminate, so the spec does not define the result."),
    ("spec_ambiguity", "extra keys in an entry",
     r"extra keys",
     'prorata_billing rule 2: "Each entry is {date, monthly_price}"; it does not say whether extra keys '
     'are an "invalid entry shape".'),
    ("spec_ambiguity", "duplicate rate keys",
     r"duplicate rate keys|silently overwrite",
     "fx_triangulation does not say what happens when two rate keys normalise to the same code (other than EUR)."),
    ("spec_ambiguity", "XIRR double root",
     r"double-root|no sign change",
     'xirr rule 11 says to raise when "no rate makes the NPV zero (no sign change ...)"; a double root makes '
     "the NPV zero without a sign change, so the two halves of the rule disagree."),
    ("shared_defect", "large values / Decimal context precision",
     r"large|precision|significant digits|28|invalidoperation|scientific|quantiz|loses cents|loses tiny|many decimal places|exact remainder|remainder order|fractional-remainder|rounded decimal shares|1e\+30",
     "Inputs are only required to be finite (apr_apy: \"There is no upper bound\"; allocate_ratios: weights "
     '"may have any number of decimal places"; weighted_average_cost uses precision 50 "for divisions"). '
     "The reference evaluates under Python's default 28-digit context (or rounds a multiplication at 50 digits), "
     "so huge or very precise valid inputs crash with InvalidOperation or lose cents."),
    ("shared_defect", "trailing newline in dates",
     r"trailing newline",
     'Dates must be "exactly YYYY-MM-DD"; the reference uses a regex with "$", which also matches before a final "\\n".'),
    ("shared_defect", "whitespace-only key or account",
     r"whitespace-only",
     'idempotent_ledger rule 4: "key" and "account" must be "a non-empty string"; " " is non-empty, '
     "but the reference strips before checking."),
    ("shared_defect", "unhashable movement type",
     r"unhashable",
     'weighted_average_cost rule 2: "any other type raises ValueError"; the reference raises TypeError for a list.'),
    ("shared_defect", "non-ASCII digits",
     r"non-ascii|unicode digits",
     'The formats are fixed digit patterns ("any other format raises ValueError"); the reference uses \\d, '
     "which also matches non-ASCII digits."),
    ("shared_defect", "currency code checks",
     r"upper\(\)|length-expanding|expand|eur rate|eur entry|eur keys|eur also|bypass the eur",
     'fx_triangulation rules 3-4: codes are "exactly 3 letters A-Z" and "If EUR is present (in any letter case) '
     'its rate must equal 1"; the reference checks length after upper() ("ß" -> "SS") and lets a second '
     "spelling of EUR hide a non-1 rate."),
]


def load_claims() -> list[dict]:
    claims = []
    for stack, folder in RUNS:
        for jsonl in sorted((REPO / "results" / folder).glob("*_D*.jsonl")):
            scope = jsonl.stem.split("_")[0]
            for line in jsonl.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                bundle = json.loads((REPO / row["bundle"].replace("\\", "/")).read_text(encoding="utf-8"))
                for round_ in bundle["rounds"]:
                    for claim in round_["claims"]:
                        if claim["status"] == "PROVEN" and claim.get("validity") == "UNCONFIRMED":
                            claims.append({
                                "stack": stack, "scope": scope, "task": row["task_id"], "target": row["target_id"],
                                "runId": row["run_id"], "round": round_["n"], "claim": claim["id"],
                                "title": claim["title"], "testSha256": claim.get("testSha256"),
                            })
    return claims


def classify(title: str) -> tuple[str, str]:
    lowered = title.lower()
    for category, family, pattern, _ in RULES:
        if re.search(pattern, lowered):
            return category, family
    return "unclassified", ""


def main() -> int:
    claims = load_claims()
    for claim in claims:
        claim["category"], claim["family"] = classify(claim["title"])

    totals = collections.Counter((c["stack"], c["scope"], c["category"]) for c in claims)
    families = collections.Counter((c["category"], c["family"]) for c in claims)
    out = REPO / "results"
    (out / "unconfirmed_classification.json").write_text(
        json.dumps({"claims": claims, "rules": [{"category": c, "family": f, "pattern": p, "rationale": r} for c, f, p, r in RULES]},
                   indent=1, ensure_ascii=False), encoding="utf-8")

    lines = ["# UNCONFIRMED claims, classified", "",
             "A proven claim is UNCONFIRMED when the reviewer's failing test also fails on our reference solution. "
             "Generated by `bench/classify_unconfirmed.py` from the committed bundles; rules and rationale are in that file.",
             "", "| models | scope | proven claims | VALID | shared defect | spec ambiguity | reviewer error | unclassified |",
             "|---|---|---|---|---|---|---|---|"]
    precision = []
    for stack, folder in RUNS:
        for jsonl in sorted((REPO / "results" / folder).glob("*_D*.jsonl")):
            scope = jsonl.stem.split("_")[0]
            rows = [json.loads(line) for line in jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
            proven = sum(r["claims_proven"] for r in rows)
            valid = sum(r["claims_valid"] for r in rows)
            n = lambda cat: totals[(stack, scope, cat)]  # noqa: E731
            lines.append(f"| {stack} | {scope} | {proven} | {valid} | {n('shared_defect')} | {n('spec_ambiguity')} | "
                         f"{n('reviewer_error')} | {n('unclassified')} |")
            large = sum(1 for c in claims if (c["stack"], c["scope"], c["family"]) == (stack, scope, MAGNITUDE))
            real = valid + n("shared_defect")
            precision.append(f"- {stack} {scope}: real defects (VALID + shared defect) {real}/{proven} = {real / proven:.2f}; "
                             f"without the {large} huge-magnitude claims {real - large}/{proven - large} = "
                             f"{(real - large) / (proven - large):.2f}; contradicted the spec: {n('reviewer_error')}.")
    lines += ["", "Reading. A stricter reader may say the specs never meant 29-digit amounts; the second figure "
              "drops those claims entirely.", ""] + precision
    lines += ["", "## Families", "", "| category | family | claims |", "|---|---|---|"]
    for (category, family), count in sorted(families.items(), key=lambda kv: (kv[0][0], -kv[1])):
        lines.append(f"| {category} | {family or '-'} | {count} |")
    lines += ["", "## Rationale", ""]
    for category, family, _, rationale in RULES:
        lines.append(f"- **{family}** ({category}): {rationale}")
    unclassified = [c for c in claims if c["category"] == "unclassified"]
    if unclassified:
        lines += ["", "## Unclassified", ""] + [f"- {c['stack']} {c['scope']} {c['task']} {c['target']}: {c['title']}" for c in unclassified]
    (out / "unconfirmed_classification.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines))
    return 1 if unclassified else 0


if __name__ == "__main__":
    sys.exit(main())
