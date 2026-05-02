from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


REQUIRED_DATASET_COLUMNS = {
    "dataset_id",
    "title",
    "modality",
    "species",
    "tissue",
    "disease",
    "accession_or_doi",
    "download_url",
    "local_path",
    "sha256",
    "license_or_terms",
    "release_status",
    "benchmark_role",
}

PUBLIC_BENCHMARK_ROLES = {
    "public_scrna_benchmark",
    "public_spatial_benchmark",
}

MISSING_TOKENS = {"", "NA", "N/A", "NAN", "TBD", "TO_BE_FILLED", "NONE", "NULL"}
PENDING_CHECKSUM_TOKENS = {"PENDING_DOWNLOAD_VERIFICATION", "PENDING_ZENODO_RELEASE"}
SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")


def is_missing(value: object) -> bool:
    if pd.isna(value):
        return True
    text = str(value).strip()
    return text.upper() in MISSING_TOKENS


def is_valid_sha256_or_pending(value: object) -> bool:
    if is_missing(value):
        return False
    text = str(value).strip()
    return bool(SHA256_RE.match(text)) or text.upper() in PENDING_CHECKSUM_TOKENS


def load_dataset_manifest(path: str | Path = "metadata/datasets.tsv") -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    table = pd.read_csv(path, sep="\t", dtype=str).fillna("")
    missing = REQUIRED_DATASET_COLUMNS.difference(table.columns)
    if missing:
        raise ValueError(f"Dataset manifest is missing columns: {sorted(missing)}")
    if table["dataset_id"].duplicated().any():
        duplicated = sorted(table.loc[table["dataset_id"].duplicated(), "dataset_id"].unique())
        raise ValueError(f"Dataset manifest has duplicated dataset_id values: {duplicated}")
    return table


def validate_dataset_manifest(
    path: str | Path = "metadata/datasets.tsv",
    require_public_downloads: bool = True,
) -> pd.DataFrame:
    """Validate dataset manifest fields needed for public reproducibility."""
    table = load_dataset_manifest(path)
    problems: list[str] = []

    for row in table.to_dict(orient="records"):
        dataset_id = str(row["dataset_id"])
        role = str(row.get("benchmark_role", ""))
        is_public_benchmark = role in PUBLIC_BENCHMARK_ROLES

        for column in ["dataset_id", "title", "modality", "species", "tissue", "disease"]:
            if is_missing(row.get(column)):
                problems.append(f"{dataset_id}: missing {column}")

        if is_public_benchmark or require_public_downloads:
            for column in ["accession_or_doi", "download_url", "local_path", "license_or_terms"]:
                if is_missing(row.get(column)):
                    problems.append(f"{dataset_id}: missing {column}")
            if not is_valid_sha256_or_pending(row.get("sha256")):
                problems.append(
                    f"{dataset_id}: sha256 must be a 64-character checksum or "
                    "PENDING_DOWNLOAD_VERIFICATION"
                )

    if problems:
        joined = "\n".join(f"- {problem}" for problem in problems)
        raise ValueError(f"Dataset manifest validation failed:\n{joined}")
    return table


def public_benchmark_manifest(path: str | Path = "metadata/datasets.tsv") -> pd.DataFrame:
    table = validate_dataset_manifest(path, require_public_downloads=False)
    return table.loc[table["benchmark_role"].isin(PUBLIC_BENCHMARK_ROLES)].reset_index(drop=True)
