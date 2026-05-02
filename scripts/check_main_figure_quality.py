#!/usr/bin/env python
"""Audit generated main-figure PDFs before manuscript submission.

Author: SheafSignal contributors
Date: 2026-05-01
Purpose: verify that generated main figures are renderable, non-empty, and
linked to evidence boundaries before any 20-50 IF journal submission attempt.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


MIN_TEXT_CHARS = 20
MIN_NONWHITE_FRACTION = 0.005
MIN_WIDTH_PT = 250.0
MAX_WIDTH_PT = 800.0
MIN_HEIGHT_PT = 200.0
MAX_HEIGHT_PT = 800.0


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


def _figure_display_item(figure_id: str) -> str:
    match = re.match(r"fig(\d+)", figure_id)
    if not match:
        return "NA"
    return f"Figure {match.group(1)}"


def _source_boundary(source_map: pd.DataFrame, display_item: str) -> tuple[bool, str]:
    if source_map.empty or "display_item" not in source_map.columns:
        return False, "NA"
    rows = source_map.loc[source_map["display_item"].astype(str) == display_item]
    if rows.empty:
        return False, "NA"
    value = rows.iloc[0].get("boundary", "")
    if pd.isna(value):
        return True, "NA"
    boundary = str(value).strip()
    if not boundary:
        return True, "NA"
    return True, boundary


def _blank_pdf_metrics() -> dict[str, object]:
    return {
        "pdf_open_status": "not_checked",
        "page_count": "NA",
        "page_width_pt": "NA",
        "page_height_pt": "NA",
        "first_page_text_chars": "NA",
        "first_page_nonwhite_fraction": "NA",
    }


def _audit_pdf(path: Path) -> dict[str, object]:
    try:
        import fitz
    except ImportError:
        return {
            **_blank_pdf_metrics(),
            "pdf_open_status": "pymupdf_unavailable",
        }

    try:
        pdf = fitz.open(path)
    except Exception as exc:  # pragma: no cover - exact PyMuPDF exceptions vary.
        return {
            **_blank_pdf_metrics(),
            "pdf_open_status": f"open_failed:{type(exc).__name__}",
        }

    try:
        page_count = pdf.page_count
        if page_count <= 0:
            return {
                **_blank_pdf_metrics(),
                "pdf_open_status": "opened",
                "page_count": 0,
            }
        page = pdf[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(0.25, 0.25), alpha=False)
        nonwhite = _nonwhite_fraction(pix.samples, pix.n)
        return {
            "pdf_open_status": "opened",
            "page_count": int(page_count),
            "page_width_pt": round(float(page.rect.width), 3),
            "page_height_pt": round(float(page.rect.height), 3),
            "first_page_text_chars": int(len(page.get_text())),
            "first_page_nonwhite_fraction": round(nonwhite, 6),
        }
    finally:
        pdf.close()


def _metric_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _row_status(row: dict[str, object]) -> tuple[str, str]:
    if not row["exists"]:
        return "fail", "figure file is missing"
    if row["suffix"].lower() != ".pdf":
        return "fail", "figure is not a PDF"
    if row["pdf_open_status"] != "opened":
        return "fail", str(row["pdf_open_status"])
    if row["page_count"] != 1:
        return "fail", "main figure PDF must contain exactly one page"
    width = _metric_float(row["page_width_pt"])
    height = _metric_float(row["page_height_pt"])
    if width is None or not (MIN_WIDTH_PT <= width <= MAX_WIDTH_PT):
        return "fail", "page width outside expected manuscript range"
    if height is None or not (MIN_HEIGHT_PT <= height <= MAX_HEIGHT_PT):
        return "fail", "page height outside expected manuscript range"
    text_chars = _metric_float(row["first_page_text_chars"]) or 0.0
    nonwhite = _metric_float(row["first_page_nonwhite_fraction"]) or 0.0
    if text_chars < MIN_TEXT_CHARS and nonwhite < MIN_NONWHITE_FRACTION:
        return "fail", "first page appears blank or lacks readable content"
    if not row["source_map_found"]:
        return "fail", "source-map entry is missing"
    if not row["boundary_present"]:
        return "fail", "source-map boundary is missing"
    return "pass", "renderable PDF with source-map boundary"


def build_figure_quality_audit(
    *,
    root: Path,
    figure_manifest_path: Path,
    source_map_path: Path,
) -> pd.DataFrame:
    manifest = _read_tsv(figure_manifest_path)
    source_map = _read_tsv(source_map_path)
    rows: list[dict[str, object]] = []

    if manifest.empty or "figure_id" not in manifest.columns or "path" not in manifest:
        rows.append(
            {
                "figure_id": "NA",
                "display_item": "NA",
                "path": _relative_or_abs(figure_manifest_path, root),
                "exists": False,
                "suffix": "NA",
                "source_map_found": False,
                "boundary_present": False,
                "boundary": "NA",
                **_blank_pdf_metrics(),
                "status": "fail",
                "notes": "figure manifest missing or invalid",
            }
        )
        return pd.DataFrame(rows)

    for item in manifest.to_dict(orient="records"):
        figure_id = str(item.get("figure_id", ""))
        if not figure_id.startswith("fig"):
            continue
        figure_path = Path(str(item.get("path", "")))
        if not figure_path.is_absolute():
            figure_path = root / figure_path
        display_item = _figure_display_item(figure_id)
        source_map_found, boundary = _source_boundary(source_map, display_item)
        exists = figure_path.exists()
        pdf_metrics = _audit_pdf(figure_path) if exists else _blank_pdf_metrics()
        row: dict[str, object] = {
            "figure_id": figure_id,
            "display_item": display_item,
            "path": _relative_or_abs(figure_path, root),
            "exists": exists,
            "suffix": figure_path.suffix,
            "source_map_found": source_map_found,
            "boundary_present": bool(source_map_found and boundary != "NA"),
            "boundary": boundary,
            **pdf_metrics,
        }
        status, notes = _row_status(row)
        row["status"] = status
        row["notes"] = notes
        rows.append(row)

    if not rows:
        rows.append(
            {
                "figure_id": "NA",
                "display_item": "NA",
                "path": _relative_or_abs(figure_manifest_path, root),
                "exists": False,
                "suffix": "NA",
                "source_map_found": False,
                "boundary_present": False,
                "boundary": "NA",
                **_blank_pdf_metrics(),
                "status": "fail",
                "notes": "no main figure rows found",
            }
        )
    return pd.DataFrame(rows).sort_values(["figure_id"]).reset_index(drop=True)


def build_figure_quality_report(audit: pd.DataFrame) -> str:
    failures = audit.loc[audit["status"].astype(str) != "pass"]
    decision = "MAIN_FIGURE_QUALITY_PASS" if failures.empty else "MAIN_FIGURE_QUALITY_FAIL"
    lines = [
        "# Main Figure Quality Audit",
        "",
        f"Decision: `{decision}`",
        "",
        f"- Audited main figures: {len(audit)}",
        f"- Passing figures: {int((audit['status'].astype(str) == 'pass').sum())}",
        f"- Figures requiring attention: {len(failures)}",
        "",
        "## Figure Results",
        "",
    ]
    for row in audit.to_dict(orient="records"):
        lines.append(
            f"- `{row['figure_id']}` `{row['status']}`: {row['path']} "
            f"({row['notes']})"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This audit checks local figure file integrity and claim-source mapping.",
            "It does not replace manual editorial review of panel labels, journal",
            "house style, color accessibility, or final production requirements.",
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
        default="manuscript/figure_quality/MAIN_FIGURE_QUALITY_AUDIT.tsv",
    )
    parser.add_argument(
        "--report-out",
        default="manuscript/figure_quality/MAIN_FIGURE_QUALITY_REPORT.md",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Write outputs and return success even when figure checks fail.",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    audit_out = root / args.audit_out
    report_out = root / args.report_out
    audit_out.parent.mkdir(parents=True, exist_ok=True)
    audit = build_figure_quality_audit(
        root=root,
        figure_manifest_path=root / args.figure_manifest,
        source_map_path=root / args.source_map,
    )
    _write_table_atomic(audit_out, audit)
    _write_text_atomic(report_out, build_figure_quality_report(audit))
    print(f"wrote {audit_out}")
    print(f"wrote {report_out}")
    has_failures = bool((audit["status"].astype(str) != "pass").any())
    if has_failures and not args.report_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
