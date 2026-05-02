#!/usr/bin/env python
"""Gate GSE154778 cell-type claims by sample support and annotation QC."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import _bootstrap  # noqa: F401
from bootstrap_gse154778_stability import update_figure_manifest
from sheafsignal.adapters import GSE154778_MARKERS


CLAIM_NOTE = (
    "we pre-specified minimum cell/sample support and excluded underpowered "
    "categories from biological claims"
)
MYELOID_CLAIM_SENTENCE = (
    "GSE154778 Myeloid remains a profile-level and lesion-stratified "
    "computational hypothesis, but it is not promoted as a standalone main "
    "biological claim after expression-mode permutation/FDR hardening."
)


def evidence_tier(n_cells: int, n_samples: int) -> str:
    if n_cells < 20:
        return "unsupported"
    if n_cells < 50 or n_samples < 3:
        return "borderline"
    return "adequate"


def claim_gate_for_cell_type(
    *,
    tiers: list[str],
    top_in_all_lesions: bool,
    bootstrap_top_frequency: float,
) -> str:
    if "unsupported" in tiers:
        return "qc_warning_only"
    if "borderline" in tiers:
        return "supplement_only"
    if top_in_all_lesions and bootstrap_top_frequency >= 0.8:
        return "main_claim"
    return "supplement_only"


def sample_support_table(metadata: pd.DataFrame) -> pd.DataFrame:
    required = {"cell_id", "cell_type", "sample_id", "lesion_type"}
    missing = required.difference(metadata.columns)
    if missing:
        raise ValueError(f"metadata is missing required columns: {sorted(missing)}")

    rows = []
    for (lesion_type, cell_type), group in metadata.groupby(["lesion_type", "cell_type"], sort=True):
        n_cells = int(len(group))
        n_samples = int(group["sample_id"].nunique())
        rows.append(
            {
                "lesion_type": lesion_type,
                "cell_type": cell_type,
                "n_cells": n_cells,
                "n_samples": n_samples,
                "sample_ids": ";".join(sorted(group["sample_id"].astype(str).unique())),
                "evidence_tier": evidence_tier(n_cells, n_samples),
                "support_note": CLAIM_NOTE,
            }
        )
    return pd.DataFrame(rows).sort_values(["cell_type", "lesion_type"])


def marker_specificity_table(marker_heatmap: pd.DataFrame) -> pd.DataFrame:
    if marker_heatmap.empty:
        return pd.DataFrame(columns=["cell_type", "marker_specificity_margin"])

    group_signal = (
        marker_heatmap.groupby(["cell_type", "marker_group"], dropna=False)["mean_expression"]
        .mean()
        .reset_index()
    )
    rows = []
    for cell_type, genes in GSE154778_MARKERS.items():
        own = group_signal.loc[
            (group_signal["cell_type"] == cell_type) & (group_signal["marker_group"] == cell_type),
            "mean_expression",
        ]
        others = group_signal.loc[
            (group_signal["cell_type"] != cell_type) & (group_signal["marker_group"] == cell_type),
            "mean_expression",
        ]
        own_value = float(own.iloc[0]) if len(own) else pd.NA
        other_max = float(others.max()) if len(others) else pd.NA
        if pd.isna(own_value) or pd.isna(other_max):
            margin = pd.NA
        else:
            margin = own_value - other_max
        rows.append(
            {
                "cell_type": cell_type,
                "marker_group": cell_type,
                "own_marker_mean_expression": own_value,
                "max_other_cell_type_marker_expression": other_max,
                "marker_specificity_margin": margin,
            }
        )
    return pd.DataFrame(rows)


def build_claim_gating(
    *,
    metadata: pd.DataFrame,
    annotation_confidence: pd.DataFrame,
    marker_heatmap: pd.DataFrame,
    stratified_summary: pd.DataFrame,
    stratified_nodes: pd.DataFrame,
    bootstrap_summary: pd.DataFrame,
    sample_level_summary: pd.DataFrame | None = None,
    permutation_node_scores: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    support = sample_support_table(metadata)
    specificity = marker_specificity_table(marker_heatmap)

    top_by_lesion = {
        row.lesion_type: row.top_frustration_cell_type
        for row in stratified_summary.itertuples(index=False)
        if getattr(row, "status", "") == "completed"
    }
    lesions = sorted(top_by_lesion)
    bootstrap_map = bootstrap_summary.set_index("cell_type")["top_frequency"].to_dict()
    annotation = annotation_confidence.set_index("cell_type").to_dict(orient="index")
    spec_map = specificity.set_index("cell_type").to_dict(orient="index")
    permutation_map: dict[str, dict[str, object]] = {}
    expression_mode_top = ""
    if permutation_node_scores is not None and not permutation_node_scores.empty:
        permutation = permutation_node_scores.copy()
        score_col = (
            "observed_frustration_score"
            if "observed_frustration_score" in permutation.columns
            else "frustration_score"
        )
        if score_col in permutation.columns and "cell_type" in permutation.columns:
            permutation = permutation.sort_values(score_col, ascending=False)
            expression_mode_top = str(permutation.iloc[0]["cell_type"])
            permutation_map = permutation.set_index("cell_type").to_dict(orient="index")

    rows = []
    for cell_type in sorted(metadata["cell_type"].astype(str).unique()):
        support_rows = support.loc[support["cell_type"] == cell_type].copy()
        tiers = support_rows["evidence_tier"].tolist()
        lesion_support = {
            f"{row.lesion_type}_tier": row.evidence_tier
            for row in support_rows.itertuples(index=False)
        }
        top_in_all = bool(lesions) and all(top_by_lesion[lesion] == cell_type for lesion in lesions)
        top_frequency = float(bootstrap_map.get(cell_type, 0.0))
        gate = claim_gate_for_cell_type(
            tiers=tiers,
            top_in_all_lesions=top_in_all,
            bootstrap_top_frequency=top_frequency,
        )
        permutation_row = permutation_map.get(cell_type, {})
        expression_score = permutation_row.get("observed_frustration_score", pd.NA)
        expression_fdr = permutation_row.get("frustration_fdr", pd.NA)
        mode_consistency_status = "not_evaluated"
        mode_consistency_note = "expression-mode permutation/FDR table not available"
        if expression_mode_top:
            if cell_type != expression_mode_top:
                mode_consistency_status = "discordant_with_expression_mode_top"
                mode_consistency_note = (
                    f"expression-mode top source is {expression_mode_top}; "
                    f"{cell_type} is not promoted to a main claim"
                )
                if gate == "main_claim":
                    gate = "supplement_only"
            elif pd.notna(expression_fdr) and float(expression_fdr) > 0.05:
                mode_consistency_status = "expression_mode_top_but_fdr_above_0_05"
                mode_consistency_note = (
                    f"{cell_type} is expression-mode top source but BH-FDR="
                    f"{float(expression_fdr):.3g}; retain as hypothesis only"
                )
                if gate == "main_claim":
                    gate = "supplement_only"
            else:
                mode_consistency_status = "consistent_with_expression_mode"
                if pd.notna(expression_fdr):
                    mode_consistency_note = (
                        f"{cell_type} is expression-mode top source with BH-FDR="
                        f"{float(expression_fdr):.3g}"
                    )
                else:
                    mode_consistency_note = (
                        f"{cell_type} is expression-mode top source; FDR not available"
                    )
        primary_node = stratified_nodes.loc[
            (stratified_nodes["lesion_type"] == "Primary") & (stratified_nodes["cell_type"] == cell_type)
        ]
        metastatic_node = stratified_nodes.loc[
            (stratified_nodes["lesion_type"] == "Metastatic") & (stratified_nodes["cell_type"] == cell_type)
        ]
        row = {
            "cell_type": cell_type,
            "claim_gate": gate,
            "claim_gate_reason": CLAIM_NOTE,
            "top_in_all_lesions": top_in_all,
            "bootstrap_top_frequency": top_frequency,
            "primary_frustration_score": (
                float(primary_node["frustration_score"].iloc[0]) if len(primary_node) else pd.NA
            ),
            "metastatic_frustration_score": (
                float(metastatic_node["frustration_score"].iloc[0]) if len(metastatic_node) else pd.NA
            ),
            "total_n_cells": int(support_rows["n_cells"].sum()) if len(support_rows) else 0,
            "min_lesion_n_cells": int(support_rows["n_cells"].min()) if len(support_rows) else 0,
            "min_lesion_n_samples": int(support_rows["n_samples"].min()) if len(support_rows) else 0,
            "all_lesions_adequate": all(tier == "adequate" for tier in tiers) if tiers else False,
            "expression_mode_top_cell_type": expression_mode_top,
            "expression_mode_frustration_score": expression_score,
            "expression_mode_frustration_fdr": expression_fdr,
            "mode_consistency_status": mode_consistency_status,
            "mode_consistency_note": mode_consistency_note,
            "manuscript_use": (
                "main_text_candidate"
                if gate == "main_claim"
                else ("supplement_qc_only" if gate == "qc_warning_only" else "supplement_context")
            ),
        }
        row.update(lesion_support)
        row.update(
            {
                "median_marker_score": annotation.get(cell_type, {}).get("median_marker_score", pd.NA),
                "median_marker_score_margin": annotation.get(cell_type, {}).get(
                    "median_marker_score_margin",
                    pd.NA,
                ),
                "low_margin_fraction_lt_0_05": annotation.get(cell_type, {}).get(
                    "low_margin_fraction_lt_0_05",
                    pd.NA,
                ),
                "marker_specificity_margin": spec_map.get(cell_type, {}).get(
                    "marker_specificity_margin",
                    pd.NA,
                ),
            }
        )
        rows.append(row)

    gating = pd.DataFrame(rows).sort_values(
        ["claim_gate", "bootstrap_top_frequency", "total_n_cells"],
        ascending=[True, False, False],
    )

    myeloid = gating.loc[gating["cell_type"] == "Myeloid"].copy()
    if myeloid.empty:
        readiness = pd.DataFrame(
            [
                {
                    "candidate_cell_type": "Myeloid",
                    "main_claim_ready": False,
                    "claim_gate": "missing",
                    "claim_sentence": MYELOID_CLAIM_SENTENCE,
                    "review_response_sentence": CLAIM_NOTE,
                }
            ]
        )
    else:
        row = myeloid.iloc[0]
        readiness_row = {
            "candidate_cell_type": "Myeloid",
            "main_claim_ready": row["claim_gate"] == "main_claim",
            "claim_gate": row["claim_gate"],
            "bootstrap_top_frequency": row["bootstrap_top_frequency"],
            "primary_frustration_score": row["primary_frustration_score"],
            "metastatic_frustration_score": row["metastatic_frustration_score"],
            "min_lesion_n_cells": row["min_lesion_n_cells"],
            "min_lesion_n_samples": row["min_lesion_n_samples"],
            "median_marker_score_margin": row["median_marker_score_margin"],
            "low_margin_fraction_lt_0_05": row["low_margin_fraction_lt_0_05"],
            "marker_specificity_margin": row["marker_specificity_margin"],
            "claim_sentence": MYELOID_CLAIM_SENTENCE,
            "review_response_sentence": CLAIM_NOTE,
        }
        if sample_level_summary is not None and not sample_level_summary.empty:
            sample_map = sample_level_summary.set_index("lesion_type").to_dict(orient="index")
            for label in ["all", "Primary", "Metastatic"]:
                values = sample_map.get(label, {})
                key = label.lower()
                readiness_row[f"sample_level_{key}_top_frequency_completed"] = values.get(
                    "myeloid_top_frequency_completed",
                    pd.NA,
                )
                readiness_row[f"sample_level_{key}_top_frequency_adequate"] = values.get(
                    "myeloid_top_frequency_adequate",
                    pd.NA,
                )
            readiness_row["sample_level_interpretation_note"] = (
                "sample-level analysis is a heterogeneity check; pooled and bootstrap "
                "signals should not be interpreted as universal in every sample"
            )
        readiness = pd.DataFrame([readiness_row])
    return support, gating, readiness


def run_claim_gating(
    *,
    processed_dir: Path,
    qc_dir: Path,
    stratified_dir: Path,
    stability_dir: Path,
    figure_manifest: Path,
) -> dict[str, Path]:
    metadata = pd.read_csv(processed_dir / "metadata.csv")
    annotation_confidence = pd.read_csv(qc_dir / "annotation_confidence.csv")
    marker_heatmap = pd.read_csv(qc_dir / "marker_heatmap.csv")
    stratified_summary = pd.read_csv(stratified_dir / "lesion_sheafsignal_summary.csv")
    stratified_nodes = pd.read_csv(stratified_dir / "lesion_frustration_by_cell_type.csv")
    bootstrap_summary = pd.read_csv(stability_dir / "bootstrap_frustration_summary.csv")
    sample_level_path = stability_dir / "sample_level_myeloid_stability_summary.csv"
    sample_level_summary = pd.read_csv(sample_level_path) if sample_level_path.exists() else None
    permutation_path = qc_dir.parent / "results" / "frustration_permutation_pvalues.csv"
    permutation_node_scores = pd.read_csv(permutation_path) if permutation_path.exists() else None

    support, gating, readiness = build_claim_gating(
        metadata=metadata,
        annotation_confidence=annotation_confidence,
        marker_heatmap=marker_heatmap,
        stratified_summary=stratified_summary,
        stratified_nodes=stratified_nodes,
        bootstrap_summary=bootstrap_summary,
        sample_level_summary=sample_level_summary,
        permutation_node_scores=permutation_node_scores,
    )

    support_path = qc_dir / "sample_support_by_cell_type.csv"
    gating_path = qc_dir / "claim_gating_by_cell_type.csv"
    readiness_path = qc_dir / "myeloid_claim_readiness_summary.csv"
    support.to_csv(support_path, index=False)
    gating.to_csv(gating_path, index=False)
    readiness.to_csv(readiness_path, index=False)
    update_figure_manifest(
        figure_manifest,
        gating_path,
        figure_id="supp_gse154778_claim_gating_table",
    )
    update_figure_manifest(
        figure_manifest,
        readiness_path,
        figure_id="supp_gse154778_myeloid_claim_readiness_table",
    )
    return {
        "support": support_path,
        "gating": gating_path,
        "readiness": readiness_path,
        "figure_manifest": figure_manifest,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-id", default="gse154778_pdac_scrna")
    parser.add_argument("--processed-dir", default=None)
    parser.add_argument("--qc-dir", default=None)
    parser.add_argument("--stratified-dir", default=None)
    parser.add_argument("--stability-dir", default=None)
    parser.add_argument("--figure-manifest", default="manuscript/figure_manifest.tsv")
    args = parser.parse_args(argv)

    dataset_id = args.dataset_id
    qc_dir = Path(args.qc_dir or f"benchmarks/results/{dataset_id}/qc")
    paths = run_claim_gating(
        processed_dir=Path(args.processed_dir or f"data/processed/{dataset_id}"),
        qc_dir=qc_dir,
        stratified_dir=Path(args.stratified_dir or f"benchmarks/results/{dataset_id}/stratified"),
        stability_dir=Path(args.stability_dir or f"benchmarks/results/{dataset_id}/stability"),
        figure_manifest=Path(args.figure_manifest),
    )
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
