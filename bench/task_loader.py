"""Shared loading for FinCode tasks under ``bench/tasks/<id>/``."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Task:
    id: str
    dir: Path
    spec: str
    public_test: str
    hidden_test: str
    reference: str
    meta: dict

    @property
    def split(self) -> str:
        return str(self.meta.get("split", ""))


def load_task(task_dir: str | Path) -> Task:
    task_dir = Path(task_dir)
    meta = json.loads((task_dir / "meta.json").read_text(encoding="utf-8"))
    return Task(
        id=str(meta.get("id") or task_dir.name),
        dir=task_dir,
        spec=(task_dir / "spec.md").read_text(encoding="utf-8"),
        public_test=(task_dir / "public_test.py").read_text(encoding="utf-8"),
        hidden_test=(task_dir / "hidden_test.py").read_text(encoding="utf-8"),
        reference=(task_dir / "reference.py").read_text(encoding="utf-8"),
        meta=meta,
    )


MUTANT_KINDS = (
    "rounding_mode", "rounding_step", "boundary", "tie_break",
    "missing_validation", "convention", "float_money", "timezone", "other",
)


def load_mutants(task: Task) -> list[dict]:
    """Return mutant metadata for *task* ([] when no mutants dir)."""
    meta_path = task.dir / "mutants" / "mutants.json"
    if not meta_path.exists():
        return []
    data = json.loads(meta_path.read_text(encoding="utf-8"))
    return list(data)


def load_targets(task: Task, targets: str = "all") -> list[tuple[str, str]]:
    """Return [(target_id, code)] for mutants/clean/all selection."""
    out: list[tuple[str, str]] = []
    if targets in ("mutants", "all"):
        for entry in load_mutants(task):
            mid = str(entry["id"])
            code = (task.dir / "mutants" / f"{mid}.py").read_text(encoding="utf-8")
            out.append((mid, code))
    if targets in ("clean", "all"):
        out.append(("clean", task.reference))
    return out


def discover_tasks(tasks_root: str | Path, split: str | None = None) -> list[Task]:
    root = Path(tasks_root)
    tasks: list[Task] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or not (child / "meta.json").exists():
            continue
        task = load_task(child)
        if split is not None and task.split != split:
            continue
        tasks.append(task)
    return tasks
