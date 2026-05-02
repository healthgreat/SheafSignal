#!/usr/bin/env python
"""Audit manuscript claims for unsupported high-impact overstatements.

Author: SheafSignal contributors
Date: 2026-04-30
Purpose: scan all manuscript-facing text for positive clinical, therapeutic,
guaranteed-publication, or broad-superiority claims before 20-50 IF submission.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re

import pandas as pd


SCAN_SUFFIXES = {".md", ".tsv", ".txt"}
EXCLUDED_FILENAMES = {
    "CLAIM_SAFETY_AUDIT.tsv",
    "CLAIM_SAFETY_AUDIT_REPORT.md",
}

SAFE_BOUNDARY_CUES = {
    "do not",
    "does not",
    "not ",
    "no ",
    "never",
    "cannot",
    "must not",
    "without",
    "avoid",
    "boundary",
    "forbidden",
    "pending",
    "not positioned",
    "not claim",
    "not imply",
    "not allowed",
    "must not claim",
    "not support",
    "requires careful",
    "unless",
    "limitation",
    "limitations",
}

TRIGGERS = {
    "guaranteed_acceptance_or_publication": re.compile(
        r"\b(guarantee|guaranteed|guarantees)\b.{0,70}\b(acceptance|publication)\b",
        re.IGNORECASE,
    ),
    "clinical_utility": re.compile(r"\bclinical utility\b", re.IGNORECASE),
    "treatment_or_therapeutic_guidance": re.compile(
        r"\b(treatment|therapeutic|therapy|clinical decision support)\b",
        re.IGNORECASE,
    ),
    "broad_superiority": re.compile(
        r"\b(superiority|superior|outperform|outperforms|better than)\b",
        re.IGNORECASE,
    ),
    "full_pretrained_nichenet": re.compile(
        r"\b(full pretrained NicheNet|pretrained NicheNet network)\b",
        re.IGNORECASE,
    ),
}

BLOCKING_POSITIVE_PATTERNS = {
    "guaranteed_acceptance_or_publication": TRIGGERS["guaranteed_acceptance_or_publication"],
    "clinical_utility_positive": re.compile(
        r"\b(demonstrate|demonstrates|establish|establishes|prove|proves|validated|validates)\b"
        r".{0,80}\bclinical utility\b",
        re.IGNORECASE,
    ),
    "treatment_guidance_positive": re.compile(
        r"\b(recommend|recommends|guide|guides|inform|informs|predict|predicts)\b"
        r".{0,90}\b(treatment|therapy|therapeutic)\b",
        re.IGNORECASE,
    ),
    "broad_superiority_positive": re.compile(
        r"\b(superior|outperform|outperforms|better than)\b.{0,90}"
        r"\b(CellChat|CellPhoneDB|LIANA|NicheNet|niche-DE|CCC|communication tools)\b",
        re.IGNORECASE,
    ),
}


def _safe_boundary_line(line: str, context: str = "") -> bool:
    lower = f"{context}\n{line}".lower()
    return any(cue in lower for cue in SAFE_BOUNDARY_CUES)


def _iter_scan_files(root: Path, manuscript_dir: Path) -> list[Path]:
    if not manuscript_dir.exists():
        return []
    files = []
    for path in manuscript_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.name in EXCLUDED_FILENAMES:
            continue
        if path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def classify_line(line: str, context: str = "") -> tuple[str, str, str] | None:
    positive_matches = [
        name for name, pattern in BLOCKING_POSITIVE_PATTERNS.items() if pattern.search(line)
    ]
    trigger_matches = [name for name, pattern in TRIGGERS.items() if pattern.search(line)]
    if not positive_matches and not trigger_matches:
        return None

    matched = ";".join(positive_matches or trigger_matches)
    snippet = line.strip()
    if _safe_boundary_line(line, context=context):
        return matched, "safe_boundary_statement", snippet
    if positive_matches:
        return matched, "blocking_positive_claim", snippet
    return matched, "needs_author_review", snippet


def build_claim_safety_audit(root: Path, manuscript_dir: Path) -> pd.DataFrame:
    rows = []
    for path in _iter_scan_files(root, manuscript_dir):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        for line_no, line in enumerate(lines, start=1):
            context = "\n".join(lines[max(0, line_no - 8) : line_no - 1])
            classified = classify_line(line, context=context)
            if classified is None:
                continue
            trigger, classification, snippet = classified
            if classification == "blocking_positive_claim":
                action = "Rewrite as a boundary statement or remove the unsupported positive claim."
            elif classification == "needs_author_review":
                action = "Author review required to confirm this is not an unsupported positive claim."
            else:
                action = "No rewrite required if this remains a negative/boundary statement."
            rows.append(
                {
                    "relative_path": rel,
                    "line_no": line_no,
                    "trigger": trigger,
                    "classification": classification,
                    "matched_text": snippet,
                    "required_action": action,
                }
            )
    columns = [
        "relative_path",
        "line_no",
        "trigger",
        "classification",
        "matched_text",
        "required_action",
    ]
    return pd.DataFrame(rows, columns=columns)


def build_claim_safety_report(audit: pd.DataFrame) -> str:
    if audit.empty:
        blocking = 0
        review = 0
        safe = 0
    else:
        counts = audit["classification"].value_counts()
        blocking = int(counts.get("blocking_positive_claim", 0))
        review = int(counts.get("needs_author_review", 0))
        safe = int(counts.get("safe_boundary_statement", 0))
    decision = "CLAIM_SAFETY_BLOCKED" if blocking else "CLAIM_SAFETY_PASS_WITH_BOUNDARY_NOTES"
    lines = [
        "# Claim Safety Audit Report",
        "",
        f"Decision: `{decision}`",
        "",
        f"- Blocking positive claims: {blocking}",
        f"- Lines needing author review: {review}",
        f"- Safe boundary statements detected: {safe}",
        "",
        "## Interpretation",
        "",
        "This audit scans manuscript-facing text for unsupported positive claims",
        "about guaranteed publication, clinical utility, treatment guidance,",
        "broad superiority, and full pretrained NicheNet benchmarking. Boundary",
        "statements are allowed and recorded so they are not mistaken for",
        "positive claims.",
        "",
    ]
    if blocking:
        lines.extend(["## Blocking Lines", ""])
        subset = audit.loc[audit["classification"] == "blocking_positive_claim"]
        for row in subset.to_dict(orient="records"):
            lines.append(
                f"- `{row['relative_path']}:{row['line_no']}` "
                f"{row['trigger']}: {row['matched_text']}"
            )
        lines.append("")
    return "\n".join(lines)


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_table_atomic(path: Path, table: pd.DataFrame) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    table.to_csv(tmp_path, sep="\t", index=False)
    tmp_path.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--manuscript-dir", default="manuscript")
    parser.add_argument("--audit-out", default="manuscript/CLAIM_SAFETY_AUDIT.tsv")
    parser.add_argument("--report-out", default="manuscript/CLAIM_SAFETY_AUDIT_REPORT.md")
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    manuscript_dir = Path(args.manuscript_dir)
    if not manuscript_dir.is_absolute():
        manuscript_dir = root / manuscript_dir
    audit = build_claim_safety_audit(root, manuscript_dir)
    audit_out = root / args.audit_out
    report_out = root / args.report_out
    audit_out.parent.mkdir(parents=True, exist_ok=True)
    _write_table_atomic(audit_out, audit)
    _write_text_atomic(report_out, build_claim_safety_report(audit))
    print(f"wrote {audit_out}")
    print(f"wrote {report_out}")

    has_blocking = bool(
        not audit.empty and (audit["classification"] == "blocking_positive_claim").any()
    )
    if has_blocking and not args.report_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
