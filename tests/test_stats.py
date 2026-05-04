from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sheafsignal.io import read_expression, read_gene_set, read_ligand_receptor_db, read_metadata
from sheafsignal.pipeline import run_pipeline
from sheafsignal.stats import _permuted_labels, benjamini_hochberg


def test_benjamini_hochberg_is_monotone_after_sorting():
    pvalues = np.array([0.01, 0.04, 0.03, np.nan, 0.20])
    qvalues = benjamini_hochberg(pvalues)
    valid_order = np.argsort(pvalues[np.isfinite(pvalues)])
    sorted_q = qvalues[np.isfinite(qvalues)][valid_order]
    assert np.all(np.diff(sorted_q) >= -1e-12)
    assert np.isnan(qvalues[3])


def test_demo_pipeline_with_permutation_writes_pvalues(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = run_pipeline(
        expression_path=root / "examples" / "demo_expression.csv",
        metadata_path=root / "examples" / "demo_metadata.csv",
        lr_db_path=root / "examples" / "demo_ligand_receptor.csv",
        gene_set_path=root / "examples" / "demo_pathway_genes.txt",
        project_dir=tmp_path,
        make_plot=False,
        n_permutations=3,
        random_seed=1,
    )

    assert result.edge_permutation_path is not None
    assert result.node_permutation_path is not None
    assert result.global_permutation_path is not None

    edge_stats = pd.read_csv(result.edge_permutation_path)
    node_stats = pd.read_csv(result.node_permutation_path)
    global_stats = pd.read_csv(result.global_permutation_path)
    assert "sheaf_energy_empirical_p" in edge_stats.columns
    assert "frustration_fdr" in node_stats.columns
    assert "n_permutations_skipped" in edge_stats.columns
    assert edge_stats["n_permutations_requested"].eq(3).all()
    assert set(global_stats["metric"]).issuperset({"total_sheaf_energy", "curl_ratio"})


def test_demo_inputs_can_be_loaded_for_statistics():
    root = Path(__file__).resolve().parents[1]
    expression = read_expression(root / "examples" / "demo_expression.csv")
    metadata = read_metadata(root / "examples" / "demo_metadata.csv")
    lr_db = read_ligand_receptor_db(root / "examples" / "demo_ligand_receptor.csv")
    genes = read_gene_set(root / "examples" / "demo_pathway_genes.txt")
    assert expression.shape[0] == metadata.shape[0]
    assert {"ligand", "receptor", "weight"}.issubset(lr_db.columns)
    assert len(genes) > 0


def test_stratified_permutation_preserves_label_counts_within_strata():
    metadata = pd.DataFrame(
        {
            "cell_id": [f"c{i}" for i in range(8)],
            "cell_type": ["A", "A", "B", "B", "A", "B", "B", "A"],
            "sample_id": ["s1", "s1", "s1", "s1", "s2", "s2", "s2", "s2"],
        }
    )
    labels = _permuted_labels(
        metadata=metadata,
        cell_type_col="cell_type",
        strata_col="sample_id",
        rng=np.random.default_rng(1),
    )
    out = metadata.copy()
    out["permuted"] = labels
    original_counts = metadata.groupby("sample_id")["cell_type"].value_counts().sort_index()
    permuted_counts = out.groupby("sample_id")["permuted"].value_counts().sort_index()
    assert original_counts.to_dict() == permuted_counts.to_dict()
