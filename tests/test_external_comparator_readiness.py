from pathlib import Path
import importlib.util
import json

import pandas as pd


def _load_script(name: str):
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _manifest_row(tmp_path: Path, dataset_id: str) -> dict[str, str]:
    processed = tmp_path / "data" / "processed" / dataset_id
    processed.mkdir(parents=True, exist_ok=True)
    (processed / "expression.csv").write_text("cell_id,G1\nc1,1\n", encoding="utf-8")
    (processed / "metadata.csv").write_text(
        "cell_id,cell_type\nc1,Myeloid\n",
        encoding="utf-8",
    )
    benchmark = tmp_path / "benchmarks" / "results" / dataset_id / "results"
    benchmark.mkdir(parents=True, exist_ok=True)
    (benchmark / "sheaf_energy_by_edge.csv").write_text(
        "sender,receiver,sheaf_energy\nA,B,1\n",
        encoding="utf-8",
    )
    return {
        "dataset_id": dataset_id,
        "title": dataset_id,
        "modality": "scRNA-seq",
        "species": "Homo sapiens",
        "tissue": "tumor",
        "disease": "cancer",
        "accession_or_doi": "TEST",
        "download_url": "https://example.org/test.csv",
        "local_path": f"data/external/{dataset_id}/test.csv",
        "sha256": "PENDING_DOWNLOAD_VERIFICATION",
        "license_or_terms": "public test",
        "release_status": "downloaded",
        "benchmark_role": "public_scrna_benchmark",
        "prepared_expression": str(processed / "expression.csv"),
        "prepared_metadata": str(processed / "metadata.csv"),
    }


def _write_liana_metadata(
    results_dir: Path,
    dataset_id: str,
    *,
    max_cells: int | None,
) -> Path:
    path = (
        results_dir
        / dataset_id
        / "comparators"
        / "liana_run"
        / "liana_run_metadata.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "dataset_id": dataset_id,
                "max_cells": max_cells,
                "n_cells_used": 1000,
                "n_perms": 1000,
                "seed": 42,
            }
        ),
        encoding="utf-8",
    )
    return path


def test_liana_execution_plan_blocks_when_package_missing(tmp_path):
    script = _load_script("check_external_comparator_readiness")
    dataset_id = "gse154778_pdac_scrna"
    manifest = pd.DataFrame([_manifest_row(tmp_path, dataset_id)])
    tool_comparison = pd.DataFrame(
        [
            {
                "dataset_id": dataset_id,
                "tool": "LIANA",
                "status": "not_run_requires_external_tool",
            }
        ]
    )
    environment = pd.DataFrame(
        [
            {
                "check_type": "python_package",
                "name": "liana",
                "present": False,
                "version_or_path": "",
                "required_for": "LIANA",
            }
        ]
    )

    plan = script.build_liana_execution_plan(
        manifest=manifest,
        tool_comparison=tool_comparison,
        environment=environment,
        results_dir=tmp_path / "benchmarks" / "results",
        target_datasets=(dataset_id,),
    )

    assert set(plan["run_phase"]) == {"smoke", "full"}
    assert not plan["ready_to_run"].any()
    assert "missing_python_package_liana" in plan.loc[0, "blockers"]


def test_liana_execution_plan_ready_when_inputs_and_env_exist(tmp_path):
    script = _load_script("check_external_comparator_readiness")
    dataset_id = "gse154778_pdac_scrna"
    manifest = pd.DataFrame([_manifest_row(tmp_path, dataset_id)])
    tool_comparison = pd.DataFrame(
        [
            {
                "dataset_id": dataset_id,
                "tool": "LIANA",
                "status": "not_run_requires_external_tool",
            }
        ]
    )
    environment = pd.DataFrame(
        [
            {
                "check_type": "python_package",
                "name": "liana",
                "present": True,
                "version_or_path": "1.4.0",
                "required_for": "LIANA",
            }
        ]
    )

    plan = script.build_liana_execution_plan(
        manifest=manifest,
        tool_comparison=tool_comparison,
        environment=environment,
        results_dir=tmp_path / "benchmarks" / "results",
        target_datasets=(dataset_id,),
    )

    assert plan["ready_to_run"].all()
    smoke = plan.loc[plan["run_phase"] == "smoke"].iloc[0]
    full = plan.loc[plan["run_phase"] == "full"].iloc[0]
    assert "--max-cells 5000" in smoke["command"]
    assert "--max-cells" not in full["command"]


