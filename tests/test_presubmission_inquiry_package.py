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


def _fixture_tables():
    public_summary = pd.DataFrame(
        [
            {
                "dataset_id": "gse154778_pdac_scrna",
                "modality": "scRNA-seq",
                "status": "completed",
                "top_frustration_cell_type": "Myeloid",
            }
        ]
    )
    tool_comparison = pd.DataFrame(
        [
            {
                "dataset_id": "gse154778_pdac_scrna",
                "tool": "LIANA",
                "status": "completed_external_import",
            },
            {
                "dataset_id": "gse154778_pdac_scrna",
                "tool": "NicheNet",
                "status": "completed_external_import",
            },
        ]
    )
    return public_summary, tool_comparison


def test_presubmission_letter_preserves_boundaries():
    script = _load_script("build_presubmission_inquiry_package")
    public_summary, tool_comparison = _fixture_tables()

    letter = script.build_inquiry_letter(public_summary, tool_comparison)
    boundary = script.build_claim_boundary_note()
    combined = letter + "\n" + boundary

    assert "Nature Methods" in letter
    assert "sheaf-valued flow" in letter
    assert "do not claim clinical utility" in letter.lower()
    assert "guaranteed acceptance" in combined
    assert "broad superiority" in combined


def test_triage_risk_table_contains_zenodo_and_comparator_risks():
    script = _load_script("build_presubmission_inquiry_package")
    table = script.build_triage_risk_table()

    assert {"risk_id", "editorial_risk", "risk_level", "current_mitigation"}.issubset(table.columns)
    assert table["editorial_risk"].str.contains("Comparator", case=False).any()
    assert table["remaining_action"].str.contains("Zenodo DOI").any()


def test_presubmission_package_writes_expected_files(tmp_path):
    script = _load_script("build_presubmission_inquiry_package")
    public_summary, tool_comparison = _fixture_tables()
    public_path = tmp_path / "public.csv"
    tool_path = tmp_path / "tools.csv"
    public_summary.to_csv(public_path, index=False)
    tool_comparison.to_csv(tool_path, index=False)

    out_dir = tmp_path / "manuscript" / "presubmission_inquiry"
    exit_code = script.main(
        [
            "--output-dir",
            str(out_dir),
            "--public-summary",
            str(public_path),
            "--tool-comparison",
            str(tool_path),
        ]
    )

    assert exit_code == 0
    expected = set(script.OUTPUT_FILES.values())
    observed = {path.name for path in out_dir.iterdir()}
    assert expected.issubset(observed)
    assert "One-Page Editor Summary" in (out_dir / "00_one_page_editor_summary.md").read_text(
        encoding="utf-8"
    )
