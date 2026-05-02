from pathlib import Path
import importlib.util

import pandas as pd


def _load_sample_script():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "sample_level_gse154778_stability.py"
    spec = importlib.util.spec_from_file_location("sample_level_gse154778_stability", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    processed = tmp_path / "processed"
    processed.mkdir()
    expr_rows = []
    meta_rows = []
    for sample, lesion in [("P01", "Primary"), ("P02", "Primary"), ("M01", "Metastatic")]:
        for cell_type, ligand, receptor, pathway in [
            ("Myeloid", 6, 1, 1),
            ("Myeloid", 5, 1, 1),
            ("Tumor/Epithelial", 1, 6, 6),
            ("Tumor/Epithelial", 1, 5, 5),
            ("T/NK", 2, 2, 2),
        ]:
            cell_id = f"{sample}_{cell_type}_{len(expr_rows)}"
            expr_rows.append({"cell_id": cell_id, "L1": ligand, "R1": receptor, "P1": pathway})
            meta_rows.append(
                {
                    "cell_id": cell_id,
                    "cell_type": cell_type,
                    "sample_id": sample,
                    "lesion_type": lesion,
                }
            )
    pd.DataFrame(expr_rows).to_csv(processed / "expression.csv", index=False)
    pd.DataFrame(meta_rows).to_csv(processed / "metadata.csv", index=False)
    lr = tmp_path / "lr.csv"
    genes = tmp_path / "genes.txt"
    pd.DataFrame({"ligand": ["L1"], "receptor": ["R1"], "weight": [1.0]}).to_csv(lr, index=False)
    genes.write_text("P1\n", encoding="utf-8")
    return processed, tmp_path / "missing_raw.csv.gz", lr, genes


def test_sample_level_stability_writes_outputs_and_manifest(tmp_path):
    sample = _load_sample_script()
    processed, raw, lr, genes = _write_fixture(tmp_path)
    output_dir = tmp_path / "stability"
    manifest = tmp_path / "manuscript" / "figure_manifest.tsv"

    paths = sample.run_sample_level(
        processed_dir=processed,
        raw_path=raw,
        lr_db_path=lr,
        gene_set_path=genes,
        output_dir=output_dir,
        figure_manifest=manifest,
        min_cell_types=2,
        min_myeloid_cells=2,
        max_cells=None,
        chunksize=1000,
    )

    for path in paths.values():
        assert Path(path).exists()
    sample_table = pd.read_csv(output_dir / "sample_level_frustration.csv")
    assert set(sample_table["status"]) == {"completed"}
    summary = pd.read_csv(output_dir / "sample_level_myeloid_stability_summary.csv")
    assert {"all", "Primary", "Metastatic"}.issubset(set(summary["lesion_type"]))
    figure_manifest = pd.read_csv(manifest, sep="\t")
    assert "supp_gse154778_sample_level_myeloid_stability" in set(
        figure_manifest["figure_id"]
    )
