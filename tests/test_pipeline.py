from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sheafsignal.pipeline import run_pipeline
from sheafsignal.pipeline import run_profile_pipeline


def test_demo_pipeline_writes_core_outputs(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = run_pipeline(
        expression_path=root / "examples" / "demo_expression.csv",
        metadata_path=root / "examples" / "demo_metadata.csv",
        lr_db_path=root / "examples" / "demo_ligand_receptor.csv",
        gene_set_path=root / "examples" / "demo_pathway_genes.txt",
        project_dir=tmp_path,
        make_plot=False,
    )

    assert result.edge_path.exists()
    assert result.score_path.exists()
    assert result.edge_permutation_path is None

    edges = pd.read_csv(result.edge_path)
    scores = pd.read_csv(result.score_path)
    assert {
        "sender",
        "receiver",
        "sheaf_energy",
        "sheaf_residual",
        "curl_component",
        "communication_hodge_curl_component",
        "frustration_hodge_curl_component",
    }.issubset(edges.columns)
    assert {
        "gradient_ratio",
        "curl_ratio",
        "harmonic_ratio",
        "frustration_gradient_ratio",
        "communication_gradient_ratio",
        "frustration_score",
    }.issubset(scores.columns)
    assert (tmp_path / "results" / "cellular_sheaf_laplacian.csv").exists()
    assert (tmp_path / "results" / "cellular_sheaf_restrictions.csv").exists()
    assert result.provenance_path is not None
    assert result.provenance_path.exists()
    assert len(edges) > 0


def test_profile_pipeline_writes_core_outputs(tmp_path):
    root = Path(__file__).resolve().parents[1]
    profile = tmp_path / "profiles.csv"
    profile.write_text(
        "cell_type,VEGFA,KDR,FLT1,TGFB1,TGFBR1,CXCL12,CXCR4,ANGPT2,TEK,MMP2,ITGAV,COL1A1,PECAM1\n"
        "CAF,8,1,1,5,2,8,1,1,1,7,2,12,1\n"
        "Endothelial,1,9,8,1,2,1,1,7,9,1,1,2,10\n"
        "Tumor,5,1,1,9,7,6,4,1,1,4,3,4,1\n",
        encoding="utf-8",
    )
    result = run_profile_pipeline(
        profile_path=profile,
        lr_db_path=root / "examples" / "demo_ligand_receptor.csv",
        gene_set_path=root / "examples" / "demo_pathway_genes.txt",
        project_dir=tmp_path,
        make_plot=False,
    )
    assert result.edge_path.exists()
    assert result.score_path.exists()
    assert result.n_cell_types == 3
