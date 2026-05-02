from pathlib import Path
import importlib.util

import pandas as pd


def _load_script():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "check_submission_provenance.py"
    spec = importlib.util.spec_from_file_location("check_submission_provenance", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_submission_provenance_static_rows_pass_generated_artifact(tmp_path):
    script = _load_script()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "manuscript").mkdir()
    (tmp_path / "benchmarks" / "results").mkdir(parents=True)
    generator = tmp_path / "scripts" / "make_publication_figures.py"
    artifact = tmp_path / "manuscript" / "figure_manifest.tsv"
    source = tmp_path / "benchmarks" / "results"
    generator.write_text("print('ok')\n", encoding="utf-8")
    artifact.write_text("figure_id\tpath\n", encoding="utf-8")

    rows = script._static_rows(tmp_path)
    row = next(item for item in rows if item["artifact_id"] == "publication_figures_manifest")

    assert row["artifact_exists"] is True
    assert row["generator_exists"] is True
    assert source.exists()
    assert row["status"] == "pass"


def test_submission_provenance_marks_external_pending(tmp_path):
    script = _load_script()
    (tmp_path / "metadata").mkdir()
    (tmp_path / "release" / "archives").mkdir(parents=True)
    (tmp_path / "metadata" / "datasets.tsv").write_text("dataset_id\n", encoding="utf-8")
    (tmp_path / "release" / "archives" / "sheafsignal_zenodo_upload.zip").write_bytes(
        b"zip"
    )

    rows = script._static_rows(tmp_path)
    row = next(item for item in rows if item["artifact_id"] == "zenodo_doi")

    assert row["status"] == "pending_external"


def test_submission_provenance_upload_manifest_rows_detect_missing_source(tmp_path):
    script = _load_script()
    package = tmp_path / "manuscript" / "submission_upload_package"
    package.mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "build_submission_upload_package.py").write_text(
        "print('ok')\n",
        encoding="utf-8",
    )
    artifact = package / "main.docx"
    artifact.write_bytes(b"docx")
    pd.DataFrame(
        [
            {
                "upload_item": "main",
                "file_path": artifact.relative_to(tmp_path).as_posix(),
                "source_path": "manuscript/missing.md",
            }
        ]
    ).to_csv(package / "submission_upload_manifest.tsv", sep="\t", index=False)

    rows = script._upload_manifest_rows(tmp_path)

    assert rows[0]["status"] == "fail"
    assert rows[0]["missing_sources"] == "manuscript/missing.md"


def test_submission_provenance_main_writes_outputs_with_report_only(tmp_path):
    script = _load_script()

    exit_code = script.main(["--root", str(tmp_path), "--report-only"])

    assert exit_code == 0
    audit_path = tmp_path / "manuscript" / "provenance" / "SUBMISSION_PROVENANCE_AUDIT.tsv"
    report_path = tmp_path / "manuscript" / "provenance" / "SUBMISSION_PROVENANCE_REPORT.md"
    assert audit_path.exists()
    assert report_path.exists()
    assert not audit_path.with_suffix(audit_path.suffix + ".tmp").exists()
    assert "SUBMISSION_PROVENANCE" in report_path.read_text(encoding="utf-8")
