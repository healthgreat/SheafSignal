from pathlib import Path
import importlib.util

import pandas as pd


def _load_script():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "check_supplementary_artifacts.py"
    spec = importlib.util.spec_from_file_location("check_supplementary_artifacts", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_pdf(path: Path) -> None:
    import fitz

    doc = fitz.open()
    page = doc.new_page(width=360, height=260)
    page.insert_text((40, 80), "Supplementary figure", fontsize=12)
    doc.save(path)
    doc.close()


def _write_source_map(path: Path, boundary: str = "Supplementary boundary.") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "display_item": "Supplementary figures and tables",
                "claim_ids": "C5",
                "source_files": "manuscript/figure_manifest.tsv",
                "allowed_claim": "Supplementary artifacts document QC.",
                "boundary": boundary,
                "main_text_allowed": False,
            }
        ]
    ).to_csv(path, sep="\t", index=False)


def test_supplementary_artifact_audit_passes_mixed_artifacts(tmp_path):
    script = _load_script()
    figures = tmp_path / "figures"
    tables = tmp_path / "tables"
    manuscript = tmp_path / "manuscript"
    figures.mkdir()
    tables.mkdir()
    manuscript.mkdir()
    pdf = figures / "supp.pdf"
    table = tables / "supp.csv"
    note = manuscript / "note.md"
    _write_pdf(pdf)
    pd.DataFrame([{"a": 1, "b": 2}]).to_csv(table, index=False)
    note.write_text("# Supplement\n\nBoundary text.\n", encoding="utf-8")
    pd.DataFrame(
        [
            {
                "figure_id": "fig1_main",
                "path": "figures/main.pdf",
                "source_results_dir": "figures",
            },
            {
                "figure_id": "supp_pdf",
                "path": pdf.relative_to(tmp_path).as_posix(),
                "source_results_dir": "figures",
            },
            {
                "figure_id": "supp_table",
                "path": table.relative_to(tmp_path).as_posix(),
                "source_results_dir": "tables",
            },
            {
                "figure_id": "supp_note",
                "path": note.relative_to(tmp_path).as_posix(),
                "source_results_dir": "manuscript",
            },
        ]
    ).to_csv(manuscript / "figure_manifest.tsv", sep="\t", index=False)
    _write_source_map(manuscript / "figure_legends" / "03_figure_source_map.tsv")

    audit = script.build_supplementary_artifact_audit(
        root=tmp_path,
        figure_manifest_path=manuscript / "figure_manifest.tsv",
        source_map_path=manuscript / "figure_legends" / "03_figure_source_map.tsv",
    )
    report = script.build_supplementary_artifact_report(audit)

    assert len(audit) == 3
    assert set(audit["status"]) == {"pass"}
    assert "SUPPLEMENTARY_ARTIFACTS_PASS" in report


def test_supplementary_artifact_audit_fails_missing_file(tmp_path):
    script = _load_script()
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    pd.DataFrame(
        [
            {
                "figure_id": "supp_missing",
                "path": "tables/missing.csv",
                "source_results_dir": "manuscript",
            }
        ]
    ).to_csv(manuscript / "figure_manifest.tsv", sep="\t", index=False)
    _write_source_map(manuscript / "figure_legends" / "03_figure_source_map.tsv")

    audit = script.build_supplementary_artifact_audit(
        root=tmp_path,
        figure_manifest_path=manuscript / "figure_manifest.tsv",
        source_map_path=manuscript / "figure_legends" / "03_figure_source_map.tsv",
    )

    assert audit.iloc[0]["status"] == "fail"
    assert audit.iloc[0]["notes"] == "supplementary artifact is missing"


def test_supplementary_artifact_main_writes_outputs_atomically(tmp_path):
    script = _load_script()
    tables = tmp_path / "tables"
    manuscript = tmp_path / "manuscript"
    tables.mkdir()
    manuscript.mkdir()
    table = tables / "supp.tsv"
    pd.DataFrame([{"a": 1}]).to_csv(table, sep="\t", index=False)
    pd.DataFrame(
        [
            {
                "figure_id": "supp_table",
                "path": table.relative_to(tmp_path).as_posix(),
                "source_results_dir": "tables",
            }
        ]
    ).to_csv(manuscript / "figure_manifest.tsv", sep="\t", index=False)
    _write_source_map(manuscript / "figure_legends" / "03_figure_source_map.tsv")

    exit_code = script.main(["--root", str(tmp_path)])

    assert exit_code == 0
    audit_path = (
        manuscript / "supplementary_quality" / "SUPPLEMENTARY_ARTIFACT_AUDIT.tsv"
    )
    report_path = (
        manuscript / "supplementary_quality" / "SUPPLEMENTARY_ARTIFACT_REPORT.md"
    )
    assert audit_path.exists()
    assert report_path.exists()
    assert not audit_path.with_suffix(audit_path.suffix + ".tmp").exists()
    assert "SUPPLEMENTARY_ARTIFACTS_PASS" in report_path.read_text(encoding="utf-8")
