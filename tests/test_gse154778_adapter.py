from pathlib import Path
import importlib.util
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sheafsignal.adapters import (
    annotate_cells_by_markers,
    prepare_gse154778_pdac_profiles,
    parse_gse154778_cell_id,
    prepare_gse154778_pdac,
    read_gse154778_dge_matrix,
    read_gse154778_selected_genes,
)


def _write_mini_dge(path: Path) -> None:
    genes_by_cells = pd.DataFrame(
        {
            "P01:1": [5, 0, 0, 0, 0, 0, 0, 0],
            "P01:2": [0, 8, 0, 0, 0, 0, 0, 0],
            "MET01:1": [0, 0, 7, 0, 0, 0, 0, 0],
            "MET01:2": [0, 0, 0, 9, 0, 0, 0, 0],
            "P02:1": [0, 0, 0, 0, 10, 0, 0, 0],
            "P02:2": [0, 0, 0, 0, 0, 6, 0, 0],
        },
        index=["EPCAM", "COL1A1", "LYZ", "PECAM1", "CD3D", "MS4A1", "KRT19", "CD68"],
    )
    genes_by_cells.to_csv(path, compression="gzip")


def _load_prepare_script():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "prepare_public_datasets.py"
    spec = importlib.util.spec_from_file_location("prepare_public_datasets", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _mini_manifest(path: Path, raw_path: Path) -> None:
    pd.DataFrame(
        [
            {
                "dataset_id": "gse154778_pdac_scrna",
                "title": "Mini GSE154778",
                "modality": "scRNA-seq",
                "species": "Homo sapiens",
                "tissue": "pancreatic tumor",
                "disease": "PDAC tumor microenvironment",
                "accession_or_doi": "GSE154778",
                "download_url": "https://example.org/GSE154778_dgeMtx.csv.gz",
                "aux_download_urls": "NA",
                "local_path": str(raw_path),
                "aux_local_paths": "NA",
                "sha256": "PENDING_DOWNLOAD_VERIFICATION",
                "license_or_terms": "GEO public processed supplementary file",
                "release_status": "manifested",
                "benchmark_role": "public_scrna_benchmark",
                "zenodo_doi": "PENDING_ZENODO_RELEASE",
                "prepared_expression": "data/processed/gse154778_pdac_scrna/expression.csv",
                "prepared_metadata": "data/processed/gse154778_pdac_scrna/metadata.csv",
                "notes": "mini test manifest",
            }
        ]
    ).to_csv(path, sep="\t", index=False)


def test_gse154778_matrix_is_transposed_to_cells_by_genes(tmp_path):
    raw = tmp_path / "mini_dge.csv.gz"
    _write_mini_dge(raw)
    expression = read_gse154778_dge_matrix(raw)
    assert list(expression.index[:3]) == ["P01:1", "P01:2", "MET01:1"]
    assert {"EPCAM", "COL1A1", "LYZ"}.issubset(expression.columns)
    assert expression.loc["P01:1", "EPCAM"] == 5


def test_gse154778_selected_gene_reader_avoids_unneeded_rows(tmp_path):
    raw = tmp_path / "mini_dge.csv.gz"
    _write_mini_dge(raw)
    expression = read_gse154778_selected_genes(raw, genes={"EPCAM", "LYZ"}, max_cells=3)
    assert list(expression.index) == ["P01:1", "P01:2", "MET01:1"]
    assert list(expression.columns) == ["EPCAM", "LYZ"]


def test_gse154778_sample_parser_identifies_lesion_type():
    assert parse_gse154778_cell_id("P01:1") == {
        "sample_id": "P01",
        "lesion_type": "Primary",
    }
    assert parse_gse154778_cell_id("MET01:1") == {
        "sample_id": "MET01",
        "lesion_type": "Metastatic",
    }


def test_marker_annotation_labels_toy_cells(tmp_path):
    raw = tmp_path / "mini_dge.csv.gz"
    _write_mini_dge(raw)
    expression = read_gse154778_dge_matrix(raw)
    metadata = annotate_cells_by_markers(expression, margin=0.0)
    labels = dict(zip(metadata["cell_id"], metadata["cell_type"]))
    assert labels["P01:1"] == "Tumor/Epithelial"
    assert labels["P01:2"] == "CAF/Fibroblast"
    assert labels["MET01:1"] == "Myeloid"
    assert labels["MET01:2"] == "Endothelial"


def test_prepare_gse154778_writes_expression_and_metadata(tmp_path):
    raw = tmp_path / "mini_dge.csv.gz"
    expression_out = tmp_path / "expression.csv"
    metadata_out = tmp_path / "metadata.csv"
    _write_mini_dge(raw)
    result = prepare_gse154778_pdac(raw, expression_out, metadata_out, max_cells=4, marker_margin=0.0)
    assert result["status"] == "prepared"
    assert expression_out.exists()
    assert metadata_out.exists()
    metadata = pd.read_csv(metadata_out)
    assert {"cell_id", "cell_type", "sample_id", "lesion_type"}.issubset(metadata.columns)
    assert set(metadata["lesion_type"]) == {"Primary", "Metastatic"}


def test_prepare_gse154778_profile_only_writes_compact_outputs(tmp_path):
    raw = tmp_path / "mini_dge.csv.gz"
    _write_mini_dge(raw)
    lr_db = tmp_path / "lr.csv"
    genes = tmp_path / "genes.txt"
    lr_db.write_text("ligand,receptor,weight\nEPCAM,PECAM1,1\nCOL1A1,LYZ,1\n", encoding="utf-8")
    genes.write_text("EPCAM\nCOL1A1\nLYZ\nPECAM1\n", encoding="utf-8")

    result = prepare_gse154778_pdac_profiles(
        raw_path=raw,
        profile_out=tmp_path / "profiles.csv",
        metadata_out=tmp_path / "metadata.csv",
        summary_out=tmp_path / "annotation_summary.csv",
        lr_db_path=lr_db,
        gene_set_path=genes,
        marker_margin=0.0,
    )
    assert result["status"] == "profile_prepared"
    profiles = pd.read_csv(tmp_path / "profiles.csv", index_col=0)
    assert {"Tumor/Epithelial", "CAF/Fibroblast", "Myeloid", "Endothelial"}.issubset(
        set(profiles.index)
    )
    assert {"EPCAM", "COL1A1", "LYZ", "PECAM1"}.issubset(profiles.columns)


def test_prepare_gse154778_profiles_can_write_selected_expression(tmp_path):
    raw = tmp_path / "mini_dge.csv.gz"
    _write_mini_dge(raw)
    lr_db = tmp_path / "lr.csv"
    genes = tmp_path / "genes.txt"
    lr_db.write_text("ligand,receptor,weight\nEPCAM,PECAM1,1\nCOL1A1,LYZ,1\n", encoding="utf-8")
    genes.write_text("EPCAM\nCOL1A1\nLYZ\nPECAM1\n", encoding="utf-8")

    result = prepare_gse154778_pdac_profiles(
        raw_path=raw,
        profile_out=tmp_path / "profiles.csv",
        metadata_out=tmp_path / "metadata.csv",
        summary_out=tmp_path / "annotation_summary.csv",
        lr_db_path=lr_db,
        gene_set_path=genes,
        expression_out=tmp_path / "expression.csv",
        marker_margin=0.0,
    )

    assert result["status"] == "prepared"
    expression = pd.read_csv(tmp_path / "expression.csv")
    assert expression.shape[0] == 6
    assert {"cell_id", "EPCAM", "COL1A1", "LYZ", "PECAM1"}.issubset(
        expression.columns
    )


def test_prepare_script_reports_missing_raw_download(tmp_path, monkeypatch):
    manifest = tmp_path / "datasets.tsv"
    raw = tmp_path / "missing.csv.gz"
    _mini_manifest(manifest, raw)
    monkeypatch.chdir(tmp_path)
    prepare = _load_prepare_script()
    assert prepare.main(["--manifest", str(manifest), "--dataset-id", "gse154778_pdac_scrna"]) == 0
    status = pd.read_csv(tmp_path / "benchmarks" / "results" / "public_dataset_preparation_plan.csv")
    assert status.loc[0, "status"] == "missing_raw_download"


def test_prepare_script_uses_gse154778_adapter_for_mini_raw(tmp_path, monkeypatch):
    manifest = tmp_path / "datasets.tsv"
    raw = tmp_path / "mini_dge.csv.gz"
    _write_mini_dge(raw)
    _mini_manifest(manifest, raw)
    monkeypatch.chdir(tmp_path)
    prepare = _load_prepare_script()
    assert (
        prepare.main(
            [
                "--manifest",
                str(manifest),
                "--dataset-id",
                "gse154778_pdac_scrna",
                "--max-cells",
                "4",
                "--marker-margin",
                "0",
            ]
        )
        == 0
    )
    expression = tmp_path / "data" / "processed" / "gse154778_pdac_scrna" / "expression.csv"
    metadata = tmp_path / "data" / "processed" / "gse154778_pdac_scrna" / "metadata.csv"
    assert expression.exists()
    assert metadata.exists()
    assert pd.read_csv(metadata).shape[0] == 4


def test_prepare_script_writes_gse154778_selected_expression_in_profile_mode(
    tmp_path,
    monkeypatch,
):
    manifest = tmp_path / "datasets.tsv"
    raw = tmp_path / "mini_dge.csv.gz"
    _write_mini_dge(raw)
    _mini_manifest(manifest, raw)
    (tmp_path / "metadata").mkdir(exist_ok=True)
    (tmp_path / "metadata" / "tme_ligand_receptor.csv").write_text(
        "ligand,receptor,weight\nEPCAM,PECAM1,1\nCOL1A1,LYZ,1\n",
        encoding="utf-8",
    )
    (tmp_path / "metadata" / "tme_pathway_genes.txt").write_text(
        "EPCAM\nCOL1A1\nLYZ\nPECAM1\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    prepare = _load_prepare_script()

    assert (
        prepare.main(
            [
                "--manifest",
                str(manifest),
                "--dataset-id",
                "gse154778_pdac_scrna",
                "--profile-only",
                "--write-selected-expression",
                "--marker-margin",
                "0",
            ]
        )
        == 0
    )

    expression = tmp_path / "data" / "processed" / "gse154778_pdac_scrna" / "expression.csv"
    plan = pd.read_csv(tmp_path / "benchmarks" / "results" / "public_dataset_preparation_plan.csv")
    assert expression.exists()
    assert pd.read_csv(expression).shape[0] == 6
    assert plan.loc[0, "status"] == "prepared"
