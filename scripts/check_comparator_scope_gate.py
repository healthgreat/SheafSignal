#!/usr/bin/env python
"""Audit comparator completion scope and manuscript comparator boundaries."""

from __future__ import annotations

import argparse
from pathlib import Path
import re

import pandas as pd


PRIMARY_SCRNA_DATASETS = [
    "gse72056_melanoma_scrna",
    "gse154778_pdac_scrna",
    "gse176078_brca_scrna",
]

PRIMARY_COMPARATOR_TOOLS = [
    "LRProductBaseline",
    "LIANA",
    "MechanisticTargetPrior",
    "NicheNet",
    "CellPhoneDB",
    "CellChat",
]

COMPLETED_STATUSES = {"completed", "completed_external_import"}

SCAN_SUFFIXES = {".md", ".tsv", ".txt"}
SCAN_DIRS = ["manuscript", "docs"]
EXCLUDED_NAME_PARTS = {
    "AI_PRE_REVIEW",
    "SUPERGROK",
    "CLAIM_SAFETY_AUDIT",
    "CLAIM_HARDENING_AUDIT",
    "VISIUM_SCOPE_AUDIT",
    "COMPARATOR_SCOPE_AUDIT",
    "COMPARATOR_SCOPE_REPORT",
}

STALE_PENDING_PATTERN = re.compile(
    r"\b(CellChat|CellPhoneDB)\b.{0,120}\bpending\b|\bpending\b.{0,120}\b(CellChat|CellPhoneDB)\b",
    re.IGNORECASE,
)

BROAD_SUPERIORITY_PATTERN = re.compile(
    r"\b(superior|outperform|outperforms|better than)\b.{0,120}"
    r"\b(CellChat|CellPhoneDB|LIANA|NicheNet|niche-DE|CCC|communication tools)\b",
    re.IGNORECASE,
)

