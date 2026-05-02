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


def _write_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    processed = tmp_path / "data" / "processed" / "toy_dataset"
    benchmark = tmp_path / "benchmarks" / "results" / "toy_dataset"
    results_dir = tmp_path / "benchmarks" / "results"
    processed.mkdir(parents=True)
    (benchmark / "results").mkdir(parents=True)

    pd.DataFrame(
        {
            "cell_type": ["A", "B", "C"],
            "L1": [1.0, 0.0, 0.0],
            "R1": [0.0, 2.0, 1.0],
        }
    ).to_csv(processed / "profiles.csv", index=False)
    pd.DataFrame(
        {
            "cell_type": ["A", "B", "C"],
            "lesion_type": ["Primary", "Primary", "Metastatic"],
            "n_cells": [10, 20, 30],
        }
    ).to_csv(processed / "annotation_summary.csv", index=False)
    pd.DataFrame({"ligand": ["L1"], "receptor": ["R1"], "weight": [1.0]}).to_csv(
        tmp_path / "lr.csv",
        index=False,
    )
    pd.DataFrame(
        {
            "sender": ["A", "A", "B"],
            "receiver": ["B", "C", "C"],
            "communication_flow": [2.0, 1.0, 0.2],
            "sheaf_energy": [5.0, 1.0, 3.0],
            "sheaf_mismatch": [2.0, 1.0, 1.5],
            "flow_z": [1.0, 0.0, -1.0],
            "pathway_gradient_z": [-1.0, 0.0, 0.5],
            "directional_agreement": [False, True, False],
            "curl_component": [0.1, 0.0, -0.1],
            "harmonic_component": [0.0, 0.0, 0.0],
            "top_lr_pairs": ["L1->R1", "L1->R1", ""],
        }
    ).to_csv(benchmark / "results" / "sheaf_energy_by_edge.csv", index=False)
    return processed, benchmark, results_dir


def test_export_comparator_inputs_writes_profile_level_bundle(tmp_path):
    export_script = _load_script("export_comparator_inputs")
    processed, benchmark, _ = _write_fixture(tmp_path)
    output_dir = tmp_path / "comparator_inputs"

    paths = export_script.export_comparator_inputs(
        dataset_id="toy_dataset",
        processed_dir=processed,
        benchmark_dir=benchmark,
        lr_db_path=tmp_path / "lr.csv",
        output_dir=output_dir,
    )

    for path in paths.values():
        assert Path(path).exists()
    template = pd.read_csv(output_dir / "external_comparator_template.csv")
    assert {"sender", "receiver", "score"}.issubset(template.columns)
    sheaf_template = pd.read_csv(output_dir / "sheafsignal_edge_template.csv")
    assert {"sender", "receiver", "sheaf_energy"}.issubset(sheaf_template.columns)


def test_export_all_completed_public_writes_summary(tmp_path, monkeypatch):
    export_script = _load_script("export_comparator_inputs")
    processed, benchmark, results_dir = _write_fixture(tmp_path)
    manifest = tmp_path / "metadata" / "datasets.tsv"
    manifest.parent.mkdir()
    pd.DataFrame(
        [
            {
                "dataset_id": "toy_dataset",
                "title": "Toy public dataset",
                "modality": "scRNA-seq",
                "species": "Homo sapiens",
                "tissue": "tumor",
                "disease": "cancer",
                "accession_or_doi": "TEST",
                "download_url": "https://example.org/toy.csv",
                "local_path": "data/external/toy.csv",
                "sha256": "PENDING_DOWNLOAD_VERIFICATION",
                "license_or_terms": "public test",
                "release_status": "manifested",
                "benchmark_role": "public_scrna_benchmark",
                "prepared_expression": str(processed / "expression.csv"),
                "prepared_metadata": str(processed / "metadata.csv"),
            }
        ]
    ).to_csv(manifest, sep="\t", index=False)

    monkeypatch.chdir(tmp_path)
    assert (
        export_script.main(
            [
                "--all-completed-public",
                "--manifest",
                str(manifest),
                "--results-dir",
                str(results_dir),
                "--lr-db",
                str(tmp_path / "lr.csv"),
            ]
        )
        == 0
    )

    summary = pd.read_csv(results_dir / "comparator_input_exports.csv")
    assert list(summary["dataset_id"]) == ["toy_dataset"]
    assert (benchmark / "comparator_inputs" / "external_comparator_template.csv").exists()


