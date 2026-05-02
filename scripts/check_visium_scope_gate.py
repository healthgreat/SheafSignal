#!/usr/bin/env python
"""Audit Visium spatial claims for hotspot-only interpretation boundaries."""

from __future__ import annotations

import argparse
from pathlib import Path
import re

import pandas as pd


SCAN_SUFFIXES = {".md", ".tsv", ".txt"}
SCAN_DIRS = ["manuscript", "docs"]
EXCLUDED_NAME_PARTS = {
    "AI_PRE_REVIEW",
    "SUPERGROK",
    "CLAIM_SAFETY_AUDIT",
    "CLAIM_HARDENING_AUDIT",
    "VISIUM_SCOPE_AUDIT",
    "VISIUM_SCOPE_REPORT",
}

REQUIRED_VISIUM_FILES = [
    "benchmarks/results/tenx_breast_visium/spatial/spatial_frustration_hotspots.csv",
    "benchmarks/results/tenx_breast_visium/spatial/spatial_hotspot_summary.csv",
    "benchmarks/results/tenx_breast_visium/spatial/qc/marker_spot_counts.csv",
    "benchmarks/results/tenx_breast_visium/spatial/qc/k_neighbors_sensitivity.csv",
    "benchmarks/results/tenx_breast_visium/spatial/qc/spatial_hotspot_qc_summary.csv",
]

UNSAFE_VISIUM_PATTERNS = {
    "visium_top_source": re.compile(
        r"\b(Visium|tenx_breast_visium)\b.{0,220}\b(top source|highest computational source)\b",
        re.IGNORECASE,
    ),
    "visium_cell_type_source": re.compile(
        r"\b(Visium|spatial|spot)\b.{0,220}\b(cell[- ]type source|source cell|cell type source)\b",
        re.IGNORECASE,
    ),
    "visium_histology_mechanism": re.compile(
        r"\b(Visium|spatial|spot)\b.{0,220}\b(histology-confirmed|single-cell)\b.{0,80}\bmechanism\b",
        re.IGNORECASE,
    ),
}

SAFE_BOUNDARY_CUES = {
    "not ",
    "do not",
    "cannot",
    "rather than",
    "boundary",
    "boundaries",
    "hotspot",
    "spot-level",
    "marker-dominant",
    "qc context",
    "demonstration",
    "workflow demonstration",
    "without deconvolution",
    "requires",
}


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_table_atomic(path: Path, table: pd.DataFrame) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    table.to_csv(tmp_path, sep="\t", index=False)
    tmp_path.replace(path)


def _is_safe_boundary(line: str, context: str = "") -> bool:
    lower = f"{context}\n{line}".lower()
    return any(cue in lower for cue in SAFE_BOUNDARY_CUES)


def _iter_scan_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for rel_dir in SCAN_DIRS:
        base = root / rel_dir
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
                continue
            if any(part in path.name for part in EXCLUDED_NAME_PARTS):
                continue
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def _file_requirement_rows(root: Path) -> list[dict[str, object]]:
    rows = []
    for rel in REQUIRED_VISIUM_FILES:
        path = root / rel
        rows.append(
            {
                "check_id": "required_visium_file_exists",
                "status": "pass" if path.exists() else "fail",
                "relative_path": rel,
                "line_no": "",
                "evidence": "exists" if path.exists() else "missing",
                "required_action": "Regenerate Visium hotspot/QC outputs." if not path.exists() else "",
            }
        )
    return rows


def _qc_metric_rows(root: Path) -> list[dict[str, object]]:
    rows = []
    summary_path = root / "benchmarks/results/tenx_breast_visium/spatial/qc/spatial_hotspot_qc_summary.csv"
    if not summary_path.exists():
        rows.append(
            {
                "check_id": "visium_hotspot_qc_metrics",
                "status": "fail",
                "relative_path": summary_path.relative_to(root).as_posix(),
                "line_no": "",
                "evidence": "missing spatial_hotspot_qc_summary.csv",
                "required_action": "Run scripts/qc_tenx_visium_spatial.py.",
            }
        )
        return rows

    summary = pd.read_csv(summary_path)
    if summary.empty:
        rows.append(
            {
                "check_id": "visium_hotspot_qc_metrics",
                "status": "fail",
                "relative_path": summary_path.relative_to(root).as_posix(),
                "line_no": "",
                "evidence": "empty spatial_hotspot_qc_summary.csv",
                "required_action": "Regenerate Visium spatial QC summary.",
            }
        )
        return rows

    row = summary.iloc[0]
    min_spearman = float(row.get("min_spearman_across_k", float("nan")))
    min_overlap = float(row.get("min_top_50_overlap_across_k", float("nan")))
    warning = str(row.get("interpretation_warning", ""))
    boundary_ok = "not as single-cell" in warning.lower() or "not single-cell" in warning.lower()
    status = "pass" if min_spearman >= 0.9 and min_overlap >= 0.8 and boundary_ok else "fail"
    rows.append(
        {
            "check_id": "visium_hotspot_qc_metrics",
            "status": status,
            "relative_path": summary_path.relative_to(root).as_posix(),
            "line_no": "",
            "evidence": (
                f"min_spearman={min_spearman:.4g}; min_top50_overlap={min_overlap:.4g}; "
                f"boundary_warning={boundary_ok}"
            ),
            "required_action": (
                "Keep Visium as hotspot-only demo."
                if status == "pass"
                else "Regenerate QC and add explicit non-single-cell boundary warning."
            ),
        }
    )
    return rows


