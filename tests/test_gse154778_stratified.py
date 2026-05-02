from pathlib import Path
import importlib.util

import pandas as pd


def _load_stratified_script():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "stratify_gse154778_lesion.py"
    spec = importlib.util.spec_from_file_location("stratify_gse154778_lesion", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    processed = tmp_path / "processed"
    processed.mkdir()
    rows = []
    meta = []
    for lesion in ["Primary", "Metastatic"]:
        for cell_type, ligand, receptor, pathway in [
            ("A", 6, 1, 1),
            ("A", 5, 1, 1),
            ("B", 1, 6, 5),
            ("B", 1, 5, 6),
            ("C", 2, 2, 2),
            ("C", 2, 2, 2),
        ]:
            cell_id = f"{lesion}_{len(rows)}"
            rows.append({"cell_id": cell_id, "L1": ligand, "R1": receptor, "P1": pathway})
            meta.append(
                {
                    "cell_id": cell_id,
                    "cell_type": cell_type,
                    "marker_score": 1.0,
                    "marker_score_margin": 1.0,
                    "sample_id": "P01" if lesion == "Primary" else "MET01",
                    "lesion_type": lesion,
                }
            )
    pd.DataFrame(rows).to_csv(processed / "expression.csv", index=False)
    pd.DataFrame(meta).to_csv(processed / "metadata.csv", index=False)
    lr = tmp_path / "lr.csv"
    genes = tmp_path / "genes.txt"
    pd.DataFrame({"ligand": ["L1"], "receptor": ["R1"], "weight": [1.0]}).to_csv(lr, index=False)
    genes.write_text("P1\n", encoding="utf-8")
    return processed, tmp_path / "missing_raw.csv.gz", lr, genes


def test_stratified_gse154778_writes_lesion_outputs_and_manifest(tmp_path):
    stratified = _load_stratified_script()
    processed, raw, lr, genes = _write_fixture(tmp_path)
    output_dir = tmp_path / "stratified"
    manifest = tmp_path / "manuscript" / "figure_manifest.tsv"

    paths = stratified.run_stratified_analysis(
        processed_dir=processed,
        raw_path=raw,
        lr_db_path=lr,
        gene_set_path=genes,
        output_dir=output_dir,
        figure_manifest=manifest,
        min_cells_per_type=3,
        max_cells=None,
        chunksize=1000,
    )

    for path in paths.values():
        assert Path(path).exists()
    summary = pd.read_csv(output_dir / "lesion_sheafsignal_summary.csv")
    assert set(summary["lesion_type"]) == {"Primary", "Metastatic"}
    assert set(summary["status"]) == {"completed"}
    nodes = pd.read_csv(output_dir / "lesion_frustration_by_cell_type.csv")
    assert {"lesion_type", "cell_type", "frustration_score", "low_count_flag"}.issubset(
        nodes.columns
    )
    figure_manifest = pd.read_csv(manifest, sep="\t")
    assert "supp_gse154778_lesion_frustration_scores" in set(figure_manifest["figure_id"])