def test_import_external_comparator_aligns_and_updates_tool_table(tmp_path):
    import_script = _load_script("import_external_comparator")
    _, benchmark, results_dir = _write_fixture(tmp_path)
    external_path = tmp_path / "liana_edges.csv"
    pd.DataFrame(
        {
            "source": ["A", "A", "B"],
            "target": ["B", "B", "C"],
            "magnitude_rank": [0.3, 0.1, 0.8],
            "ligand": ["L1", "L2", "L3"],
            "receptor": ["R1", "R2", "R3"],
        }
    ).to_csv(external_path, index=False)

    paths = import_script.import_external_comparator(
        dataset_id="toy_dataset",
        tool="LIANA",
        input_path=external_path,
        benchmark_dir=benchmark,
        results_dir=results_dir,
        sender_col="source",
        receiver_col="target",
        score_col="magnitude_rank",
        ligand_col="ligand",
        receptor_col="receptor",
        aggregate="max",
        score_ascending=True,
        input_format="generic",
    )

    for path in paths.values():
        assert Path(path).exists()
    aligned = pd.read_csv(paths["aligned"])
    assert {"sheaf_energy", "comparator_edge_score", "discordance_class"}.issubset(
        aligned.columns
    )
    tool_table = pd.read_csv(paths["tool_comparison"])
    row = tool_table.loc[tool_table["tool"] == "LIANA"].iloc[0]
    assert row["status"] == "completed_external_import"
    assert "top_lr_jaccard" in tool_table.columns


def test_import_cellphonedb_comparator_wide_output(tmp_path):
    import_script = _load_script("import_external_comparator")
    _, benchmark, results_dir = _write_fixture(tmp_path)
    external_path = tmp_path / "cellphonedb_significant_means.txt"
    pd.DataFrame(
        {
            "interacting_pair": ["L1_R1", "L2_R2"],
            "gene_a": ["L1", "L2"],
            "gene_b": ["R1", "R2"],
            "A|B": [0.4, 0.3],
            "B|C": [0.0, 0.5],
        }
    ).to_csv(external_path, sep="\t", index=False)

    paths = import_script.import_external_comparator(
        dataset_id="toy_dataset",
        tool="CellPhoneDB",
        input_path=external_path,
        benchmark_dir=benchmark,
        results_dir=results_dir,
        sender_col="sender",
        receiver_col="receiver",
        score_col="score",
        ligand_col=None,
        receptor_col=None,
        aggregate="sum",
        score_ascending=False,
        input_format="cellphonedb",
    )

    standardized = pd.read_csv(paths["standardized"])
    assert {"sender", "receiver", "comparator_edge_score", "top_lr_pairs"}.issubset(
        standardized.columns
    )
    row = pd.read_csv(paths["tool_comparison"]).loc[
        lambda x: x["tool"] == "CellPhoneDB"
    ].iloc[0]
    assert row["status"] == "completed_external_import"


def test_cellphonedb_input_writer_creates_meta_counts_and_command(tmp_path):
    script = _load_script("run_cellphonedb_comparator")
    processed = tmp_path / "processed"
    processed.mkdir()
    pd.DataFrame(
        {
            "cell_id": ["c1", "c2"],
            "cell_type": ["A", "B"],
        }
    ).to_csv(processed / "metadata.csv", index=False)
    pd.DataFrame(
        {
            "cell_id": ["c1", "c2"],
            "L1": [1.0, 0.0],
            "R1": [0.0, 2.0],
        }
    ).to_csv(processed / "expression.csv", index=False)

    paths = script.prepare_cellphonedb_inputs(
        processed_dir=processed,
        output_dir=tmp_path / "cpdb",
    )

    assert paths["meta"].exists()
    assert paths["counts"].exists()
    assert "statistical_analysis" in paths["command"].read_text(encoding="utf-8")
    counts = pd.read_csv(paths["counts"], sep="\t")
    assert list(counts.columns) == ["Gene", "c1", "c2"]


