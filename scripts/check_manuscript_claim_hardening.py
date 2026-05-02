#!/usr/bin/env python
"""Strict claim-hardening scanner for the 20-50 IF remediation cycle."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


SCAN_FILES = [
    "manuscript/SCI_MANUSCRIPT_V2_POLISHED.md",
    "manuscript/SCI_MANUSCRIPT_V2_POLISHED_claim_tracked.md",
    "manuscript/nature_methods_package/01_abstract.md",
    "manuscript/nature_methods_package/09_full_manuscript_draft.md",
]

RISK_PATTERNS = {
    "driver_language": re.compile(r"\b(driver|drives|driving)\b", re.IGNORECASE),
    "feedback_architecture": re.compile(r"\bfeedback architecture\b", re.IGNORECASE),
    "biological_frustration_architecture": re.compile(
        r"\bbiological frustration architecture\b",
        re.IGNORECASE,
    ),
    "main_mechanism": re.compile(r"\bmain mechanism\b", re.IGNORECASE),
    "clinical_or_therapeutic": re.compile(
        r"\b(clinical utility|therapeutic|treatment guidance|prognosis)\b",
        re.IGNORECASE,
    ),
    "unqualified_top_source": re.compile(r"\btop source\b(?!.*computational)", re.IGNORECASE),
}

BOUNDARY_TERMS = re.compile(
    r"\b(not|does not|do not|hypothesis-generating|computational|not as a confirmed|boundary)\b",
    re.IGNORECASE,
)


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def scan_claims(root: Path) -> pd.DataFrame:
    rows = []
    for rel in SCAN_FILES:
        path = root / rel
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for line_no, line in enumerate(lines, start=1):
            context = " ".join(lines[max(0, line_no - 2) : line_no])
            for pattern_id, pattern in RISK_PATTERNS.items():
                match = pattern.search(line)
                if not match:
                    continue
                has_boundary = bool(BOUNDARY_TERMS.search(context))
                rows.append(
                    {
                        "relative_path": rel,
                        "line_no": line_no,
                        "pattern_id": pattern_id,
                        "classification": "boundary_context" if has_boundary else "blocking_risky_claim",
                        "matched_text": match.group(0),
                        "line": line.strip(),
                        "required_action": (
                            "Keep only if explicitly framed as computational/hypothesis-generating."
                            if has_boundary
                            else "Downgrade or remove before 20-50 IF submission."
                        ),
                    }
                )
    return pd.DataFrame(rows)


def build_claim_hardening_outputs(root: Path, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    audit = scan_claims(root)
    audit_path = output_dir / "CLAIM_HARDENING_AUDIT.tsv"
    report_path = output_dir / "CLAIM_HARDENING_REPORT.md"
    audit.to_csv(audit_path, sep="\t", index=False)
    blocking = audit.loc[audit["classification"] == "blocking_risky_claim"] if not audit.empty else audit
    lines = [
        "# Claim Hardening Report",
        "",
        f"- Risk rows: {len(audit)}",
        f"- Blocking risky claims: {len(blocking)}",
        "- Boundary: real-data biology must remain computational and hypothesis-generating.",
        "",
        "## Blocking Rows",
        "",
    ]
    if blocking.empty:
        lines.append("None.")
    else:
        for row in blocking.to_dict(orient="records"):
            lines.append(
                f"- `{row['relative_path']}:{row['line_no']}` `{row['pattern_id']}`: "
                f"{row['line']}"
            )
    lines.append("")
    _write_text_atomic(report_path, "\n".join(lines))
    return {"audit": audit_path, "report": report_path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-dir", default="manuscript/claim_hardening")
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    paths = build_claim_hardening_outputs(root, root / args.output_dir)
    for path in paths.values():
        print(f"wrote {path}")
    audit = pd.read_csv(paths["audit"], sep="\t") if paths["audit"].exists() else pd.DataFrame()
    has_blocking = (
        not audit.empty and (audit["classification"].astype(str) == "blocking_risky_claim").any()
    )
    return 0 if args.report_only or not has_blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
