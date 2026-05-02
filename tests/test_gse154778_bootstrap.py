from pathlib import Path
import importlib.util

import pandas as pd


def _load_bootstrap_script():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "bootstrap_gse154778_stability.py"
    spec = importlib.util.spec_from_file_location("bootstrap_gse154778_stability", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    processed = tmp_path / "processed"
    processed.mkdir()
    pd.DataFrame(
        {
            "cell_id": ["A1", "A2", "B1", "B2", "C1", "C2"],
            "L1": [6, 5, 1, 1, 2, 2],
            "R1": [1, 1, 5, 6, 2, 2],
            "P1": [1, 1, 6, 5, 2, 2],
        }
    ).to_csv(processed / "expression.csv", index=False)
    pd.DataFrame(
        {
            "cell_id": ["A1", "A2", "B1", "B2", "C1", "C2"],
            "cell_type": ["A", "A", "B", "B", "C", "C"],
            "marker_score": [1, 1, 1, 1, 1, 1],
            "marker_score_margin": [1, 1, 1, 1, 1, 1],
            "sample_id": ["P01", "P01", "P01", "P01", "MET01", "MET01"],
            "lesion_type": ["Primary", "Primary", "Primary", "Primary", "Metastatic", "Metastatic"],
        }
    ).to_csv(processed / "metadata.csv", index=False)
    lr = tmp_path / "lr.csv"
    genes = tmp_path / "genes.txt"
    pd.DataFrame({"ligand": ["L1"], "receptor": ["R1"], "weight": [1.0]}).to_csv(lr, index=False)
    genes.write_text("P1\n", encoding="utf-8")
    return processed, tmp_path / "missing_raw.csv.gz", lr, genes


def test_bootstrap_stability_writes_tables_figure_and_manifest(tmp_path):
    bootstrap = _load_bootstrap_script()
    processed, raw, lr, genes = _write_fixture(tmp_path)
    output_dir = tmp_path / "stability"
    manifest = tmp_path / "manuscript" / "figure_manifest.tsv"

    paths = bootstrap.run_bootstrap(
        processed_dir=processed,
        raw_path=raw,
        lr_db_path=lr,
        gene_set_path=genes,
        output_dir=output_dir,
        figure_manifest=manifest,
        n_bootstraps=5,
        random_seed=1,
        max_cells=None,
        chunksize=1000,
    )

    for path in paths.values():
        assert Path(path).exists()
    summary = pd.read_csv(output_dir / "bootstrap_frustration_summary.csv")
    assert {"cell_type", "top_frequency", "bootstrap_note"}.issubset(summary.columns)
    assert summary["top_frequency"].between(0, 1).all()
    assert "computational stability" in summary.iloc[0]["bootstrap_note"]
    figure_manifest = pd.read_csv(manifest, sep="\t")
    assert "supp_gse154778_bootstrap_frustration_stability" in set(
        figure_manifest["figure_id"]
    )
