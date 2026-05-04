import gzip
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sheafsignal.adapters import (
    prepare_gse154778_pdac_profiles,
    prepare_gse72056_melanoma_profiles,
)


def _write_gse154778_fixture(path: Path) -> None:
    matrix = pd.DataFrame(
        {
            "P01:1": [9, 0, 0, 0, 0],
            "P01:2": [7, 0, 0, 0, 0],
            "MET01:1": [0, 8, 0, 0, 0],
            "MET01:2": [0, 6, 0, 0, 0],
            "P02:1": [0, 0, 10, 0, 0],
            "P02:2": [0, 0, 12, 0, 0],
        },
        index=["EPCAM", "LYZ", "COL1A1", "CCR2", "KRT19"],
    )
    matrix.to_csv(path, compression="gzip")


def _write_gse72056_fixture(path: Path) -> None:
    rows = pd.DataFrame(
        {
            "CellA": [72, 1, 3, 10, 0, 0, 1],
            "CellB": [72, 1, 3, 8, 0, 0, 1],
            "CellC": [71, 2, 0, 0, 9, 0, 0],
            "CellD": [71, 2, 0, 0, 7, 0, 0],
            "CellE": [73, 1, 5, 0, 0, 11, 0],
        },
        index=[
            "tumor",
            "malignant(1=no,2=yes,0=unresolved)",
            "non-malignant cell type (1=T,2=B,3=Macro.4=Endo.,5=CAF;6=NK)",
            "LYZ",
            "EPCAM",
            "COL1A1",
            "CD3D",
        ],
    )
    rows.to_csv(path, sep="\t", index_label="Cell", compression="gzip")


def _write_lr_and_gene_set(tmp_path: Path) -> tuple[Path, Path]:
    lr = tmp_path / "lr.csv"
    genes = tmp_path / "genes.txt"
    lr.write_text(
        "ligand,receptor,weight\nEPCAM,CCR2,1\nCOL1A1,LYZ,1\n",
        encoding="utf-8",
    )
    genes.write_text("EPCAM\nLYZ\nCOL1A1\nCCR2\nKRT19\n", encoding="utf-8")
    return lr, genes


def _metadata_counts(metadata_path: Path) -> pd.DataFrame:
    metadata = pd.read_csv(metadata_path)
    return (
        metadata.groupby("cell_type", dropna=False)
        .size()
        .reset_index(name="metadata_n_cells")
        .sort_values("cell_type")
        .reset_index(drop=True)
    )


def test_gse154778_profile_summary_matches_metadata_counts(tmp_path):
    raw = tmp_path / "gse154778.csv.gz"
    _write_gse154778_fixture(raw)
    lr, genes = _write_lr_and_gene_set(tmp_path)
    out = tmp_path / "gse154778"

    result = prepare_gse154778_pdac_profiles(
        raw_path=raw,
        profile_out=out / "profiles.csv",
        metadata_out=out / "metadata.csv",
        summary_out=out / "annotation_summary.csv",
        lr_db_path=lr,
        gene_set_path=genes,
        expression_out=out / "expression.csv",
        marker_margin=0.0,
    )

    metadata = pd.read_csv(out / "metadata.csv")
    summary = pd.read_csv(out / "annotation_summary.csv")
    count_check = summary.groupby("cell_type")["n_cells"].sum().reset_index()
    count_check = count_check.merge(_metadata_counts(out / "metadata.csv"), on="cell_type")
    profiles = pd.read_csv(out / "profiles.csv", index_col=0)

    assert result["n_cells"] == 6
    assert set(metadata["lesion_type"]) == {"Primary", "Metastatic"}
    assert (count_check["n_cells"] == count_check["metadata_n_cells"]).all()
    assert set(count_check["cell_type"]) == set(profiles.index)


def test_gse72056_profile_summary_matches_metadata_counts(tmp_path):
    raw = tmp_path / "gse72056.txt.gz"
    _write_gse72056_fixture(raw)
    lr, genes = _write_lr_and_gene_set(tmp_path)
    out = tmp_path / "gse72056"

    result = prepare_gse72056_melanoma_profiles(
        raw_path=raw,
        profile_out=out / "profiles.csv",
        metadata_out=out / "metadata.csv",
        summary_out=out / "annotation_summary.csv",
        lr_db_path=lr,
        gene_set_path=genes,
        expression_out=out / "expression.csv",
    )

    summary = pd.read_csv(out / "annotation_summary.csv")
    count_check = summary.merge(_metadata_counts(out / "metadata.csv"), on="cell_type")
    profiles = pd.read_csv(out / "profiles.csv", index_col=0)

    assert result["n_cells"] == 5
    assert (count_check["n_cells"] == count_check["metadata_n_cells"]).all()
    assert set(count_check["cell_type"]) == set(profiles.index)


def test_gse72056_adapter_reads_gzip_text_fixture_without_plaintext_side_effect(tmp_path):
    raw = tmp_path / "gse72056.txt.gz"
    _write_gse72056_fixture(raw)

    with gzip.open(raw, "rt", encoding="utf-8") as handle:
        first_line = handle.readline()

    assert first_line.startswith("Cell\tCellA")
    assert not (tmp_path / "gse72056.txt").exists()
