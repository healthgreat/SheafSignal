from pathlib import Path
import importlib.util

import pandas as pd


def _load_script(name: str):
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_claim_safety_distinguishes_positive_and_boundary_lines():
    script = _load_script("check_claim_safety")

    blocking = script.classify_line("SheafSignal demonstrates clinical utility in PDAC.")
    safe = script.classify_line("SheafSignal does not claim clinical utility in PDAC.")
    review = script.classify_line("Clinical utility will be evaluated in future work.")

    assert blocking[1] == "blocking_positive_claim"
    assert safe[1] == "safe_boundary_statement"
    assert review[1] == "needs_author_review"


def test_claim_safety_audit_scans_manuscript_files(tmp_path):
    script = _load_script("check_claim_safety")
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "safe.md").write_text(
        "This report does not guarantee journal acceptance.\n",
        encoding="utf-8",
    )
    (manuscript / "bad.md").write_text(
        "This method guides treatment selection.\n",
        encoding="utf-8",
    )

    audit = script.build_claim_safety_audit(tmp_path, manuscript)

    assert {"safe_boundary_statement", "blocking_positive_claim"}.issubset(
        set(audit["classification"])
    )
    bad = audit.loc[audit["relative_path"] == "manuscript/bad.md"].iloc[0]
    assert bad["trigger"] == "treatment_guidance_positive"


def test_claim_safety_main_report_only_writes_outputs(tmp_path):
    script = _load_script("check_claim_safety")
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "draft.md").write_text(
        "This method outperforms all CCC tools.\n",
        encoding="utf-8",
    )

    exit_code = script.main(["--root", str(tmp_path), "--report-only"])

    assert exit_code == 0
    audit_path = tmp_path / "manuscript" / "CLAIM_SAFETY_AUDIT.tsv"
    report_path = tmp_path / "manuscript" / "CLAIM_SAFETY_AUDIT_REPORT.md"
    assert audit_path.exists()
    assert report_path.exists()
    audit = pd.read_csv(audit_path, sep="\t")
    assert "blocking_positive_claim" in set(audit["classification"])
    assert "CLAIM_SAFETY_BLOCKED" in report_path.read_text(encoding="utf-8")