SAFE_BOUNDARY_CUES = {
    "do not",
    "does not",
    "not ",
    "no ",
    "never",
    "without",
    "boundary",
    "not claim",
    "not allowed",
    "not imply",
    "complementarity",
    "alignment",
    "bounded",
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


def _load_tool_comparison(root: Path) -> pd.DataFrame:
    path = root / "benchmarks/results/tool_comparison.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _primary_comparator_rows(root: Path) -> list[dict[str, object]]:
    table = _load_tool_comparison(root)
    rows = []
    if table.empty:
        return [
            {
                "check_id": "primary_scrna_comparator_completion",
                "status": "fail",
                "dataset_id": "",
                "tool": "",
                "relative_path": "benchmarks/results/tool_comparison.csv",
                "line_no": "",
                "evidence": "missing or empty tool_comparison.csv",
                "required_action": "Regenerate comparator imports and tool_comparison.csv.",
            }
        ]

    for dataset_id in PRIMARY_SCRNA_DATASETS:
        for tool in PRIMARY_COMPARATOR_TOOLS:
            subset = table.loc[
                (table["dataset_id"].astype(str) == dataset_id)
                & (table["tool"].astype(str) == tool)
            ]
            completed = bool(
                not subset.empty
                and subset["status"].astype(str).isin(COMPLETED_STATUSES).any()
            )
            rows.append(
                {
                    "check_id": "primary_scrna_comparator_completion",
                    "status": "pass" if completed else "fail",
                    "dataset_id": dataset_id,
                    "tool": tool,
                    "relative_path": "benchmarks/results/tool_comparison.csv",
                    "line_no": "",
                    "evidence": "completed in primary scRNA scope" if completed else "missing",
                    "required_action": (
                        "" if completed else f"Complete or remove primary-scope claim for {tool} on {dataset_id}."
                    ),
                }
            )
    return rows


def _out_of_scope_rows(root: Path) -> list[dict[str, object]]:
    table = _load_tool_comparison(root)
    if table.empty:
        return []
    out_scope = table.loc[
        ~table["dataset_id"].astype(str).isin(PRIMARY_SCRNA_DATASETS)
        & ~table["status"].astype(str).isin(COMPLETED_STATUSES)
    ].copy()
    return [
        {
            "check_id": "out_of_scope_pending_comparators",
            "status": "pass",
            "dataset_id": "outside_primary_scrna_scope",
            "tool": "",
            "relative_path": "benchmarks/results/tool_comparison.csv",
            "line_no": "",
            "evidence": f"{len(out_scope)} pending rows are outside the primary scRNA comparator scope",
            "required_action": "Do not claim comparator completeness for demo, Visium, GSE103322, or niche-DE.",
        }
    ]


def _text_scope_rows(root: Path) -> list[dict[str, object]]:
    rows = []
    for path in _iter_scan_files(root):
        rel = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        for line_no, line in enumerate(lines, start=1):
            context = "\n".join(lines[max(0, line_no - 6) : line_no - 1])
            stale_pending = STALE_PENDING_PATTERN.search(line)
            broad_superiority = BROAD_SUPERIORITY_PATTERN.search(line)
            if stale_pending:
                rows.append(
                    {
                        "check_id": "text_scope::stale_cellchat_cellphonedb_pending",
                        "status": "fail",
                        "dataset_id": "",
                        "tool": "",
                        "relative_path": rel,
                        "line_no": line_no,
                        "evidence": line.strip(),
                        "required_action": (
                            "State that CellChat/CellPhoneDB are complete for the primary scRNA "
                            "scope, and list only out-of-scope pending comparators separately."
                        ),
                    }
                )
            if broad_superiority:
                safe = _is_safe_boundary(line, context=context)
                rows.append(
                    {
                        "check_id": "text_scope::broad_superiority",
                        "status": "pass" if safe else "fail",
                        "dataset_id": "",
                        "tool": "",
                        "relative_path": rel,
                        "line_no": line_no,
                        "evidence": line.strip(),
                        "required_action": (
                            "No action; boundary wording is present."
                            if safe
                            else "Rewrite as complementarity/alignment, not superiority."
                        ),
                    }
                )
    if not rows:
        rows.append(
            {
                "check_id": "text_scope::comparator_claim_scan",
                "status": "pass",
                "dataset_id": "",
                "tool": "",
                "relative_path": "",
                "line_no": "",
                "evidence": "No stale comparator-pending or positive broad-superiority claims detected.",
                "required_action": "",
            }
        )
    return rows


def build_comparator_scope_audit(root: Path) -> pd.DataFrame:
    rows = []
    rows.extend(_primary_comparator_rows(root))
    rows.extend(_out_of_scope_rows(root))
    rows.extend(_text_scope_rows(root))
    columns = [
        "check_id",
        "status",
        "dataset_id",
        "tool",
        "relative_path",
        "line_no",
        "evidence",
        "required_action",
    ]
    return pd.DataFrame(rows, columns=columns)


def build_comparator_scope_report(audit: pd.DataFrame) -> str:
    failures = audit.loc[audit["status"] == "fail"] if not audit.empty else audit
    decision = "COMPARATOR_SCOPE_BLOCKED" if len(failures) else "COMPARATOR_SCOPE_PASS_PRIMARY_SCRNA"
    lines = [
        "# Comparator Scope Gate Report",
        "",
        f"Decision: `{decision}`",
        "",
        f"- Checks: {len(audit)}",
        f"- Failures: {len(failures)}",
        "",
        "## Allowed Comparator Scope",
        "",
        "Primary comparator claims are limited to GSE72056, GSE154778 and",
        "GSE176078 scRNA-seq benchmarks. Within that scope, the required",
        "comparators are LRProductBaseline, LIANA, MechanisticTargetPrior,",
        "bounded NicheNet/nichenetr-engine, CellPhoneDB and CellChat.",
        "Pending rows for demo data, Visium, GSE103322 or niche-DE do not block",
        "submission if the manuscript does not claim completeness for those scopes.",
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


def build_comparator_scope_outputs(root: Path, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    audit = build_comparator_scope_audit(root)
    audit_path = output_dir / "COMPARATOR_SCOPE_AUDIT.tsv"
    report_path = output_dir / "COMPARATOR_SCOPE_REPORT.md"
    _write_table_atomic(audit_path, audit)
    _write_text_atomic(report_path, build_comparator_scope_report(audit))
    return {"audit": audit_path, "report": report_path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-dir", default="manuscript/comparator_scope")
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    paths = build_comparator_scope_outputs(root, root / args.output_dir)
    for path in paths.values():
        print(f"wrote {path}")
    audit = pd.read_csv(paths["audit"], sep="\t")
    has_failures = bool((audit["status"] == "fail").any())
    return 0 if args.report_only or not has_failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
