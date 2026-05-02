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


def test_write_tool_comparison_preserves_completed_external_imports(tmp_path):
    script = _load_script("run_tme_benchmark")
    results_dir = tmp_path / "benchmarks" / "results"
    results_dir.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "dataset_id": "dataset_a",
                "tool": "LIANA",
                "status": "completed_external_import",
                "comparison_level": "cell_type_edge",
                "edge_score_table": "old_liana_edges.csv",
                "aligned_edge_table": "old_aligned.csv",
                "spearman_sheaf_energy_vs_tool_score": 0.42,
            }
        ]
    ).to_csv(results_dir / "tool_comparison.csv", index=False)
    summary = pd.DataFrame(
        [
            {
                "dataset_id": "dataset_a",
                "status": "completed",
            }
        ]
    )

    output = script.write_tool_comparison(summary, results_dir)

    table = pd.read_csv(output)
    liana = table.loc[table["tool"] == "LIANA"].iloc[0]
    assert liana["status"] == "completed_external_import"
    assert liana["edge_score_table"] == "old_liana_edges.csv"
    assert liana["spearman_sheaf_energy_vs_tool_score"] == 0.42
    assert "CellPhoneDB" in set(table["tool"])


def test_select_permutation_strata_uses_sample_id_for_multisample_metadata(tmp_path):
    script = _load_script("run_tme_benchmark")
    metadata = tmp_path / "metadata.csv"
    pd.DataFrame(
        {
            "cell_id": ["c1", "c2", "c3", "c4"],
            "cell_type": ["A", "B", "A", "B"],
            "sample_id": ["s1", "s1", "s2", "s2"],
        }
    ).to_csv(metadata, index=False)

    strata_col, design = script._select_permutation_strata(metadata)

    assert strata_col == "sample_id"
    assert design == "sample_stratified"
