from pathlib import Path
import io
import sys
import tarfile

import h5py
import pandas as pd
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sheafsignal.adapters import (
    prepare_tenx_breast_visium,
    read_10x_h5_selected_genes,
    read_visium_spatial_positions,
)
from sheafsignal.spatial import run_spatial_hotspot_pipeline
from scripts.qc_tenx_visium_spatial import run_qc as run_visium_spatial_qc


def _write_mini_10x_h5(path: Path) -> None:
    genes = ["EPCAM", "COL1A1", "LYZ", "CD3D", "CD74", "CXCL12"]
    barcodes = ["SpotA-1", "SpotB-1", "SpotC-1", "SpotD-1"]
    dense = [
        [10, 0, 0, 1],
        [0, 8, 0, 2],
        [0, 0, 7, 1],
        [0, 1, 0, 9],
        [4, 3, 8, 2],
        [1, 6, 2, 0],
    ]
    matrix = sparse.csc_matrix(dense)
    with h5py.File(path, "w") as h5:
        group = h5.create_group("matrix")
        group.create_dataset("data", data=matrix.data)
        group.create_dataset("indices", data=matrix.indices)
        group.create_dataset("indptr", data=matrix.indptr)
        group.create_dataset("shape", data=matrix.shape)
        group.create_dataset("barcodes", data=[value.encode("utf-8") for value in barcodes])
        features = group.create_group("features")
        features.create_dataset("name", data=[value.encode("utf-8") for value in genes])
        features.create_dataset("id", data=[value.encode("utf-8") for value in genes])
        features.create_dataset("feature_type", data=[b"Gene Expression"] * len(genes))
        features.create_dataset("genome", data=[b"GRCh38"] * len(genes))


def _add_text_member(tar: tarfile.TarFile, name: str, text: str) -> None:
    payload = text.encode("utf-8")
    info = tarfile.TarInfo(name)
    info.size = len(payload)
    tar.addfile(info, io.BytesIO(payload))


def _write_mini_spatial_tar(path: Path) -> None:
    positions = "\n".join(
        [
            "SpotA-1,1,0,0,100,100",
            "SpotB-1,1,0,1,100,200",
            "SpotC-1,1,1,0,200,100",
            "SpotD-1,1,1,1,200,200",
            "",
        ]
    )
    with tarfile.open(path, "w:gz") as tar:
        _add_text_member(tar, "spatial/tissue_positions_list.csv", positions)
        _add_text_member(tar, "spatial/scalefactors_json.json", "{}")


def test_10x_h5_reader_selects_requested_genes(tmp_path):
    h5_path = tmp_path / "mini.h5"
    _write_mini_10x_h5(h5_path)

    expression = read_10x_h5_selected_genes(h5_path, genes={"EPCAM", "LYZ"})

    assert list(expression.index) == ["SpotA-1", "SpotB-1", "SpotC-1", "SpotD-1"]
    assert list(expression.columns) == ["EPCAM", "LYZ"]
    assert expression.loc["SpotA-1", "EPCAM"] == 10
    assert expression.loc["SpotC-1", "LYZ"] == 7


def test_visium_spatial_positions_reader(tmp_path):
    spatial = tmp_path / "spatial.tar.gz"
    _write_mini_spatial_tar(spatial)

    positions = read_visium_spatial_positions(spatial)

    assert list(positions["cell_id"]) == ["SpotA-1", "SpotB-1", "SpotC-1", "SpotD-1"]
    assert positions.loc[0, "x"] == 100
    assert positions.loc[1, "y"] == 100


def test_prepare_tenx_visium_outputs_profiles_and_metadata(tmp_path):
    h5_path = tmp_path / "mini.h5"
    spatial = tmp_path / "spatial.tar.gz"
    _write_mini_10x_h5(h5_path)
    _write_mini_spatial_tar(spatial)
    lr_db = tmp_path / "lr.csv"
    genes = tmp_path / "genes.txt"
    lr_db.write_text("ligand,receptor,weight\nEPCAM,CD74,1\nCXCL12,CD3D,1\n", encoding="utf-8")
    genes.write_text("EPCAM\nCOL1A1\nLYZ\nCD3D\nCD74\nCXCL12\n", encoding="utf-8")

    result = prepare_tenx_breast_visium(
        h5_path=h5_path,
        spatial_tar_path=spatial,
        expression_out=tmp_path / "expression.csv",
        metadata_out=tmp_path / "metadata.csv",
        profile_out=tmp_path / "profiles.csv",
        summary_out=tmp_path / "annotation_summary.csv",
        lr_db_path=lr_db,
        gene_set_path=genes,
    )

    assert result["status"] == "prepared"
    assert result["n_cells"] == 4
    metadata = pd.read_csv(tmp_path / "metadata.csv")
    assert {"cell_id", "spot_id", "cell_type", "x", "y", "marker_score_margin"}.issubset(
        metadata.columns
    )
    assert (tmp_path / "profiles.csv").exists()


