from pathlib import Path

import pandas as pd

from scripts.build_confirmatory_permutation_subset import (
    CONFIRMATORY_DATASET,
    READINESS_PATH,
    REPORT_PATH,
    ROUND2_POOLED_FDR,
    SUBSET_PATH,
    build_outputs,
    classify_decision,
)


def _write_round2_fixture(root: Path) -> None:
    pooled_path = root / ROUND2_POOLED_FDR
    pooled_path.parent.mkdir(parents=True, exist_ok=True)
    source = (
        "benchmarks/results/round2_hardening/"
        f"{CONFIRMATORY_DATASET}/results/global_permutation_pvalues.csv"
    )
    pooled = pd.DataFrame(
        [
            {
                "dataset_id": CONFIRMATORY_DATASET,
                "family": "global_metrics",
                "label": "curl_ratio",
                "p_value": 0.001,
                "source_table": source,
                "pooled_fdr_within_family": 0.004,
                "pooled_fdr_all_tests": 0.003,
            },
            {
                "dataset_id": CONFIRMATORY_DATASET,
                "family": "node_frustration",
                "label": "Myeloid",
                "p_value": 0.001,
                "source_table": source.replace("global", "frustration"),
                "pooled_fdr_within_family": 0.002,
                "pooled_fdr_all_tests": 0.003,
            },
            {
                "dataset_id": CONFIRMATORY_DATASET,
                "family": "edge_sheaf_energy",
                "label": "Myeloid->Tumor/Epithelial",
                "p_value": 0.001,
                "source_table": source.replace("global", "sheaf_energy"),
                "pooled_fdr_within_family": 0.006,
                "pooled_fdr_all_tests": 0.003,
            },
            {
                "dataset_id": CONFIRMATORY_DATASET,
                "family": "edge_curl",
                "label": "Myeloid->CAF/Fibroblast",
                "p_value": 0.001,
                "source_table": source.replace("global", "sheaf_energy"),
                "pooled_fdr_within_family": 0.002,
                "pooled_fdr_all_tests": 0.003,
            },
        ]
    )
    pooled.to_csv(pooled_path, index=False)

    result_root = root / "benchmarks/results/round2_hardening" / CONFIRMATORY_DATASET / "results"
    result_root.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [{"metric": "curl_ratio", "empirical_p": 0.001, "n_permutations": 1000}]
    ).to_csv(result_root / "global_permutation_pvalues.csv", index=False)
    pd.DataFrame(
        [{"cell_type": "Myeloid", "frustration_empirical_p": 0.001, "n_permutations": 1000}]
    ).to_csv(result_root / "frustration_permutation_pvalues.csv", index=False)
    pd.DataFrame(
        [
            {
                "edge_id": "Myeloid->Tumor/Epithelial",
                "sheaf_energy_empirical_p": 0.001,
                "curl_empirical_p": 0.5,
                "n_permutations": 1000,
            },
            {
                "edge_id": "Myeloid->CAF/Fibroblast",
                "sheaf_energy_empirical_p": 0.9,
                "curl_empirical_p": 0.001,
                "n_permutations": 1000,
            },
        ]
    ).to_csv(result_root / "sheaf_energy_permutation_pvalues.csv", index=False)


