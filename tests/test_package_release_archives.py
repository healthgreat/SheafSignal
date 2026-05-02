from pathlib import Path
import importlib.util
import zipfile

import pandas as pd


def _load_script(name: str):
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_package_release_archives_writes_zip_and_manifest(tmp_path):
    script = _load_script("package_release_archives")
    release = tmp_path / "release"
    release.mkdir()
    (tmp_path / "src").mkdir()
    module = tmp_path / "src" / "module.py"
    module.write_text("print('ok')\n", encoding="utf-8")
    processed = tmp_path / "data" / "processed" / "dataset"
    processed.mkdir(parents=True)
    metadata = processed / "metadata.csv"
    metadata.write_text("cell_id\nc1\n", encoding="utf-8")

    pd.DataFrame(
        [
            {
                    "relative_path": "src/module.py",
                    "release_target": "github",
                    "sha256": script.sha256_file(module),
                }
        ]
    ).to_csv(release / "github_release_manifest.tsv", sep="\t", index=False)
    pd.DataFrame(
        [
                {
                    "relative_path": "data/processed/dataset/metadata.csv",
                    "release_target": "zenodo",
                    "sha256": script.sha256_file(metadata),
            }
        ]
    ).to_csv(release / "zenodo_upload_manifest.tsv", sep="\t", index=False)
    (release / "REPRODUCIBILITY_RELEASE_SUMMARY.md").write_text(
        "summary\n",
        encoding="utf-8",
    )

    paths = script.package_release_archives(
        root=tmp_path,
        release_dir=release,
        archive_dir=release / "archives",
    )

    assert paths["github_archive"].exists()
    assert paths["zenodo_archive"].exists()
    archive_manifest = pd.read_csv(paths["archive_manifest"], sep="\t")
    assert set(archive_manifest["archive_target"]) == {"github", "zenodo"}
    with zipfile.ZipFile(paths["github_archive"]) as archive:
        assert "src/module.py" in archive.namelist()
        assert "release/REPRODUCIBILITY_RELEASE_SUMMARY.md" in archive.namelist()
    with zipfile.ZipFile(paths["zenodo_archive"]) as archive:
        assert "data/processed/dataset/metadata.csv" in archive.namelist()

    first = pd.read_csv(paths["archive_manifest"], sep="\t").set_index("archive_target")
    paths = script.package_release_archives(
        root=tmp_path,
        release_dir=release,
        archive_dir=release / "archives",
    )
    second = pd.read_csv(paths["archive_manifest"], sep="\t").set_index("archive_target")
    assert first.loc["github", "sha256"] == second.loc["github", "sha256"]
    assert first.loc["zenodo", "sha256"] == second.loc["zenodo", "sha256"]


def test_package_release_archives_rejects_checksum_mismatch(tmp_path):
    script = _load_script("package_release_archives")
    release = tmp_path / "release"
    release.mkdir()
    (tmp_path / "README.md").write_text("changed\n", encoding="utf-8")
    row = {
        "relative_path": "README.md",
        "release_target": "github",
        "sha256": "0" * 64,
    }
    pd.DataFrame([row]).to_csv(release / "github_release_manifest.tsv", sep="\t", index=False)
    pd.DataFrame([row]).to_csv(release / "zenodo_upload_manifest.tsv", sep="\t", index=False)

    try:
        script.package_release_archives(
            root=tmp_path,
            release_dir=release,
            archive_dir=release / "archives",
        )
    except ValueError as exc:
        assert "SHA256 mismatch" in str(exc)
    else:
        raise AssertionError("Expected checksum mismatch to fail packaging")
