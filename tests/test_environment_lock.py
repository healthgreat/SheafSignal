from pathlib import Path
import importlib.util

import pandas as pd


def _load_script():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "build_environment_lock.py"
    spec = importlib.util.spec_from_file_location("build_environment_lock", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_environment_lock_audit_detects_pinned_and_local_references():
    script = _load_script()
    audit = script.audit_lock_lines(
        [
            "numpy==2.0.0",
            "xenaPython @ git+https://github.com/ucscXena/xenaPython@f243bbff036f5b9e417a77efc95ccc76672ca306",
            "example @ file:///tmp/example",
        ]
    )

    statuses = dict(zip(audit["requirement"], audit["status"]))
    assert statuses["numpy==2.0.0"] == "pass"
    assert (
        statuses[
            "xenaPython @ git+https://github.com/ucscXena/xenaPython@f243bbff036f5b9e417a77efc95ccc76672ca306"
        ]
        == "pass"
    )
    assert statuses["example @ file:///tmp/example"] == "warn"


def test_core_lock_selects_known_packages():
    script = _load_script()
    lines = script.build_core_lock_lines(
        [
            "numpy==2.0.0",
            "pandas==2.2.0",
            "unrelated==1.0.0",
        ]
    )

    assert lines == ["numpy==2.0.0", "pandas==2.2.0"]


def test_build_environment_lock_writes_outputs(tmp_path):
    script = _load_script()
    paths = script.build_environment_lock(
        tmp_path,
        freeze_lines=[
            "numpy==2.0.0",
            "pandas==2.2.0",
            "pytest==8.0.0",
        ],
    )

    for path in paths.values():
        assert path.exists()
    summary = pd.read_csv(paths["summary"], sep="\t")
    assert summary.iloc[0]["decision"] == "ENVIRONMENT_LOCK_PASS"
    assert "numpy==2.0.0" in paths["full_lock"].read_text(encoding="utf-8")
