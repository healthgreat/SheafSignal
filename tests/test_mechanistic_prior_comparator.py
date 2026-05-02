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


def _write_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    dataset_id = "toy_dataset"
    processed = tmp_path / "data" / "processed" / dataset_id
    benchmark = tmp_path / "benchmarks" / "results" / dataset_id
    results_dir = tmp_path / "benchmarks" / "results"
    processed.mkdir(parents=True)
    (benchmark / "results").mkdir(parents=True)

    pd.DataFrame(
        {
            "cell_type": ["Sender", "Receiver"],
            "L1": [4.0, 0.1],
            "R1": [0.2, 3.0],
            "T1": [0.0, 5.0],
            "T2": [0.0, 2.0],
        }
    ).to_csv(processed / "profiles.csv", index=False)
    pd.DataFrame(
        {
            "sender": ["Sender"],
            "receiver": ["Receiver"],
            "sheaf_energy": [1.5],
            "sheaf_mismatch": [0.4],
            "communication_flow": [2.0],
        }
    ).to_csv(benchmark / "results" / "sheaf_energy_by_edge.csv", index=False)
    lr_db = tmp_path / "lr.csv"
    lr_db.write_text("ligand,receptor,weight\nL1,R1,0.5\n", encoding="utf-8")
    prior = tmp_path / "prior.csv"
    prior.write_text(
        "ligand,target,weight,source_evidence\nL1,T1,1.0,toy\nL1,T2,0.5,toy\n",
        encoding="utf-8",
    )
    return processed, benchmark, results_dir, lr_db, prior


def test_mechanistic_prior_scores_receiver_target_program(tmp_path):
    script = _load_script("run_mechanistic_prior_comparator")
    processed, benchmark, _, lr_db, prior = _write_fixture(tmp_path)
    profiles = script.load_profiles(processed / "profiles.csv")
    lr = script.load_lr_database(lr_db)
    target_prior = script.load_ligand_target_prior(prior)
    sheaf = pd.read_csv(benchmark / "results" / "sheaf_energy_by_edge.csv")

    edges = script.mechanistic_prior_edges(
        profiles=profiles,
        lr_db=lr,
        ligand_target_prior=target_prior,
        sheaf_edges=sheaf,
    )

    row = edges.iloc[0]
    assert row["sender"] == "Sender"
    assert row["receiver"] == "Receiver"
    assert row["ligand"] == "L1"
    assert row["receptor"] == "R1"
    assert row["n_targets_available"] == 2
    assert row["score"] > 0


def test_run_mechanistic_prior_comparator_imports_tool_row(tmp_path):
    script = _load_script("run_mechanistic_prior_comparator")
    processed, benchmark, results_dir, lr_db, prior = _write_fixture(tmp_path)

    paths = script.run_mechanistic_prior_comparator(
        dataset_id="toy_dataset",
        processed_dir=processed,
        benchmark_dir=benchmark,
        results_dir=results_dir,
        lr_db_path=lr_db,
        ligand_target_prior_path=prior,
        output_dir=benchmark / "comparators" / "mechanistic_target_prior_run",
        min_target_genes=1,
    )

    for path in paths.values():
        assert Path(path).exists()
    tool_table = pd.read_csv(paths["tool_comparison"])
    row = tool_table.loc[tool_table["tool"] == "MechanisticTargetPrior"].iloc[0]
    assert row["status"] == "completed_external_import"
    aligned = pd.read_csv(paths["aligned"])
    assert "discordance_class" in aligned.columns
