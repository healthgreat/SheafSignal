from pathlib import Path
import importlib.util

import pandas as pd


def _load_script():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "check_comparator_scope_gate.py"
    spec = importlib.util.spec_from_file_location("check_comparator_scope_gate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_tool_comparison(root: Path, missing_tool: str | None = None) -> None:
    path = root / "benchmarks" / "results"
    path.mkdir(parents=True)
    rows = []
    for dataset_id in [
        "gse72056_melanoma_scrna",
        "gse154778_pdac_scrna",
        "gse176078_brca_scrna",
    ]:
        for tool in [
            "LRProductBaseline",
            "LIANA",
            "MechanisticTargetPrior",
            "NicheNet",
            "CellPhoneDB",
            "CellChat",
        ]:
            if tool == missing_tool:
                continue
            rows.append({"dataset_id": dataset_id, "tool": tool, "status": "completed"})
    rows.append(
        {
            "dataset_id": "tenx_breast_visium",
            "tool": "CellChat",
            "status": "not_run_requires_external_tool",
        }
    )
    pd.DataFrame(rows).to_csv(path / "tool_comparison.csv", index=False)


def test_comparator_scope_passes_primary_scrna_completion(tmp_path):
    script = _load_script()
    _write_tool_comparison(tmp_path)
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "draft.md").write_text(
        "Comparator evidence supports complementarity, not broad superiority.\n",
        encoding="utf-8",
    )

    audit = script.build_comparator_scope_audit(tmp_path)
    report = script.build_comparator_scope_report(audit)

    assert "fail" not in set(audit["status"])
    assert "COMPARATOR_SCOPE_PASS_PRIMARY_SCRNA" in report


def test_comparator_scope_fails_missing_primary_tool(tmp_path):
    script = _load_script()
    _write_tool_comparison(tmp_path, missing_tool="CellChat")

    audit = script.build_comparator_scope_audit(tmp_path)
    failures = audit.loc[audit["status"] == "fail"]

    assert "primary_scrna_comparator_completion" in set(failures["check_id"])
    assert "CellChat" in set(failures["tool"])


def test_comparator_scope_flags_stale_cellchat_pending_text(tmp_path):
    script = _load_script()
    _write_tool_comparison(tmp_path)
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "draft.md").write_text(
        "CellChat, CellPhoneDB and niche-DE remain pending.\n",
        encoding="utf-8",
    )

    audit = script.build_comparator_scope_audit(tmp_path)
    failures = audit.loc[audit["status"] == "fail"]

    assert "text_scope::stale_cellchat_cellphonedb_pending" in set(failures["check_id"])


def test_comparator_scope_main_writes_outputs(tmp_path):
    script = _load_script()
    _write_tool_comparison(tmp_path)
    (tmp_path / "manuscript").mkdir()

    exit_code = script.main(["--root", str(tmp_path)])

    assert exit_code == 0
    assert (
        tmp_path / "manuscript" / "comparator_scope" / "COMPARATOR_SCOPE_AUDIT.tsv"
    ).exists()
    assert (
        tmp_path / "manuscript" / "comparator_scope" / "COMPARATOR_SCOPE_REPORT.md"
    ).exists()
