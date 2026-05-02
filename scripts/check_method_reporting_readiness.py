#!/usr/bin/env python
"""Audit method-reporting readiness for the SheafSignal manuscript package.

Author: SheafSignal contributors
Date: 2026-05-01
Purpose: collect reviewer-facing method, benchmark, comparator, claim-boundary,
and release-readiness checks into machine-readable reports before submission.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_table_atomic(path: Path, table: pd.DataFrame) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    table.to_csv(tmp_path, sep="\t", index=False)
    tmp_path.replace(path)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _read_table(path: Path, sep: str = ",") -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep=sep)


def _add_check(
    rows: list[dict[str, str]],
    *,
    check_id: str,
    domain: str,
    status: str,
    evidence: str,
    required_action: str,
) -> None:
    rows.append(
        {
            "check_id": check_id,
            "domain": domain,
            "status": status,
            "evidence": evidence,
            "required_action": required_action,
        }
    )


def _required_present(table: pd.DataFrame, columns: list[str]) -> bool:
    if table.empty:
        return False
    if any(column not in table.columns for column in columns):
        return False
    subset = table[columns].astype(str)
    invalid = subset.apply(
        lambda col: col.str.strip().isin(["", "NA", "nan", "PENDING_DOWNLOAD_VERIFICATION"])
    )
    return not bool(invalid.any().any())


def _status_for_required_files(root: Path, rel_paths: list[str]) -> tuple[str, str]:
    missing = [rel for rel in rel_paths if not (root / rel).exists()]
    if missing:
        return "fail", ";".join(missing)
    return "pass", ";".join(rel_paths)


def build_method_reporting_audit(root: Path) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    manuscript_text = "\n".join(
        [
            _read_text(root / "manuscript/SCI_MANUSCRIPT_V2_POLISHED.md"),
            _read_text(root / "manuscript/nature_methods_package/04_methods_skeleton.md"),
            _read_text(root / "README.md"),
        ]
    )

    required_terms = [
        "sheaf-valued flow",
        "Hodge decomposition",
        "sheaf_energy",
        "gradient_ratio",
        "curl_ratio",
        "harmonic_ratio",
        "frustration_score",
    ]
    missing_terms = [term for term in required_terms if term not in manuscript_text]
    _add_check(
        rows,
        check_id="algorithm_primitives_reported",
        domain="method_definition",
        status="pass" if not missing_terms else "fail",
        evidence=(
            "all required SheafSignal primitives found"
            if not missing_terms
            else "missing_terms=" + ";".join(missing_terms)
        ),
        required_action="Define every reported SheafSignal metric in manuscript-facing text.",
    )

    component = _read_table(root / "benchmarks/results/component_recovery.csv")
    expected_scenarios = {"gradient_chain", "triangle_curl", "harmonic_ring", "mixed"}
    scenario_set = (
        set(component["scenario"].astype(str))
        if not component.empty and "scenario" in component.columns
        else set()
    )
    missing_scenarios = sorted(expected_scenarios - scenario_set)
    _add_check(
        rows,
        check_id="simulation_ground_truth_recovery_present",
        domain="simulation",
        status="pass" if not missing_scenarios else "fail",
        evidence=(
            "component_recovery.csv covers gradient/curl/harmonic/mixed"
            if not missing_scenarios
            else "missing_scenarios=" + ";".join(missing_scenarios)
        ),
        required_action="Regenerate component recovery benchmark.",
    )

    datasets = _read_table(root / "metadata/datasets.tsv", sep="\t")
    public_datasets = (
        datasets.loc[datasets["benchmark_role"].astype(str).str.startswith("public")]
        if not datasets.empty and "benchmark_role" in datasets.columns
        else pd.DataFrame()
    )
    manifest_columns = [
        "dataset_id",
        "accession_or_doi",
        "download_url",
        "sha256",
        "license_or_terms",
        "prepared_expression",
        "prepared_metadata",
    ]
    _add_check(
        rows,
        check_id="public_dataset_manifest_complete",
        domain="data_availability",
        status="pass" if _required_present(public_datasets, manifest_columns) else "fail",
        evidence=f"public_benchmark_rows={len(public_datasets)}",
        required_action="Fill accession, URL, checksum, terms, and prepared paths for every public benchmark.",
    )

    zenodo_pending = (
        not public_datasets.empty
        and "zenodo_doi" in public_datasets.columns
        and public_datasets["zenodo_doi"].astype(str).str.contains("PENDING").any()
    )
    _add_check(
        rows,
        check_id="zenodo_doi_external_release",
        domain="data_availability",
        status="pending_external" if zenodo_pending else "pass",
        evidence=(
            "PENDING_ZENODO_RELEASE present"
            if zenodo_pending
            else "Zenodo DOI fields are not pending"
        ),
        required_action="Mint Zenodo DOI and run finalize_zenodo_doi.py before submission.",
    )

    summary = _read_table(root / "benchmarks/results/public_tme_sheafsignal_summary.csv")
    completed_public = (
        summary.loc[
            (summary["dataset_id"].astype(str) != "demo_synthetic")
            & (summary["status"].astype(str) == "completed")
        ]
        if not summary.empty and {"dataset_id", "status"}.issubset(summary.columns)
        else pd.DataFrame()
    )
    _add_check(
        rows,
        check_id="public_tme_benchmarks_completed",
        domain="benchmark",
        status="pass" if len(completed_public) >= 4 else "fail",
        evidence=f"completed_public_benchmarks={len(completed_public)}",
        required_action="Run public TME benchmarks until PDAC, melanoma, breast scRNA-seq, and Visium are complete.",
    )

    tool_comparison = _read_table(root / "benchmarks/results/tool_comparison.csv")
    completed_tools = (
        tool_comparison.loc[
            (tool_comparison["dataset_id"].astype(str) != "demo_synthetic")
            & tool_comparison["status"].astype(str).str.startswith("completed")
        ]
        if not tool_comparison.empty
        and {"dataset_id", "tool", "status"}.issubset(tool_comparison.columns)
        else pd.DataFrame()
    )
    tool_counts = (
        completed_tools.groupby("tool")["dataset_id"].nunique().to_dict()
        if not completed_tools.empty
        else {}
    )
    comparator_pass = (
        tool_counts.get("LIANA", 0) >= 3
        and tool_counts.get("NicheNet", 0) >= 3
        and tool_counts.get("MechanisticTargetPrior", 0) >= 3
        and tool_counts.get("LRProductBaseline", 0) >= 4
    )
    _add_check(
        rows,
        check_id="external_comparator_coverage_bounded",
        domain="comparator",
        status="pass" if comparator_pass else "warning",
        evidence=";".join(f"{tool}={count}" for tool, count in sorted(tool_counts.items())),
        required_action="Keep comparator language bounded; add CellChat/CellPhoneDB/niche-DE only if full outputs are generated.",
    )

    claim_gating = _read_table(
        root / "benchmarks/results/gse154778_pdac_scrna/qc/claim_gating_by_cell_type.csv"
    )
    main_claims = (
        sorted(
            claim_gating.loc[
                claim_gating["claim_gate"].astype(str) == "main_claim", "cell_type"
            ]
            .astype(str)
            .tolist()
        )
        if not claim_gating.empty and {"claim_gate", "cell_type"}.issubset(claim_gating)
        else []
    )
    _add_check(
        rows,
        check_id="gse154778_claim_gate_no_unvalidated_main_source",
        domain="claim_boundary",
        status="pass" if main_claims == [] else "fail",
        evidence="main_claim_cell_types=" + ";".join(main_claims),
        required_action=(
            "Do not promote GSE154778 cell types to main biological source claims "
            "until annotation and expression-mode permutation/FDR gates agree."
        ),
    )

    spatial = _read_table(
        root / "benchmarks/results/tenx_breast_visium/spatial/qc/k_neighbors_sensitivity.csv"
    )
    if not spatial.empty and "spearman_with_reference" in spatial.columns:
        min_spearman = float(pd.to_numeric(spatial["spearman_with_reference"]).min())
        min_overlap = float(pd.to_numeric(spatial["top_50_overlap_with_reference"]).min())
        spatial_pass = min_spearman >= 0.9 and min_overlap >= 0.8
        spatial_evidence = f"min_spearman={min_spearman:.4f};min_top50_overlap={min_overlap:.4f}"
    else:
        spatial_pass = False
        spatial_evidence = "spatial sensitivity table missing"
    _add_check(
        rows,
        check_id="visium_spatial_k_sensitivity",
        domain="spatial_qc",
        status="pass" if spatial_pass else "warning",
        evidence=spatial_evidence,
        required_action="Keep Visium claims limited to hotspot localization unless annotation is strengthened.",
    )

    figure_quality = _read_table(
        root / "manuscript/figure_quality/MAIN_FIGURE_QUALITY_AUDIT.tsv", sep="\t"
    )
    figure_quality_pass = (
        not figure_quality.empty
        and "status" in figure_quality
        and (figure_quality["status"].astype(str) == "pass").all()
    )
    _add_check(
        rows,
        check_id="main_figures_quality_and_boundaries",
        domain="figures",
        status="pass" if figure_quality_pass else "fail",
        evidence="MAIN_FIGURE_QUALITY_AUDIT.tsv",
        required_action="Run check_main_figure_quality.py and fix any failing figure.",
    )

    supplementary_audit = _read_table(
        root / "manuscript/supplementary_quality/SUPPLEMENTARY_ARTIFACT_AUDIT.tsv",
        sep="\t",
    )
    supplementary_pass = (
        not supplementary_audit.empty
        and "status" in supplementary_audit
        and (supplementary_audit["status"].astype(str) == "pass").all()
    )
    _add_check(
        rows,
        check_id="supplementary_artifacts_manifest_readable",
        domain="supplement",
        status="pass" if supplementary_pass else "fail",
        evidence=(
            f"supplementary_artifacts={len(supplementary_audit)}"
            if not supplementary_audit.empty
            else "supplementary artifact audit missing"
        ),
        required_action="Run check_supplementary_artifacts.py and fix any failing supplementary item.",
    )

    benchmark_contract = _read_table(
        root / "benchmarks/results/BENCHMARK_RESULT_CONTRACT_AUDIT.tsv",
        sep="\t",
    )
    benchmark_contract_pass = (
        not benchmark_contract.empty
        and "status" in benchmark_contract
        and not (benchmark_contract["status"].astype(str) == "fail").any()
    )
    _add_check(
        rows,
        check_id="benchmark_result_contracts_valid",
        domain="benchmark",
        status="pass" if benchmark_contract_pass else "fail",
        evidence=(
            f"benchmark_contract_checks={len(benchmark_contract)}"
            if not benchmark_contract.empty
            else "benchmark contract audit missing"
        ),
        required_action="Run check_benchmark_result_contracts.py and resolve failed result-table checks.",
    )

    provenance_audit = _read_table(
        root / "manuscript/provenance/SUBMISSION_PROVENANCE_AUDIT.tsv",
        sep="\t",
    )
    provenance_pass = (
        not provenance_audit.empty
        and "status" in provenance_audit
        and not (provenance_audit["status"].astype(str) == "fail").any()
    )
    _add_check(
        rows,
        check_id="submission_provenance_traceable",
        domain="provenance",
        status="pass" if provenance_pass else "fail",
        evidence=(
            f"provenance_rows={len(provenance_audit)}"
            if not provenance_audit.empty
            else "submission provenance audit missing"
        ),
        required_action="Run check_submission_provenance.py and resolve local provenance failures.",
    )

    claim_safety_report = _read_text(root / "manuscript/CLAIM_SAFETY_AUDIT_REPORT.md")
    _add_check(
        rows,
        check_id="claim_safety_no_blocking_positive_claims",
        domain="claim_boundary",
        status="pass" if "Blocking positive claims: 0" in claim_safety_report else "fail",
        evidence="CLAIM_SAFETY_AUDIT_REPORT.md",
        required_action="Resolve all blocking positive claims before submission.",
    )

    reference_gap = _read_text(root / "manuscript/references/SCI_REFERENCE_GAP_REPORT.md")
    _add_check(
        rows,
        check_id="reference_placeholders_resolved",
        domain="references",
        status="pass" if "REFERENCE_PLACEHOLDERS_RESOLVED" in reference_gap else "fail",
        evidence="SCI_REFERENCE_GAP_REPORT.md",
        required_action="Resolve manuscript reference placeholders.",
    )

    archive_manifest = _read_table(root / "release/archive_manifest.tsv", sep="\t")
    if not archive_manifest.empty and {"archive_target", "sha256"}.issubset(
        archive_manifest.columns
    ):
        targets = set(archive_manifest["archive_target"].astype(str))
        checksums_ok = archive_manifest["sha256"].astype(str).str.fullmatch(r"[0-9a-f]{64}").all()
        archive_pass = {"github", "zenodo"}.issubset(targets) and bool(checksums_ok)
        archive_evidence = ";".join(sorted(targets))
    else:
        archive_pass = False
        archive_evidence = "archive manifest missing"
    _add_check(
        rows,
        check_id="release_archives_checksum_tracked",
        domain="reproducibility",
        status="pass" if archive_pass else "fail",
        evidence=archive_evidence,
        required_action="Rebuild release archives and archive_manifest.tsv.",
    )

    status, evidence = _status_for_required_files(
        root,
        [
            "manuscript/submission_upload_package/SheafSignal_main_manuscript_v2.docx",
            "manuscript/submission_upload_package/SheafSignal_cover_letter_NatureMethods.docx",
            "manuscript/submission_upload_package/SheafSignal_supplementary_information.docx",
            "manuscript/submission_upload_package/submission_upload_preflight_checklist.tsv",
        ],
    )
    _add_check(
        rows,
        check_id="submission_upload_package_present",
        domain="submission_package",
        status=status,
        evidence=evidence,
        required_action="Run build_submission_upload_package.py.",
    )

    return pd.DataFrame(rows)


def build_reviewer_risk_register(audit: pd.DataFrame) -> pd.DataFrame:
    status_map = dict(zip(audit["check_id"], audit["status"]))
    evidence_map = dict(zip(audit["check_id"], audit["evidence"]))

    def ok(*ids: str) -> bool:
        return all(status_map.get(item) == "pass" for item in ids)

    rows = [
        {
            "risk_id": "RR1_algorithm_rebranding",
            "reviewer_risk": "Reviewer may argue that SheafSignal is only a ligand-receptor intensity score.",
            "mitigation_evidence": evidence_map.get("algorithm_primitives_reported", "NA"),
            "residual_boundary": "Do not claim broad superiority; claim a distinct sheaf/Hodge object and measured consistency signals.",
            "status": "mitigated" if ok("algorithm_primitives_reported") else "open",
        },
        {
            "risk_id": "RR2_simulation_ground_truth",
            "reviewer_risk": "Reviewer may ask whether gradient, curl, and harmonic components are identifiable.",
            "mitigation_evidence": evidence_map.get("simulation_ground_truth_recovery_present", "NA"),
            "residual_boundary": "Simulation supports component recovery, not biological truth.",
            "status": "mitigated" if ok("simulation_ground_truth_recovery_present") else "open",
        },
        {
            "risk_id": "RR3_public_data_reproducibility",
            "reviewer_risk": "Reviewer may ask whether all public data and processed objects are traceable.",
            "mitigation_evidence": evidence_map.get("public_dataset_manifest_complete", "NA"),
            "residual_boundary": "Zenodo DOI remains an external submission step until minted.",
            "status": (
                "external_pending"
                if status_map.get("zenodo_doi_external_release") == "pending_external"
                else "mitigated" if ok("public_dataset_manifest_complete") else "open"
            ),
        },
        {
            "risk_id": "RR4_comparator_scope",
            "reviewer_risk": "Reviewer may request external CCC comparator evidence beyond internal LR baseline.",
            "mitigation_evidence": evidence_map.get("external_comparator_coverage_bounded", "NA"),
            "residual_boundary": "CellChat, CellPhoneDB, and niche-DE are not claimed as completed unless their outputs are imported.",
            "status": (
                "mitigated"
                if status_map.get("external_comparator_coverage_bounded") == "pass"
                else "boundary_note_required"
            ),
        },
        {
            "risk_id": "RR5_sparse_cell_types",
            "reviewer_risk": "Reviewer may object that sparse cell types are overinterpreted.",
            "mitigation_evidence": evidence_map.get(
                "gse154778_claim_gate_no_unvalidated_main_source",
                "NA",
            ),
            "residual_boundary": (
                "GSE154778 main text should not promote Myeloid, CAF/Fibroblast, "
                "or any other cell type as a validated source mechanism until "
                "annotation and expression-mode permutation/FDR gates agree."
            ),
            "status": (
                "mitigated"
                if ok("gse154778_claim_gate_no_unvalidated_main_source")
                else "open"
            ),
        },
        {
            "risk_id": "RR6_spatial_neighbor_choice",
            "reviewer_risk": "Reviewer may ask whether Visium hotspot ranking depends on arbitrary k.",
            "mitigation_evidence": evidence_map.get("visium_spatial_k_sensitivity", "NA"),
            "residual_boundary": "Spatial claims are hotspot-localization claims, not single-cell annotation proof.",
            "status": (
                "mitigated"
                if status_map.get("visium_spatial_k_sensitivity") == "pass"
                else "boundary_note_required"
            ),
        },
        {
            "risk_id": "RR7_overclaiming",
            "reviewer_risk": "Reviewer may reject unsupported clinical utility, therapeutic, or broad-superiority claims.",
            "mitigation_evidence": evidence_map.get("claim_safety_no_blocking_positive_claims", "NA"),
            "residual_boundary": "Keep the article framed as a reproducible methods manuscript.",
            "status": "mitigated" if ok("claim_safety_no_blocking_positive_claims") else "open",
        },
        {
            "risk_id": "RR8_figure_traceability",
            "reviewer_risk": "Reviewer or editor may ask whether each figure maps to source data and safe claims.",
            "mitigation_evidence": evidence_map.get("main_figures_quality_and_boundaries", "NA"),
            "residual_boundary": "Automated audit does not replace final manual journal production review.",
            "status": "mitigated" if ok("main_figures_quality_and_boundaries") else "open",
        },
        {
            "risk_id": "RR9_supplementary_artifact_completeness",
            "reviewer_risk": "Reviewer or editor may ask whether supplementary figures, tables, and support files are complete and readable.",
            "mitigation_evidence": evidence_map.get("supplementary_artifacts_manifest_readable", "NA"),
            "residual_boundary": "Artifact readability does not replace manual caption or journal production review.",
            "status": (
                "mitigated"
                if ok("supplementary_artifacts_manifest_readable")
                else "open"
            ),
        },
        {
            "risk_id": "RR10_result_table_integrity",
            "reviewer_risk": "Reviewer may question whether benchmark result tables, metric ranges, and comparator file links are internally consistent.",
            "mitigation_evidence": evidence_map.get("benchmark_result_contracts_valid", "NA"),
            "residual_boundary": "Contract checks support table integrity, not broader biological or clinical validity.",
            "status": (
                "mitigated" if ok("benchmark_result_contracts_valid") else "open"
            ),
        },
        {
            "risk_id": "RR11_artifact_provenance",
            "reviewer_risk": "Reviewer, editor, or coauthor may ask which script or source generated each submission artifact.",
            "mitigation_evidence": evidence_map.get("submission_provenance_traceable", "NA"),
            "residual_boundary": "Provenance audit does not complete external DOI, GitHub publication, or author metadata.",
            "status": "mitigated" if ok("submission_provenance_traceable") else "open",
        },
    ]
    return pd.DataFrame(rows)


def build_method_reporting_report(audit: pd.DataFrame, risk_register: pd.DataFrame) -> str:
    failures = audit.loc[audit["status"].astype(str) == "fail"]
    warnings = audit.loc[audit["status"].astype(str).isin(["warning", "pending_external"])]
    decision = (
        "METHOD_REPORTING_FAIL"
        if not failures.empty
        else "METHOD_REPORTING_PASS_WITH_BOUNDARY_NOTES"
        if not warnings.empty
        else "METHOD_REPORTING_PASS"
    )
    lines = [
        "# Method Reporting Readiness Audit",
        "",
        f"Decision: `{decision}`",
        "",
        f"- Checks: {len(audit)}",
        f"- Failures: {len(failures)}",
        f"- Warnings or external-pending checks: {len(warnings)}",
        "",
        "## Checks Requiring Attention",
        "",
    ]
    if warnings.empty and failures.empty:
        lines.append("None.")
    else:
        for row in pd.concat([failures, warnings]).to_dict(orient="records"):
            lines.append(
                f"- `{row['check_id']}` `{row['status']}`: {row['evidence']} "
                f"Action: {row['required_action']}"
            )
    lines.extend(["", "## Reviewer Risk Status", ""])
    for row in risk_register.to_dict(orient="records"):
        lines.append(
            f"- `{row['risk_id']}` `{row['status']}`: {row['residual_boundary']}"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This audit strengthens local reporting readiness. It does not guarantee",
            "acceptance and does not replace author metadata, DOI minting, public GitHub",
            "release, institutional ethics review, or journal-specific submission checks.",
            "",
        ]
    )
    return "\n".join(lines)


def build_reviewer_risk_report(risk_register: pd.DataFrame) -> str:
    open_rows = risk_register.loc[
        ~risk_register["status"].astype(str).isin(["mitigated", "external_pending"])
    ]
    lines = [
        "# Reviewer Risk Register",
        "",
        f"- Risks tracked: {len(risk_register)}",
        f"- Open or boundary-note risks: {len(open_rows)}",
        "",
    ]
    for row in risk_register.to_dict(orient="records"):
        lines.extend(
            [
                f"## {row['risk_id']}",
                "",
                f"- Status: `{row['status']}`",
                f"- Reviewer risk: {row['reviewer_risk']}",
                f"- Mitigation evidence: {row['mitigation_evidence']}",
                f"- Residual boundary: {row['residual_boundary']}",
                "",
            ]
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--output-dir",
        default="manuscript/method_reporting",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Write outputs and return success even when method checks fail.",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    output_dir = root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    audit = build_method_reporting_audit(root)
    risk_register = build_reviewer_risk_register(audit)
    audit_out = output_dir / "METHOD_REPORTING_AUDIT.tsv"
    report_out = output_dir / "METHOD_REPORTING_REPORT.md"
    risk_out = output_dir / "REVIEWER_RISK_REGISTER.tsv"
    risk_report_out = output_dir / "REVIEWER_RISK_REPORT.md"
    _write_table_atomic(audit_out, audit)
    _write_text_atomic(report_out, build_method_reporting_report(audit, risk_register))
    _write_table_atomic(risk_out, risk_register)
    _write_text_atomic(risk_report_out, build_reviewer_risk_report(risk_register))
    print(f"wrote {audit_out}")
    print(f"wrote {report_out}")
    print(f"wrote {risk_out}")
    print(f"wrote {risk_report_out}")
    has_failures = bool((audit["status"].astype(str) == "fail").any())
    if has_failures and not args.report_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
