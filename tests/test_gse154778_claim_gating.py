from pathlib import Path
import importlib.util

import pandas as pd


def _load_claim_script():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "qc_gse154778_claim_gating.py"
    spec = importlib.util.spec_from_file_location("qc_gse154778_claim_gating", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_evidence_tier_thresholds():
    claim = _load_claim_script()
    assert claim.evidence_tier(19, 10) == "unsupported"
    assert claim.evidence_tier(20, 10) == "borderline"
    assert claim.evidence_tier(50, 2) == "borderline"
    assert claim.evidence_tier(50, 3) == "adequate"


def test_claim_gate_rules():
    claim = _load_claim_script()
    assert (
        claim.claim_gate_for_cell_type(
            tiers=["unsupported", "adequate"],
            top_in_all_lesions=True,
            bootstrap_top_frequency=1.0,
        )
        == "qc_warning_only"
    )
    assert (
        claim.claim_gate_for_cell_type(
            tiers=["adequate", "adequate"],
            top_in_all_lesions=True,
            bootstrap_top_frequency=0.9,
        )
        == "main_claim"
    )


def test_build_claim_gating_marks_myeloid_main_and_sparse_caf_warning():
    claim = _load_claim_script()
    metadata_rows = []
    for lesion, samples, counts in [
        ("Primary", ["P01", "P02", "P03"], {"Myeloid": 60, "CAF/Fibroblast": 60}),
        ("Metastatic", ["M01", "M02", "M03"], {"Myeloid": 60, "CAF/Fibroblast": 2}),
    ]:
        for cell_type, n_cells in counts.items():
            for idx in range(n_cells):
                metadata_rows.append(
                    {
                        "cell_id": f"{lesion}_{cell_type}_{idx}",
                        "cell_type": cell_type,
                        "sample_id": samples[idx % len(samples)],
                        "lesion_type": lesion,
                    }
                )
    metadata = pd.DataFrame(metadata_rows)
    annotation = pd.DataFrame(
        {
            "cell_type": ["Myeloid", "CAF/Fibroblast"],
            "n_cells": [120, 62],
            "median_marker_score": [1.0, 1.0],
            "median_marker_score_margin": [0.5, 0.5],
            "low_margin_fraction_lt_0_05": [0.01, 0.01],
        }
    )
    marker_heatmap = pd.DataFrame(
        {
            "cell_type": ["Myeloid", "CAF/Fibroblast", "Myeloid", "CAF/Fibroblast"],
            "marker_group": ["Myeloid", "Myeloid", "CAF/Fibroblast", "CAF/Fibroblast"],
            "gene": ["LYZ", "LYZ", "COL1A1", "COL1A1"],
            "mean_expression": [5.0, 1.0, 1.0, 5.0],
        }
    )
    stratified_summary = pd.DataFrame(
        {
            "lesion_type": ["Primary", "Metastatic"],
            "status": ["completed", "completed"],
            "top_frustration_cell_type": ["Myeloid", "Myeloid"],
        }
    )
    stratified_nodes = pd.DataFrame(
        {
            "lesion_type": ["Primary", "Metastatic", "Primary", "Metastatic"],
            "cell_type": ["Myeloid", "Myeloid", "CAF/Fibroblast", "CAF/Fibroblast"],
            "frustration_score": [0.5, 0.8, 0.2, 0.1],
        }
    )
    bootstrap = pd.DataFrame(
        {
            "cell_type": ["Myeloid", "CAF/Fibroblast"],
            "top_frequency": [1.0, 0.0],
        }
    )

    support, gating, readiness = claim.build_claim_gating(
        metadata=metadata,
        annotation_confidence=annotation,
        marker_heatmap=marker_heatmap,
        stratified_summary=stratified_summary,
        stratified_nodes=stratified_nodes,
        bootstrap_summary=bootstrap,
    )

    assert set(support["evidence_tier"]) == {"adequate", "unsupported"}
    myeloid_gate = gating.loc[gating["cell_type"] == "Myeloid", "claim_gate"].iloc[0]
    caf_gate = gating.loc[gating["cell_type"] == "CAF/Fibroblast", "claim_gate"].iloc[0]
    assert myeloid_gate == "main_claim"
    assert caf_gate == "qc_warning_only"
    assert bool(readiness.iloc[0]["main_claim_ready"]) is True


def test_expression_mode_permutation_downgrades_discordant_myeloid_claim():
    claim = _load_claim_script()
    metadata_rows = []
    for lesion, samples in [
        ("Primary", ["P01", "P02", "P03"]),
        ("Metastatic", ["M01", "M02", "M03"]),
    ]:
        for cell_type in ["Myeloid", "CAF/Fibroblast"]:
            for idx in range(60):
                metadata_rows.append(
                    {
                        "cell_id": f"{lesion}_{cell_type}_{idx}",
                        "cell_type": cell_type,
                        "sample_id": samples[idx % len(samples)],
                        "lesion_type": lesion,
                    }
                )
    metadata = pd.DataFrame(metadata_rows)
    annotation = pd.DataFrame(
        {
            "cell_type": ["Myeloid", "CAF/Fibroblast"],
            "median_marker_score": [1.0, 1.0],
            "median_marker_score_margin": [0.5, 0.5],
            "low_margin_fraction_lt_0_05": [0.01, 0.01],
        }
    )
    marker_heatmap = pd.DataFrame(
        {
            "cell_type": ["Myeloid", "CAF/Fibroblast"],
            "marker_group": ["Myeloid", "CAF/Fibroblast"],
            "mean_expression": [5.0, 5.0],
        }
    )
    stratified_summary = pd.DataFrame(
        {
            "lesion_type": ["Primary", "Metastatic"],
            "status": ["completed", "completed"],
            "top_frustration_cell_type": ["Myeloid", "Myeloid"],
        }
    )
    stratified_nodes = pd.DataFrame(
        {
            "lesion_type": ["Primary", "Metastatic"],
            "cell_type": ["Myeloid", "Myeloid"],
            "frustration_score": [0.5, 0.8],
        }
    )
    bootstrap = pd.DataFrame(
        {"cell_type": ["Myeloid", "CAF/Fibroblast"], "top_frequency": [1.0, 0.0]}
    )
    permutation = pd.DataFrame(
        {
            "cell_type": ["CAF/Fibroblast", "Myeloid"],
            "observed_frustration_score": [0.31, 0.13],
            "frustration_fdr": [0.069, 0.208],
        }
    )

    _, gating, readiness = claim.build_claim_gating(
        metadata=metadata,
        annotation_confidence=annotation,
        marker_heatmap=marker_heatmap,
        stratified_summary=stratified_summary,
        stratified_nodes=stratified_nodes,
        bootstrap_summary=bootstrap,
        permutation_node_scores=permutation,
    )

    myeloid = gating.loc[gating["cell_type"] == "Myeloid"].iloc[0]
    assert myeloid["claim_gate"] == "supplement_only"
    assert myeloid["mode_consistency_status"] == "discordant_with_expression_mode_top"
    assert bool(readiness.iloc[0]["main_claim_ready"]) is False
