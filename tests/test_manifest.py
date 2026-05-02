from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sheafsignal.manifest import public_benchmark_manifest, validate_dataset_manifest
from scripts.download_public_datasets import main as download_main


def test_public_manifest_has_fixed_tme_datasets():
    root = Path(__file__).resolve().parents[1]
    table = public_benchmark_manifest(root / "metadata" / "datasets.tsv")
    assert set(table["dataset_id"]) == {
        "gse72056_melanoma_scrna",
        "gse154778_pdac_scrna",
        "gse176078_brca_scrna",
        "gse103322_hnsc_scrna",
        "tenx_breast_visium",
    }
    assert table["accession_or_doi"].ne("").all()
    assert table["download_url"].str.startswith(("http://", "https://")).all()


def test_manifest_rejects_missing_public_accession_checksum_and_license(tmp_path):
    path = tmp_path / "datasets.tsv"
    pd.DataFrame(
        [
            {
                "dataset_id": "bad_public",
                "title": "Bad public dataset",
                "modality": "scRNA-seq",
                "species": "Homo sapiens",
                "tissue": "tumor",
                "disease": "cancer",
                "accession_or_doi": "",
                "download_url": "https://example.org/file.txt.gz",
                "local_path": "data/external/file.txt.gz",
                "sha256": "",
                "license_or_terms": "",
                "release_status": "manifested",
                "benchmark_role": "public_scrna_benchmark",
            }
        ]
    ).to_csv(path, sep="\t", index=False)

    with pytest.raises(ValueError, match="accession_or_doi"):
        validate_dataset_manifest(path)


def test_download_script_can_filter_dataset_id_without_downloading(capsys):
    root = Path(__file__).resolve().parents[1]
    rc = download_main(
        [
            "--manifest",
            str(root / "metadata" / "datasets.tsv"),
            "--dataset-id",
            "gse154778_pdac_scrna",
            "--dry-run",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "gse154778_pdac_scrna" in captured.out
    assert "gse72056_melanoma_scrna" not in captured.out


def test_download_script_reports_aux_downloads_without_downloading(tmp_path, capsys):
    manifest = tmp_path / "datasets.tsv"
    pd.DataFrame(
        [
            {
                "dataset_id": "with_aux",
                "title": "Dataset with aux file",
                "modality": "Visium spatial transcriptomics",
                "species": "Homo sapiens",
                "tissue": "tumor",
                "disease": "cancer",
                "accession_or_doi": "TEST",
                "download_url": "https://example.org/main.h5",
                "aux_download_urls": "https://example.org/spatial.tar.gz",
                "local_path": "data/external/main.h5",
                "aux_local_paths": "data/external/spatial.tar.gz",
                "sha256": "PENDING_DOWNLOAD_VERIFICATION",
                "aux_sha256": "PENDING_DOWNLOAD_VERIFICATION",
                "license_or_terms": "public test",
                "release_status": "manifested",
                "benchmark_role": "public_spatial_benchmark",
            }
        ]
    ).to_csv(manifest, sep="\t", index=False)

    rc = download_main(["--manifest", str(manifest), "--dataset-id", "with_aux", "--dry-run"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "main.h5" in captured.out
    assert "spatial.tar.gz" in captured.out
