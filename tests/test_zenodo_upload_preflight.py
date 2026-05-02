from pathlib import Path
import importlib.util
import json
import sys
import zipfile


def _load_script(name: str):
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _write_minimal_package(tmp_path: Path, script) -> None:
    release = tmp_path / "release"
    archive_dir = release / "archives"
    metadata = tmp_path / "metadata"
    archive_dir.mkdir(parents=True)
    metadata.mkdir()
    archive = archive_dir / "sheafsignal_zenodo_upload.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("benchmarks/results/demo.csv", "x\n1\n")
    sha = script.sha256_file(archive)
    (release / "archive_manifest.tsv").write_text(
        "archive_target\tarchive_path\tn_files\tsize_bytes\tsize_mb\tsha256\ttracked_in_git\n"
        f"zenodo\trelease/archives/sheafsignal_zenodo_upload.zip\t1\t{archive.stat().st_size}\t0.001\t{sha}\tFalse\n",
        encoding="utf-8",
    )
    (release / "zenodo_deposition_metadata.json").write_text(
        json.dumps(
            {
                "title": "SheafSignal",
                "upload_type": "dataset",
                "description": "demo",
                "creators": [{"name": "Chen, Chongfa"}],
                "license": "cc-by-4.0",
                "notes": f"Archive SHA256: {sha}.",
                "related_identifiers": [
                    {"identifier": "https://github.com/healthgreat/SheafSignal"}
                ],
            }
        ),
        encoding="utf-8",
    )
    (release / "ZENODO_DEPOSITION_INSTRUCTIONS.md").write_text(
        f"Archive SHA256: `{sha}`\n",
        encoding="utf-8",
    )
    (release / "DATA_AVAILABILITY_STATEMENT_DRAFT.md").write_text(
        "Current DOI status: `PENDING_ZENODO_RELEASE`.\n",
        encoding="utf-8",
    )
    (metadata / "datasets.tsv").write_text(
        "dataset_id\tbenchmark_role\tzenodo_doi\n"
        "gse154778\tpublic_scrna_benchmark\tPENDING_ZENODO_RELEASE\n",
        encoding="utf-8",
    )


def test_zenodo_preflight_ready_for_manual_upload(tmp_path):
    script = _load_script("check_zenodo_upload_preflight")
    _write_minimal_package(tmp_path, script)

    rows = script.build_preflight_rows(tmp_path, tmp_path / "missing_token.txt")

    assert script.classify_decision(rows) == (
        "ZENODO_UPLOAD_PREFLIGHT_READY_FOR_MANUAL_UPLOAD_DOI_PENDING"
    )
    assert not [row for row in rows if row.severity == "blocking"]


def test_zenodo_preflight_blocks_sha_mismatch(tmp_path):
    script = _load_script("check_zenodo_upload_preflight")
    _write_minimal_package(tmp_path, script)
    manifest = tmp_path / "release" / "archive_manifest.tsv"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace("zenodo\t", "zenodo\t").replace(
            "False", "False"
        ).replace("0.001\t", "0.001\t" + "0" * 64 + "\t", 1),
        encoding="utf-8",
    )

    rows = script.build_preflight_rows(tmp_path, tmp_path / "missing_token.txt")

    assert script.classify_decision(rows) == "ZENODO_UPLOAD_PREFLIGHT_BLOCKED"


def test_zenodo_preflight_writes_report(tmp_path):
    script = _load_script("check_zenodo_upload_preflight")
    _write_minimal_package(tmp_path, script)
    rows = script.build_preflight_rows(tmp_path, tmp_path / "missing_token.txt")

    outputs = script.write_outputs(tmp_path, rows)

    assert outputs["status"].exists()
    assert outputs["report"].exists()
    assert "does not mint a DOI" in outputs["report"].read_text(encoding="utf-8")
