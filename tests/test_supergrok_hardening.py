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


def test_novelty_overlap_table_contains_required_comparison_classes(tmp_path):
    script = _load_script("build_novelty_overlap_table")

    paths = script.build_novelty_overlap_table(tmp_path)

    table = pd.read_csv(paths["table"], sep="\t")
    assert {
        "standard_ccc_tools",
        "graph_signal_processing",
        "hodge_biology_omics",
        "cellular_sheaf_methods",
    }.issubset(set(table["comparison_class"]))
    assert paths["report"].exists()


def test_claim_hardening_flags_unqualified_driver_language(tmp_path):
    script = _load_script("check_manuscript_claim_hardening")
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "SCI_MANUSCRIPT_V2_POLISHED.md").write_text(
        "Myeloid is a driver of frustration.\n"
        "This is a computational hypothesis-generating signal, not a driver claim.\n",
        encoding="utf-8",
    )

    audit = script.scan_claims(tmp_path)

    assert "blocking_risky_claim" in set(audit["classification"])
    assert "boundary_context" in set(audit["classification"])


def test_sensitivity_panel_computes_edge_threshold_rows(tmp_path):
    script = _load_script("build_sensitivity_panel")
    results = tmp_path / "benchmarks" / "results"
    dataset_dir = results / "toy_dataset" / "results"
    dataset_dir.mkdir(parents=True)
    pd.DataFrame(
        [
            {"dataset_id": "toy_dataset", "status": "completed"},
        ]
    ).to_csv(results / "public_tme_sheafsignal_summary.csv", index=False)
    pd.DataFrame(
        {
            "sender": ["A", "A", "B", "C"],
            "receiver": ["B", "C", "C", "A"],
            "communication_flow": [1.0, 2.0, 3.0, 4.0],
            "sheaf_energy": [0.2, 0.5, 0.7, 0.1],
            "flow_z": [0.1, 0.4, -0.2, 0.3],
        }
    ).to_csv(dataset_dir / "sheaf_energy_by_edge.csv", index=False)

    paths = script.build_sensitivity_panel(results, results / "sensitivity")

    panel = pd.read_csv(paths["table"])
    assert "edge_threshold" in set(panel["sensitivity_axis"])
    assert "permutation_fdr" in set(panel["sensitivity_axis"])
    assert paths["report"].exists()


def test_sensitivity_panel_reads_pipeline_permutation_filename(tmp_path):
    script = _load_script("build_sensitivity_panel")
    results = tmp_path / "benchmarks" / "results"
    dataset_dir = results / "toy_dataset" / "results"
    dataset_dir.mkdir(parents=True)
    pd.DataFrame([{"dataset_id": "toy_dataset", "status": "completed"}]).to_csv(
        results / "public_tme_sheafsignal_summary.csv",
        index=False,
    )
    pd.DataFrame(
        {
            "sender": ["A", "B"],
            "receiver": ["B", "A"],
            "communication_flow": [1.0, 2.0],
            "sheaf_energy": [0.2, 0.5],
            "flow_z": [0.1, -0.1],
        }
    ).to_csv(dataset_dir / "sheaf_energy_by_edge.csv", index=False)
    pd.DataFrame(
        {
            "sheaf_energy_empirical_p": [0.01, 0.2],
        }
    ).to_csv(dataset_dir / "sheaf_energy_permutation_pvalues.csv", index=False)

    paths = script.build_sensitivity_panel(results, results / "sensitivity")

    panel = pd.read_csv(paths["table"])
    fdr = panel.loc[panel["sensitivity_axis"] == "permutation_fdr"].iloc[0]
    assert str(fdr["statistical_status"]).startswith("min_fdr=")


def test_reannotation_readiness_reports_missing_optional_dependencies(tmp_path):
    script = _load_script("reannotate_gse154778_scanpy")
    processed = tmp_path / "processed"
    processed.mkdir()
    pd.DataFrame({"cell_id": ["P01:1"], "cell_type": ["Myeloid"]}).to_csv(
        processed / "metadata.csv",
        index=False,
    )

    paths = script.build_reannotation_readiness(
        raw_path=tmp_path / "missing_dge.csv.gz",
        processed_dir=processed,
        output_dir=tmp_path / "reannotation",
    )

    readiness = pd.read_csv(paths["readiness"])
    assert "raw_processed_geo_matrix" in set(readiness["check_id"])
    assert "missing_input" in set(readiness["status"])
    assert paths["report"].exists()


def test_reannotation_h5ad_builder_preserves_sample_metadata(tmp_path):
    script = _load_script("reannotate_gse154778_scanpy")
    raw_path = tmp_path / "GSE154778_dgeMtx.csv.gz"
    pd.DataFrame(
        {
            "P01:1": [1, 0, 3],
            "MET01:1": [0, 2, 4],
        },
        index=["EPCAM", "LYZ", "KRT19"],
    ).to_csv(raw_path, compression="gzip")
    metadata = tmp_path / "metadata.csv"
    pd.DataFrame(
        {
            "cell_id": ["P01:1", "MET01:1"],
            "cell_type": ["Tumor/Epithelial", "Myeloid"],
        }
    ).to_csv(metadata, index=False)
    h5ad_path = tmp_path / "gse154778.h5ad"

    script.build_gse154778_h5ad(
        raw_path=raw_path,
        current_metadata_path=metadata,
        output_h5ad=h5ad_path,
    )

    import anndata as ad

    adata = ad.read_h5ad(h5ad_path)
    assert list(adata.obs_names) == ["P01:1", "MET01:1"]
    assert list(adata.var_names) == ["EPCAM", "LYZ", "KRT19"]
    assert list(adata.obs["lesion_type"]) == ["Primary", "Metastatic"]
    assert "coarse_cell_type" in adata.obs.columns
