from pathlib import Path
import importlib.util

import pandas as pd


def _load_script():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "check_method_reporting_readiness.py"
    spec = importlib.util.spec_from_file_location(
        "check_method_reporting_readiness", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_fixture(root: Path) -> None:
    (root / "manuscript" / "nature_methods_package").mkdir(parents=True)
    (root / "manuscript" / "figure_quality").mkdir(parents=True)
    (root / "manuscript" / "supplementary_quality").mkdir(parents=True)
    (root / "manuscript" / "provenance").mkdir(parents=True)
    (root / "manuscript" / "references").mkdir(parents=True)
    (root / "manuscript" / "submission_upload_package").mkdir(parents=True)
    (root / "benchmarks" / "results" / "gse154778_pdac_scrna" / "qc").mkdir(
        parents=True
    )
    (
        root
        / "benchmarks"
        / "results"
        / "tenx_breast_visium"
        / "spatial"
        / "qc"
    ).mkdir(parents=True)
    (root / "metadata").mkdir()
    (root / "release").mkdir()

    method_terms = (
        "sheaf-valued flow Hodge decomposition sheaf_energy gradient_ratio "
        "curl_ratio harmonic_ratio frustration_score"
    )
    (root / "README.md").write_text(method_terms, encoding="utf-8")
    (root / "manuscript" / "SCI_MANUSCRIPT_V2_POLISHED.md").write_text(
        "SheafSignal methods manuscript.",
        encoding="utf-8",
    )
    (
        root / "manuscript" / "nature_methods_package" / "04_methods_skeleton.md"
    ).write_text(method_terms, encoding="utf-8")

    pd.DataFrame(
        [
            {"scenario": "gradient_chain"},
            {"scenario": "triangle_curl"},
            {"scenario": "harmonic_ring"},
            {"scenario": "mixed"},
        ]
    ).to_csv(root / "benchmarks" / "results" / "component_recovery.csv", index=False)

    dataset_rows = []
    for dataset_id in [
        "gse72056_melanoma_scrna",
        "gse154778_pdac_scrna",
        "gse176078_brca_scrna",
        "tenx_breast_visium",
    ]:
        dataset_rows.append(
            {
                "dataset_id": dataset_id,
                "benchmark_role": "public_scrna_benchmark",
                "accession_or_doi": dataset_id,
                "download_url": "https://example.org/file",
                "sha256": "a" * 64,
                "license_or_terms": "public processed data",
                "prepared_expression": f"data/processed/{dataset_id}/expression.csv",
                "prepared_metadata": f"data/processed/{dataset_id}/metadata.csv",
                "zenodo_doi": "PENDING_ZENODO_RELEASE",
            }
        )
    pd.DataFrame(dataset_rows).to_csv(
        root / "metadata" / "datasets.tsv", sep="\t", index=False
    )

    pd.DataFrame(
        [
            {"dataset_id": dataset_id, "status": "completed"}
            for dataset_id in [
                "gse72056_melanoma_scrna",
                "gse154778_pdac_scrna",
                "gse176078_brca_scrna",
                "tenx_breast_visium",
            ]
        ]
    ).to_csv(root / "benchmarks" / "results" / "public_tme_sheafsignal_summary.csv")

    tool_rows = []
    for tool in ["LIANA", "NicheNet", "MechanisticTargetPrior"]:
        for dataset_id in [
            "gse72056_melanoma_scrna",
            "gse154778_pdac_scrna",
            "gse176078_brca_scrna",
        ]:
            tool_rows.append(
                {"tool": tool, "dataset_id": dataset_id, "status": "completed"}
            )
    for dataset_id in [
        "gse72056_melanoma_scrna",
        "gse154778_pdac_scrna",
        "gse176078_brca_scrna",
        "tenx_breast_visium",
    ]:
        tool_rows.append(
            {"tool": "LRProductBaseline", "dataset_id": dataset_id, "status": "completed"}
        )
    pd.DataFrame(tool_rows).to_csv(
        root / "benchmarks" / "results" / "tool_comparison.csv", index=False
    )

    pd.DataFrame(
        [
            {"cell_type": "Myeloid", "claim_gate": "supplement_only"},
            {"cell_type": "CAF/Fibroblast", "claim_gate": "qc_warning_only"},
        ]
    ).to_csv(
        root
        / "benchmarks"
        / "results"
        / "gse154778_pdac_scrna"
        / "qc"
        / "claim_gating_by_cell_type.csv",
        index=False,
    )
    pd.DataFrame(
        [
            {"spearman_with_reference": 0.93, "top_50_overlap_with_reference": 0.86},
            {"spearman_with_reference": 1.0, "top_50_overlap_with_reference": 1.0},
        ]
    ).to_csv(
        root
        / "benchmarks"
        / "results"
        / "tenx_breast_visium"
        / "spatial"
        / "qc"
        / "k_neighbors_sensitivity.csv",
        index=False,
    )
    pd.DataFrame([{"figure_id": "fig1", "status": "pass"}]).to_csv(
        root / "manuscript" / "figure_quality" / "MAIN_FIGURE_QUALITY_AUDIT.tsv",
        sep="\t",
        index=False,
    )
    pd.DataFrame([{"artifact_id": "supp1", "status": "pass"}]).to_csv(
        root
        / "manuscript"
        / "supplementary_quality"
        / "SUPPLEMENTARY_ARTIFACT_AUDIT.tsv",
        sep="\t",
        index=False,
    )
    pd.DataFrame([{"check_id": "component_recovery_schema", "status": "pass"}]).to_csv(
        root
        / "benchmarks"
        / "results"
        / "BENCHMARK_RESULT_CONTRACT_AUDIT.tsv",
        sep="\t",
        index=False,
    )
    pd.DataFrame([{"artifact_id": "main", "status": "pass"}]).to_csv(
        root / "manuscript" / "provenance" / "SUBMISSION_PROVENANCE_AUDIT.tsv",
        sep="\t",
        index=False,
    )
    (root / "manuscript" / "CLAIM_SAFETY_AUDIT_REPORT.md").write_text(
        "Blocking positive claims: 0\n",
        encoding="utf-8",
    )
    (root / "manuscript" / "references" / "SCI_REFERENCE_GAP_REPORT.md").write_text(
        "Decision: `REFERENCE_PLACEHOLDERS_RESOLVED`\n",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {"archive_target": "github", "sha256": "a" * 64},
            {"archive_target": "zenodo", "sha256": "b" * 64},
        ]
    ).to_csv(root / "release" / "archive_manifest.tsv", sep="\t", index=False)
    for name in [
        "SheafSignal_main_manuscript_v2.docx",
        "SheafSignal_cover_letter_NatureMethods.docx",
        "SheafSignal_supplementary_information.docx",
        "submission_upload_preflight_checklist.tsv",
    ]:
        (root / "manuscript" / "submission_upload_package" / name).write_text(
            "ok\n",
            encoding="utf-8",
        )


