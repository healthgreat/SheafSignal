#!/usr/bin/env python
"""Preflight-check the Zenodo upload package before DOI minting.

Author: SheafSignal maintainers
Date: 2026-05-03
Purpose: verify archive checksums, deposition metadata, upload instructions,
and expected DOI placeholders before a Zenodo record is created.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
import zipfile


DEFAULT_ARCHIVE_MANIFEST = Path("release/archive_manifest.tsv")
DEFAULT_METADATA = Path("release/zenodo_deposition_metadata.json")
DEFAULT_INSTRUCTIONS = Path("release/ZENODO_DEPOSITION_INSTRUCTIONS.md")
DEFAULT_DATA_AVAILABILITY = Path("release/DATA_AVAILABILITY_STATEMENT_DRAFT.md")
DEFAULT_DATASET_MANIFEST = Path("metadata/datasets.tsv")
DEFAULT_TOKEN_PATH = Path(r"D:\secrets\zenodo_token.txt")
DEFAULT_STATUS = Path("release/ZENODO_UPLOAD_PREFLIGHT_STATUS.tsv")
DEFAULT_REPORT = Path("release/ZENODO_UPLOAD_PREFLIGHT_REPORT.md")


@dataclass(frozen=True)
class PreflightRow:
    check_id: str
    severity: str
    status: str
    evidence: str
    required_action: str


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _write_tsv_atomic(path: Path, rows: list[PreflightRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    fieldnames = ["check_id", "severity", "status", "evidence", "required_action"]
    with tmp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)
    tmp_path.replace(path)


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _pass(check_id: str, evidence: str) -> PreflightRow:
    return PreflightRow(check_id, "pass", "pass", evidence, "None.")


def _pending(check_id: str, evidence: str, action: str) -> PreflightRow:
    return PreflightRow(check_id, "pending", "pending", evidence, action)


def _blocking(check_id: str, evidence: str, action: str) -> PreflightRow:
    return PreflightRow(check_id, "blocking", "fail", evidence, action)


def zenodo_archive_row(root: Path) -> dict[str, str] | None:
    rows = _read_tsv(root / DEFAULT_ARCHIVE_MANIFEST)
    for row in rows:
        if row.get("archive_target") == "zenodo":
            return row
    return None


def check_archive(root: Path) -> list[PreflightRow]:
    row = zenodo_archive_row(root)
    if row is None:
        return [
            _blocking(
                "zenodo_archive_manifest_row",
                "No zenodo row found in release/archive_manifest.tsv.",
                "Run python scripts/package_release_archives.py.",
            )
        ]
    archive_path = root / str(row["archive_path"])
    checks = [
        _pass(
            "zenodo_archive_manifest_row",
            f"{row['archive_path']} sha256={row.get('sha256', 'NA')}",
        )
    ]
    if not archive_path.exists() or archive_path.stat().st_size == 0:
        checks.append(
            _blocking(
                "zenodo_archive_exists",
                f"{archive_path} is missing or empty.",
                "Run python scripts/package_release_archives.py.",
            )
        )
        return checks
    observed_sha = sha256_file(archive_path)
    expected_sha = str(row.get("sha256", ""))
    if observed_sha == expected_sha:
        checks.append(_pass("zenodo_archive_sha256", f"sha256={observed_sha}"))
    else:
        checks.append(
            _blocking(
                "zenodo_archive_sha256",
                f"expected={expected_sha}; observed={observed_sha}",
                "Regenerate release archives and archive manifest.",
            )
        )
    expected_size = int(float(row.get("size_bytes", 0)))
    observed_size = int(archive_path.stat().st_size)
    if observed_size == expected_size:
        checks.append(
            _pass(
                "zenodo_archive_size",
                f"size_bytes={observed_size}; size_mb={float(row.get('size_mb', 0.0)):.3f}",
            )
        )
    else:
        checks.append(
            _blocking(
                "zenodo_archive_size",
                f"expected={expected_size}; observed={observed_size}",
                "Regenerate release archives and archive manifest.",
            )
        )
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            names = archive.namelist()
            bad_names = [
                name
                for name in names
                if "secret" in name.lower()
                or "token" in name.lower()
                or name.startswith(".git/")
            ]
    except zipfile.BadZipFile:
        checks.append(
            _blocking(
                "zenodo_archive_zip_integrity",
                "Archive is not a valid zip file.",
                "Regenerate release archives.",
            )
        )
        return checks
    expected_files = int(float(row.get("n_files", 0)))
    if len(names) == expected_files:
        checks.append(_pass("zenodo_archive_file_count", f"n_files={len(names)}"))
    else:
        checks.append(
            _blocking(
                "zenodo_archive_file_count",
                f"expected={expected_files}; observed={len(names)}",
                "Regenerate release archives and archive manifest.",
            )
        )
    if bad_names:
        checks.append(
            _blocking(
                "zenodo_archive_sensitive_names",
                ";".join(bad_names[:20]),
                "Remove secrets/tokens/.git contents from the archive manifest.",
            )
        )
    else:
        checks.append(_pass("zenodo_archive_sensitive_names", "No sensitive names detected."))
    return checks


def check_metadata(root: Path) -> list[PreflightRow]:
    metadata_path = root / DEFAULT_METADATA
    if not metadata_path.exists():
        return [
            _blocking(
                "zenodo_metadata_exists",
                f"{DEFAULT_METADATA} is missing.",
                "Run python scripts/build_zenodo_deposition_package.py.",
            )
        ]
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    text = json.dumps(metadata, ensure_ascii=False)
    rows = [_pass("zenodo_metadata_exists", str(DEFAULT_METADATA))]
    required_fields = ["title", "upload_type", "description", "creators", "license"]
    missing_fields = [field for field in required_fields if not metadata.get(field)]
    if missing_fields:
        rows.append(
            _blocking(
                "zenodo_metadata_required_fields",
                ",".join(missing_fields),
                "Fill required Zenodo metadata fields before upload.",
            )
        )
    else:
        rows.append(_pass("zenodo_metadata_required_fields", "required fields present"))
    if metadata.get("upload_type") == "dataset":
        rows.append(_pass("zenodo_metadata_upload_type", "dataset"))
    else:
        rows.append(
            _blocking(
                "zenodo_metadata_upload_type",
                str(metadata.get("upload_type")),
                "Use upload_type=dataset for the large processed benchmark archive.",
            )
        )
    creators = metadata.get("creators", [])
    creator_issues = [
        str(item)
        for item in creators
        if not str(item.get("name", "")).strip()
        or str(item.get("name", "")).strip().upper() == "TBD"
    ]
    if creator_issues:
        rows.append(
            _blocking(
                "zenodo_metadata_creators",
                ";".join(creator_issues),
                "Replace TBD or empty creator names.",
            )
        )
    else:
        rows.append(_pass("zenodo_metadata_creators", f"n_creators={len(creators)}"))
    if "github.com/TBD" in text or "PENDING_ARCHIVE_SHA256" in text:
        rows.append(
            _blocking(
                "zenodo_metadata_placeholders",
                "GitHub or archive placeholder detected.",
                "Run GitHub URL finalization and Zenodo deposition package rebuild.",
            )
        )
    else:
        rows.append(_pass("zenodo_metadata_placeholders", "No GitHub/archive placeholders."))
    archive_row = zenodo_archive_row(root)
    notes = str(metadata.get("notes", ""))
    if archive_row and str(archive_row.get("sha256", "")) in notes:
        rows.append(_pass("zenodo_metadata_sha_matches_archive", archive_row["sha256"]))
    else:
        rows.append(
            _blocking(
                "zenodo_metadata_sha_matches_archive",
                "Archive SHA is missing from metadata notes.",
                "Run python scripts/build_zenodo_deposition_package.py.",
            )
        )
    if "https://github.com/healthgreat/SheafSignal" in text:
        rows.append(_pass("zenodo_metadata_github_url", "https://github.com/healthgreat/SheafSignal"))
    else:
        rows.append(
            _blocking(
                "zenodo_metadata_github_url",
                "Expected public GitHub URL not found.",
                "Run python scripts/finalize_github_repository_url.py.",
            )
        )
    return rows


def check_instructions_and_placeholders(root: Path) -> list[PreflightRow]:
    rows: list[PreflightRow] = []
    instructions = root / DEFAULT_INSTRUCTIONS
    archive_row = zenodo_archive_row(root)
    if not instructions.exists():
        rows.append(
            _blocking(
                "zenodo_instructions_exist",
                f"{DEFAULT_INSTRUCTIONS} is missing.",
                "Run python scripts/build_zenodo_deposition_package.py.",
            )
        )
    else:
        text = instructions.read_text(encoding="utf-8")
        rows.append(_pass("zenodo_instructions_exist", str(DEFAULT_INSTRUCTIONS)))
        if archive_row and str(archive_row.get("sha256", "")) in text:
            rows.append(_pass("zenodo_instructions_sha_matches_archive", archive_row["sha256"]))
        else:
            rows.append(
                _blocking(
                    "zenodo_instructions_sha_matches_archive",
                    "Archive SHA is missing from upload instructions.",
                    "Run python scripts/build_zenodo_deposition_package.py.",
                )
            )
    placeholder_sources = [
        DEFAULT_DATA_AVAILABILITY,
        DEFAULT_DATASET_MANIFEST,
    ]
    placeholder_hits = [
        rel_path.as_posix()
        for rel_path in placeholder_sources
        if (root / rel_path).exists()
        and "PENDING_ZENODO_RELEASE" in (root / rel_path).read_text(encoding="utf-8")
    ]
    if placeholder_hits:
        rows.append(
            _pending(
                "zenodo_doi_placeholders_expected",
                ";".join(placeholder_hits),
                "Mint DOI and run scripts/finalize_zenodo_doi.py after upload.",
            )
        )
    else:
        rows.append(_pass("zenodo_doi_placeholders_expected", "No DOI placeholders remain."))
    return rows


def check_token(token_path: Path) -> list[PreflightRow]:
    if not token_path.exists():
        return [
            _pending(
                "zenodo_token_file",
                f"{token_path} does not exist.",
                "Use manual Zenodo web upload or save a token at this path for API upload.",
            )
        ]
    if token_path.stat().st_size == 0:
        return [
            _blocking(
                "zenodo_token_file",
                f"{token_path} exists but is empty.",
                "Overwrite it with a valid Zenodo token or remove it and use manual upload.",
            )
        ]
    return [
        _pass(
            "zenodo_token_file",
            f"{token_path} exists; size={token_path.stat().st_size} bytes. Token content was not printed.",
        )
    ]


def build_preflight_rows(root: Path, token_path: Path = DEFAULT_TOKEN_PATH) -> list[PreflightRow]:
    rows: list[PreflightRow] = []
    rows.extend(check_archive(root))
    rows.extend(check_metadata(root))
    rows.extend(check_instructions_and_placeholders(root))
    rows.extend(check_token(token_path))
    return rows


def classify_decision(rows: list[PreflightRow]) -> str:
    if any(row.severity == "blocking" for row in rows):
        return "ZENODO_UPLOAD_PREFLIGHT_BLOCKED"
    token_ready = any(
        row.check_id == "zenodo_token_file" and row.severity == "pass" for row in rows
    )
    doi_pending = any(row.check_id == "zenodo_doi_placeholders_expected" and row.severity == "pending" for row in rows)
    if token_ready and doi_pending:
        return "ZENODO_UPLOAD_PREFLIGHT_READY_FOR_API_UPLOAD_DOI_PENDING"
    if doi_pending:
        return "ZENODO_UPLOAD_PREFLIGHT_READY_FOR_MANUAL_UPLOAD_DOI_PENDING"
    return "ZENODO_UPLOAD_PREFLIGHT_READY_NO_DOI_PLACEHOLDERS"


def build_report(rows: list[PreflightRow]) -> str:
    decision = classify_decision(rows)
    counts = {
        "pass": sum(row.severity == "pass" for row in rows),
        "pending": sum(row.severity == "pending" for row in rows),
        "blocking": sum(row.severity == "blocking" for row in rows),
    }
    blocking_lines = [
        f"- `{row.check_id}`: {row.evidence}. Action: {row.required_action}"
        for row in rows
        if row.severity == "blocking"
    ] or ["- none"]
    pending_lines = [
        f"- `{row.check_id}`: {row.evidence}. Action: {row.required_action}"
        for row in rows
        if row.severity == "pending"
    ] or ["- none"]
    return "\n".join(
        [
            "# Zenodo Upload Preflight Report",
            "",
            f"- Decision: `{decision}`",
            f"- Passed checks: `{counts['pass']}`",
            f"- Pending checks: `{counts['pending']}`",
            f"- Blocking checks: `{counts['blocking']}`",
            "",
            "## Blocking Checks",
            "",
            *blocking_lines,
            "",
            "## Pending Checks",
            "",
            *pending_lines,
            "",
            "## Next Commands",
            "",
            "```bash",
            "python scripts/upload_zenodo_deposition.py --dry-run",
            "python scripts/finalize_zenodo_doi.py --doi <ZENODO_DOI>",
            "python scripts/check_final_submission_blockers.py --report-only",
            "```",
            "",
            "## Boundary",
            "",
            "This report checks Zenodo upload readiness. It does not upload files,",
            "does not mint a DOI, does not print token contents, and does not",
            "guarantee journal acceptance.",
            "",
        ]
    )


def write_outputs(
    root: Path,
    rows: list[PreflightRow],
    status_path: Path = DEFAULT_STATUS,
    report_path: Path = DEFAULT_REPORT,
) -> dict[str, Path]:
    status_out = root / status_path
    report_out = root / report_path
    _write_tsv_atomic(status_out, rows)
    _write_text_atomic(report_out, build_report(rows))
    return {"status": status_out, "report": report_out}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--token-path", default=str(DEFAULT_TOKEN_PATH))
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    rows = build_preflight_rows(root, Path(args.token_path))
    outputs = write_outputs(root, rows)
    print(f"decision: {classify_decision(rows)}")
    for label, path in outputs.items():
        print(f"wrote {label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