def test_cellphonedb_api_fallback_marks_smoke_as_pending_full(tmp_path, monkeypatch):
    script = _load_script("run_cellphonedb_comparator")
    command_path = tmp_path / "cellphonedb_command.txt"
    meta_path = tmp_path / "cellphonedb_meta.tsv"
    counts_path = tmp_path / "cellphonedb_counts.tsv"
    db_path = tmp_path / "cellphonedb.zip"
    command_path.write_text("cellphonedb method statistical_analysis\n", encoding="utf-8")
    meta_path.write_text("Cell\tcell_type\nc1\tA\n", encoding="utf-8")
    counts_path.write_text("Gene\tc1\nL1\t1\n", encoding="utf-8")
    db_path.write_text("test database placeholder\n", encoding="utf-8")

    monkeypatch.setattr(script.shutil, "which", lambda _name: None)
    monkeypatch.setattr(
        script,
        "_run_cellphonedb_api",
        lambda **_kwargs: {"status": "completed", "api_result_keys": ["means"]},
    )

    metadata = script.run_cellphonedb(
        command_path=command_path,
        meta_path=meta_path,
        counts_path=counts_path,
        output_dir=tmp_path,
        run=True,
        cpdb_database=db_path,
        iterations=100,
        max_cells=100,
    )

    assert metadata["execution_mode"] == "python_api"
    assert metadata["status"] == "smoke_completed_pending_full"


def test_cellphonedb_full_status_requires_full_cells_and_1000_iterations():
    script = _load_script("run_cellphonedb_comparator")

    assert (
        script._full_run_completed_status(max_cells=None, iterations=1000)
        == "completed_external_run_pending_import"
    )
    assert (
        script._full_run_completed_status(max_cells=100, iterations=1000)
        == "smoke_completed_pending_full"
    )
    assert (
        script._full_run_completed_status(max_cells=None, iterations=100)
        == "smoke_completed_pending_full"
    )


def test_cellphonedb_status_updates_tool_comparison_without_overwriting_import(tmp_path):
    script = _load_script("run_cellphonedb_comparator")
    results_dir = tmp_path / "benchmarks" / "results"
    results_dir.mkdir(parents=True)
    metadata_path = results_dir / "dataset_a" / "comparators" / "cellphonedb_run" / "run.json"
    metadata_path.parent.mkdir(parents=True)

    path = script.update_tool_comparison_status(
        results_dir=results_dir,
        dataset_id="dataset_a",
        metadata_path=metadata_path,
        run_metadata={
            "status": "missing_cellphonedb_executable",
            "command_path": "cpdb/cellphonedb_command.txt",
        },
    )
    table = pd.read_csv(path)
    row = table.loc[table["tool"] == "CellPhoneDB"].iloc[0]
    assert row["status"] == "missing_cellphonedb_executable"
    assert "executable was not found" in row["notes"]

    script.update_tool_comparison_status(
        results_dir=results_dir,
        dataset_id="dataset_a",
        metadata_path=metadata_path,
        run_metadata={"status": "smoke_completed_pending_full"},
    )
    smoke = pd.read_csv(path).loc[lambda x: x["tool"] == "CellPhoneDB"].iloc[0]
    assert smoke["status"] == "smoke_completed_pending_full"
    assert "not full reviewer-facing comparator evidence" in smoke["notes"]

    table.loc[0, "status"] = "completed_external_import"
    table.to_csv(path, index=False)
    script.update_tool_comparison_status(
        results_dir=results_dir,
        dataset_id="dataset_a",
        metadata_path=metadata_path,
        run_metadata={"status": "prepared_not_run"},
    )
    preserved = pd.read_csv(path).loc[lambda x: x["tool"] == "CellPhoneDB"].iloc[0]
    assert preserved["status"] == "completed_external_import"


def test_sync_external_comparator_statuses_records_cellchat_missing_dependency(tmp_path):
    script = _load_script("sync_external_comparator_status")
    results_dir = tmp_path / "benchmarks" / "results"
    status_dir = results_dir / "dataset_a" / "comparators" / "cellchat_run"
    status_dir.mkdir(parents=True)
    pd.DataFrame([{"dataset_id": "dataset_a"}]).to_csv(
        results_dir / "public_tme_sheafsignal_summary.csv",
        index=False,
    )
    (status_dir / "cellchat_run_status.tsv").write_text(
        "status\tmissing_dependency\nrequired_package\tCellChat\n",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "dataset_id": "dataset_a",
                "tool": "CellChat",
                "status": "not_run_requires_external_tool",
            }
        ]
    ).to_csv(results_dir / "tool_comparison.csv", index=False)

    path = script.sync_external_comparator_statuses(results_dir)

    row = pd.read_csv(path).loc[lambda x: x["tool"] == "CellChat"].iloc[0]
    assert row["status"] == "missing_cellchat_dependency"
    assert "was invoked" in row["notes"]


