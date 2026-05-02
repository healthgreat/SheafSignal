#!/usr/bin/env python
"""Audit Nature Methods formatting readiness for SheafSignal drafts.

Author: SheafSignal contributors
Date: 2026-04-30
Purpose: convert Nature Methods/Nature Portfolio formatting expectations into
local, reproducible pre-submission checks.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


TITLE_MAX_CHARS = 75
ABSTRACT_MAX_WORDS = 150
MAIN_TEXT_MAX_WORDS = 3000
DISPLAY_ITEM_MAX = 6


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _word_count(text: str) -> int:
    clean = re.sub(r"`[^`]+`", " ", text)
    clean = re.sub(r"https?://\S+", " ", clean)
    clean = re.sub(r"[^A-Za-z0-9_+-]+", " ", clean)
    return len([token for token in clean.split() if token])


def _first_heading(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip()
    return ""


def _section_text_after_heading(text: str, heading: str) -> str:
    lines = text.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.strip().lower() == heading.lower():
            start = idx + 1
            break
    if start is None:
        return ""
    collected = []
    for line in lines[start:]:
        if line.startswith("#"):
            break
        collected.append(line)
    return "\n".join(collected).strip()


def _add_check(
    rows: list[dict[str, object]],
    *,
    check_id: str,
    status: str,
    observed: object,
    requirement: str,
    action: str,
) -> None:
    rows.append(
        {
            "check_id": check_id,
            "status": status,
            "observed": observed,
            "requirement": requirement,
            "action": action,
        }
    )


def build_format_audit(root: Path) -> pd.DataFrame:
    package = root / "manuscript/nature_methods_package"
    title_text = _read_text(package / "00_title_page.md")
    abstract_text = _read_text(package / "01_abstract.md")
    full_text = _read_text(package / "09_full_manuscript_draft.md")
    figure_plan = root / "manuscript/nature_methods_package/06_figure_plan.tsv"
    rows: list[dict[str, object]] = []

    title = _first_heading(title_text)
    _add_check(
        rows,
        check_id="title_length",
        status="pass" if 0 < len(title) <= TITLE_MAX_CHARS else "format_issue",
        observed=len(title),
        requirement=f"Nature title target <= {TITLE_MAX_CHARS} characters.",
        action="Shorten the title before final upload." if len(title) > TITLE_MAX_CHARS else "No action.",
    )

    abstract_body = _section_text_after_heading(abstract_text, "# Abstract Draft")
    abstract_body = abstract_body.split("Boundary:")[0].strip()
    abstract_words = _word_count(abstract_body)
    _add_check(
        rows,
        check_id="abstract_word_count",
        status="pass" if 0 < abstract_words <= ABSTRACT_MAX_WORDS else "format_issue",
        observed=abstract_words,
        requirement=f"Nature Methods Resource/Analysis abstract <= {ABSTRACT_MAX_WORDS} words.",
        action="Shorten abstract to <=150 words." if abstract_words > ABSTRACT_MAX_WORDS else "No action.",
    )

    main_without_abstract = re.sub(
        r"## Abstract.*?## Introduction",
        "## Introduction",
        full_text,
        flags=re.DOTALL,
    )
    main_words = _word_count(main_without_abstract)
    _add_check(
        rows,
        check_id="main_text_word_count",
        status="pass" if 0 < main_words <= MAIN_TEXT_MAX_WORDS else "format_issue",
        observed=main_words,
        requirement=f"Nature Methods Resource/Analysis main text target <= {MAIN_TEXT_MAX_WORDS} words.",
        action="Shorten main text." if main_words > MAIN_TEXT_MAX_WORDS else "No action.",
    )

    for check_id, phrase, action in [
        ("has_results", "## Results", "Add Results section."),
        ("has_discussion", "## Discussion", "Add Discussion section."),
        ("has_data_availability", "## Data Availability", "Add a separate Data Availability section."),
        ("has_code_availability", "## Code Availability", "Add a separate Code Availability section."),
    ]:
        present = phrase in full_text
        _add_check(
            rows,
            check_id=check_id,
            status="pass" if present else "format_issue",
            observed=present,
            requirement=f"Manuscript contains {phrase}.",
            action="No action." if present else action,
        )

    if figure_plan.exists():
        plan = pd.read_csv(figure_plan, sep="\t")
        display_items = int(plan["figure"].astype(str).str.startswith("Figure").sum())
    else:
        display_items = 0
    _add_check(
        rows,
        check_id="display_item_count",
        status="pass" if 0 < display_items <= DISPLAY_ITEM_MAX else "format_issue",
        observed=display_items,
        requirement=f"Nature Methods Resource/Analysis display items <= {DISPLAY_ITEM_MAX}.",
        action="Reduce planned main display items." if display_items > DISPLAY_ITEM_MAX else "No action.",
    )

    for check_id, rel, action in [
        (
            "has_author_metadata_template",
            "manuscript/submission_metadata/AUTHOR_METADATA_TEMPLATE.tsv",
            "Generate and fill author metadata.",
        ),
        (
            "has_competing_interests_template",
            "manuscript/submission_metadata/COMPETING_INTERESTS_TEMPLATE.md",
            "Generate and fill competing interests.",
        ),
        (
            "has_reporting_boundary",
            "manuscript/nature_methods_package/08_claim_boundaries_and_limitations.md",
            "Generate claim-boundary file.",
        ),
    ]:
        exists = (root / rel).exists()
        _add_check(
            rows,
            check_id=check_id,
            status="pass" if exists else "format_issue",
            observed=exists,
            requirement=f"Required local submission-support file exists: {rel}.",
            action="No action." if exists else action,
        )

    return pd.DataFrame(rows)


def build_report(audit: pd.DataFrame) -> str:
    issues = audit.loc[audit["status"] != "pass"]
    decision = "FORMAT_PENDING" if not issues.empty else "FORMAT_LOCALLY_READY"
    lines = [
        "# Nature Methods Format Audit Report",
        "",
        f"Decision: `{decision}`",
        "",
        f"- Checks passed: {int((audit['status'] == 'pass').sum())}",
        f"- Format issues: {len(issues)}",
        "",
        "## Issues",
        "",
    ]
    if issues.empty:
        lines.append("None.")
    else:
        for row in issues.to_dict(orient="records"):
            lines.append(
                f"- `{row['check_id']}` observed `{row['observed']}`. "
                f"Requirement: {row['requirement']} Action: {row['action']}"
            )
    lines.extend(
        [
            "",
            "## Source Basis",
            "",
            "- Nature Methods content-type guidance: Resource/Analysis abstract up to 150 words, main text around 3,000 words, and up to 6 display items.",
            "- Nature Portfolio formatting guidance: include Methods plus separate Data Availability and Code Availability statements.",
            "",
            "This audit is a local pre-submission check and does not guarantee acceptance.",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--audit-out", default="manuscript/NATURE_METHODS_FORMAT_AUDIT.tsv")
    parser.add_argument("--report-out", default="manuscript/NATURE_METHODS_FORMAT_AUDIT_REPORT.md")
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    audit = build_format_audit(root)
    audit_out = root / args.audit_out
    report_out = root / args.report_out
    audit_out.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(audit_out, sep="\t", index=False)
    _write_text_atomic(report_out, build_report(audit))
    print(f"wrote {audit_out}")
    print(f"wrote {report_out}")

    has_issues = bool((audit["status"] != "pass").any())
    if has_issues and not args.report_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