def _scan_visium_text(root: Path) -> list[dict[str, object]]:
    rows = []
    for path in _iter_scan_files(root):
        rel = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        for line_no, line in enumerate(lines, start=1):
            context = "\n".join(lines[max(0, line_no - 6) : line_no - 1])
            for pattern_id, pattern in UNSAFE_VISIUM_PATTERNS.items():
                match = pattern.search(line)
                if not match:
                    continue
                is_safe = _is_safe_boundary(line, context=context)
                rows.append(
                    {
                        "check_id": f"text_scope::{pattern_id}",
                        "status": "pass" if is_safe else "fail",
                        "relative_path": rel,
                        "line_no": line_no,
                        "evidence": line.strip(),
                        "required_action": (
                            "No action; boundary wording is present."
                            if is_safe
                            else "Rewrite Visium wording as hotspot-only, spot-level workflow demonstration."
                        ),
                    }
                )
    if not rows:
        rows.append(
            {
                "check_id": "text_scope::visium_overclaim_scan",
                "status": "pass",
                "relative_path": "",
                "line_no": "",
                "evidence": "No Visium top-source or cell-type-source overclaim patterns detected.",
                "required_action": "",
            }
        )
    return rows


def build_visium_scope_audit(root: Path) -> pd.DataFrame:
    rows = []
    rows.extend(_file_requirement_rows(root))
    rows.extend(_qc_metric_rows(root))
    rows.extend(_scan_visium_text(root))
    columns = ["check_id", "status", "relative_path", "line_no", "evidence", "required_action"]
    return pd.DataFrame(rows, columns=columns)


def build_visium_scope_report(audit: pd.DataFrame) -> str:
    failures = audit.loc[audit["status"] == "fail"] if not audit.empty else audit
    decision = "VISIUM_SCOPE_BLOCKED" if len(failures) else "VISIUM_SCOPE_PASS_HOTSPOT_ONLY"
    lines = [
        "# Visium Scope Gate Report",
        "",
        f"Decision: `{decision}`",
        "",
        f"- Checks: {len(audit)}",
        f"- Failures: {len(failures)}",
        "",
        "## Required Interpretation",
        "",
        "The 10x breast Visium analysis is allowed as a spot-level spatial hotspot",
        "workflow demonstration with k-neighbor sensitivity and marker-program QC.",
        "It must not be described as a cell-type source analysis, histology-confirmed",
        "single-cell mechanism, or validated tumor biology result without additional",
        "deconvolution/histology evidence.",
        "",
        "## Blocking Rows",
        "",
    ]
    if failures.empty:
        lines.append("None.")
    else:
        for row in failures.to_dict(orient="records"):
            loc = row["relative_path"]
            if row["line_no"] != "":
                loc = f"{loc}:{row['line_no']}"
            lines.append(f"- `{loc}` `{row['check_id']}`: {row['evidence']}")
            lines.append(f"  Action: {row['required_action']}")
    lines.append("")
    return "\n".join(lines)


def build_visium_scope_outputs(root: Path, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    audit = build_visium_scope_audit(root)
    audit_path = output_dir / "VISIUM_SCOPE_AUDIT.tsv"
    report_path = output_dir / "VISIUM_SCOPE_REPORT.md"
    _write_table_atomic(audit_path, audit)
    _write_text_atomic(report_path, build_visium_scope_report(audit))
    return {"audit": audit_path, "report": report_path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-dir", default="manuscript/visium_scope")
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    paths = build_visium_scope_outputs(root, root / args.output_dir)
    for path in paths.values():
        print(f"wrote {path}")
    audit = pd.read_csv(paths["audit"], sep="\t")
    has_failures = bool((audit["status"] == "fail").any())
    return 0 if args.report_only or not has_failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