def _write_confirmatory_fixture(root: Path) -> None:
    result_root = (
        root
        / "benchmarks"
        / "results"
        / "confirmatory_10000"
        / CONFIRMATORY_DATASET
        / "results"
    )
    result_root.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "metric": "curl_ratio",
                "empirical_p": 0.0001,
                "fdr": 0.0004,
                "n_permutations": 10000,
            }
        ]
    ).to_csv(result_root / "global_permutation_pvalues.csv", index=False)
    pd.DataFrame(
        [
            {
                "cell_type": "Myeloid",
                "observed_frustration_score": 0.2,
                "frustration_empirical_p": 0.0001,
                "frustration_fdr": 0.0002,
                "n_permutations": 10000,
            }
        ]
    ).to_csv(result_root / "frustration_permutation_pvalues.csv", index=False)
    pd.DataFrame(
        [
            {
                "edge_id": "Myeloid->Tumor/Epithelial",
                "sheaf_energy_empirical_p": 0.0001,
                "sheaf_energy_fdr": 0.0006,
                "curl_empirical_p": 0.7,
                "curl_fdr": 0.8,
                "n_permutations": 10000,
            },
            {
                "edge_id": "Myeloid->CAF/Fibroblast",
                "sheaf_energy_empirical_p": 0.8,
                "sheaf_energy_fdr": 0.8,
                "curl_empirical_p": 0.0001,
                "curl_fdr": 0.0002,
                "n_permutations": 10000,
            },
        ]
    ).to_csv(result_root / "sheaf_energy_permutation_pvalues.csv", index=False)

    summary_path = root / "benchmarks/results/confirmatory_10000/public_tme_sheafsignal_summary.csv"
    pd.DataFrame(
        [
            {
                "dataset_id": CONFIRMATORY_DATASET,
                "top_frustration_cell_type": "CAF/Fibroblast",
                "top_frustration_score": 0.43,
            }
        ]
    ).to_csv(summary_path, index=False)

    claim_path = root / "benchmarks/results/gse154778_pdac_scrna/qc/claim_gating_by_cell_type.csv"
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "cell_type": "CAF/Fibroblast",
                "claim_gate": "qc_warning_only",
                "manuscript_use": "supplement_qc_only",
                "claim_gate_reason": "sparse lesion support",
            },
            {
                "cell_type": "Myeloid",
                "claim_gate": "supplement_only",
                "manuscript_use": "supplement_context",
                "claim_gate_reason": "hypothesis only",
            },
        ]
    ).to_csv(claim_path, index=False)


def test_confirmatory_decision_ready_not_run():
    rows = [
        {
            "current_n_permutations": 1000,
            "confirmatory_result_status": "ready_not_run",
        }
    ]

    assert classify_decision(rows) == "CONFIRMATORY_10000_READY_NOT_RUN"


def test_confirmatory_decision_completed():
    rows = [
        {
            "current_n_permutations": 1000,
            "confirmatory_result_status": "completed_10000",
        }
    ]

    assert classify_decision(rows) == "CONFIRMATORY_10000_COMPLETED"


def test_build_outputs_writes_subset_and_status(tmp_path: Path):
    _write_round2_fixture(tmp_path)

    summary = build_outputs(tmp_path)

    assert summary["decision"] == "CONFIRMATORY_10000_READY_NOT_RUN"
    assert (tmp_path / SUBSET_PATH).exists()
    assert (tmp_path / READINESS_PATH).exists()
    assert (tmp_path / REPORT_PATH).exists()

    subset = pd.read_csv(tmp_path / SUBSET_PATH, sep="\t")
    assert set(subset["label"]).issuperset({"curl_ratio", "Myeloid"})
    assert subset["current_n_permutations"].min() == 1000
    assert subset["confirmatory_result_status"].eq("ready_not_run").all()


def test_build_outputs_records_completed_boundary_for_pooled_top_source(tmp_path: Path):
    _write_round2_fixture(tmp_path)
    _write_confirmatory_fixture(tmp_path)

    summary = build_outputs(tmp_path)

    assert summary["decision"] == "CONFIRMATORY_10000_COMPLETED"
    subset = pd.read_csv(tmp_path / SUBSET_PATH, sep="\t")
    assert subset["confirmatory_n_permutations"].min() == 10000
    assert subset["confirmatory_result_status"].eq("completed_10000").all()

    report = (tmp_path / REPORT_PATH).read_text(encoding="utf-8")
    assert "completed_statistical_strengthening_not_mechanism_validation" in report
    assert "pooled confirmatory summary ranks `CAF/Fibroblast`" in report
    assert "qc_warning_only" in report
    assert "Myeloid remains bounded" in report
