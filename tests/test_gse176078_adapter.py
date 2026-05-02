from pathlib import Path
import importlib.util
import io
import sys
import tarfile

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sheafsignal.adapters import (
    prepare_gse176078_brca_profiles,
    read_gse176078_selected_genes,
)


def _add_text_member(tar: tarfile.TarFile, name: str, text: str) -> None:
    payload = text.encode("utf-8")
    info = tarfile.TarInfo(name)
    info.size = len(payload)
    tar.addfile(info, io.BytesIO(payload))


def _write_mini_gse176078_archive(path: Path) -> None:
    prefix = "Wu_etal_2021_BRCA_scRNASeq"
    genes = "LYZ\nEPCAM\nCOL1A1\nCD3D\nMS4A1\nCXCL12\n"
    barcodes = "CellA\nCellB\nCellC\nCellD\nCellE\n"
    mtx = "\n".join(
        [
            "%%MatrixMarket matrix coordinate integer general",
            "6 5 6",
            "1 1 10",
            "2 2 12",
            "3 3 8",
            "4 4 7",
            "5 5 9",
            "6 3 2",
            "",
        ]
    )
    metadata = pd.DataFrame(
        {
            "Unnamed: 0": ["CellA", "CellB", "CellC", "CellD", "CellE"],
            "orig.ident": ["CID1", "CID1", "CID2", "CID2", "CID3"],
            "nCount_RNA": [100, 120, 80, 70, 90],
            "nFeature_RNA": [10, 12, 8, 7, 9],
            "percent.mito": [1.0, 2.0, 3.0, 1.5, 2.5],
            "subtype": ["TNBC", "TNBC", "ER+", "ER+", "HER2+"],
            "celltype_subset": ["Macrophage", "Cancer", "CAFs", "CD4", "B cells"],
            "celltype_minor": ["Macrophage", "Cancer LumA SC", "CAFs", "T cells CD4+", "B cells"],
            "celltype_major": ["Myeloid", "Cancer Epithelial", "CAFs", "T-cells", "B-cells"],
        }
    ).to_csv(index=False)

    with tarfile.open(path, "w:gz") as tar:
        _add_text_member(tar, f"{prefix}/count_matrix_genes.tsv", genes)
        _add_text_member(tar, f"{prefix}/count_matrix_barcodes.tsv", barcodes)
        _add_text_member(tar, f"{prefix}/count_matrix_sparse.mtx", mtx)
        _add_text_member(tar, f"{prefix}/metadata.csv", metadata)


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
                "dataset_id": "gse176078_brca_scrna",
                "title": "Mini GSE176078",
                "modality": "scRNA-seq",
                "species": "Homo sapiens",
                "tissue": "breast tumor",
                "disease": "breast cancer tumor microenvironment",
                "accession_or_doi": "GSE176078",
                "download_url": "https://example.org/GSE176078.tar.gz",
                "aux_download_urls": "NA",
                "local_path": str(raw_path),
                "aux_local_paths": "NA",
                "sha256": "PENDING_DOWNLOAD_VERIFICATION",
                "license_or_terms": "GEO public processed supplementary file",
                "release_status": "manifested",
                "benchmark_role": "public_scrna_benchmark",
                "zenodo_doi": "PENDING_ZENODO_RELEASE",
                "prepared_expression": "data/processed/gse176078_brca_scrna/expression.csv",
                "prepared_metadata": "data/processed/gse176078_brca_scrna/metadata.csv",
                "notes": "mini test manifest",
            }
        ]
    ).to_csv(path, sep="\t", index=False)


def test_gse176078_reader_streams_selected_genes_and_maps_author_annotations(tmp_path):
    raw = tmp_path / "mini_gse176078.tar.gz"
    _write_mini_gse176078_archive(raw)

    expression, metadata = read_gse176078_selected_genes(
        raw,
        genes={"LYZ", "EPCAM", "COL1A1", "CD3D", "MS4A1"},
    )

    assert list(expression.index) == ["CellA", "CellB", "CellC", "CellD", "CellE"]
    assert list(expression.columns) == ["CD3D", "COL1A1", "EPCAM", "LYZ", "MS4A1"]
    assert expression.loc["CellA", "LYZ"] == 10
    assert expression.loc["CellC", "COL1A1"] == 8

    labels = dict(zip(metadata["cell_id"], metadata["cell_type"]))
    assert labels["CellA"] == "Myeloid"
    assert labels["CellB"] == "Tumor/Malignant"
    assert labels["CellC"] == "CAF/Fibroblast"
    assert labels["CellD"] == "T/NK"
    assert labels["CellE"] == "B/Plasma"


