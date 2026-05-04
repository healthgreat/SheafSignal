#!/usr/bin/env python
"""Triage returned external beta reviews for SheafSignal.

Author: SheafSignal contributors
Date: 2026-05-03
Purpose: convert human or external-AI beta-review files into a reproducible
severity/action matrix for 20-50 IF submission hardening.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path


DEFAULT_INPUT_DIR = Path("external_ai_review_packet/returned_reviews")
DEFAULT_TRIAGE = Path("external_ai_review_packet/external_beta_review_triage.tsv")
DEFAULT_ACTION_MATRIX = Path("external_ai_review_packet/external_beta_review_action_matrix.tsv")
DEFAULT_REPORT = Path("external_ai_review_packet/EXTERNAL_BETA_REVIEW_TRIAGE_REPORT.md")
DEFAULT_REVIEWER_METADATA = Path("external_ai_review_packet/external_beta_review_reviewer_metadata.tsv")

SEVERITY_PATTERNS = [
    ("fatal", re.compile(r"\b(fatal|desk rejection|reject|not ready|near-fatal)\b", re.I)),
    ("major", re.compile(r"\b(major|mandatory|required|must|critical)\b", re.I)),
    ("minor", re.compile(r"\b(minor|optional|nice to have|polish)\b", re.I)),
]

DOMAIN_PATTERNS = [
    ("methods", re.compile(r"\b(sheaf|hodge|algorithm|method|mathematical|novelty)\b", re.I)),
    ("code_quality", re.compile(r"\b(code|bug|api|cli|test|pytest|ruff|package|import|exception|error handling|stale output|path)\b", re.I)),
    ("security_privacy", re.compile(r"\b(token|secret|password|credential|privacy|patient|unsafe|leak|raw data|absolute path)\b", re.I)),
    ("single_cell", re.compile(r"\b(scanpy|seurat|annotation|myeloid|gse154778|cell type)\b", re.I)),
    ("statistics", re.compile(r"\b(permutation|fdr|bootstrap|p-value|confidence|power)\b", re.I)),
    ("comparators", re.compile(r"\b(cellchat|cellphonedb|nichenet|liana|comparator)\b", re.I)),
    ("reproducibility", re.compile(r"\b(github|zenodo|doi|clone|reproducib|environment)\b", re.I)),
    ("claims", re.compile(r"\b(overclaim|driver|mechanism|causal|feedback|clinical)\b", re.I)),
    ("journal_fit", re.compile(r"\b(nature methods|nature biotechnology|molecular cancer|journal|if)\b", re.I)),
]


@dataclass(frozen=True)
class ReviewFinding:
    source_file: str
    reviewer: str
    severity: str
    domain: str
    finding: str
    suggested_action: str
    blocks_20_50_if: str


@dataclass(frozen=True)
class ReviewerMetadata:
    source_file: str
    reviewer: str
    reviewer_model_name: str
    reviewer_model_version: str
    review_timestamp_with_timezone: str
    claimed_training_data_cutoff: str
    external_references_consulted: str


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _should_ignore_review_file(path: Path) -> bool:
    lowered = path.name.lower()
    return (
        lowered == "readme.md"
        or lowered.startswith("00_readme")
        or lowered.endswith("_template.tsv")
        or path.name.startswith("_")
    )


def _normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip(" -*\t|"))


def _classify_severity(text: str) -> str:
    for severity, pattern in SEVERITY_PATTERNS:
        if pattern.search(text):
            return severity
    return "comment"


def _classify_domain(text: str) -> str:
    for domain, pattern in DOMAIN_PATTERNS:
        if pattern.search(text):
            return domain
    return "general"


def _suggest_action(severity: str, domain: str) -> str:
    if domain == "reproducibility":
        return "Check release blockers, GitHub/Zenodo identifiers, and public clean-clone evidence."
    if domain == "code_quality":
        return "Map concern to source files, tests, packaging, CLI behavior, and add regression coverage."
    if domain == "security_privacy":
        return "Check source/review bundles for credentials, raw data, private paths, and unsafe file inclusion."
    if domain == "claims":
        return "Run claim-safety audit and downgrade unsupported causal/mechanistic wording."
    if domain == "statistics":
        return "Map concern to permutation/FDR/bootstrap/sensitivity outputs and rerun if needed."
    if domain == "single_cell":
        return "Map concern to annotation validation, claim gating, and sample-level robustness outputs."
    if domain == "methods":
        return "Map concern to formal sheaf API, Hodge target, novelty table, and simulation baselines."
    if domain == "comparators":
        return "Map concern to comparator scope gate and aligned CellChat/CellPhoneDB/LIANA summaries."
    if domain == "journal_fit":
        return "Update IF20-50 distance report and journal routing table with the reviewer-specific risk."
    if severity in {"fatal", "major"}:
        return "Add to response matrix and assign an owner before submission."
    return "Record as optional polishing unless repeated by another reviewer."


def _reviewer_name(path: Path, text: str) -> str:
    for line in text.splitlines()[:20]:
        if line.lower().startswith("- reviewer") or line.lower().startswith("reviewer"):
            parts = line.split(":", 1)
            if len(parts) == 2 and parts[1].strip():
                return parts[1].strip()
    return path.stem


def _metadata_key(raw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", raw.lower()).strip("_")


def _clean_metadata_value(raw: str) -> str:
    value = raw.strip()
    value = re.sub(r"^\*+\s*", "", value)
    value = re.sub(r"\s*\*+$", "", value)
    return value.strip() or "not_reported"


def parse_reviewer_metadata(path: Path) -> ReviewerMetadata:
    text = _read_text(path)
    values = {
        "reviewer_model_name": "not_reported",
        "reviewer_model_version": "not_reported",
        "review_timestamp_with_timezone": "not_reported",
        "claimed_training_data_cutoff": "not_reported",
        "external_references_consulted": "not_reported",
    }
    aliases = {
        "reviewer_model_name": "reviewer_model_name",
        "model_name": "reviewer_model_name",
        "reviewer_model_version": "reviewer_model_version",
        "model_version": "reviewer_model_version",
        "review_timestamp_with_timezone": "review_timestamp_with_timezone",
        "review_timestamp": "review_timestamp_with_timezone",
        "claimed_training_data_cutoff": "claimed_training_data_cutoff",
        "training_data_cutoff": "claimed_training_data_cutoff",
        "knowledge_cutoff": "claimed_training_data_cutoff",
        "external_references_consulted": "external_references_consulted",
        "references_consulted": "external_references_consulted",
    }
    for line in text.splitlines()[:80]:
        clean = line.strip().lstrip("-*").strip()
        if ":" not in clean:
            continue
        key_raw, value = clean.split(":", 1)
        key = aliases.get(_metadata_key(key_raw))
        if key and value.strip():
            values[key] = _clean_metadata_value(value)
    return ReviewerMetadata(
        source_file=path.as_posix(),
        reviewer=_reviewer_name(path, text),
        **values,
    )


def _candidate_lines(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        clean = _normalize_line(line)
        if len(clean) < 25:
            continue
        severity = _classify_severity(clean)
        domain = _classify_domain(clean)
        if severity != "comment" or domain != "general":
            lines.append(clean)
    return lines


def _parse_tsv(path: Path) -> list[ReviewFinding]:
    rows = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for idx, row in enumerate(reader, start=1):
            text = " ".join(str(value) for value in row.values() if value)
            if not text.strip():
                continue
            severity = str(row.get("severity", "") or _classify_severity(text)).strip().lower()
            if severity not in {"fatal", "major", "minor", "comment"}:
                severity = _classify_severity(text)
            domain = str(row.get("domain", "") or _classify_domain(text)).strip().lower()
            finding = str(row.get("finding", "") or row.get("concern", "") or text).strip()
            rows.append(
                ReviewFinding(
                    source_file=path.as_posix(),
                    reviewer=str(row.get("reviewer", "") or path.stem).strip(),
                    severity=severity,
                    domain=domain,
                    finding=finding,
                    suggested_action=str(row.get("suggested_action", "") or _suggest_action(severity, domain)).strip(),
                    blocks_20_50_if="yes" if severity in {"fatal", "major"} else "no",
                )
            )
    return rows


def parse_review_file(path: Path) -> list[ReviewFinding]:
    if path.suffix.lower() == ".tsv":
        return _parse_tsv(path)
    text = _read_text(path)
    reviewer = _reviewer_name(path, text)
    findings = []
    seen = set()
    for line in _candidate_lines(text):
        if line in seen:
            continue
        seen.add(line)
        severity = _classify_severity(line)
        domain = _classify_domain(line)
        findings.append(
            ReviewFinding(
                source_file=path.as_posix(),
                reviewer=reviewer,
                severity=severity,
                domain=domain,
                finding=line,
                suggested_action=_suggest_action(severity, domain),
                blocks_20_50_if="yes" if severity in {"fatal", "major"} else "no",
            )
        )
    return findings


def collect_review_findings(input_dir: Path) -> list[ReviewFinding]:
    if not input_dir.exists():
        return []
    findings = []
    for path in sorted(input_dir.glob("*")):
        if _should_ignore_review_file(path):
            continue
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".tsv"}:
            findings.extend(parse_review_file(path))
    return findings


def collect_reviewer_metadata(input_dir: Path) -> list[ReviewerMetadata]:
    if not input_dir.exists():
        return []
    rows = []
    for path in sorted(input_dir.glob("*")):
        if _should_ignore_review_file(path):
            continue
        if path.is_file() and path.suffix.lower() in {".md", ".txt"}:
            rows.append(parse_reviewer_metadata(path))
    return rows


def classify_decision(findings: list[ReviewFinding]) -> str:
    if not findings:
        return "EXTERNAL_BETA_REVIEW_NO_RETURNED_REVIEWS"
    if any(finding.severity == "fatal" for finding in findings):
        return "EXTERNAL_BETA_REVIEW_TRIAGED_FATAL_OR_REJECT_CONCERNS"
    if any(finding.severity == "major" for finding in findings):
        return "EXTERNAL_BETA_REVIEW_TRIAGED_MAJOR_CONCERNS"
    return "EXTERNAL_BETA_REVIEW_TRIAGED_NO_MAJOR_BLOCKERS"


def _write_tsv_atomic(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    tmp_path.replace(path)


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def build_action_matrix(findings: list[ReviewFinding]) -> list[dict[str, object]]:
    priority_order = {"fatal": "P0", "major": "P1", "minor": "P2", "comment": "P3"}
    rows = []
    for finding in findings:
        rows.append(
            {
                "priority": priority_order.get(finding.severity, "P3"),
                "domain": finding.domain,
                "severity": finding.severity,
                "finding": finding.finding,
                "suggested_action": finding.suggested_action,
                "owner": "codex_or_authors",
                "status": "open_external_review_item",
                "blocks_20_50_if": finding.blocks_20_50_if,
                "source_file": finding.source_file,
            }
        )
    return rows


def build_report(findings: list[ReviewFinding], input_dir: Path) -> str:
    decision = classify_decision(findings)
    severity_counts = {
        severity: sum(finding.severity == severity for finding in findings)
        for severity in ["fatal", "major", "minor", "comment"]
    }
    domain_counts = {}
    for finding in findings:
        domain_counts[finding.domain] = domain_counts.get(finding.domain, 0) + 1
    domain_lines = [f"- `{domain}`: `{count}`" for domain, count in sorted(domain_counts.items())] or ["- none"]
    top_lines = [
        f"- `{finding.severity}` / `{finding.domain}`: {finding.finding}"
        for finding in findings[:10]
    ] or ["- none"]
    return "\n".join(
        [
            "# External Beta Review Triage Report",
            "",
            f"- Decision: `{decision}`",
            f"- Input directory: `{input_dir.as_posix()}`",
            f"- Returned review findings: `{len(findings)}`",
            f"- Fatal findings: `{severity_counts['fatal']}`",
            f"- Major findings: `{severity_counts['major']}`",
            f"- Minor findings: `{severity_counts['minor']}`",
            "",
            "## Domain Counts",
            "",
            *domain_lines,
            "",
            "## Top Parsed Findings",
            "",
            *top_lines,
            "",
            "## How To Use This",
            "",
            "Place returned human or external-AI reviews in the input directory as `.md`, `.txt`, or `.tsv` files, then rerun:",
            "",
            "```bash",
            "python scripts/triage_external_beta_reviews.py",
            "```",
            "",
            "Fatal or major returned-review items should be transferred into the response matrix before a 20-50 IF submission decision.",
            "Reviewer model metadata is written to `external_ai_review_packet/external_beta_review_reviewer_metadata.tsv` when returned reviews report it.",
            "",
            "## Boundary",
            "",
            "This triage is keyword-assisted and reviewer-facing. It does not replace human judgment, public GitHub release, Zenodo DOI, author confirmation, or final clean-clone reproduction.",
            "",
        ]
    )


def write_outputs(root: Path, findings: list[ReviewFinding], input_dir: Path) -> dict[str, Path]:
    triage_path = root / DEFAULT_TRIAGE
    action_path = root / DEFAULT_ACTION_MATRIX
    report_path = root / DEFAULT_REPORT
    metadata_path = root / DEFAULT_REVIEWER_METADATA
    rows = [finding.__dict__ for finding in findings]
    _write_tsv_atomic(
        triage_path,
        rows,
        ["source_file", "reviewer", "severity", "domain", "finding", "suggested_action", "blocks_20_50_if"],
    )
    _write_tsv_atomic(
        action_path,
        build_action_matrix(findings),
        [
            "priority",
            "domain",
            "severity",
            "finding",
            "suggested_action",
            "owner",
            "status",
            "blocks_20_50_if",
            "source_file",
        ],
    )
    try:
        display_input_dir = input_dir.relative_to(root)
    except ValueError:
        display_input_dir = input_dir
    metadata_rows = [
        row.__dict__ for row in collect_reviewer_metadata(input_dir)
    ]
    _write_tsv_atomic(
        metadata_path,
        metadata_rows,
        [
            "source_file",
            "reviewer",
            "reviewer_model_name",
            "reviewer_model_version",
            "review_timestamp_with_timezone",
            "claimed_training_data_cutoff",
            "external_references_consulted",
        ],
    )
    _write_text_atomic(report_path, build_report(findings, display_input_dir))
    return {
        "triage": triage_path,
        "action_matrix": action_path,
        "reviewer_metadata": metadata_path,
        "report": report_path,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    input_dir = Path(args.input_dir)
    if not input_dir.is_absolute():
        input_dir = root / input_dir
    findings = collect_review_findings(input_dir)
    outputs = write_outputs(root, findings, input_dir)
    print(classify_decision(findings))
    print(f"Findings: {len(findings)}")
    for label, path in outputs.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
