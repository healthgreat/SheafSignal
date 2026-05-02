#!/usr/bin/env python
"""Download public datasets listed in metadata/datasets.tsv.

This script intentionally skips rows without a real download URL. Large files
should remain outside Git and be fetched reproducibly from public repositories.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path

import _bootstrap  # noqa: F401
from sheafsignal.manifest import is_missing, validate_dataset_manifest


DOWNLOAD_USER_AGENT = "Mozilla/5.0 SheafSignal-public-benchmark/0.1"


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _append_download_log(message: str) -> None:
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat(timespec="seconds")
    with (log_dir / "download.log").open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp}\t{message}\n")


def _part_path(output_path: Path) -> Path:
    return output_path.with_name(f"{output_path.name}.part")


def _write_ok_sentinel(output_path: Path, sha256: str | None = None) -> None:
    sentinel = output_path.with_name(f"{output_path.name}.ok")
    text = f"sha256={sha256}\n" if sha256 else "download_complete=true\n"
    sentinel.write_text(text, encoding="utf-8")


def _remove_possible_corrupt_files(output_path: Path) -> None:
    for path in [output_path, _part_path(output_path), output_path.with_name(f"{output_path.name}.part.aria2")]:
        if path.exists():
            path.unlink()


def download(url: str, output_path: Path) -> None:
    """Download to a resumable .part file, then atomically promote to final path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    part_path = _part_path(output_path)
    aria2c = shutil.which("aria2c")
    if aria2c:
        cmd = [
            aria2c,
            "--continue=true",
            "--max-tries=20",
            "--retry-wait=10",
            "--allow-overwrite=true",
            "--auto-file-renaming=false",
            "--file-allocation=none",
            f"--user-agent={DOWNLOAD_USER_AGENT}",
            "--dir",
            str(output_path.parent),
            "--out",
            part_path.name,
            url,
        ]
        _append_download_log(f"aria2c_start\t{url}\t{part_path}")
        subprocess.run(cmd, check=True)
        if not part_path.exists():
            raise FileNotFoundError(f"Download did not create expected part file: {part_path}")
        part_path.replace(output_path)
        _append_download_log(f"download_complete\t{url}\t{output_path}")
        return

    headers = {}
    mode = "wb"
    if part_path.exists():
        existing = part_path.stat().st_size
        if existing > 0:
            headers["Range"] = f"bytes={existing}-"
            mode = "ab"

    _append_download_log(f"python_download_start\t{url}\t{part_path}")
    request_headers = {"User-Agent": DOWNLOAD_USER_AGENT, **headers}
    request = urllib.request.Request(url, headers=request_headers)
    with urllib.request.urlopen(request) as response, part_path.open(mode) as handle:
        if mode == "ab" and getattr(response, "status", None) == 200:
            handle.seek(0)
            handle.truncate()
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
    part_path.replace(output_path)
    _append_download_log(f"download_complete\t{url}\t{output_path}")


def _split_optional_list(value: object) -> list[str]:
    if is_missing(value):
        return []
    return [item.strip() for item in str(value).split(";") if item.strip()]


def _download_plan_for_row(row: dict[str, object]) -> list[tuple[str, Path, str]]:
    urls = [str(row["download_url"]).strip()] + _split_optional_list(row.get("aux_download_urls"))
    paths = [Path(str(row["local_path"]).strip())]
    aux_paths = _split_optional_list(row.get("aux_local_paths"))
    paths.extend(Path(path) for path in aux_paths)
    if len(paths) != len(urls):
        raise ValueError(
            f"{row['dataset_id']}: number of download URLs does not match local paths"
        )
    checksums = [str(row.get("sha256", "")).strip()]
    aux_checksums = _split_optional_list(row.get("aux_sha256"))
    if aux_checksums and len(aux_checksums) != len(aux_paths):
        raise ValueError(
            f"{row['dataset_id']}: number of aux_sha256 values does not match aux_local_paths"
        )
    checksums.extend(aux_checksums or ["PENDING_DOWNLOAD_VERIFICATION"] * len(aux_paths))
    return list(zip(urls, paths, checksums))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="metadata/datasets.tsv")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--dataset-id", action="append", default=[])
    args = parser.parse_args(argv)

    table = validate_dataset_manifest(args.manifest, require_public_downloads=False)
    selected = set(args.dataset_id)
    if selected:
        table = table.loc[table["dataset_id"].isin(selected)].reset_index(drop=True)
        missing = selected.difference(set(table["dataset_id"]))
        if missing:
            raise ValueError(f"Unknown dataset_id values: {sorted(missing)}")
    if args.validate_only:
        print(f"manifest ok: {Path(args.manifest).resolve()}")
        return 0

    for row in table.to_dict(orient="records"):
        dataset_id = str(row["dataset_id"])
        if is_missing(row["download_url"]):
            print(f"skip {dataset_id}: no public download_url")
            continue

        for url, local_path, expected in _download_plan_for_row(row):
            if args.dry_run:
                print(f"would download {dataset_id}: {url} -> {local_path}")
                continue

            if local_path.exists() and not args.force:
                print(f"skip {dataset_id}: already exists at {local_path}")
            else:
                print(f"download {dataset_id}: {url} -> {local_path}")
                download(str(url), local_path)

            if not is_missing(expected) and len(str(expected)) == 64:
                observed = sha256sum(local_path)
                if observed.lower() != str(expected).lower():
                    print(
                        f"checksum mismatch for {dataset_id}: expected {expected}, observed {observed}",
                        file=sys.stderr,
                    )
                    _append_download_log(
                        f"checksum_mismatch\t{dataset_id}\texpected={expected}\tobserved={observed}"
                    )
                    _remove_possible_corrupt_files(local_path)
                    return 2
                _write_ok_sentinel(local_path, observed)
                print(f"checksum ok {dataset_id}")
            else:
                _write_ok_sentinel(local_path)
                print(f"checksum pending {dataset_id}: {local_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