def test_liana_standardization_inverts_lower_is_better_rank():
    liana_script = _load_script("run_liana_comparator")
    raw = pd.DataFrame(
        {
            "source": ["A", "B"],
            "target": ["B", "A"],
            "ligand_complex": ["L1", "L2"],
            "receptor_complex": ["R1", "R2"],
            "magnitude_rank": [0.1, 0.9],
        }
    )

    standardized = liana_script.standardize_liana_edges(raw)

    assert list(standardized["sender"]) == ["A", "B"]
    assert list(standardized["receiver"]) == ["B", "A"]
    assert standardized.loc[0, "score"] == 0.9
    assert standardized.loc[1, "score"] == 0.09999999999999998
    assert standardized.loc[0, "ligand"] == "L1"
    assert "1-magnitude_rank" in standardized.loc[0, "notes"]


def test_liana_anndata_loader_aligns_metadata_and_expression(tmp_path):
    liana_script = _load_script("run_liana_comparator")
    processed = tmp_path / "data" / "processed" / "toy_dataset"
    processed.mkdir(parents=True)
    pd.DataFrame(
        {
            "cell_id": ["c2", "c1", "c3"],
            "cell_type": ["B", "A", "A"],
            "sample_id": ["S1", "S1", "S2"],
        }
    ).to_csv(processed / "metadata.csv", index=False)
    pd.DataFrame(
        {
            "cell_id": ["c1", "c2", "c3"],
            "L1": [1.0, 2.0, 3.0],
            "R1": [4.0, 5.0, 6.0],
        }
    ).to_csv(processed / "expression.csv", index=False)

    adata = liana_script.load_liana_anndata(
        processed_dir=processed,
        cell_type_col="cell_type",
        max_cells=None,
        seed=42,
    )

    assert list(adata.obs_names) == ["c2", "c1", "c3"]
    assert list(adata.var_names) == ["L1", "R1"]
    assert list(adata.obs["cell_type"]) == ["B", "A", "A"]
    assert adata.X[0, 0] == 2.0
    summary = adata.uns["sheafsignal_liana_input_summary"]
    assert summary["n_expression_cells_read"] == 3
    assert summary["n_metadata_cells_read"] == 3
    assert summary["n_common_cells_before_sampling"] == 3


def test_comparator_readiness_keeps_external_tools_pending():
    reviewer_script = _load_script("build_reviewer_objection_table")
    table = pd.DataFrame(
        [
            {
                "dataset_id": "dataset_a",
                "tool": "LRProductBaseline",
                "status": "completed",
                "spearman_sheaf_energy_vs_tool_score": 0.2,
            },
            {
                "dataset_id": "dataset_a",
                "tool": "LIANA",
                "status": "not_run_requires_external_tool",
                "spearman_sheaf_energy_vs_tool_score": pd.NA,
            },
        ]
    )

    readiness = reviewer_script.comparator_readiness_matrix(table)

    assert readiness.loc[0, "internal_lr_product_completed"] == True  # noqa: E712
    assert readiness.loc[0, "external_comparator_gate"] == "pending_external_tools"
    assert "LIANA" in readiness.loc[0, "external_tools_pending"]


def test_comparator_readiness_marks_mechanistic_prior_partial():
    reviewer_script = _load_script("build_reviewer_objection_table")
    table = pd.DataFrame(
        [
            {
                "dataset_id": "dataset_a",
                "tool": "MechanisticTargetPrior",
                "status": "completed_external_import",
            }
        ]
    )

    readiness = reviewer_script.comparator_readiness_matrix(table)

    assert readiness.loc[0, "mechanistic_comparator_gate"] == (
        "partial_mechanistic_prior_baseline"
    )
    assert readiness.loc[0, "mechanistic_tools_completed"] == "MechanisticTargetPrior"
    assert "NicheNet" in readiness.loc[0, "mechanistic_tools_pending"]


def test_comparator_readiness_marks_nichenet_engine_pass():
    reviewer_script = _load_script("build_reviewer_objection_table")
    table = pd.DataFrame(
        [
            {
                "dataset_id": "dataset_a",
                "tool": "NicheNet",
                "status": "completed_external_import",
            }
        ]
    )

    readiness = reviewer_script.comparator_readiness_matrix(table)

    assert readiness.loc[0, "mechanistic_comparator_gate"] == (
        "pass_nichenetr_engine_with_prior"
    )
    assert readiness.loc[0, "mechanistic_tools_completed"] == "NicheNet"