def test_spatial_hotspot_pipeline_writes_completed_hotspots(tmp_path):
    h5_path = tmp_path / "mini.h5"
    spatial = tmp_path / "spatial.tar.gz"
    _write_mini_10x_h5(h5_path)
    _write_mini_spatial_tar(spatial)
    lr_db = tmp_path / "lr.csv"
    genes = tmp_path / "genes.txt"
    lr_db.write_text("ligand,receptor,weight\nEPCAM,CD74,1\nCXCL12,CD3D,1\n", encoding="utf-8")
    genes.write_text("EPCAM\nCOL1A1\nLYZ\nCD3D\nCD74\nCXCL12\n", encoding="utf-8")

    prepare_tenx_breast_visium(
        h5_path=h5_path,
        spatial_tar_path=spatial,
        expression_out=tmp_path / "expression.csv",
        metadata_out=tmp_path / "metadata.csv",
        profile_out=tmp_path / "profiles.csv",
        summary_out=tmp_path / "annotation_summary.csv",
        lr_db_path=lr_db,
        gene_set_path=genes,
    )
    _, hotspot_path, summary_path = run_spatial_hotspot_pipeline(
        expression_path=tmp_path / "expression.csv",
        metadata_path=tmp_path / "metadata.csv",
        lr_db_path=lr_db,
        gene_set_path=genes,
        output_dir=tmp_path / "spatial",
        dataset_id="mini_visium",
        k_neighbors=2,
    )

    hotspots = pd.read_csv(hotspot_path)
    summary = pd.read_csv(summary_path)
    assert set(hotspots["status"]) == {"completed"}
    assert hotspots["frustration_score"].sum() > 0
    assert summary.loc[0, "n_spots"] == 4


def test_visium_spatial_qc_writes_tables_and_pdfs(tmp_path):
    h5_path = tmp_path / "mini.h5"
    spatial = tmp_path / "spatial.tar.gz"
    _write_mini_10x_h5(h5_path)
    _write_mini_spatial_tar(spatial)
    lr_db = tmp_path / "lr.csv"
    genes = tmp_path / "genes.txt"
    lr_db.write_text("ligand,receptor,weight\nEPCAM,CD74,1\nCXCL12,CD3D,1\n", encoding="utf-8")
    genes.write_text("EPCAM\nCOL1A1\nLYZ\nCD3D\nCD74\nCXCL12\n", encoding="utf-8")

    prepare_tenx_breast_visium(
        h5_path=h5_path,
        spatial_tar_path=spatial,
        expression_out=tmp_path / "expression.csv",
        metadata_out=tmp_path / "metadata.csv",
        profile_out=tmp_path / "profiles.csv",
        summary_out=tmp_path / "annotation_summary.csv",
        lr_db_path=lr_db,
        gene_set_path=genes,
    )
    _, hotspot_path, _ = run_spatial_hotspot_pipeline(
        expression_path=tmp_path / "expression.csv",
        metadata_path=tmp_path / "metadata.csv",
        lr_db_path=lr_db,
        gene_set_path=genes,
        output_dir=tmp_path / "spatial",
        dataset_id="mini_visium",
        k_neighbors=2,
    )

    paths = run_visium_spatial_qc(
        expression_path=tmp_path / "expression.csv",
        metadata_path=tmp_path / "metadata.csv",
        hotspot_path=hotspot_path,
        lr_db_path=lr_db,
        gene_set_path=genes,
        output_dir=tmp_path / "spatial" / "qc",
        dataset_id="mini_visium",
        k_values=[1, 2, 3],
        reference_k=2,
        top_n=2,
    )

    for path in paths.values():
        assert path.exists()
    sensitivity = pd.read_csv(paths["k_neighbors_sensitivity_csv"])
    assert set(sensitivity["k_neighbors"]) == {1, 2, 3}
    assert "spearman_with_reference" in sensitivity.columns
