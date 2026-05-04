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


def _write_required_files(root: Path, script) -> None:
    for rel in [
        *script.REQUIRED_NATURE_METHODS_FILES,
        *script.REQUIRED_RELEASE_FILES,
        *script.REQUIRED_SUBMISSION_METADATA_FILES,
        *script.REQUIRED_RESPONSE_TRANSFER_FILES,
        *script.REQUIRED_FIGURE_LEGEND_FILES,
        *script.REQUIRED_FIGURE_QUALITY_FILES,
        *script.REQUIRED_SUPPLEMENTARY_QUALITY_FILES,
        *script.REQUIRED_BENCHMARK_CONTRACT_FILES,
        *script.REQUIRED_SUBMISSION_PROVENANCE_FILES,
        *script.REQUIRED_METHOD_REPORTING_FILES,
        *script.REQUIRED_CLAIM_SAFETY_FILES,
        *script.REQUIRED_FORMAL_MANUSCRIPT_FILES,
        *script.REQUIRED_REFERENCE_FILES,
        *script.REQUIRED_POLISHED_MANUSCRIPT_FILES,
        *script.REQUIRED_SUBMISSION_UPLOAD_FILES,
    ]:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok\n", encoding="utf-8")
    pd.DataFrame([{"check_id": "title_length", "status": "pass"}]).to_csv(
        root / "manuscript" / "NATURE_METHODS_FORMAT_AUDIT.tsv",
        sep="\t",
        index=False,
    )


def test_final_submission_blockers_flags_pending_zenodo(tmp_path):
    script = _load_script("check_final_submission_blockers")
    _write_required_files(tmp_path, script)
    (tmp_path / "metadata").mkdir(exist_ok=True)
    pd.DataFrame(
        [
            {
                "dataset_id": "gse154778_pdac_scrna",
                "benchmark_role": "public_scrna_benchmark",
                "zenodo_doi": "PENDING_ZENODO_RELEASE",
            }
        ]
    ).to_csv(tmp_path / "metadata" / "datasets.tsv", sep="\t", index=False)
    (tmp_path / "release" / "DATA_AVAILABILITY_STATEMENT_DRAFT.md").write_text(
        "Current DOI status: `PENDING_ZENODO_RELEASE`.\n",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "item": "Zenodo DOI minted",
                "status": "blocking_pending",
                "evidence_or_action": "Mint DOI.",
            }
        ]
    ).to_csv(
        tmp_path
        / "manuscript"
        / "nature_methods_package"
        / "07_submission_checklist.tsv",
        sep="\t",
        index=False,
    )

    blockers = script.build_blocker_table(tmp_path)

    blocking_ids = set(blockers.loc[blockers["severity"] == "blocking", "blocker_id"])
    assert "zenodo_doi::dataset_manifest" in blocking_ids
    assert "zenodo_doi::data_availability_statement" in blocking_ids
    assert "checklist::Zenodo DOI minted" in blocking_ids


def test_final_submission_go_report_returns_no_go_for_blockers(tmp_path):
    script = _load_script("check_final_submission_blockers")
    blockers = pd.DataFrame(
        [
            {
                "blocker_id": "zenodo_doi::dataset_manifest",
                "severity": "blocking",
                "status": "pending",
                "evidence": "gse154778",
                "required_action": "Mint DOI.",
            },
            {
                "blocker_id": "checklist::author metadata",
                "severity": "pending",
                "status": "tbd_by_authors",
                "evidence": "Authors fill metadata.",
                "required_action": "Authors fill metadata.",
            },
        ]
    )

    report = script.build_go_no_go_report(blockers)

    assert "Decision: `NO_GO`" in report
    assert "Blocking items: 1" in report
    assert "does not guarantee journal acceptance" in report


def test_final_submission_blockers_use_claim_safety_audit(tmp_path):
    script = _load_script("check_final_submission_blockers")
    path = tmp_path / "manuscript" / "CLAIM_SAFETY_AUDIT.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "relative_path": "manuscript/draft.md",
                "line_no": 1,
                "trigger": "clinical_utility_positive",
                "classification": "blocking_positive_claim",
                "matched_text": "SheafSignal demonstrates clinical utility.",
                "required_action": "Rewrite.",
            }
        ]
    ).to_csv(path, sep="\t", index=False)

    rows = script.check_claim_safety_audit(tmp_path)
    table = pd.DataFrame(rows)

    assert "claim_safety_audit::manuscript_wide" in set(table["blocker_id"])
    assert table.iloc[0]["severity"] == "blocking"


def test_final_submission_blockers_use_reference_gap_report(tmp_path):
    script = _load_script("check_final_submission_blockers")
    path = tmp_path / "manuscript" / "references" / "SCI_REFERENCE_GAP_REPORT.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Decision: `REFERENCE_GAPS_FOUND`\n", encoding="utf-8")

    rows = script.check_reference_gap_report(tmp_path)
    table = pd.DataFrame(rows)

    assert "reference_gap_report::placeholders" in set(table["blocker_id"])
    assert table.iloc[0]["severity"] == "blocking"


def test_final_submission_blockers_use_main_figure_quality_audit(tmp_path):
    script = _load_script("check_final_submission_blockers")
    path = tmp_path / "manuscript" / "figure_quality" / "MAIN_FIGURE_QUALITY_AUDIT.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "figure_id": "fig1",
                "status": "fail",
                "notes": "source-map boundary is missing",
            }
        ]
    ).to_csv(path, sep="\t", index=False)

    rows = script.check_main_figure_quality(tmp_path)
    table = pd.DataFrame(rows)

    assert "main_figure_quality::pdfs_and_source_boundaries" in set(
        table["blocker_id"]
    )
    assert table.iloc[0]["severity"] == "blocking"


