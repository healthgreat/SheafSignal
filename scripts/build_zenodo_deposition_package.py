#!/usr/bin/env python
"""Build Zenodo deposition metadata and upload instructions.

Author: SheafSignal contributors
Date: 2026-04-30
Purpose: prepare the non-code deposition package needed before a 20-50 IF
methods submission.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_tsv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t")


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_json_atomic(path: Path, payload: dict) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def build_deposition_metadata(
    *,
    base_metadata: dict,
    zenodo_manifest: pd.DataFrame,
    archive_manifest: pd.DataFrame,
) -> dict:
    archive_row = {}
    if not archive_manifest.empty:
        subset = archive_manifest.loc[archive_manifest["archive_target"].astype(str) == "zenodo"]
        if not subset.empty:
            archive_row = subset.iloc[0].to_dict()

    n_files = int(len(zenodo_manifest)) if not zenodo_manifest.empty else 0
    total_mb = float(pd.to_numeric(zenodo_manifest.get("size_mb", pd.Series(dtype=float)), errors="coerce").sum())
    description = (
        "Frozen processed benchmark objects and large generated spatial result "
        "tables for the SheafSignal methods manuscript. Raw public datasets are "
        "not redistributed here; source accessions and checksums are listed in "
        "metadata/datasets.tsv. This deposition is intended to pair with the "
        "public GitHub source-code release."
    )
    payload = {
        "title": base_metadata.get(
            "title",
            "SheafSignal: sheaf-valued Hodge analysis of cell-cell communication networks",
        ),
        "upload_type": "dataset",
        "description": description,
        "creators": base_metadata.get("creators", [{"name": "TBD"}]),
        "license": "cc-by-4.0",
        "keywords": base_metadata.get(
            "keywords",
            [
                "single-cell RNA-seq",
                "spatial transcriptomics",
                "cell-cell communication",
                "sheaf theory",
                "Hodge decomposition",
            ],
        ),
        "notes": (
            f"Zenodo upload file: {archive_row.get('archive_path', 'release/archives/sheafsignal_zenodo_upload.zip')}. "
            f"Archive SHA256: {archive_row.get('sha256', 'PENDING_ARCHIVE_SHA256')}. "
            f"Manifest files: {n_files}; manifest total size MB: {total_mb:.3f}."
        ),
        "related_identifiers": [
            {
                "identifier": "https://github.com/TBD/SheafSignal",
                "relation": "isSupplementTo",
                "resource_type": "software",
            }
        ],
    }
    return payload


def build_upload_instructions(
    *,
    metadata_path: Path,
    archive_manifest: pd.DataFrame,
    zenodo_manifest: pd.DataFrame,
) -> str:
    archive_text = "release/archives/sheafsignal_zenodo_upload.zip"
    archive_sha = "PENDING_ARCHIVE_SHA256"
    archive_size = "NA"
    if not archive_manifest.empty:
        subset = archive_manifest.loc[archive_manifest["archive_target"].astype(str) == "zenodo"]
        if not subset.empty:
            row = subset.iloc[0]
            archive_text = str(row["archive_path"])
            archive_sha = str(row["sha256"])
            archive_size = f"{float(row['size_mb']):.3f} MB"
    n_files = int(len(zenodo_manifest)) if not zenodo_manifest.empty else 0
    return f"""# Zenodo Deposition Upload Instructions

## Upload Target

- Upload archive: `{archive_text}`
- Archive size: `{archive_size}`
- Archive SHA256: `{archive_sha}`
- Deposition metadata JSON: `{metadata_path.as_posix()}`
- Frozen files represented in `release/zenodo_upload_manifest.tsv`: {n_files}

## Steps

1. Create a new Zenodo deposition for a dataset.
2. Use the metadata from `release/zenodo_deposition_metadata.json`.
3. Upload `{archive_text}`.
4. Confirm the archive checksum equals `{archive_sha}`.
5. Publish the Zenodo record and copy the DOI.
6. Run:

```bash
python scripts/finalize_zenodo_doi.py --doi <ZENODO_DOI>
python scripts/check_final_submission_blockers.py
```

## Boundary

Do not submit the manuscript while `NATURE_METHODS_GO_NO_GO_REPORT.md` says
`NO_GO`. This instruction file does not mint a DOI and does not guarantee
journal acceptance.
"""


def build_package(root: Path, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    base_metadata = _read_json(root / ".zenodo.json")
    zenodo_manifest = _read_tsv(root / "release/zenodo_upload_manifest.tsv")
    archive_manifest = _read_tsv(root / "release/archive_manifest.tsv")
    metadata = build_deposition_metadata(
        base_metadata=base_metadata,
        zenodo_manifest=zenodo_manifest,
        archive_manifest=archive_manifest,
    )
    metadata_path = output_dir / "zenodo_deposition_metadata.json"
    instructions_path = output_dir / "ZENODO_DEPOSITION_INSTRUCTIONS.md"
    _write_json_atomic(metadata_path, metadata)
    _write_text_atomic(
        instructions_path,
        build_upload_instructions(
            metadata_path=metadata_path.relative_to(root),
            archive_manifest=archive_manifest,
            zenodo_manifest=zenodo_manifest,
        ),
    )
    return {
        "metadata": metadata_path,
        "instructions": instructions_path,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-dir", default="release")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    paths = build_package(root, output_dir)
    for path in paths.values():
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
