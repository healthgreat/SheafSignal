from pathlib import Path
import importlib.util

import pandas as pd


def _load_script():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "check_benchmark_result_contracts.py"
    spec = importlib.util.spec_from_file_location("check_benchmark_result_contracts", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_fixture(root: Path) -> None:
    results = root / "benchmarks" / "results"
    results.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "scenario": "gradient_chain",
                "expected_dominant_component": "gradient_ratio",
                "gradient_ratio": 1.0,
                "curl_ratio": 0.0,
                "harmonic_ratio": 0.0,
                "total_flow_energy": 4.0,
                "n_pair_edges": 4,
                "n_triangles": 0,
            },
            {
                "scenario": "triangle_curl",
                "expected_dominant_component": "curl_ratio",
                "gradient_ratio": 0.0,
                "curl_ratio": 1.0,
                "harmonic_ratio": 0.0,
                "total_flow_energy": 3.0,
                "n_pair_edges": 3,
                "n_triangles": 1,
            },
            {
                "scenario": "harmonic_ring",
                "expected_dominant_component": "harmonic_ratio",
                "gradient_ratio": 0.0,
                "curl_ratio": 0.0,
                "harmonic_ratio": 1.0,
                "total_flow_energy": 5.0,
                "n_pair_edges": 5,
                "n_triangles": 0,
            },
            {
                "scenario": "mixed",
                "expected_dominant_component": "mixed",
                "gradient_ratio": 0.4,
                "curl_ratio": 0.3,
                "harmonic_ratio": 0.3,
                "total_flow_energy": 6.0,
                "n_pair_edges": 11,
                "n_triangles": 1,
            },
        ]
    ).to_csv(results / "component_recovery.csv", index=False)

    pd.DataFrame(
        [
            {
                "dataset_id": dataset_id,
                "modality": "scRNA-seq",
                "disease": "TME",
                "status": "completed",
                "input_mode": "profile",
                "n_edges": 42,
                "n_cell_types": 7,
                "total_sheaf_energy": 10.0,
                "gradient_ratio": 0.8,
                "curl_ratio": 0.1,
                "harmonic_ratio": 0.1,
                "top_frustration_cell_type": "Myeloid",
                "top_frustration_score": 0.5,
            }
            for dataset_id in [
                "gse72056_melanoma_scrna",
                "gse154778_pdac_scrna",
                "gse176078_brca_scrna",
                "tenx_breast_visium",
            ]
        ]
    ).to_csv(results / "public_tme_sheafsignal_summary.csv", index=False)

    comparator_rows = []
    for tool, datasets in {
        "LRProductBaseline": [
            "gse72056_melanoma_scrna",
            "gse154778_pdac_scrna",
            "gse176078_brca_scrna",
            "tenx_breast_visium",
        ],
        "LIANA": [
            "gse72056_melanoma_scrna",
            "gse154778_pdac_scrna",
            "gse176078_brca_scrna",
        ],
        "NicheNet": [
            "gse72056_melanoma_scrna",
            "gse154778_pdac_scrna",
            "gse176078_brca_scrna",
        ],
        "MechanisticTargetPrior": [
            "gse72056_melanoma_scrna",
            "gse154778_pdac_scrna",
            "gse176078_brca_scrna",
        ],
    }.items():
        for dataset_id in datasets:
            comp_dir = results / dataset_id / "comparators"
            comp_dir.mkdir(parents=True, exist_ok=True)
            edge = comp_dir / f"{tool.lower()}_edges.csv"
            aligned = comp_dir / f"sheafsignal_vs_{tool.lower()}.csv"
            pd.DataFrame([{"sender": "A", "receiver": "B", "score": 1.0}]).to_csv(
                edge,
                index=False,
            )
            pd.DataFrame([{"sender": "A", "receiver": "B", "score": 1.0}]).to_csv(
                aligned,
                index=False,
            )
            comparator_rows.append(
                {
                    "dataset_id": dataset_id,
                    "tool": tool,
                    "status": "completed_external_import",
                    "comparison_level": "cell_type_edge",
                    "edge_score_table": edge.relative_to(root).as_posix(),
                    "aligned_edge_table": aligned.relative_to(root).as_posix(),
                    "notes": "fixture",
                    "n_edges": 42,
                    "spearman_sheaf_energy_vs_tool_score": 0.3,
                    "high_sheaf_low_tool_edges": 1,
                    "high_tool_low_sheaf_edges": 1,
                    "concordant_high_edges": 2,
                    "unaligned_edges": 0,
                }
            )
    pd.DataFrame(comparator_rows).to_csv(results / "tool_comparison.csv", index=False)

    claim_dir = results / "gse154778_pdac_scrna" / "qc"
    claim_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "cell_type": "Myeloid",
                "claim_gate": "supplement_only",
                "total_n_cells": 1819,
                "min_lesion_n_cells": 497,
                "min_lesion_n_samples": 6,
                "manuscript_use": "supplement_context",
                "expression_mode_top_cell_type": "CAF/Fibroblast",
                "mode_consistency_status": "discordant_with_expression_mode_top",
            },
            {
                "cell_type": "CAF/Fibroblast",
                "claim_gate": "qc_warning_only",
                "total_n_cells": 2000,
                "min_lesion_n_cells": 2,
                "min_lesion_n_samples": 2,
                "manuscript_use": "supplement_qc_only",
                "expression_mode_top_cell_type": "CAF/Fibroblast",
                "mode_consistency_status": "expression_mode_top_but_fdr_above_0_05",
            },
        ]
    ).to_csv(claim_dir / "claim_gating_by_cell_type.csv", index=False)

    spatial_dir = results / "tenx_breast_visium" / "spatial" / "qc"
    spatial_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "dataset_id": "tenx_breast_visium",
                "k_neighbors": k,
                "n_spots": 3798,
                "n_spatial_edges": 3798 * k,
                "total_spatial_sheaf_energy": 100.0,
                "top_50_overlap_with_reference": 0.9,
                "spearman_with_reference": 0.95,
            }
            for k in [4, 6, 8, 10, 12]
        ]
    ).to_csv(spatial_dir / "k_neighbors_sensitivity.csv", index=False)


