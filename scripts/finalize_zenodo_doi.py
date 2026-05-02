#!/usr/bin/env python
"""Finalize SheafSignal release files after a Zenodo DOI is minted."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


DOI_RE = re.compile(r"^(https://doi\.org/)?10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$")


def validate_doi(doi: str) -> str:
    doi = doi.strip()
    if not DOI_RE.match(doi):
        raise ValueError(f"Invalid DOI format: {doi}")
    if doi.startswith("https://doi.org/"):
        return doi.removeprefix("https://doi.org/")
    return doi


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_table_atomic(path: Path, table: pd.DataFrame, sep: str = "\t") -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    table.to_csv(tmp_path, sep=sep, index=False)
    tmp_path.replace(path)


def finalize_dataset_manifest(path: Path, doi: str) -> list[str]:
    table = pd.read_csv(path, sep="\t", keep_default_na=False)
    if "benchmark_role" not in table.columns or "zenodo_doi" not in table.columns:
        raise ValueError("metadata/datasets.tsv must contain benchmark_role and zenodo_doi")
    mask = table["benchmark_role"].astype(str).str.contains("public_", na=False)
    updated = table.loc[mask, "dataset_id"].astype(str).tolist()
    table.loc[mask, "zenodo_doi"] = doi
    _write_table_atomic(path, table, sep="\t")
    return updated


def finalize_data_availability(path: Path, doi: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    replacement = (
        f"Current DOI status: `https://doi.org/{doi}`.\n\n"
        f"Frozen processed benchmark objects are available at https://doi.org/{doi}."
    )
    if "Current DOI status:" in text:
        text = re.sub(
            r"Current DOI status: `[^`]+`\.",
            replacement,
            text,
        )
    else:
        text = text.rstrip() + "\n\n" + replacement + "\n"
    _write_text_atomic(path, text)


def finalize_submission_checklist(path: Path, doi: str) -> None:
    table = pd.read_csv(path, sep="\t", keep_default_na=False)
    if "item" not in table.columns or "status" not in table.columns:
        raise ValueError("submission checklist must contain item and status")
    mask = table["item"].astype(str).str.lower() == "zenodo doi minted"
    table.loc[mask, "status"] = "complete_after_doi"
    table.loc[mask, "evidence_or_action"] = f"https://doi.org/{doi}"
    _write_table_atomic(path, table, sep="\t")


def build_finalize_summary(doi: str, updated_datasets: list[str]) -> str:
    dataset_text = ";".join(updated_datasets) if updated_datasets else "none"
    return f"""# Zenodo DOI Finalization Summary

DOI: https://doi.org/{doi}

Updated public benchmark rows: {dataset_text}

Next required commands:

```bash
python scripts/check_final_submission_blockers.py
python scripts/build_submission_readiness_report.py
python scripts/build_reproducibility_release.py
python scripts/package_release_archives.py
python -m pytest
python scripts/release_audit.py
```

Boundary: DOI finalization removes the Zenodo blocker only. It does not
guarantee journal acceptance and does not replace author metadata or final
journal-format checks.
"""


def finalize_release(root: Path, doi: str) -> dict[str, Path | list[str]]:
    doi = validate_doi(doi)
    updated = finalize_dataset_manifest(root / "metadata/datasets.tsv", doi)
    finalize_data_availability(root / "release/DATA_AVAILABILITY_STATEMENT_DRAFT.md", doi)
    finalize_submission_checklist(
        root / "manuscript/nature_methods_package/07_submission_checklist.tsv",
        doi,
    )
    summary = root / "release/ZENODO_DOI_FINALIZATION_SUMMARY.md"
    _write_text_atomic(summary, build_finalize_summary(doi, updated))
    return {
        "updated_datasets": updated,
        "summary": summary,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--doi", required=True)
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    result = finalize_release(root, args.doi)
    print(f"updated datasets: {';'.join(result['updated_datasets'])}")
    print(f"wrote {result['summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
