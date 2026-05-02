from pathlib import Path
import importlib.util
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def _load_qc_script():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "qc_gse154778_annotation.py"
    spec = importlib.util.spec_from_file_location("qc_gse154778_annotation", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_qc_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    processed = tmp_path / "processed"
    benchmark = tmp_path / "benchmark"
    qc_dir = benchmark / "qc"
    manifest = tmp_path / "manuscript" / "figure_manifest.tsv"
    processed.mkdir(parents=True)
    (benchmark / "results").mkdir(parents=True)

    pd.DataFrame(
        {
            "cell_type": ["Tumor/Epithelial", "CAF/Fibroblast", "Myeloid", "Unknown"],
            "EPCAM": [5.0, 0.1, 0.2, 0.0],
            "KRT8": [4.0, 0.2, 0.1, 0.0],
            "COL1A1": [0.1, 5.0, 0.2, 0.0],
            "DCN": [0.0, 4.0, 0.1, 0.0],
            "LYZ": [0.0, 0.2, 6.0, 0.0],
            "CD68": [0.0, 0.1, 5.0, 0.0],
        }
    ).to_csv(processed / "profiles.csv", index=False)

    pd.DataFrame(
        {
            "cell_id": ["c1", "c2", "c3", "c4", "c5"],
            "cell_type": ["Tumor/Epithelial", "CAF/Fibroblast", "Myeloid", "Unknown", "Myeloid"],
            "marker_score": [1.1, 1.2, 1.4, 0.0, 1.5],
            "marker_score_margin": [0.5, 0.4, 0.3, 0.0, 0.02],
            "sample_id": ["P01", "P01", "MET01", "MET01", "P02"],
            "lesion_type": ["Primary", "Primary", "Metastatic", "Metastatic", "Primary"],
        }
    ).to_csv(processed / "metadata.csv", index=False)

    pd.DataFrame(
        {
            "cell_type": ["Tumor/Epithelial", "CAF/Fibroblast", "Myeloid", "Unknown"],
            "lesion_type": ["Primary", "Primary", "Metastatic", "Metastatic"],
            "n_cells": [1, 1, 1, 1],
        }
    ).to_csv(processed / "annotation_summary.csv", index=False)

    pd.DataFrame(
        {
            "scope": ["global", "cell_type", "cell_type", "cell_type", "cell_type"],
            "cell_type": ["all", "Tumor/Epithelial", "CAF/Fibroblast", "Myeloid", "Unknown"],
            "frustration_score": [None, 0.1, 0.2, 0.6, 0.1],
            "outgoing_sheaf_energy": [None, 1.0, 2.0, 6.0, 1.0],
            "incoming_sheaf_energy": [None, 2.0, 1.0, 1.0, 1.0],
            "curl_participation": [None, 0.2, 0.3, 0.4, 0.1],
        }
    ).to_csv(benchmark / "results" / "hodge_decomposition_scores.csv", index=False)
    return processed, benchmark, qc_dir, manifest


def test_gse154778_qc_script_writes_tables_figures_and_manifest(tmp_path):
    qc = _load_qc_script()
    processed, benchmark, qc_dir, manifest = _write_qc_fixture(tmp_path)
    paths = qc.run_qc(processed, benchmark, qc_dir, manifest)

    for key, path in paths.items():
        assert Path(path).exists(), key

    heatmap = pd.read_csv(qc_dir / "marker_heatmap.csv")
    assert {"Tumor/Epithelial", "Myeloid"}.issubset(set(heatmap["cell_type"]))
    assert {"EPCAM", "LYZ"}.issubset(set(heatmap["gene"]))

    counts = pd.read_csv(qc_dir / "cell_type_counts.csv")
    assert {"cell_type", "lesion_type", "n_cells"}.issubset(counts.columns)

    confidence = pd.read_csv(qc_dir / "annotation_confidence.csv")
    unknown = confidence.loc[confidence["cell_type"] == "Unknown"].iloc[0]
    assert unknown["low_margin_fraction_lt_0_05"] == 1.0

    overlay = pd.read_csv(qc_dir / "frustration_annotation_overlay.csv")
    assert overlay.iloc[0]["cell_type"] == "Myeloid"
    assert "computational hypothesis" in overlay.iloc[0]["annotation_qc_note"]

    figure_manifest = pd.read_csv(manifest, sep="\t")
    assert "supp_gse154778_marker_heatmap" in set(figure_manifest["figure_id"])


def test_gse154778_qc_missing_hodge_scores_has_clear_error(tmp_path):
    qc = _load_qc_script()
    processed, benchmark, qc_dir, manifest = _write_qc_fixture(tmp_path)
    (benchmark / "results" / "hodge_decomposition_scores.csv").unlink()
    with pytest.raises(FileNotFoundError, match="hodge_decomposition_scores"):
        qc.run_qc(processed, benchmark, qc_dir, manifest)