def test_final_submission_blockers_use_method_reporting_audit(tmp_path):
    script = _load_script("check_final_submission_blockers")
    path = (
        tmp_path
        / "manuscript"
        / "method_reporting"
        / "METHOD_REPORTING_AUDIT.tsv"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "check_id": "public_dataset_manifest_complete",
                "status": "fail",
                "evidence": "missing checksum",
            }
        ]
    ).to_csv(path, sep="\t", index=False)

    rows = script.check_method_reporting_readiness(tmp_path)
    table = pd.DataFrame(rows)

    assert "method_reporting::local_readiness" in set(table["blocker_id"])
    assert table.iloc[0]["severity"] == "blocking"


def test_final_submission_blockers_use_supplementary_artifact_audit(tmp_path):
    script = _load_script("check_final_submission_blockers")
    path = (
        tmp_path
        / "manuscript"
        / "supplementary_quality"
        / "SUPPLEMENTARY_ARTIFACT_AUDIT.tsv"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "artifact_id": "supp_missing",
                "status": "fail",
                "notes": "supplementary artifact is missing",
            }
        ]
    ).to_csv(path, sep="\t", index=False)

    rows = script.check_supplementary_artifact_quality(tmp_path)
    table = pd.DataFrame(rows)

    assert "supplementary_artifacts::manifest_readability" in set(
        table["blocker_id"]
    )
    assert table.iloc[0]["severity"] == "blocking"


def test_final_submission_blockers_use_benchmark_result_contract_audit(tmp_path):
    script = _load_script("check_final_submission_blockers")
    path = (
        tmp_path
        / "benchmarks"
        / "results"
        / "BENCHMARK_RESULT_CONTRACT_AUDIT.tsv"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "check_id": "component_recovery_metric_contract",
                "status": "fail",
                "evidence": "bad dominant component",
            }
        ]
    ).to_csv(path, sep="\t", index=False)

    rows = script.check_benchmark_result_contracts(tmp_path)
    table = pd.DataFrame(rows)

    assert "benchmark_result_contracts::tables_and_links" in set(table["blocker_id"])
    assert table.iloc[0]["severity"] == "blocking"


def test_final_submission_blockers_use_external_beta_review_action_matrix(tmp_path):
    script = _load_script("check_final_submission_blockers")
    path = tmp_path / "external_ai_review_packet" / "external_beta_review_action_matrix.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "priority": "P0",
                "domain": "methods",
                "severity": "fatal",
                "finding": "Simulation benchmark is circular.",
                "suggested_action": "Fix benchmark.",
                "owner": "codex_or_authors",
                "status": "open_external_review_item",
                "blocks_20_50_if": "yes",
                "source_file": "reviewer4_code_review.md",
            }
        ]
    ).to_csv(path, sep="\t", index=False)

    rows = script.check_external_beta_review_gate(tmp_path)
    table = pd.DataFrame(rows)

    assert "external_beta_review::returned_findings" in set(table["blocker_id"])
    assert table.iloc[0]["severity"] == "blocking"


def test_final_submission_blockers_use_submission_provenance_audit(tmp_path):
    script = _load_script("check_final_submission_blockers")
    path = (
        tmp_path
        / "manuscript"
        / "provenance"
        / "SUBMISSION_PROVENANCE_AUDIT.tsv"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "artifact_id": "main_manuscript",
                "status": "fail",
                "notes": "artifact is missing",
            }
        ]
    ).to_csv(path, sep="\t", index=False)

    rows = script.check_submission_provenance(tmp_path)
    table = pd.DataFrame(rows)

    assert "submission_provenance::local_traceability" in set(table["blocker_id"])
    assert table.iloc[0]["severity"] == "blocking"


def test_final_submission_script_report_only_writes_outputs(tmp_path):
    script = _load_script("check_final_submission_blockers")
    _write_required_files(tmp_path, script)
    (tmp_path / "metadata").mkdir(exist_ok=True)
    pd.DataFrame(
        [
            {
                "dataset_id": "gse154778_pdac_scrna",
                "benchmark_role": "public_scrna_benchmark",
                "zenodo_doi": "PENDING_ZENODO_RELEASE",
            }
        ]
    ).to_csv(tmp_path / "metadata" / "datasets.tsv", sep="\t", index=False)
    (tmp_path / "release" / "DATA_AVAILABILITY_STATEMENT_DRAFT.md").write_text(
        "Current DOI status: `PENDING_ZENODO_RELEASE`.\n",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "item": "Zenodo DOI minted",
                "status": "blocking_pending",
                "evidence_or_action": "Mint DOI.",
            }
        ]
    ).to_csv(
        tmp_path
        / "manuscript"
        / "nature_methods_package"
        / "07_submission_checklist.tsv",
        sep="\t",
        index=False,
    )

    exit_code = script.main(["--root", str(tmp_path), "--report-only"])

    assert exit_code == 0
    assert (tmp_path / "manuscript" / "FINAL_SUBMISSION_BLOCKERS.tsv").exists()
    assert (tmp_path / "manuscript" / "NATURE_METHODS_GO_NO_GO_REPORT.md").exists()