def test_reviewer_objection_table_contains_external_gate():
    reviewer_script = _load_script("build_reviewer_objection_table")
    public_summary = pd.DataFrame(
        [
            {
                "dataset_id": "dataset_a",
                "status": "completed",
                "top_frustration_cell_type": "Myeloid",
                "top_frustration_score": 0.8,
            }
        ]
    )
    readiness = pd.DataFrame(
        [
            {
                "dataset_id": "dataset_a",
                "internal_lr_product_completed": True,
                "external_tools_completed": "",
                "external_tools_pending": "LIANA",
                "external_comparator_gate": "pending_external_tools",
                "max_abs_spearman_internal_lr_product": 0.2,
            }
        ]
    )
    claim_gate = pd.DataFrame([{"cell_type": "Myeloid", "claim_use": "main_claim"}])
    visium_qc = pd.DataFrame(
        [
            {
                "min_spearman_across_k": 0.93,
                "min_top_50_overlap_across_k": 0.86,
            }
        ]
    )

    objections = reviewer_script.reviewer_objection_table(
        public_summary,
        readiness,
        claim_gate,
        visium_qc,
    )

    external = objections.loc[objections["objection_id"] == "R2_no_external_comparator"].iloc[0]
    assert external["gate_status"] == "pending_external_tools"
    assert "not state" in external["response_position"]


def test_reviewer_objection_table_marks_liana_imports_as_partial_external_evidence():
    reviewer_script = _load_script("build_reviewer_objection_table")
    readiness = pd.DataFrame(
        [
            {
                "dataset_id": "gse154778_pdac_scrna",
                "internal_lr_product_completed": True,
                "external_tools_completed": "LIANA",
                "external_tools_pending": "CellChat;CellPhoneDB;NicheNet;niche-DE",
                "external_comparator_gate": "pending_external_tools",
                "max_abs_spearman_internal_lr_product": 0.7,
            },
            {
                "dataset_id": "gse72056_melanoma_scrna",
                "internal_lr_product_completed": True,
                "external_tools_completed": "LIANA",
                "external_tools_pending": "CellChat;CellPhoneDB;NicheNet;niche-DE",
                "external_comparator_gate": "pending_external_tools",
                "max_abs_spearman_internal_lr_product": 0.3,
            },
            {
                "dataset_id": "gse176078_brca_scrna",
                "internal_lr_product_completed": True,
                "external_tools_completed": "LIANA",
                "external_tools_pending": "CellChat;CellPhoneDB;NicheNet;niche-DE",
                "external_comparator_gate": "pending_external_tools",
                "max_abs_spearman_internal_lr_product": 0.5,
            },
        ]
    )

    objections = reviewer_script.reviewer_objection_table(
        pd.DataFrame(),
        readiness,
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(
            [
                {
                    "gate_id": "external_liana_comparator",
                    "gate_status": "partially_satisfied_smoke_only",
                    "n_smoke_completed_datasets": 3,
                    "n_full_completed_datasets": 0,
                }
            ]
        ),
    )

    external = objections.loc[
        objections["objection_id"] == "R2_no_external_comparator"
    ].iloc[0]
    assert external["gate_status"] == "partial_liana_smoke_import_done"
    assert "LIANA smoke imports" in external["current_evidence"]
    assert "3 public scRNA-seq datasets" in external["current_evidence"]
    assert "broad superiority" in external["claim_boundary"]


