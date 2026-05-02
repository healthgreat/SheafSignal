#!/usr/bin/env python
"""Package GitHub and Zenodo release archives from frozen manifests.

Author: SheafSignal contributors
Date: 2026-04-30
Purpose: create local upload-ready archives from release manifests while keeping
large archive files out of Git.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import zipfile

import pandas as pd


FIXED_ZIP_TIMESTAMP = (2026, 4, 30, 0, 0, 0)

RELEASE_METADATA_FILES = (
    "release/release_file_inventory.tsv",
    "release/github_release_manifest.tsv",
    "release/zenodo_upload_manifest.tsv",
    "release/github_sha256sums.txt",
    "release/zenodo_sha256sums.txt",
    "release/REPRODUCIBILITY_RELEASE_SUMMARY.md",
    "release/DATA_AVAILABILITY_STATEMENT_DRAFT.md",
    "release/zenodo_deposition_metadata.json",
    "release/ZENODO_DEPOSITION_INSTRUCTIONS.md",
    "release/ZENODO_DOI_FINALIZATION_SUMMARY.md",
    "release/GITHUB_RELEASE_INSTRUCTIONS.md",
)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_manifest(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing release manifest: {path}")
    manifest = pd.read_csv(path, sep="\t")
    required = {"relative_path", "sha256", "release_target"}
    missing = required.difference(manifest.columns)
    if missing:
        raise ValueError(f"Release manifest is missing columns: {sorted(missing)}")
    return manifest


def _verify_manifest_files(root: Path, manifest: pd.DataFrame) -> list[Path]:
    files: list[Path] = []
    for row in manifest.to_dict(orient="records"):
        rel = str(row["relative_path"])
        path = root / rel
        if not path.exists():
            raise FileNotFoundError(f"Manifest file is missing: {rel}")
        observed = sha256_file(path)
        expected = str(row["sha256"])
        if observed != expected:
            raise ValueError(
                f"SHA256 mismatch for {rel}: expected {expected}, observed {observed}"
            )
        files.append(path)
    return files


def _write_zip_atomic(root: Path, files: list[Path], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    if tmp.exists():
        tmp.unlink()
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
            arcname = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(arcname, date_time=FIXED_ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
    tmp.replace(output)


def package_release_archives(
    *,
    root: Path,
    release_dir: Path,
    archive_dir: Path,
    github_name: str = "sheafsignal_github_release.zip",
    zenodo_name: str = "sheafsignal_zenodo_upload.zip",
) -> dict[str, Path]:
    github_manifest = _read_manifest(release_dir / "github_release_manifest.tsv")
    zenodo_manifest = _read_manifest(release_dir / "zenodo_upload_manifest.tsv")

    github_files = _verify_manifest_files(root, github_manifest)
    for rel in RELEASE_METADATA_FILES:
        path = root / rel
        if path.exists() and path not in github_files:
            github_files.append(path)
    zenodo_files = _verify_manifest_files(root, zenodo_manifest)

    github_archive = archive_dir / github_name
    zenodo_archive = archive_dir / zenodo_name
    _write_zip_atomic(root, github_files, github_archive)
    _write_zip_atomic(root, zenodo_files, zenodo_archive)

    rows = []
    for target, path, n_files in [
        ("github", github_archive, len(github_files)),
        ("zenodo", zenodo_archive, len(zenodo_files)),
    ]:
        rows.append(
            {
                "archive_target": target,
                "archive_path": path.relative_to(root).as_posix(),
                "n_files": n_files,
                "size_bytes": int(path.stat().st_size),
                "size_mb": round(path.stat().st_size / 1024 / 1024, 6),
                "sha256": sha256_file(path),
                "tracked_in_git": False,
            }
        )
    archive_manifest = release_dir / "archive_manifest.tsv"
    pd.DataFrame(rows).to_csv(archive_manifest, sep="\t", index=False)

    readme = archive_dir / "README.md"
    readme.write_text(
        "# Local Release Archives\n\n"
        "These zip files are generated from `release/github_release_manifest.tsv` "
        "and `release/zenodo_upload_manifest.tsv`. They are intentionally ignored "
        "by Git. Use `release/archive_manifest.tsv` for archive checksums.\n",
        encoding="utf-8",
    )
    return {
        "github_archive": github_archive,
        "zenodo_archive": zenodo_archive,
        "archive_manifest": archive_manifest,
        "archive_readme": readme,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--release-dir", default="release")
    parser.add_argument("--archive-dir", default="release/archives")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    release_dir = Path(args.release_dir)
    archive_dir = Path(args.archive_dir)
    if not release_dir.is_absolute():
        release_dir = root / release_dir
    if not archive_dir.is_absolute():
        archive_dir = root / archive_dir

    paths = package_release_archives(
        root=root,
        release_dir=release_dir,
        archive_dir=archive_dir,
    )
    for path in paths.values():
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
