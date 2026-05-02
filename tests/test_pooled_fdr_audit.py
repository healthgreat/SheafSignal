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


def test_pooled_fdr_audit_collects_edge_node_and_global_tables(tmp_path):
    script = _load_script("build_pooled_fdr_audit")
    result_dir = tmp_path / "benchmarks" / "results" / "toy_dataset" / "results"
    result_dir.mkdir(parents=True)
    pd.DataFrame(
        {
            "edge_id": ["A->B", "B->C"],
            "sheaf_energy_empirical_p": [0.01, 0.2],
            "curl_empirical_p": [0.05, 0.5],
        }
    ).to_csv(result_dir / "sheaf_energy_permutation_pvalues.csv", index=False)
    pd.DataFrame(
        {"cell_type": ["A", "B"], "frustration_empirical_p": [0.03, 0.4]}
    ).to_csv(result_dir / "frustration_permutation_pvalues.csv", index=False)
    pd.DataFrame({"metric": ["curl_ratio"], "empirical_p": [0.02]}).to_csv(
        result_dir / "global_permutation_pvalues.csv",
        index=False,
    )

    paths = script.build_pooled_fdr(tmp_path / "benchmarks" / "results", tmp_path / "out")

    table = pd.read_csv(paths["table"])
    assert {"edge_sheaf_energy", "edge_curl", "node_frustration", "global_metrics"}.issubset(
        set(table["family"])
    )
    assert "pooled_fdr_all_tests" in table.columns
    assert paths["report"].exists()

