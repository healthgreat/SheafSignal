from pathlib import Path
import importlib.util
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sheafsignal.adapters import (
    prepare_gse72056_melanoma_profiles,
    read_gse72056_selected_genes,
)


def _write_mini_gse72056(path: Path) -> None:
    genes_by_cells = pd.DataFrame(
        {
            "CellA": [72, 1, 3, 10, 0, 0, 1],
            "CellB": [58, 1, 6, 0, 0, 0, 8],
            "CellC": [71, 2, 0, 0, 12, 0, 0],
            "CellD": [72, 1, 5, 0, 0, 9, 0],
            "CellE": [90, 0, 0, 0, 0, 0, 0],
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
    genes_by_cells.to_csv(path, sep="\t", index_label="Cell", compression="gzip")


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
                "dataset_id": "gse72056_melanoma_scrna",
                "title": "Mini GSE72056",
                "modality": "scRNA-seq",
                "species": "Homo sapiens",
                "tissue": "melanoma tumor",
                "disease": "tumor microenvironment",
                "accession_or_doi": "GSE72056",
                "download_url": "https://example.org/GSE72056.txt.gz",
                "aux_download_urls": "NA",
                "local_path": str(raw_path),
                "aux_local_paths": "NA",
                "sha256": "PENDING_DOWNLOAD_VERIFICATION",
                "license_or_terms": "GEO public processed supplementary file",
                "release_status": "manifested",
                "benchmark_role": "public_scrna_benchmark",
                "zenodo_doi": "PENDING_ZENODO_RELEASE",
                "prepared_expression": "data/processed/gse72056_melanoma_scrna/expression.csv",
                "prepared_metadata": "data/processed/gse72056_melanoma_scrna/metadata.csv",
                "notes": "mini test manifest",
            }
        ]
    ).to_csv(path, sep="\t", index=False)


def test_gse72056_reader_transposes_and_maps_author_annotations(tmp_path):
    raw = tmp_path / "mini_gse72056.txt.gz"
    _write_mini_gse72056(raw)

    expression, metadata = read_gse72056_selected_genes(raw, genes={"LYZ", "EPCAM", "COL1A1", "CD3D"})

    assert list(expression.index) == ["CellA", "CellB", "CellC", "CellD", "CellE"]
    assert list(expression.columns) == ["CD3D", "COL1A1", "EPCAM", "LYZ"]
    assert expression.loc["CellA", "LYZ"] == 10

    labels = dict(zip(metadata["cell_id"], metadata["cell_type"]))
    assert labels["CellA"] == "Myeloid"
    assert labels["CellB"] == "T/NK"
    assert labels["CellC"] == "Tumor/Malignant"
    assert labels["CellD"] == "CAF/Fibroblast"
    assert labels["CellE"] == "Unknown"

    samples = dict(zip(metadata["cell_id"], metadata["sample_id"]))
    assert samples["CellA"] == "Mel72"
    assert samples["CellC"] == "Mel71"


def test_prepare_gse72056_profile_outputs_author_annotation_summary(tmp_path):
    raw = tmp_path / "mini_gse72056.txt.gz"
    _write_mini_gse72056(raw)
    lr_db = tmp_path / "lr.csv"
    genes = tmp_path / "genes.txt"
    lr_db.write_text("ligand,receptor,weight\nLYZ,EPCAM,1\nCOL1A1,CD3D,1\n", encoding="utf-8")
    genes.write_text("LYZ\nEPCAM\nCOL1A1\nCD3D\n", encoding="utf-8")

    result = prepare_gse72056_melanoma_profiles(
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
    assert result["n_cell_types"] == 5
    expression = pd.read_csv(tmp_path / "expression.csv")
    assert {"cell_id", "LYZ", "EPCAM"}.issubset(expression.columns)
    profiles = pd.read_csv(tmp_path / "profiles.csv", index_col=0)
    assert {"Myeloid", "T/NK", "Tumor/Malignant", "CAF/Fibroblast", "Unknown"}.issubset(
        set(profiles.index)
    )
    summary = pd.read_csv(tmp_path / "annotation_summary.csv")
    assert {"cell_type", "n_cells", "n_samples"}.issubset(summary.columns)
    assert int(summary.loc[summary["cell_type"] == "CAF/Fibroblast", "n_cells"].iloc[0]) == 1


def test_prepare_script_uses_gse72056_adapter_for_mini_raw(tmp_path, monkeypatch):
    manifest = tmp_path / "datasets.tsv"
    raw = tmp_path / "mini_gse72056.txt.gz"
    _write_mini_gse72056(raw)
    _mini_manifest(manifest, raw)

    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir()
    (metadata_dir / "tme_ligand_receptor.csv").write_text(
        "ligand,receptor,weight\nLYZ,EPCAM,1\nCOL1A1,CD3D,1\n",
        encoding="utf-8",
    )
    (metadata_dir / "tme_pathway_genes.txt").write_text(
        "LYZ\nEPCAM\nCOL1A1\nCD3D\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    prepare = _load_prepare_script()
    assert prepare.main(["--manifest", str(manifest), "--dataset-id", "gse72056_melanoma_scrna"]) == 0

    plan = pd.read_csv(tmp_path / "benchmarks" / "results" / "public_dataset_preparation_plan.csv")
    assert plan.loc[0, "status"] == "profile_prepared"
    profile = tmp_path / "data" / "processed" / "gse72056_melanoma_scrna" / "profiles.csv"
    metadata = tmp_path / "data" / "processed" / "gse72056_melanoma_scrna" / "metadata.csv"
    assert profile.exists()
    assert metadata.exists()


def test_prepare_public_script_can_write_gse72056_selected_expression(tmp_path, monkeypatch):
    script = _load_prepare_script()
    monkeypatch.chdir(tmp_path)
    (tmp_path / "metadata").mkdir()
    (tmp_path / "data" / "external" / "gse72056_melanoma_scrna").mkdir(parents=True)
    raw = tmp_path / "data" / "external" / "gse72056_melanoma_scrna" / "mini.txt.gz"
    _write_mini_gse72056(raw)
    _mini_manifest(tmp_path / "metadata" / "datasets.tsv", raw)
    (tmp_path / "metadata" / "tme_ligand_receptor.csv").write_text(
        "ligand,receptor\nLYZ,EPCAM\n",
        encoding="utf-8",
    )
    (tmp_path / "metadata" / "tme_pathway_genes.txt").write_text(
        "COL1A1\nCD3D\n",
        encoding="utf-8",
    )

    assert (
        script.main(
            [
                "--dataset-id",
                "gse72056_melanoma_scrna",
                "--write-selected-expression",
            ]
        )
        == 0
    )

    plan = pd.read_csv(tmp_path / "benchmarks" / "results" / "public_dataset_preparation_plan.csv")
    assert plan.loc[0, "status"] == "prepared"
    expression = tmp_path / "data" / "processed" / "gse72056_melanoma_scrna" / "expression.csv"
    assert expression.exists()