def test_reviewer_objection_table_reports_mixed_liana_full_and_smoke_evidence():
    reviewer_script = _load_script("build_reviewer_objection_table")
    readiness = pd.DataFrame(
        [
            {
                "dataset_id": "gse154778_pdac_scrna",
                "internal_lr_product_completed": True,
                "external_tools_completed": "LIANA",
                "external_tools_pending": "CellChat;CellPhoneDB;NicheNet;niche-DE",
                "external_comparator_gate": "pending_external_tools",
                "max_abs_spearman_internal_lr_product": 0.7,
            },
            {
                "dataset_id": "gse72056_melanoma_scrna",
                "internal_lr_product_completed": True,
                "external_tools_completed": "LIANA",
                "external_tools_pending": "CellChat;CellPhoneDB;NicheNet;niche-DE",
                "external_comparator_gate": "pending_external_tools",
                "max_abs_spearman_internal_lr_product": 0.3,
            },
        ]
    )

    objections = reviewer_script.reviewer_objection_table(
        pd.DataFrame(),
        readiness,
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(
            [
                {
                    "gate_id": "external_liana_comparator",
                    "gate_status": "partially_satisfied_mixed",
                    "n_smoke_completed_datasets": 2,
                    "n_full_completed_datasets": 1,
                }
            ]
        ),
    )

    external = objections.loc[
        objections["objection_id"] == "R2_no_external_comparator"
    ].iloc[0]
    assert external["gate_status"] == "partial_liana_mixed_import_done"
    assert "Full LIANA imports completed for 1 dataset" in external["current_evidence"]
    assert "complete LIANA benchmarking" in external["claim_boundary"]


def test_reviewer_objection_table_reports_mechanistic_prior_boundary():
    reviewer_script = _load_script("build_reviewer_objection_table")
    readiness = pd.DataFrame(
        [
            {
                "dataset_id": "gse154778_pdac_scrna",
                "internal_lr_product_completed": True,
                "external_tools_completed": "LIANA",
                "external_tools_pending": "CellChat;CellPhoneDB;NicheNet;niche-DE",
                "external_comparator_gate": "pending_external_tools",
                "mechanistic_tools_completed": "MechanisticTargetPrior",
                "mechanistic_tools_pending": "NicheNet",
                "mechanistic_comparator_gate": "partial_mechanistic_prior_baseline",
                "max_abs_spearman_internal_lr_product": 0.7,
            }
        ]
    )

    objections = reviewer_script.reviewer_objection_table(
        pd.DataFrame(),
        readiness,
        pd.DataFrame(),
        pd.DataFrame(),
    )

    mechanistic = objections.loc[
        objections["objection_id"] == "R7_no_mechanistic_comparator"
    ].iloc[0]
    assert mechanistic["gate_status"] == "partial_mechanistic_prior_done"
    assert "MechanisticTargetPrior is completed" in mechanistic["current_evidence"]
    assert "not an official nichenetr/NicheNet" in mechanistic["current_evidence"]
    assert "must not be described as official NicheNet" in mechanistic["response_position"]


def test_build_reviewer_tables_writes_csv_and_tsv(tmp_path):
    reviewer_script = _load_script("build_reviewer_objection_table")
    results_dir = tmp_path / "benchmarks" / "results"
    manuscript_dir = tmp_path / "manuscript"
    qc_dir = results_dir / "gse154778_pdac_scrna" / "qc"
    visium_dir = results_dir / "tenx_breast_visium" / "spatial" / "qc"
    qc_dir.mkdir(parents=True)
    visium_dir.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "dataset_id": "dataset_a",
                "status": "completed",
                "top_frustration_cell_type": "Myeloid",
                "top_frustration_score": 0.8,
            }
        ]
    ).to_csv(results_dir / "public_tme_sheafsignal_summary.csv", index=False)
    pd.DataFrame(
        [
            {
                "dataset_id": "dataset_a",
                "tool": "LRProductBaseline",
                "status": "completed",
                "spearman_sheaf_energy_vs_tool_score": 0.2,
            },
            {
                "dataset_id": "dataset_a",
                "tool": "LIANA",
                "status": "not_run_requires_external_tool",
            },
        ]
    ).to_csv(results_dir / "tool_comparison.csv", index=False)
    pd.DataFrame([{"cell_type": "Myeloid", "claim_use": "main_claim"}]).to_csv(
        qc_dir / "claim_gating_by_cell_type.csv",
        index=False,
    )
    pd.DataFrame(
        [
            {
                "min_spearman_across_k": 0.93,
                "min_top_50_overlap_across_k": 0.86,
            }
        ]
    ).to_csv(visium_dir / "spatial_hotspot_qc_summary.csv", index=False)

    paths = reviewer_script.build_tables(
        results_dir=results_dir,
        manuscript_dir=manuscript_dir,
        output_dir=results_dir,
    )

    for path in paths.values():
        assert path.exists()
    objections = pd.read_csv(paths["reviewer_objection_csv"])
    assert "R2_no_external_comparator" in set(objections["objection_id"])