def test_gse176078_reader_respects_max_cells(tmp_path):
    raw = tmp_path / "mini_gse176078.tar.gz"
    _write_mini_gse176078_archive(raw)

    expression, metadata = read_gse176078_selected_genes(
        raw,
        genes={"LYZ", "EPCAM", "COL1A1", "CD3D", "MS4A1"},
        max_cells=3,
    )

    assert list(expression.index) == ["CellA", "CellB", "CellC"]
    assert list(metadata["cell_id"]) == ["CellA", "CellB", "CellC"]


def test_prepare_gse176078_profile_outputs_author_annotation_summary(tmp_path):
    raw = tmp_path / "mini_gse176078.tar.gz"
    _write_mini_gse176078_archive(raw)
    lr_db = tmp_path / "lr.csv"
    genes = tmp_path / "genes.txt"
    lr_db.write_text("ligand,receptor,weight\nLYZ,EPCAM,1\nCOL1A1,CD3D,1\n", encoding="utf-8")
    genes.write_text("LYZ\nEPCAM\nCOL1A1\nCD3D\nMS4A1\n", encoding="utf-8")

    result = prepare_gse176078_brca_profiles(
        raw_path=raw,
        profile_out=tmp_path / "profiles.csv",
        metadata_out=tmp_path / "metadata.csv",
        summary_out=tmp_path / "annotation_summary.csv",
        lr_db_path=lr_db,
        gene_set_path=genes,
        expression_out=tmp_path / "expression.csv",
    )

    assert result["status"] == "prepared"
    assert result["n_cells"] == 5
    expression = pd.read_csv(tmp_path / "expression.csv")
    assert {"cell_id", "LYZ", "EPCAM"}.issubset(expression.columns)
    profiles = pd.read_csv(tmp_path / "profiles.csv", index_col=0)
    assert {"Myeloid", "Tumor/Malignant", "CAF/Fibroblast", "T/NK", "B/Plasma"}.issubset(
        set(profiles.index)
    )
    summary = pd.read_csv(tmp_path / "annotation_summary.csv")
    assert {"cell_type", "subtype", "n_cells", "n_samples"}.issubset(summary.columns)


def test_prepare_script_uses_gse176078_adapter_for_mini_raw(tmp_path, monkeypatch):
    manifest = tmp_path / "datasets.tsv"
    raw = tmp_path / "mini_gse176078.tar.gz"
    _write_mini_gse176078_archive(raw)
    _mini_manifest(manifest, raw)

    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir()
    (metadata_dir / "tme_ligand_receptor.csv").write_text(
        "ligand,receptor,weight\nLYZ,EPCAM,1\nCOL1A1,CD3D,1\n",
        encoding="utf-8",
    )
    (metadata_dir / "tme_pathway_genes.txt").write_text(
        "LYZ\nEPCAM\nCOL1A1\nCD3D\nMS4A1\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    prepare = _load_prepare_script()
    assert prepare.main(["--manifest", str(manifest), "--dataset-id", "gse176078_brca_scrna"]) == 0

    plan = pd.read_csv(tmp_path / "benchmarks" / "results" / "public_dataset_preparation_plan.csv")
    assert plan.loc[0, "status"] == "profile_prepared"
    profile = tmp_path / "data" / "processed" / "gse176078_brca_scrna" / "profiles.csv"
    metadata = tmp_path / "data" / "processed" / "gse176078_brca_scrna" / "metadata.csv"
    assert profile.exists()
    assert metadata.exists()


def test_prepare_public_script_can_write_gse176078_selected_expression(tmp_path, monkeypatch):
    script = _load_prepare_script()
    monkeypatch.chdir(tmp_path)
    (tmp_path / "metadata").mkdir()
    (tmp_path / "data" / "external" / "gse176078_brca_scrna").mkdir(parents=True)
    raw = tmp_path / "data" / "external" / "gse176078_brca_scrna" / "mini.tar.gz"
    _write_mini_gse176078_archive(raw)
    _mini_manifest(tmp_path / "metadata" / "datasets.tsv", raw)
    (tmp_path / "metadata" / "tme_ligand_receptor.csv").write_text(
        "ligand,receptor\nLYZ,EPCAM\n",
        encoding="utf-8",
    )
    (tmp_path / "metadata" / "tme_pathway_genes.txt").write_text(
        "COL1A1\nCD3D\nMS4A1\n",
        encoding="utf-8",
    )

    assert (
        script.main(
            [
                "--dataset-id",
                "gse176078_brca_scrna",
                "--write-selected-expression",
            ]
        )
        == 0
    )

    plan = pd.read_csv(tmp_path / "benchmarks" / "results" / "public_dataset_preparation_plan.csv")
    assert plan.loc[0, "status"] == "prepared"
    expression = tmp_path / "data" / "processed" / "gse176078_brca_scrna" / "expression.csv"
    assert expression.exists()