def test_method_reporting_audit_passes_with_external_zenodo_pending(tmp_path):
    script = _load_script()
    _write_fixture(tmp_path)

    audit = script.build_method_reporting_audit(tmp_path)
    report = script.build_method_reporting_report(
        audit,
        script.build_reviewer_risk_register(audit),
    )

    statuses = dict(zip(audit["check_id"], audit["status"]))
    assert "fail" not in set(audit["status"])
    assert statuses["public_tme_benchmarks_completed"] == "pass"
    assert statuses["supplementary_artifacts_manifest_readable"] == "pass"
    assert statuses["benchmark_result_contracts_valid"] == "pass"
    assert statuses["submission_provenance_traceable"] == "pass"
    assert statuses["zenodo_doi_external_release"] == "pending_external"
    assert "METHOD_REPORTING_PASS_WITH_BOUNDARY_NOTES" in report


def test_method_reporting_audit_fails_when_any_gse154778_main_claim_remains(tmp_path):
    script = _load_script()
    _write_fixture(tmp_path)
    pd.DataFrame(
        [
            {"cell_type": "Myeloid", "claim_gate": "supplement_only"},
            {"cell_type": "CAF/Fibroblast", "claim_gate": "main_claim"},
        ]
    ).to_csv(
        tmp_path
        / "benchmarks"
        / "results"
        / "gse154778_pdac_scrna"
        / "qc"
        / "claim_gating_by_cell_type.csv",
        index=False,
    )

    audit = script.build_method_reporting_audit(tmp_path)
    row = audit.loc[
        audit["check_id"] == "gse154778_claim_gate_no_unvalidated_main_source"
    ].iloc[0]

    assert row["status"] == "fail"
    assert "CAF/Fibroblast" in row["evidence"]


def test_method_reporting_main_writes_all_outputs(tmp_path):
    script = _load_script()
    _write_fixture(tmp_path)

    exit_code = script.main(["--root", str(tmp_path)])

    assert exit_code == 0
    output_dir = tmp_path / "manuscript" / "method_reporting"
    assert (output_dir / "METHOD_REPORTING_AUDIT.tsv").exists()
    assert (output_dir / "METHOD_REPORTING_REPORT.md").exists()
    assert (output_dir / "REVIEWER_RISK_REGISTER.tsv").exists()
    assert (output_dir / "REVIEWER_RISK_REPORT.md").exists()
    text = (
        output_dir / "REVIEWER_RISK_REPORT.md"
    ).read_text(encoding="utf-8")
    assert "RR4_comparator_scope" in text
    assert "RR9_supplementary_artifact_completeness" in text
    assert "RR10_result_table_integrity" in text
    assert "RR11_artifact_provenance" in text
