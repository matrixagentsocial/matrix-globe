import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_index", REPO / "site" / "build_index.py")
build_index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_index)


def row(target, *, fixed, damaged=False, proven=0, valid=0, usd=0.1, seed=0, task="t1", regressions=0):
    return {
        "task_id": task, "target_id": target, "seed": seed, "fixed": fixed, "damaged": damaged,
        "all_pass": fixed, "regressions": regressions, "claims_proposed": proven, "claims_proven": proven,
        "claims_valid": valid, "claims_unconfirmed": proven - valid, "usd": usd,
    }


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def test_summary_counts_fixed_damage_precision_and_cost(tmp_path):
    write_jsonl(tmp_path / "final" / "pr_D.jsonl", [
        row("buggy_a", fixed=True, proven=3, valid=1, usd=0.3),
        row("buggy_b", fixed=False, proven=1, valid=1, usd=0.1, regressions=2),
        row("clean", fixed=True, damaged=True, proven=2, valid=0, usd=0.2),
    ])
    write_jsonl(tmp_path / "final" / "pr_B.jsonl", [row("regen", fixed=True, usd=0.4)])
    write_jsonl(tmp_path / "final_open" / "single_D_open.jsonl", [row("m1", fixed=True, seed=0), row("m1", fixed=True, seed=1)])

    summary = build_index.build_summary(tmp_path)

    assert summary["status"] == "final"
    meta_pr, open_single = summary["tables"]
    assert (meta_pr["stack"], meta_pr["scope"]) == ("meta", "pr")
    d, b = meta_pr["conditions"]  # sorted R, C, E, D, B
    assert (d["id"], d["fixed"], d["buggy"], d["damaged"], d["clean"]) == ("D", 1, 2, 1, 1)
    assert d["regressions"] == 2
    assert d["precision"] == round(2 / 6, 2)
    assert d["usdPerTarget"] == 0.2
    assert (b["id"], b["regenPassed"], b["regen"], b["buggy"]) == ("B", 1, 1, 0)
    assert (open_single["stack"], open_single["scope"]) == ("open", "single")
    assert open_single["conditions"][0]["id"] == "D"
    assert open_single["conditions"][0]["seeds"] == 2


def test_summary_pending_without_results(tmp_path):
    assert build_index.build_summary(tmp_path)["status"] == "pending"


def test_committed_final_rows_match_their_bundle_hashes():
    """Every final-run row's recorded certificate hash is the hash the viewer will show."""
    checked = 0
    for jsonl in sorted((REPO / "results").glob("final*/*.jsonl")):
        for line in jsonl.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            bundle = json.loads((REPO / r["bundle"].replace("\\", "/")).read_text(encoding="utf-8"))
            assert build_index.sha256_text(build_index.canonical_json(bundle)) == r["bundle_sha256"], r["run_id"]
            checked += 1
    assert checked > 0
