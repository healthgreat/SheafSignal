from pathlib import Path
import importlib.util

import pandas as pd


def _load_script():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "check_main_figure_quality.py"
    spec = importlib.util.spec_from_file_location("check_main_figure_quality", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_pdf(path: Path, text: str = "Figure 1 evidence-linked panel") -> None:
    import fitz

    doc = fitz.open()
    page = doc.new_page(width=360, height=260)
    page.insert_text((48, 80), text, fontsize=12)
    page.insert_text((48, 110), "Renderable PDF with source-map boundary.", fontsize=10)
    doc.save(path)
    doc.close()


def test_main_figure_quality_passes_renderable_pdf_with_source_boundary(tmp_path):
    script = _load_script()
    figures = tmp_path / "figures"
    manuscript = tmp_path / "manuscript"
    legends = manuscript / "figure_legends"
    figures.mkdir()
    legends.mkdir(parents=True)
    pdf = figures / "figure1.pdf"
    _write_pdf(pdf)
    pd.DataFrame(
        [
            {
                "figure_id": "fig1_test",
                "path": pdf.relative_to(tmp_path).as_posix(),
                "source_results_dir": "benchmarks/results",
            }
        ]
    ).to_csv(manuscript / "figure_manifest.tsv", sep="\t", index=False)
    pd.DataFrame(
        [
            {
                "display_item": "Figure 1",
                "claim_ids": "C1",
                "source_files": "figures/figure1.pdf",
                "allowed_claim": "Test allowed claim.",
                "boundary": "Do not overclaim from this test figure.",
                "main_text_allowed": True,
            }
        ]
    ).to_csv(legends / "03_figure_source_map.tsv", sep="\t", index=False)

    audit = script.build_figure_quality_audit(
        root=tmp_path,
        figure_manifest_path=manuscript / "figure_manifest.tsv",
        source_map_path=legends / "03_figure_source_map.tsv",
    )
    report = script.build_figure_quality_report(audit)

    assert audit.iloc[0]["status"] == "pass"
    assert audit.iloc[0]["page_count"] == 1
    assert bool(audit.iloc[0]["source_map_found"]) is True
    assert "MAIN_FIGURE_QUALITY_PASS" in report


def test_main_figure_quality_fails_missing_source_map_boundary(tmp_path):
    script = _load_script()
    figures = tmp_path / "figures"
    manuscript = tmp_path / "manuscript"
    legends = manuscript / "figure_legends"
    figures.mkdir()
    legends.mkdir(parents=True)
    pdf = figures / "figure1.pdf"
    _write_pdf(pdf)
    pd.DataFrame(
        [
            {
                "figure_id": "fig1_test",
                "path": pdf.relative_to(tmp_path).as_posix(),
                "source_results_dir": "benchmarks/results",
            }
        ]
    ).to_csv(manuscript / "figure_manifest.tsv", sep="\t", index=False)
    pd.DataFrame(
        [
            {
                "display_item": "Figure 1",
                "claim_ids": "C1",
                "source_files": "figures/figure1.pdf",
                "allowed_claim": "Test allowed claim.",
                "boundary": "",
                "main_text_allowed": True,
            }
        ]
    ).to_csv(legends / "03_figure_source_map.tsv", sep="\t", index=False)

    audit = script.build_figure_quality_audit(
        root=tmp_path,
        figure_manifest_path=manuscript / "figure_manifest.tsv",
        source_map_path=legends / "03_figure_source_map.tsv",
    )

    assert audit.iloc[0]["status"] == "fail"
    assert audit.iloc[0]["notes"] == "source-map boundary is missing"


def test_main_figure_quality_main_writes_outputs_atomically(tmp_path):
    script = _load_script()
    figures = tmp_path / "figures"
    manuscript = tmp_path / "manuscript"
    legends = manuscript / "figure_legends"
    figures.mkdir()
    legends.mkdir(parents=True)
    pdf = figures / "figure1.pdf"
    _write_pdf(pdf)
    pd.DataFrame(
        [
            {
                "figure_id": "fig1_test",
                "path": pdf.relative_to(tmp_path).as_posix(),
                "source_results_dir": "benchmarks/results",
            }
        ]
    ).to_csv(manuscript / "figure_manifest.tsv", sep="\t", index=False)
    pd.DataFrame(
        [
            {
                "display_item": "Figure 1",
                "claim_ids": "C1",
                "source_files": "figures/figure1.pdf",
                "allowed_claim": "Test allowed claim.",
                "boundary": "Do not overclaim from this test figure.",
                "main_text_allowed": True,
            }
        ]
    ).to_csv(legends / "03_figure_source_map.tsv", sep="\t", index=False)

    exit_code = script.main(["--root", str(tmp_path)])

    assert exit_code == 0
    audit_path = manuscript / "figure_quality" / "MAIN_FIGURE_QUALITY_AUDIT.tsv"
    report_path = manuscript / "figure_quality" / "MAIN_FIGURE_QUALITY_REPORT.md"
    assert audit_path.exists()
    assert report_path.exists()
    assert not audit_path.with_suffix(audit_path.suffix + ".tmp").exists()
    assert "MAIN_FIGURE_QUALITY_PASS" in report_path.read_text(encoding="utf-8")
