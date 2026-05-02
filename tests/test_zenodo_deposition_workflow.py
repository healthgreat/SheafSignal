from pathlib import Path
import importlib.util
import json

import pandas as pd
import pytest


def _load_script(name: str):
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_zenodo_deposition_metadata_uses_archive_manifest():
    script = _load_script("build_zenodo_deposition_package")
    base = {
        "title": "SheafSignal",
        "creators": [{"name": "A. Author"}],
        "keywords": ["sheaf theory"],
    }
    zenodo_manifest = pd.DataFrame(
        [
            {"relative_path": "data/processed/x.csv", "size_mb": 1.5},
            {"relative_path": "data/processed/y.csv", "size_mb": 2.0},
        ]
    )
    archive_manifest = pd.DataFrame(
        [
            {
                "archive_target": "zenodo",
                "archive_path": "release/archives/sheafsignal_zenodo_upload.zip",
                "sha256": "a" * 64,
            }
        ]
    )

    metadata = script.build_deposition_metadata(
        base_metadata=base,
        zenodo_manifest=zenodo_manifest,
        archive_manifest=archive_manifest,
    )

    assert metadata["upload_type"] == "dataset"
    assert metadata["license"] == "cc-by-4.0"
    assert "a" * 64 in metadata["notes"]
    assert "3.500" in metadata["notes"]


def test_zenodo_deposition_package_writes_json_and_instructions(tmp_path):
    script = _load_script("build_zenodo_deposition_package")
    (tmp_path / ".zenodo.json").write_text(
        json.dumps({"title": "SheafSignal", "creators": [{"name": "TBD"}]}),
        encoding="utf-8",
    )
    release = tmp_path / "release"
    release.mkdir()
    pd.DataFrame(
        [{"relative_path": "data/processed/x.csv", "size_mb": 1.0}]
    ).to_csv(release / "zenodo_upload_manifest.tsv", sep="\t", index=False)
    pd.DataFrame(
        [
            {
                "archive_target": "zenodo",
                "archive_path": "release/archives/sheafsignal_zenodo_upload.zip",
                "size_mb": 9.0,
                "sha256": "b" * 64,
            }
        ]
    ).to_csv(release / "archive_manifest.tsv", sep="\t", index=False)

    paths = script.build_package(tmp_path, release)

    assert paths["metadata"].exists()
    assert paths["instructions"].exists()
    metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["title"] == "SheafSignal"
    assert "release/archives/sheafsignal_zenodo_upload.zip" in paths[
        "instructions"
    ].read_text(encoding="utf-8")


def test_finalize_zenodo_doi_updates_manifest_statement_and_checklist(tmp_path):
    script = _load_script("finalize_zenodo_doi")
    (tmp_path / "metadata").mkdir()
    (tmp_path / "release").mkdir()
    package = tmp_path / "manuscript" / "nature_methods_package"
    package.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "dataset_id": "demo_synthetic",
                "benchmark_role": "ci_demo",
                "zenodo_doi": "NA",
            },
            {
                "dataset_id": "gse154778_pdac_scrna",
                "benchmark_role": "public_scrna_benchmark",
                "zenodo_doi": "PENDING_ZENODO_RELEASE",
            },
        ]
    ).to_csv(tmp_path / "metadata" / "datasets.tsv", sep="\t", index=False)
    (tmp_path / "release" / "DATA_AVAILABILITY_STATEMENT_DRAFT.md").write_text(
        "Current DOI status: `PENDING_ZENODO_RELEASE`.\n",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "item": "Zenodo DOI minted",
                "status": "blocking_pending",
                "evidence_or_action": "Mint DOI.",
            }
        ]
    ).to_csv(package / "07_submission_checklist.tsv", sep="\t", index=False)

    result = script.finalize_release(tmp_path, "10.5281/zenodo.1234567")

    datasets = pd.read_csv(
        tmp_path / "metadata" / "datasets.tsv",
        sep="\t",
        keep_default_na=False,
    )
    public_row = datasets.loc[datasets["dataset_id"] == "gse154778_pdac_scrna"].iloc[0]
    demo_row = datasets.loc[datasets["dataset_id"] == "demo_synthetic"].iloc[0]
    assert public_row["zenodo_doi"] == "10.5281/zenodo.1234567"
    assert demo_row["zenodo_doi"] == "NA"
    assert "https://doi.org/10.5281/zenodo.1234567" in (
        tmp_path / "release" / "DATA_AVAILABILITY_STATEMENT_DRAFT.md"
    ).read_text(encoding="utf-8")
    checklist = pd.read_csv(package / "07_submission_checklist.tsv", sep="\t")
    assert checklist.loc[0, "status"] == "complete_after_doi"
    assert result["summary"].exists()


def test_finalize_zenodo_doi_rejects_invalid_doi():
    script = _load_script("finalize_zenodo_doi")

    with pytest.raises(ValueError):
        script.validate_doi("not-a-doi")

    assert script.validate_doi("https://doi.org/10.5281/zenodo.123") == "10.5281/zenodo.123"
