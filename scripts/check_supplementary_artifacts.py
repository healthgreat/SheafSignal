#!/usr/bin/env python
"""Audit supplementary artifacts listed in the SheafSignal figure manifest.

Author: SheafSignal contributors
Date: 2026-05-01
Purpose: verify that supplementary figures, tables, manuscript support files,
and release artifacts are present and readable before journal submission.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


MIN_PDF_NONWHITE_FRACTION = 0.001
MIN_PDF_TEXT_CHARS = 5

TABLE_SUFFIXES = {".csv", ".tsv"}
TEXT_SUFFIXES = {".md", ".txt", ".bib", ".cff", ".yml", ".yaml"}
JSON_SUFFIXES = {".json"}
PDF_SUFFIXES = {".pdf"}


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_table_atomic(path: Path, table: pd.DataFrame) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    table.to_csv(tmp_path, sep="\t", index=False)
    tmp_path.replace(path)


def _read_tsv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t")


def _relative_or_abs(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _nonwhite_fraction(samples: bytes, n_channels: int) -> float:
    if n_channels <= 0:
        return 0.0
    n_pixels = len(samples) // n_channels
    if n_pixels == 0:
        return 0.0
    nonwhite = 0
    for idx in range(0, len(samples), n_channels):
        rgb = samples[idx : idx + min(3, n_channels)]
        if any(channel < 245 for channel in rgb):
            nonwhite += 1
    return nonwhite / n_pixels


def _supplementary_boundary(source_map: pd.DataFrame) -> tuple[bool, str]:
    if source_map.empty or "display_item" not in source_map.columns:
        return False, "NA"
    rows = source_map.loc[
        source_map["display_item"].astype(str) == "Supplementary figures and tables"
    ]
    if rows.empty:
        return False, "NA"
    value = rows.iloc[0].get("boundary", "")
    if pd.isna(value):
        return True, "NA"
    boundary = str(value).strip()
    return True, boundary if boundary else "NA"


def _audit_pdf(path: Path) -> dict[str, object]:
    try:
        import fitz
    except ImportError:
        return {
            "read_status": "pymupdf_unavailable",
            "n_rows_or_pages": "NA",
            "n_columns": "NA",
            "text_chars": "NA",
            "nonwhite_fraction": "NA",
        }
    try:
        pdf = fitz.open(path)
    except Exception as exc:  # pragma: no cover - exact PyMuPDF exceptions vary.
        return {
            "read_status": f"open_failed:{type(exc).__name__}",
            "n_rows_or_pages": "NA",
            "n_columns": "NA",
            "text_chars": "NA",
            "nonwhite_fraction": "NA",
        }
    try:
        if pdf.page_count <= 0:
            return {
                "read_status": "opened",
                "n_rows_or_pages": 0,
                "n_columns": "NA",
                "text_chars": 0,
                "nonwhite_fraction": 0.0,
            }
        page = pdf[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(0.25, 0.25), alpha=False)
        return {
            "read_status": "opened",
            "n_rows_or_pages": int(pdf.page_count),
            "n_columns": "NA",
            "text_chars": int(len(page.get_text())),
            "nonwhite_fraction": round(_nonwhite_fraction(pix.samples, pix.n), 6),
        }
    finally:
        pdf.close()


def _audit_table(path: Path, suffix: str) -> dict[str, object]:
    try:
        sep = "\t" if suffix == ".tsv" else ","
        table = pd.read_csv(path, sep=sep)
    except Exception as exc:  # pragma: no cover - parser errors vary by pandas.
        return {
            "read_status": f"parse_failed:{type(exc).__name__}",
            "n_rows_or_pages": "NA",
            "n_columns": "NA",
            "text_chars": "NA",
            "nonwhite_fraction": "NA",
        }
    return {
        "read_status": "parsed",
        "n_rows_or_pages": int(len(table)),
        "n_columns": int(len(table.columns)),
        "text_chars": "NA",
        "nonwhite_fraction": "NA",
    }


def _audit_text(path: Path) -> dict[str, object]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "read_status": "read",
        "n_rows_or_pages": "NA",
        "n_columns": "NA",
        "text_chars": int(len(text.strip())),
        "nonwhite_fraction": "NA",
    }


def _audit_json(path: Path) -> dict[str, object]:
    try:
        text = path.read_text(encoding="utf-8")
        json.loads(text)
    except Exception as exc:  # pragma: no cover - exact JSON errors vary.
        return {
            "read_status": f"parse_failed:{type(exc).__name__}",
            "n_rows_or_pages": "NA",
            "n_columns": "NA",
            "text_chars": "NA",
            "nonwhite_fraction": "NA",
        }
    return {
        "read_status": "parsed",
        "n_rows_or_pages": "NA",
        "n_columns": "NA",
        "text_chars": int(len(text.strip())),
        "nonwhite_fraction": "NA",
    }


def _audit_known_file(path: Path) -> dict[str, object]:
    suffix = path.suffix.lower()
    if suffix in PDF_SUFFIXES:
        return _audit_pdf(path)
    if suffix in TABLE_SUFFIXES:
        return _audit_table(path, suffix)
    if suffix in JSON_SUFFIXES:
        return _audit_json(path)
    if suffix in TEXT_SUFFIXES:
        return _audit_text(path)
    return {
        "read_status": "exists_unparsed_extension",
        "n_rows_or_pages": "NA",
        "n_columns": "NA",
        "text_chars": "NA",
        "nonwhite_fraction": "NA",
    }


def _status_for_row(row: dict[str, object]) -> tuple[str, str]:
    if not row["exists"]:
        return "fail", "supplementary artifact is missing"
    if not row["source_dir_exists"]:
        return "fail", "source_results_dir is missing"
    if not row["supplementary_boundary_found"]:
        return "fail", "global supplementary source-map boundary is missing"
    if not row["supplementary_boundary_present"]:
        return "fail", "global supplementary source-map boundary text is empty"
    read_status = str(row["read_status"])
    if "failed" in read_status or read_status == "pymupdf_unavailable":
        return "fail", read_status
    suffix = str(row["suffix"]).lower()
    if suffix in TABLE_SUFFIXES:
        if row["n_columns"] == 0:
            return "fail", "parsed table has zero columns"
        return "pass", "supplementary table parsed"
    if suffix in PDF_SUFFIXES:
        pages = float(row["n_rows_or_pages"])
        text_chars = float(row["text_chars"])
        nonwhite = float(row["nonwhite_fraction"])
        if pages <= 0:
            return "fail", "supplementary PDF has zero pages"
        if text_chars < MIN_PDF_TEXT_CHARS and nonwhite < MIN_PDF_NONWHITE_FRACTION:
            return "fail", "supplementary PDF appears blank"
        return "pass", "supplementary PDF rendered"
    if suffix in JSON_SUFFIXES:
        if float(row["text_chars"]) <= 0:
            return "fail", "JSON artifact is empty"
        return "pass", "supplementary JSON parsed"
    if suffix in TEXT_SUFFIXES:
        if float(row["text_chars"]) <= 0:
            return "fail", "text artifact is empty"
        return "pass", "supplementary text read"
    return "pass", "supplementary artifact exists"


def build_supplementary_artifact_audit(
    *,
    root: Path,
    figure_manifest_path: Path,
    source_map_path: Path,
) -> pd.DataFrame:
    manifest = _read_tsv(figure_manifest_path)
    source_map = _read_tsv(source_map_path)
    boundary_found, boundary = _supplementary_boundary(source_map)
    rows: list[dict[str, object]] = []

    if manifest.empty or "figure_id" not in manifest.columns or "path" not in manifest:
        return pd.DataFrame(
            [
                {
                    "artifact_id": "NA",
                    "path": _relative_or_abs(figure_manifest_path, root),
                    "source_results_dir": "NA",
                    "exists": False,
                    "source_dir_exists": False,
                    "suffix": "NA",
                    "size_bytes": "NA",
                    "read_status": "not_checked",
                    "n_rows_or_pages": "NA",
                    "n_columns": "NA",
                    "text_chars": "NA",
                    "nonwhite_fraction": "NA",
                    "supplementary_boundary_found": boundary_found,
                    "supplementary_boundary_present": boundary != "NA",
                    "status": "fail",
                    "notes": "figure manifest missing or invalid",
                }
            ]
        )

    for item in manifest.to_dict(orient="records"):
        artifact_id = str(item.get("figure_id", ""))
        if not artifact_id.startswith("supp_"):
            continue
        artifact_path = Path(str(item.get("path", "")))
        if not artifact_path.is_absolute():
            artifact_path = root / artifact_path
        source_dir = Path(str(item.get("source_results_dir", "")))
        if not source_dir.is_absolute():
            source_dir = root / source_dir
        exists = artifact_path.exists()
        metrics = _audit_known_file(artifact_path) if exists else {
            "read_status": "not_checked",
            "n_rows_or_pages": "NA",
            "n_columns": "NA",
            "text_chars": "NA",
            "nonwhite_fraction": "NA",
        }
        row: dict[str, object] = {
            "artifact_id": artifact_id,
            "path": _relative_or_abs(artifact_path, root),
            "source_results_dir": _relative_or_abs(source_dir, root),
            "exists": exists,
            "source_dir_exists": source_dir.exists(),
            "suffix": artifact_path.suffix.lower(),
            "size_bytes": int(artifact_path.stat().st_size) if exists else "NA",
            **metrics,
            "supplementary_boundary_found": boundary_found,
            "supplementary_boundary_present": boundary != "NA",
        }
        status, notes = _status_for_row(row)
        row["status"] = status
        row["notes"] = notes
        rows.append(row)

    if not rows:
        rows.append(
            {
                "artifact_id": "NA",
                "path": _relative_or_abs(figure_manifest_path, root),
                "source_results_dir": "NA",
                "exists": False,
                "source_dir_exists": False,
                "suffix": "NA",
                "size_bytes": "NA",
                "read_status": "not_checked",
                "n_rows_or_pages": "NA",
                "n_columns": "NA",
                "text_chars": "NA",
                "nonwhite_fraction": "NA",
                "supplementary_boundary_found": boundary_found,
                "supplementary_boundary_present": boundary != "NA",
                "status": "fail",
                "notes": "no supplementary artifacts found in figure manifest",
            }
        )
    return pd.DataFrame(rows).sort_values(["artifact_id"]).reset_index(drop=True)


def build_supplementary_artifact_report(audit: pd.DataFrame) -> str:
    failures = audit.loc[audit["status"].astype(str) != "pass"]
    decision = (
        "SUPPLEMENTARY_ARTIFACTS_PASS"
        if failures.empty
        else "SUPPLEMENTARY_ARTIFACTS_FAIL"
    )
    by_suffix = audit["suffix"].astype(str).value_counts().sort_index()
    lines = [
        "# Supplementary Artifact Audit",
        "",
        f"Decision: `{decision}`",
        "",
        f"- Audited supplementary artifacts: {len(audit)}",
        f"- Passing artifacts: {int((audit['status'].astype(str) == 'pass').sum())}",
        f"- Artifacts requiring attention: {len(failures)}",
        "",
        "## Artifact Types",
        "",
    ]
    for suffix, count in by_suffix.items():
        lines.append(f"- `{suffix}`: {count}")
    lines.extend(["", "## Items Requiring Attention", ""])
    if failures.empty:
        lines.append("None.")
    else:
        for row in failures.to_dict(orient="records"):
            lines.append(
                f"- `{row['artifact_id']}` `{row['status']}`: {row['path']} "
                f"({row['notes']})"
            )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This audit verifies local readability and manifest traceability of",
            "supplementary artifacts. It does not replace final journal production",
            "checks, manual caption review, or data-use review for public release.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--figure-manifest", default="manuscript/figure_manifest.tsv")
    parser.add_argument(
        "--source-map",
        default="manuscript/figure_legends/03_figure_source_map.tsv",
    )
    parser.add_argument(
        "--audit-out",
        default="manuscript/supplementary_quality/SUPPLEMENTARY_ARTIFACT_AUDIT.tsv",
    )
    parser.add_argument(
        "--report-out",
        default="manuscript/supplementary_quality/SUPPLEMENTARY_ARTIFACT_REPORT.md",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Write outputs and return success even when supplementary checks fail.",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    audit_out = root / args.audit_out
    report_out = root / args.report_out
    audit_out.parent.mkdir(parents=True, exist_ok=True)
    audit = build_supplementary_artifact_audit(
        root=root,
        figure_manifest_path=root / args.figure_manifest,
        source_map_path=root / args.source_map,
    )
    _write_table_atomic(audit_out, audit)
    _write_text_atomic(report_out, build_supplementary_artifact_report(audit))
    print(f"wrote {audit_out}")
    print(f"wrote {report_out}")
    has_failures = bool((audit["status"].astype(str) != "pass").any())
    if has_failures and not args.report_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