def test_liana_execution_plan_distinguishes_smoke_from_full_import(tmp_path):
    script = _load_script("check_external_comparator_readiness")
    dataset_id = "gse154778_pdac_scrna"
    results_dir = tmp_path / "benchmarks" / "results"
    manifest = pd.DataFrame([_manifest_row(tmp_path, dataset_id)])
    _write_liana_metadata(results_dir, dataset_id, max_cells=5000)
    tool_comparison = pd.DataFrame(
        [
            {
                "dataset_id": dataset_id,
                "tool": "LIANA",
                "status": "completed_external_import",
            }
        ]
    )
    environment = pd.DataFrame(
        [
            {
                "check_type": "python_package",
                "name": "liana",
                "present": True,
                "version_or_path": "1.7.1",
                "required_for": "LIANA",
            }
        ]
    )

    plan = script.build_liana_execution_plan(
        manifest=manifest,
        tool_comparison=tool_comparison,
        environment=environment,
        results_dir=results_dir,
        target_datasets=(dataset_id,),
    )

    status_by_phase = dict(zip(plan["run_phase"], plan["current_import_status"]))
    assert status_by_phase["smoke"] == "completed_smoke_import"
    assert status_by_phase["full"] == "not_run_full_after_smoke"
    gate = script.build_gate_summary(execution_plan=plan, environment=environment)
    row = gate.iloc[0]
    assert row["gate_status"] == "partially_satisfied_smoke_only"
    assert row["n_smoke_completed_datasets"] == 1
    assert row["n_full_completed_datasets"] == 0


def test_liana_gate_marks_mixed_smoke_and_full_imports(tmp_path):
    script = _load_script("check_external_comparator_readiness")
    smoke_dataset = "gse154778_pdac_scrna"
    full_dataset = "gse72056_melanoma_scrna"
    results_dir = tmp_path / "benchmarks" / "results"
    manifest = pd.DataFrame(
        [
            _manifest_row(tmp_path, smoke_dataset),
            _manifest_row(tmp_path, full_dataset),
        ]
    )
    _write_liana_metadata(results_dir, smoke_dataset, max_cells=5000)
    _write_liana_metadata(results_dir, full_dataset, max_cells=None)
    tool_comparison = pd.DataFrame(
        [
            {
                "dataset_id": smoke_dataset,
                "tool": "LIANA",
                "status": "completed_external_import",
            },
            {
                "dataset_id": full_dataset,
                "tool": "LIANA",
                "status": "completed_external_import",
            },
        ]
    )
    environment = pd.DataFrame(
        [
            {
                "check_type": "python_package",
                "name": "liana",
                "present": True,
                "version_or_path": "1.7.1",
                "required_for": "LIANA",
            }
        ]
    )

    plan = script.build_liana_execution_plan(
        manifest=manifest,
        tool_comparison=tool_comparison,
        environment=environment,
        results_dir=results_dir,
        target_datasets=(smoke_dataset, full_dataset),
    )

    gate = script.build_gate_summary(execution_plan=plan, environment=environment)
    row = gate.iloc[0]
    assert row["gate_status"] == "partially_satisfied_mixed"
    assert row["n_smoke_completed_datasets"] == 2
    assert row["n_full_completed_datasets"] == 1
    assert row["n_prepared_subset_completed_datasets"] == 0


