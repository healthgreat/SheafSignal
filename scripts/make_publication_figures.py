#!/usr/bin/env python
"""Create manuscript-level figures from standardized benchmark tables."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SUPPLEMENTARY_MANIFEST_ENTRIES = [
    {
        "figure_id": "supp_gse154778_marker_heatmap",
        "path": "benchmarks\\results\\gse154778_pdac_scrna\\qc\\marker_heatmap.pdf",
        "source_results_dir": "benchmarks\\results\\gse154778_pdac_scrna\\qc",
    },
    {
        "figure_id": "supp_gse154778_cell_type_counts",
        "path": "benchmarks\\results\\gse154778_pdac_scrna\\qc\\cell_type_counts.pdf",
        "source_results_dir": "benchmarks\\results\\gse154778_pdac_scrna\\qc",
    },
    {
        "figure_id": "supp_gse154778_annotation_confidence",
        "path": "benchmarks\\results\\gse154778_pdac_scrna\\qc\\annotation_confidence.pdf",
        "source_results_dir": "benchmarks\\results\\gse154778_pdac_scrna\\qc",
    },
    {
        "figure_id": "supp_gse154778_frustration_overlay",
        "path": "benchmarks\\results\\gse154778_pdac_scrna\\qc\\frustration_annotation_overlay.pdf",
        "source_results_dir": "benchmarks\\results\\gse154778_pdac_scrna\\qc",
    },
    {
        "figure_id": "supp_gse154778_bootstrap_frustration_stability",
        "path": "benchmarks\\results\\gse154778_pdac_scrna\\stability\\bootstrap_frustration_stability.pdf",
        "source_results_dir": "benchmarks\\results\\gse154778_pdac_scrna\\stability",
    },
    {
        "figure_id": "supp_gse154778_lesion_frustration_scores",
        "path": "benchmarks\\results\\gse154778_pdac_scrna\\stratified\\lesion_frustration_scores.pdf",
        "source_results_dir": "benchmarks\\results\\gse154778_pdac_scrna\\stratified",
    },
    {
        "figure_id": "supp_gse154778_sample_level_myeloid_stability",
        "path": "benchmarks\\results\\gse154778_pdac_scrna\\stability\\sample_level_myeloid_stability.pdf",
        "source_results_dir": "benchmarks\\results\\gse154778_pdac_scrna\\stability",
    },
    {
        "figure_id": "supp_gse154778_claim_gating_table",
        "path": "benchmarks\\results\\gse154778_pdac_scrna\\qc\\claim_gating_by_cell_type.csv",
        "source_results_dir": "benchmarks\\results\\gse154778_pdac_scrna\\qc",
    },
    {
        "figure_id": "supp_gse154778_myeloid_claim_readiness_table",
        "path": "benchmarks\\results\\gse154778_pdac_scrna\\qc\\myeloid_claim_readiness_summary.csv",
        "source_results_dir": "benchmarks\\results\\gse154778_pdac_scrna\\qc",
    },
    {
        "figure_id": "supp_gse72056_author_annotation_counts",
        "path": "data\\processed\\gse72056_melanoma_scrna\\annotation_summary.csv",
        "source_results_dir": "data\\processed\\gse72056_melanoma_scrna",
    },
    {
        "figure_id": "supp_gse72056_lr_product_alignment",
        "path": (
            "benchmarks\\results\\gse72056_melanoma_scrna\\comparators\\"
            "sheafsignal_vs_lr_product_baseline.csv"
        ),
        "source_results_dir": "benchmarks\\results\\gse72056_melanoma_scrna\\comparators",
    },
    {
        "figure_id": "supp_gse72056_mechanistic_prior_alignment",
        "path": (
            "benchmarks\\results\\gse72056_melanoma_scrna\\comparators\\"
            "sheafsignal_vs_mechanistictargetprior.csv"
        ),
        "source_results_dir": "benchmarks\\results\\gse72056_melanoma_scrna\\comparators",
    },
    {
        "figure_id": "supp_gse72056_nichenet_alignment",
        "path": (
            "benchmarks\\results\\gse72056_melanoma_scrna\\comparators\\"
            "sheafsignal_vs_nichenet.csv"
        ),
        "source_results_dir": "benchmarks\\results\\gse72056_melanoma_scrna\\comparators",
    },
    {
        "figure_id": "supp_gse176078_author_annotation_counts",
        "path": "data\\processed\\gse176078_brca_scrna\\annotation_summary.csv",
        "source_results_dir": "data\\processed\\gse176078_brca_scrna",
    },
    {
        "figure_id": "supp_gse176078_lr_product_alignment",
        "path": (
            "benchmarks\\results\\gse176078_brca_scrna\\comparators\\"
            "sheafsignal_vs_lr_product_baseline.csv"
        ),
        "source_results_dir": "benchmarks\\results\\gse176078_brca_scrna\\comparators",
    },
    {
        "figure_id": "supp_gse176078_mechanistic_prior_alignment",
        "path": (
            "benchmarks\\results\\gse176078_brca_scrna\\comparators\\"
            "sheafsignal_vs_mechanistictargetprior.csv"
        ),
        "source_results_dir": "benchmarks\\results\\gse176078_brca_scrna\\comparators",
    },
    {
        "figure_id": "supp_gse176078_nichenet_alignment",
        "path": (
            "benchmarks\\results\\gse176078_brca_scrna\\comparators\\"
            "sheafsignal_vs_nichenet.csv"
        ),
        "source_results_dir": "benchmarks\\results\\gse176078_brca_scrna\\comparators",
    },
    {
        "figure_id": "supp_tenx_breast_visium_marker_spot_counts",
        "path": "data\\processed\\tenx_breast_visium\\annotation_summary.csv",
        "source_results_dir": "data\\processed\\tenx_breast_visium",
    },
    {
        "figure_id": "supp_tenx_breast_visium_spatial_hotspots",
        "path": "benchmarks\\results\\tenx_breast_visium\\spatial\\spatial_frustration_hotspots.csv",
        "source_results_dir": "benchmarks\\results\\tenx_breast_visium\\spatial",
    },
    {
        "figure_id": "supp_tenx_breast_visium_spatial_hotspot_summary",
        "path": "benchmarks\\results\\tenx_breast_visium\\spatial\\spatial_hotspot_summary.csv",
        "source_results_dir": "benchmarks\\results\\tenx_breast_visium\\spatial",
    },
    {
        "figure_id": "supp_tenx_breast_visium_hotspot_spatial_scatter",
        "path": "benchmarks\\results\\tenx_breast_visium\\spatial\\qc\\hotspot_spatial_scatter.pdf",
        "source_results_dir": "benchmarks\\results\\tenx_breast_visium\\spatial\\qc",
    },
    {
        "figure_id": "supp_tenx_breast_visium_k_neighbors_sensitivity",
        "path": "benchmarks\\results\\tenx_breast_visium\\spatial\\qc\\k_neighbors_sensitivity.pdf",
        "source_results_dir": "benchmarks\\results\\tenx_breast_visium\\spatial\\qc",
    },
    {
        "figure_id": "supp_tenx_breast_visium_spatial_hotspot_qc_summary",
        "path": "benchmarks\\results\\tenx_breast_visium\\spatial\\qc\\spatial_hotspot_qc_summary.csv",
        "source_results_dir": "benchmarks\\results\\tenx_breast_visium\\spatial\\qc",
    },
    {
        "figure_id": "supp_comparator_readiness_matrix",
        "path": "benchmarks\\results\\comparator_readiness_matrix.csv",
        "source_results_dir": "benchmarks\\results",
    },
    {
        "figure_id": "supp_ligand_target_prior_table",
        "path": "metadata\\tme_ligand_target_prior.csv",
        "source_results_dir": "metadata",
    },
    {
        "figure_id": "supp_gse154778_mechanistic_prior_alignment",
        "path": (
            "benchmarks\\results\\gse154778_pdac_scrna\\comparators\\"
            "sheafsignal_vs_mechanistictargetprior.csv"
        ),
        "source_results_dir": "benchmarks\\results\\gse154778_pdac_scrna\\comparators",
    },
    {
        "figure_id": "supp_gse154778_nichenet_alignment",
        "path": (
            "benchmarks\\results\\gse154778_pdac_scrna\\comparators\\"
            "sheafsignal_vs_nichenet.csv"
        ),
        "source_results_dir": "benchmarks\\results\\gse154778_pdac_scrna\\comparators",
    },
    {
        "figure_id": "supp_reviewer_objection_response_table",
        "path": "manuscript\\reviewer_objection_response_table.tsv",
        "source_results_dir": "manuscript",
    },
    {
        "figure_id": "supp_external_comparator_environment_status",
        "path": "benchmarks\\results\\external_comparator_environment_status.csv",
        "source_results_dir": "benchmarks\\results",
    },
    {
        "figure_id": "supp_external_comparator_execution_plan",
        "path": "benchmarks\\results\\external_comparator_execution_plan.csv",
        "source_results_dir": "benchmarks\\results",
    },
    {
        "figure_id": "supp_external_comparator_gate_summary",
        "path": "manuscript\\external_comparator_gate_summary.tsv",
        "source_results_dir": "manuscript",
    },
    {
        "figure_id": "supp_release_github_manifest",
        "path": "release\\github_release_manifest.tsv",
        "source_results_dir": "release",
    },
    {
        "figure_id": "supp_release_zenodo_manifest",
        "path": "release\\zenodo_upload_manifest.tsv",
        "source_results_dir": "release",
    },
    {
        "figure_id": "supp_release_summary",
        "path": "release\\REPRODUCIBILITY_RELEASE_SUMMARY.md",
        "source_results_dir": "release",
    },
    {
        "figure_id": "supp_release_archive_manifest",
        "path": "release\\archive_manifest.tsv",
        "source_results_dir": "release",
    },
    {
        "figure_id": "supp_submission_readiness_report",
        "path": "manuscript\\SUBMISSION_READINESS_REPORT.md",
        "source_results_dir": "manuscript",
    },
    {
        "figure_id": "supp_journal_targets_20_50",
        "path": "manuscript\\JOURNAL_TARGETS_20_50.tsv",
        "source_results_dir": "manuscript",
    },
    {
        "figure_id": "supp_sci20_50_action_board",
        "path": "manuscript\\SCI20_50_ACTION_BOARD.md",
        "source_results_dir": "manuscript",
    },
    {
        "figure_id": "supp_nm_title_page_draft",
        "path": "manuscript\\nature_methods_package\\00_title_page.md",
        "source_results_dir": "manuscript\\nature_methods_package",
    },
    {
        "figure_id": "supp_nm_abstract_draft",
        "path": "manuscript\\nature_methods_package\\01_abstract.md",
        "source_results_dir": "manuscript\\nature_methods_package",
    },
    {
        "figure_id": "supp_nm_claim_evidence_map",
        "path": "manuscript\\nature_methods_package\\05_claim_evidence_map.tsv",
        "source_results_dir": "manuscript\\nature_methods_package",
    },
    {
        "figure_id": "supp_nm_submission_checklist",
        "path": "manuscript\\nature_methods_package\\07_submission_checklist.tsv",
        "source_results_dir": "manuscript\\nature_methods_package",
    },
    {
        "figure_id": "supp_nm_full_manuscript_draft",
        "path": "manuscript\\nature_methods_package\\09_full_manuscript_draft.md",
        "source_results_dir": "manuscript\\nature_methods_package",
    },
    {
        "figure_id": "supp_nm_supplementary_information_draft",
        "path": "manuscript\\nature_methods_package\\10_supplementary_information_draft.md",
        "source_results_dir": "manuscript\\nature_methods_package",
    },
    {
        "figure_id": "supp_final_submission_blockers",
        "path": "manuscript\\FINAL_SUBMISSION_BLOCKERS.tsv",
        "source_results_dir": "manuscript",
    },
    {
        "figure_id": "supp_nature_methods_go_no_go_report",
        "path": "manuscript\\NATURE_METHODS_GO_NO_GO_REPORT.md",
        "source_results_dir": "manuscript",
    },
    {
        "figure_id": "supp_zenodo_deposition_metadata",
        "path": "release\\zenodo_deposition_metadata.json",
        "source_results_dir": "release",
    },
    {
        "figure_id": "supp_zenodo_deposition_instructions",
        "path": "release\\ZENODO_DEPOSITION_INSTRUCTIONS.md",
        "source_results_dir": "release",
    },
    {
        "figure_id": "supp_submission_author_metadata_template",
        "path": "manuscript\\submission_metadata\\AUTHOR_METADATA_TEMPLATE.tsv",
        "source_results_dir": "manuscript\\submission_metadata",
    },
    {
        "figure_id": "supp_submission_system_metadata_checklist",
        "path": "manuscript\\submission_metadata\\SUBMISSION_SYSTEM_METADATA_CHECKLIST.tsv",
        "source_results_dir": "manuscript\\submission_metadata",
    },
    {
        "figure_id": "supp_github_release_instructions",
        "path": "release\\GITHUB_RELEASE_INSTRUCTIONS.md",
        "source_results_dir": "release",
    },
    {
        "figure_id": "supp_nature_methods_format_audit",
        "path": "manuscript\\NATURE_METHODS_FORMAT_AUDIT.tsv",
        "source_results_dir": "manuscript",
    },
    {
        "figure_id": "supp_nature_methods_format_audit_report",
        "path": "manuscript\\NATURE_METHODS_FORMAT_AUDIT_REPORT.md",
        "source_results_dir": "manuscript",
    },
    {
        "figure_id": "supp_presubmission_inquiry_letter",
        "path": "manuscript\\presubmission_inquiry\\01_presubmission_inquiry_letter.md",
        "source_results_dir": "manuscript\\presubmission_inquiry",
    },
    {
        "figure_id": "supp_editorial_triage_risk_audit",
        "path": "manuscript\\presubmission_inquiry\\02_editorial_triage_risk_audit.tsv",
        "source_results_dir": "manuscript\\presubmission_inquiry",
    },
    {
        "figure_id": "supp_editor_novelty_evidence_matrix",
        "path": "manuscript\\presubmission_inquiry\\03_novelty_evidence_matrix.tsv",
        "source_results_dir": "manuscript\\presubmission_inquiry",
    },
    {
        "figure_id": "supp_response_transfer_decision_tree",
        "path": "manuscript\\response_transfer\\00_decision_tree.md",
        "source_results_dir": "manuscript\\response_transfer",
    },
    {
        "figure_id": "supp_response_transfer_by_journal",
        "path": "manuscript\\response_transfer\\03_transfer_package_by_journal.tsv",
        "source_results_dir": "manuscript\\response_transfer",
    },
    {
        "figure_id": "supp_response_transfer_rewrite_actions",
        "path": "manuscript\\response_transfer\\04_target_specific_rewrite_actions.tsv",
        "source_results_dir": "manuscript\\response_transfer",
    },
    {
        "figure_id": "supp_response_transfer_do_not_claim",
        "path": "manuscript\\response_transfer\\05_do_not_claim_checklist.md",
        "source_results_dir": "manuscript\\response_transfer",
    },
    {
        "figure_id": "supp_figure_legend_inventory",
        "path": "manuscript\\figure_legends\\00_figure_legend_inventory.tsv",
        "source_results_dir": "manuscript\\figure_legends",
    },
    {
        "figure_id": "supp_main_figure_legends_draft",
        "path": "manuscript\\figure_legends\\01_main_figure_legends.md",
        "source_results_dir": "manuscript\\figure_legends",
    },
    {
        "figure_id": "supp_supplementary_figure_legends_draft",
        "path": "manuscript\\figure_legends\\02_supplementary_figure_legends.md",
        "source_results_dir": "manuscript\\figure_legends",
    },
    {
        "figure_id": "supp_figure_source_map",
        "path": "manuscript\\figure_legends\\03_figure_source_map.tsv",
        "source_results_dir": "manuscript\\figure_legends",
    },
    {
        "figure_id": "supp_figure_claim_boundary_checklist",
        "path": "manuscript\\figure_legends\\04_figure_claim_boundary_checklist.tsv",
        "source_results_dir": "manuscript\\figure_legends",
    },
    {
        "figure_id": "supp_claim_safety_audit",
        "path": "manuscript\\CLAIM_SAFETY_AUDIT.tsv",
        "source_results_dir": "manuscript",
    },
    {
        "figure_id": "supp_claim_safety_audit_report",
        "path": "manuscript\\CLAIM_SAFETY_AUDIT_REPORT.md",
        "source_results_dir": "manuscript",
    },
    {
        "figure_id": "supp_sci_title_abstract_keywords",
        "path": "manuscript\\SCI_TITLE_ABSTRACT_KEYWORDS.md",
        "source_results_dir": "manuscript",
    },
    {
        "figure_id": "supp_sci_manuscript_v1",
        "path": "manuscript\\SCI_MANUSCRIPT_V1.md",
        "source_results_dir": "manuscript",
    },
    {
        "figure_id": "supp_sci_manuscript_v1_claim_tracked",
        "path": "manuscript\\SCI_MANUSCRIPT_V1_claim_tracked.md",
        "source_results_dir": "manuscript",
    },
    {
        "figure_id": "supp_sci_manuscript_v2_polished",
        "path": "manuscript\\SCI_MANUSCRIPT_V2_POLISHED.md",
        "source_results_dir": "manuscript",
    },
    {
        "figure_id": "supp_sci_manuscript_v2_claim_tracked",
        "path": "manuscript\\SCI_MANUSCRIPT_V2_POLISHED_claim_tracked.md",
        "source_results_dir": "manuscript",
    },
    {
        "figure_id": "supp_sci_manuscript_v2_editorial_audit",
        "path": "manuscript\\SCI_MANUSCRIPT_V2_EDITORIAL_AUDIT.tsv",
        "source_results_dir": "manuscript",
    },
    {
        "figure_id": "supp_sci_manuscript_v2_changelog",
        "path": "manuscript\\SCI_MANUSCRIPT_V2_CHANGELOG.tsv",
        "source_results_dir": "manuscript",
    },
    {
        "figure_id": "supp_submission_upload_manifest",
        "path": "manuscript\\submission_upload_package\\submission_upload_manifest.tsv",
        "source_results_dir": "manuscript\\submission_upload_package",
    },
    {
        "figure_id": "supp_submission_upload_preflight_checklist",
        "path": (
            "manuscript\\submission_upload_package\\"
            "submission_upload_preflight_checklist.tsv"
        ),
        "source_results_dir": "manuscript\\submission_upload_package",
    },
    {
        "figure_id": "supp_submission_main_figure_upload_manifest",
        "path": (
            "manuscript\\submission_upload_package\\" "main_figure_upload_manifest.tsv"
        ),
        "source_results_dir": "manuscript\\submission_upload_package",
    },
    {
        "figure_id": "supp_submission_upload_docx_text_check",
        "path": "manuscript\\submission_upload_package\\DOCX_TEXT_EXTRACTION_CHECK.md",
        "source_results_dir": "manuscript\\submission_upload_package",
    },
    {
        "figure_id": "supp_submission_upload_docx_layout_check",
        "path": "manuscript\\submission_upload_package\\DOCX_LAYOUT_CHECK.tsv",
        "source_results_dir": "manuscript\\submission_upload_package",
    },
    {
        "figure_id": "supp_sci_cover_letter_nature_methods",
        "path": "manuscript\\SCI_COVER_LETTER_NatureMethods.md",
        "source_results_dir": "manuscript",
    },
    {
        "figure_id": "supp_sci_references_verified",
        "path": "manuscript\\references\\SCI_REFERENCES_VERIFIED.tsv",
        "source_results_dir": "manuscript\\references",
    },
    {
        "figure_id": "supp_sci_references_bibtex",
        "path": "manuscript\\references\\SCI_REFERENCES.bib",
        "source_results_dir": "manuscript\\references",
    },
    {
        "figure_id": "supp_sci_reference_gap_report",
        "path": "manuscript\\references\\SCI_REFERENCE_GAP_REPORT.md",
        "source_results_dir": "manuscript\\references",
    },
    {
        "figure_id": "supp_sci_manuscript_v1_referenced",
        "path": "manuscript\\references\\SCI_MANUSCRIPT_V1_referenced.md",
        "source_results_dir": "manuscript\\references",
    },
]


def _setup_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _placeholder_panel(ax, message: str) -> None:
    ax.text(
        0.5,
        0.5,
        message,
        ha="center",
        va="center",
        fontsize=11,
        wrap=True,
    )
    ax.axis("off")


def plot_sheafsignal_concept(figures_dir: Path) -> Path:
    plt = _setup_matplotlib()
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    boxes = [
        (0.5, 4.1, "Expression\nmatrix"),
        (0.5, 2.5, "Cell type /\nspot labels"),
        (2.7, 4.1, "Ligand-receptor\nevidence"),
        (2.7, 2.5, "Pathway-state\ntransition"),
        (5.0, 3.3, "Sheaf-valued\ncommunication flow"),
        (7.4, 4.3, "Sheaf energy\nfrustration"),
        (7.4, 3.0, "Gradient\nsignal"),
        (7.4, 1.7, "Curl / harmonic\nfeedback"),
    ]
    colors = {
        "input": "#F2F2F2",
        "evidence": "#DCEAF7",
        "flow": "#E3F1DF",
        "output": "#F9E3CF",
    }
    for x, y, label in boxes:
        if x < 2:
            color = colors["input"]
        elif x < 5:
            color = colors["evidence"]
        elif x < 7:
            color = colors["flow"]
        else:
            color = colors["output"]
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=10,
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": color,
                "edgecolor": "#333333",
                "linewidth": 1,
            },
        )

    arrows = [
        ((1.25, 4.1), (2.0, 4.1)),
        ((1.25, 2.5), (2.0, 2.5)),
        ((3.55, 4.1), (4.35, 3.55)),
        ((3.55, 2.5), (4.35, 3.05)),
        ((5.9, 3.3), (6.9, 4.15)),
        ((5.9, 3.3), (6.9, 3.0)),
        ((5.9, 3.3), (6.9, 1.85)),
    ]
    for start, end in arrows:
        ax.annotate(
            "",
            xy=end,
            xytext=start,
            arrowprops={"arrowstyle": "->", "lw": 1.4, "color": "#333333"},
        )

    ax.text(
        5.0,
        0.55,
        "Question shift: from pairwise communication intensity to graph-level consistency",
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
    )
    ax.set_title("SheafSignal formulation", fontsize=13, fontweight="bold")
    fig.tight_layout()
    output = figures_dir / "publication_figure1_sheafsignal_concept.pdf"
    fig.savefig(output)
    plt.close(fig)
    return output


def plot_component_recovery(results_dir: Path, figures_dir: Path) -> Path:
    plt = _setup_matplotlib()
    table = pd.read_csv(results_dir / "component_recovery.csv")
    metrics = ["gradient_ratio", "curl_ratio", "harmonic_ratio"]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    x = range(len(table))
    width = 0.24
    for idx, metric in enumerate(metrics):
        ax.bar(
            [i + (idx - 1) * width for i in x], table[metric], width=width, label=metric
        )
    ax.set_xticks(list(x))
    ax.set_xticklabels(table["scenario"], rotation=20, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Energy ratio")
    ax.set_title("Ground-truth Hodge component recovery")
    ax.legend(frameon=False)
    fig.tight_layout()
    output = figures_dir / "publication_figure2_component_recovery.pdf"
    fig.savefig(output)
    legacy = figures_dir / "publication_figure_component_recovery.pdf"
    fig.savefig(legacy)
    plt.close(fig)
    return output


def plot_tme_summary(results_dir: Path, figures_dir: Path) -> Path:
    plt = _setup_matplotlib()
    table = pd.read_csv(results_dir / "public_tme_sheafsignal_summary.csv")
    completed = table.loc[table["status"] == "completed"].copy()
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    if completed.empty:
        ax.text(
            0.5,
            0.5,
            "Public TME datasets are manifested.\nPrepared data not yet generated.",
            ha="center",
            va="center",
            fontsize=12,
        )
        ax.axis("off")
    else:
        x = list(range(len(completed)))
        ax.bar(x, completed["total_sheaf_energy"], color="#4C78A8")
        for xpos, (_, row) in zip(x, completed.iterrows(), strict=False):
            ax.text(
                xpos,
                row["total_sheaf_energy"],
                str(row.get("top_frustration_cell_type", "")),
                ha="center",
                va="bottom",
                rotation=90,
                fontsize=8,
            )
        ax.set_ylabel("Total sheaf energy")
        ax.set_xticks(x)
        ax.set_xticklabels(completed["dataset_id"], rotation=25, ha="right")
        ax.set_title("Public TME SheafSignal benchmark")
    fig.tight_layout()
    output = figures_dir / "publication_figure3_tme_summary.pdf"
    fig.savefig(output)
    legacy = figures_dir / "publication_figure_tme_summary.pdf"
    fig.savefig(legacy)
    plt.close(fig)
    return output


def plot_gse154778_claim_gating(results_dir: Path, figures_dir: Path) -> Path:
    plt = _setup_matplotlib()
    claim_path = (
        results_dir / "gse154778_pdac_scrna" / "qc" / "claim_gating_by_cell_type.csv"
    )
    stability_path = (
        results_dir
        / "gse154778_pdac_scrna"
        / "stability"
        / "sample_level_myeloid_stability_summary.csv"
    )
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 4.4))
    if not claim_path.exists():
        _placeholder_panel(axes[0], "GSE154778 claim-gating table not available")
    else:
        claim = pd.read_csv(claim_path)
        claim = claim.sort_values("metastatic_frustration_score", ascending=False)
        y = list(range(len(claim)))
        colors = [
            "#2F7D32" if gate == "main_claim" else "#BDBDBD"
            for gate in claim["claim_gate"].astype(str)
        ]
        axes[0].barh(
            y,
            claim["metastatic_frustration_score"],
            color=colors,
            label="Metastatic",
        )
        axes[0].barh(
            y,
            -claim["primary_frustration_score"],
            color="#9ECAE1",
            label="Primary",
        )
        axes[0].axvline(0, color="#333333", linewidth=0.8)
        axes[0].set_yticks(y)
        axes[0].set_yticklabels(claim["cell_type"])
        axes[0].set_xlabel("Frustration score\nleft=Primary, right=Metastatic")
        axes[0].set_title("Claim-gated lesion signal")
        axes[0].legend(frameon=False, fontsize=8)

    if not stability_path.exists():
        _placeholder_panel(
            axes[1], "Sample-level Myeloid stability table not available"
        )
    else:
        stability = pd.read_csv(stability_path)
        stability = stability.loc[stability["lesion_type"].astype(str) != "all"].copy()
        x = list(range(len(stability)))
        axes[1].bar(
            x,
            stability["myeloid_top_frequency_adequate"],
            color="#6A51A3",
        )
        axes[1].set_ylim(0, 1.05)
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(stability["lesion_type"], rotation=0)
        axes[1].set_ylabel("Myeloid top-source frequency\nadequate samples")
        axes[1].set_title("Sample-level robustness")
        for xpos, (_, row) in zip(x, stability.iterrows(), strict=False):
            axes[1].text(
                xpos,
                row["myeloid_top_frequency_adequate"] + 0.03,
                f"n={int(row['n_myeloid_adequate_samples'])}",
                ha="center",
                fontsize=9,
            )
    fig.suptitle("GSE154778 Myeloid claim gate", fontsize=13, fontweight="bold")
    fig.tight_layout()
    output = figures_dir / "publication_figure4_gse154778_claim_gating.pdf"
    fig.savefig(output)
    plt.close(fig)
    return output


def plot_comparator_alignment(results_dir: Path, figures_dir: Path) -> Path:
    plt = _setup_matplotlib()
    path = results_dir / "tool_comparison.csv"
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.3))
    if not path.exists():
        _placeholder_panel(axes[0], "Comparator table not available")
        _placeholder_panel(axes[1], "Comparator table not available")
    else:
        table = pd.read_csv(path)
        non_demo = table.loc[table["dataset_id"].astype(str) != "demo_synthetic"].copy()
        completed = non_demo.loc[
            non_demo["status"].astype(str).str.startswith("completed")
        ].copy()
        if completed.empty:
            _placeholder_panel(axes[0], "Completed comparator imports pending")
        else:
            tools = sorted(completed["tool"].astype(str).unique())
            datasets = sorted(completed["dataset_id"].astype(str).unique())
            tool_to_x = {tool: idx for idx, tool in enumerate(tools)}
            offsets = {
                dataset: (idx - (len(datasets) - 1) / 2) * 0.12
                for idx, dataset in enumerate(datasets)
            }
            for dataset, subset in completed.groupby("dataset_id"):
                xs = [
                    tool_to_x[str(tool)] + offsets[str(dataset)]
                    for tool in subset["tool"]
                ]
                axes[0].scatter(
                    xs,
                    subset["spearman_sheaf_energy_vs_tool_score"],
                    label=str(dataset),
                    s=45,
                    alpha=0.85,
                )
            axes[0].axhline(0, color="#444444", linewidth=0.8)
            axes[0].set_xticks(list(tool_to_x.values()))
            axes[0].set_xticklabels(tools, rotation=25, ha="right")
            axes[0].set_ylabel("Spearman vs sheaf energy")
            axes[0].set_title("Aligned comparator scores")
            axes[0].legend(frameon=False, fontsize=7)

        status_summary = (
            non_demo.assign(
                status_group=non_demo["status"]
                .astype(str)
                .str.startswith("completed")
                .map({True: "completed", False: "pending"})
            )
            .groupby(["tool", "status_group"])
            .size()
            .unstack(fill_value=0)
        )
        if status_summary.empty:
            _placeholder_panel(axes[1], "Comparator readiness summary pending")
        else:
            status_summary = status_summary.sort_index()
            bottom = None
            colors = {"completed": "#3182BD", "pending": "#D9D9D9"}
            x = list(range(len(status_summary)))
            for col in ["completed", "pending"]:
                values = (
                    status_summary[col].values
                    if col in status_summary.columns
                    else [0] * len(status_summary)
                )
                axes[1].bar(
                    x,
                    values,
                    bottom=bottom,
                    color=colors[col],
                    label=col,
                )
                bottom = values if bottom is None else bottom + values
            axes[1].set_xticks(x)
            axes[1].set_xticklabels(status_summary.index, rotation=25, ha="right")
            axes[1].set_ylabel("Dataset-tool rows")
            axes[1].set_title("Comparator readiness")
            axes[1].legend(frameon=False, fontsize=8)
    fig.suptitle("Comparator alignment and boundaries", fontsize=13, fontweight="bold")
    fig.tight_layout()
    output = figures_dir / "publication_figure5_comparator_alignment.pdf"
    fig.savefig(output)
    plt.close(fig)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", default="benchmarks/results")
    parser.add_argument("--figures-dir", default="figures")
    parser.add_argument("--manifest-out", default="manuscript/figure_manifest.tsv")
    args = parser.parse_args(argv)

    results_dir = Path(args.results_dir)
    figures_dir = Path(args.figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)

    figure_rows = []
    for figure_id, path in [
        ("fig1_sheafsignal_concept", plot_sheafsignal_concept(figures_dir)),
        ("fig2_component_recovery", plot_component_recovery(results_dir, figures_dir)),
        ("fig3_tme_summary", plot_tme_summary(results_dir, figures_dir)),
        (
            "fig4_gse154778_claim_gating",
            plot_gse154778_claim_gating(results_dir, figures_dir),
        ),
        (
            "fig5_comparator_alignment",
            plot_comparator_alignment(results_dir, figures_dir),
        ),
    ]:
        figure_rows.append(
            {
                "figure_id": figure_id,
                "path": str(path),
                "source_results_dir": str(results_dir),
            }
        )
    figure_rows.extend(SUPPLEMENTARY_MANIFEST_ENTRIES)

    manifest_out = Path(args.manifest_out)
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(figure_rows).to_csv(manifest_out, sep="\t", index=False)
    print(f"wrote {manifest_out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