def test_benchmark_result_contract_audit_passes_fixture(tmp_path):
    script = _load_script()
    _write_fixture(tmp_path)

    audit = script.build_benchmark_contract_audit(tmp_path)
    report = script.build_benchmark_contract_report(audit)

    assert "fail" not in set(audit["status"])
    assert "BENCHMARK_RESULT_CONTRACT_PASS" in report
    assert "completed_comparator_metric_contract" in set(audit["check_id"])


def test_benchmark_result_contract_fails_bad_component_ratio(tmp_path):
    script = _load_script()
    _write_fixture(tmp_path)
    component = pd.read_csv(tmp_path / "benchmarks" / "results" / "component_recovery.csv")
    component.loc[component["scenario"] == "gradient_chain", "gradient_ratio"] = 0.5
    component.to_csv(tmp_path / "benchmarks" / "results" / "component_recovery.csv", index=False)

    audit = script.build_benchmark_contract_audit(tmp_path)
    row = audit.loc[audit["check_id"] == "component_recovery_metric_contract"].iloc[0]

    assert row["status"] == "fail"
    assert "dominant_failures" in row["evidence"]


def test_benchmark_result_contract_main_writes_outputs(tmp_path):
    script = _load_script()
    _write_fixture(tmp_path)

    exit_code = script.main(["--root", str(tmp_path)])

    assert exit_code == 0
    audit_path = tmp_path / "benchmarks" / "results" / "BENCHMARK_RESULT_CONTRACT_AUDIT.tsv"
    report_path = tmp_path / "benchmarks" / "results" / "BENCHMARK_RESULT_CONTRACT_REPORT.md"
    assert audit_path.exists()
    assert report_path.exists()
    assert not audit_path.with_suffix(audit_path.suffix + ".tmp").exists()
    assert "BENCHMARK_RESULT_CONTRACT_PASS" in report_path.read_text(encoding="utf-8")
