"""validate_tasks on a fixture task (M1)."""
import json
from pathlib import Path

from bench.validate_tasks import validate_task
from bench.task_loader import load_task


def _write_task(root: Path) -> Path:
    task_dir = root / "fixture_add"
    task_dir.mkdir(parents=True)
    (task_dir / "spec.md").write_text(
        "# Add\n\nImplement `add(a, b)` returning the sum.\n", encoding="utf-8"
    )
    (task_dir / "reference.py").write_text(
        "def add(a, b):\n    return a + b\n", encoding="utf-8"
    )
    (task_dir / "public_test.py").write_text(
        "from solution import add\n\ndef test_add_public():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    (task_dir / "hidden_test.py").write_text(
        "from solution import add\n\n"
        "def test_add_hidden_negative():\n    assert add(-1, -2) == -3\n\n"
        "def test_add_hidden_zero():\n    assert add(0, 5) == 5\n",
        encoding="utf-8",
    )
    (task_dir / "meta.json").write_text(
        json.dumps(
            {"id": "fixture_add", "split": "dev", "tags": ["fixture"], "difficulty": "easy"}
        ),
        encoding="utf-8",
    )
    return task_dir


def test_validate_fixture_task(tmp_path):
    task_dir = _write_task(tmp_path)
    result = validate_task(load_task(task_dir))
    assert result.reference_ok is True
    assert result.naive_fails_hidden is True
    assert result.hidden_not_subset is True
    assert result.ok is True


def test_validate_detects_duplicate_hidden_names(tmp_path):
    task_dir = _write_task(tmp_path)
    (task_dir / "hidden_test.py").write_text(
        "from solution import add\n\n"
        "def test_add_hidden_unique():\n    assert add(-1, -2) == -3\n\n"
        "def test_add_hidden_unique():\n    assert add(0, 5) == 5\n",
        encoding="utf-8",
    )
    result = validate_task(load_task(task_dir))
    assert result.hidden_names_unique is False
    assert result.ok is False


def test_validate_detects_non_stdlib_import(tmp_path):
    task_dir = _write_task(tmp_path)
    (task_dir / "reference.py").write_text(
        "import numpy\n\ndef add(a, b):\n    return a + b\n", encoding="utf-8"
    )
    result = validate_task(load_task(task_dir))
    assert result.stdlib_only is False
    assert result.ok is False


def test_validate_detects_hidden_subset(tmp_path):
    task_dir = _write_task(tmp_path)
    # Make hidden names a subset of public names.
    (task_dir / "hidden_test.py").write_text(
        "from solution import add\n\ndef test_add_public():\n    assert add(2, 2) == 4\n",
        encoding="utf-8",
    )
    result = validate_task(load_task(task_dir))
    assert result.hidden_not_subset is False
    assert result.ok is False
