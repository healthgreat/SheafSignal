from pathlib import Path

import pandas as pd

from scripts.build_gse103322_replication_supplement import (
    ANNOTATION_SUMMARY_PATH,
    DATASET_ID,
    EDGE_PATH,
    GLOBAL_PERMUTATION_PATH,
    LR_ALIGNMENT_PATH,
    METADATA_PATH,
    NODE_PERMUTATION_PATH,
    PUBLIC_SUMMARY_PATH,
    READINESS_PATH,
    REPORT_PATH,
    SUMMARY_PATH,
    build_outputs,
    classify_decision,
)


def _write_fixture(root: Path, n_permutations: int = 100, strata: str = "") -> None:
    public_path = root / PUBLIC_SUMMARY_PATH
    public_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "dataset_id": DATASET_ID,
                "status": "completed",
                "n_edges": 2,
                "top_frustration_cell_type": "Endothelial",
                "top_frustration_score": 0.2,
            }
        ]
    ).to_csv(public_path, index=False)

    metadata_path = root / METADATA_PATH
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "cell_id": "c1",
                "cell_type": "Endothelial",
                "sample_id": "s1",
                "patient_id": "p1",
                "lesion_type": "Primary",
            },
            {
                "cell_id": "c2",
                "cell_type": "Myeloid",
                "sample_id": "s2",
                "patient_id": "p2",
                "lesion_type": "LymphNode",
            },
        ]
    ).to_csv(metadata_path, index=False)

    annotation_path = root / ANNOTATION_SUMMARY_PATH
    annotation_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{"cell_type": "Endothelial", "lesion_type": "Primary", "n_cells": 1}]).to_csv(
        annotation_path, index=False
    )

    global_path = root / GLOBAL_PERMUTATION_PATH
    global_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "metric": "curl_ratio",
                "observed": 0.03,
                "fdr": 0.04,
                "n_permutations": n_permutations,
                "permutation_strata_col": strata,
            }
        ]
    ).to_csv(global_path, index=False)

    node_path = root / NODE_PERMUTATION_PATH
    node_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "cell_type": "Endothelial",
                "observed_frustration_score": 0.2,
                "frustration_fdr": 0.2,
                "n_permutations": n_permutations,
                "permutation_strata_col": strata,
            }
        ]
    ).to_csv(node_path, index=False)

    edge_path = root / EDGE_PATH
    edge_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {"sender": "Endothelial", "receiver": "Myeloid", "sheaf_energy": 1.0},
            {"sender": "Myeloid", "receiver": "Endothelial", "sheaf_energy": 0.5},
        ]
    ).to_csv(edge_path, index=False)

    lr_path = root / LR_ALIGNMENT_PATH
    lr_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {"sheaf_energy": 1.0, "comparator_edge_score": 2.0},
            {"sheaf_energy": 0.5, "comparator_edge_score": 1.0},
        ]
    ).to_csv(lr_path, index=False)


def test_decision_exploratory_when_permutation_is_low_or_unstratified():
    summary = {
        "benchmark_status": "completed",
        "n_cells": 2,
        "min_n_permutations": 100,
        "permutation_strata_status": "missing_or_unstratified",
    }

    assert classify_decision(summary) == "GSE103322_REPLICATION_EXPLORATORY_READY_RERUN_RECOMMENDED"


def test_decision_ready_when_1000_sample_stratified():
    summary = {
        "benchmark_status": "completed",
        "n_cells": 2,
        "min_n_permutations": 1000,
        "permutation_strata_status": "sample_id_stratified",
    }

    assert classify_decision(summary) == "GSE103322_REPLICATION_SUPPLEMENT_READY"


def test_build_outputs_writes_replication_report(tmp_path: Path):
    _write_fixture(tmp_path)

    summary = build_outputs(tmp_path)

    assert summary["decision"] == "GSE103322_REPLICATION_EXPLORATORY_READY_RERUN_RECOMMENDED"
    assert (tmp_path / SUMMARY_PATH).exists()
    assert (tmp_path / READINESS_PATH).exists()
    assert (tmp_path / REPORT_PATH).exists()

    table = pd.read_csv(tmp_path / SUMMARY_PATH, sep="\t")
    assert int(table.loc[0, "n_cells"]) == 2
    assert table.loc[0, "permutation_strata_status"] == "missing_or_unstratified"