def test_liana_gate_demotes_full_command_on_prepared_subset(tmp_path):
    script = _load_script("check_external_comparator_readiness")
    dataset_id = "gse154778_pdac_scrna"
    results_dir = tmp_path / "benchmarks" / "results"
    manifest = pd.DataFrame([_manifest_row(tmp_path, dataset_id)])
    processed = tmp_path / "data" / "processed" / dataset_id
    pd.DataFrame(
        {
            "cell_id": [f"c{i}" for i in range(10)],
            "G1": [1.0] * 10,
        }
    ).to_csv(processed / "expression.csv", index=False)
    pd.DataFrame(
        {
            "cell_id": [f"c{i}" for i in range(100)],
            "cell_type": ["Myeloid"] * 100,
        }
    ).to_csv(processed / "metadata.csv", index=False)
    metadata_path = _write_liana_metadata(results_dir, dataset_id, max_cells=None)
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    payload["processed_dir"] = str(processed)
    metadata_path.write_text(json.dumps(payload), encoding="utf-8")
    tool_comparison = pd.DataFrame(
        [
            {
                "dataset_id": dataset_id,
                "tool": "LIANA",
                "status": "completed_external_import",
            }
        ]
    )
    environment = pd.DataFrame(
        [
            {
                "check_type": "python_package",
                "name": "liana",
                "present": True,
                "version_or_path": "1.7.1",
                "required_for": "LIANA",
            }
        ]
    )

    plan = script.build_liana_execution_plan(
        manifest=manifest,
        tool_comparison=tool_comparison,
        environment=environment,
        results_dir=results_dir,
        target_datasets=(dataset_id,),
    )

    status_by_phase = dict(zip(plan["run_phase"], plan["current_import_status"]))
    assert status_by_phase["smoke"] == "superseded_by_prepared_subset_import"
    assert status_by_phase["full"] == "completed_prepared_subset_import"
    gate = script.build_gate_summary(execution_plan=plan, environment=environment)
    row = gate.iloc[0]
    assert row["gate_status"] == "partially_satisfied_prepared_subset_only"
    assert row["n_full_completed_datasets"] == 0
    assert row["n_prepared_subset_completed_datasets"] == 1


def test_liana_execution_plan_uses_conda_run_when_liana_env_exists(tmp_path):
    script = _load_script("check_external_comparator_readiness")
    dataset_id = "gse154778_pdac_scrna"
    manifest = pd.DataFrame([_manifest_row(tmp_path, dataset_id)])
    tool_comparison = pd.DataFrame(
        [
            {
                "dataset_id": dataset_id,
                "tool": "LIANA",
                "status": "not_run_requires_external_tool",
            }
        ]
    )
    environment = pd.DataFrame(
        [
            {
                "check_type": "python_package",
                "name": "liana",
                "present": False,
                "version_or_path": "",
                "required_for": "LIANA",
            },
            {
                "check_type": "conda_env_package",
                "name": "sheafsignal-liana:liana",
                "present": True,
                "version_or_path": "1.7.1",
                "required_for": "LIANA isolated execution",
            },
        ]
    )

    plan = script.build_liana_execution_plan(
        manifest=manifest,
        tool_comparison=tool_comparison,
        environment=environment,
        results_dir=tmp_path / "benchmarks" / "results",
        target_datasets=(dataset_id,),
    )

    assert plan["ready_to_run"].all()
    assert plan.loc[0, "environment_status"] == "ready_conda_env:sheafsignal-liana"
    assert plan.loc[0, "command"].startswith("conda run -n sheafsignal-liana python")


def test_write_readiness_outputs_writes_csv_and_tsv(tmp_path, monkeypatch):
    script = _load_script("check_external_comparator_readiness")
    manifest_path = tmp_path / "metadata" / "datasets.tsv"
    results_dir = tmp_path / "benchmarks" / "results"
    manuscript_dir = tmp_path / "manuscript"
    manifest_path.parent.mkdir(parents=True)
    pd.DataFrame([_manifest_row(tmp_path, "gse154778_pdac_scrna")]).to_csv(
        manifest_path,
        sep="\t",
        index=False,
    )
    pd.DataFrame(
        [
            {
                "dataset_id": "gse154778_pdac_scrna",
                "tool": "LIANA",
                "status": "not_run_requires_external_tool",
            }
        ]
    ).to_csv(results_dir / "tool_comparison.csv", index=False)

    monkeypatch.setattr(
        script,
        "detect_environment_status",
        lambda: pd.DataFrame(
            [
                {
                    "check_type": "python_package",
                    "name": "liana",
                    "present": False,
                    "version_or_path": "",
                    "required_for": "LIANA",
                }
            ]
        ),
    )

    paths = script.write_readiness_outputs(
        manifest_path=manifest_path,
        results_dir=results_dir,
        manuscript_dir=manuscript_dir,
        output_dir=results_dir,
    )

    for path in paths.values():
        assert path.exists()
    gate = pd.read_csv(paths["gate_summary_csv"])
    assert gate.loc[0, "gate_status"] == "blocked_environment_or_inputs"
