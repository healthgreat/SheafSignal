#!/usr/bin/env python
"""Build a journal metric, CAS-zone, and warning-list audit for SheafSignal.

Author: SheafSignal contributors
Date: 2026-05-02
Purpose: keep 20-50 IF target selection tied to citable metric sources and
separate open-web evidence from CAS-zone/warning-list checks that require an
official institutional lookup before submission.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


OUTPUT_DIR = Path("manuscript/journal_metric_audit")
AUDIT_PATH = OUTPUT_DIR / "JOURNAL_METRIC_AUDIT.tsv"
REPORT_PATH = OUTPUT_DIR / "JOURNAL_METRIC_AUDIT_REPORT.md"


JOURNAL_ROWS = [
    {
        "priority": 1,
        "journal": "Nature Methods",
        "route_role": "primary_methods_target",
        "jif_2024": "32.1",
        "five_year_jif_2024": "51.7",
        "if20_50_status": "in_range_by_2year_jif; around_50_by_5year_jif",
        "metric_source_type": "publisher_official",
        "metric_source_url": "https://www.nature.com/nature-portfolio/about/journal-metrics",
        "metric_source_note": "Nature Portfolio 2024 journal metrics list Nature Methods JIF 32.1 and 5-year JIF 51.7.",
        "open_web_cas_zone_status": "third_party_suggests_cas_1q_top_but_not_officially_verified",
        "cas_zone_source_url": "https://www.ivysci.com/journals/1548-7091?lang=zh",
        "warning_list_status": "not_detected_in_accessible_2025_warning_list_mirrors",
        "warning_source_url": "https://kjc.ahau.edu.cn/info/1031/10329.htm",
        "final_submission_action": "Verify CAS zone and warning-list status on official CAS partition platform or institutional library on submission day.",
        "route_decision": "keep_primary",
    },
    {
        "priority": 2,
        "journal": "Nature Biotechnology",
        "route_role": "stretch_methods_platform_target",
        "jif_2024": "41.7",
        "five_year_jif_2024": "59.5",
        "if20_50_status": "in_range_by_2year_jif; above_50_by_5year_jif",
        "metric_source_type": "publisher_official",
        "metric_source_url": "https://www.nature.com/nbt/journal-impact",
        "metric_source_note": "Nature Biotechnology journal metrics page lists 2024 JIF 41.7 and 5-year JIF 59.5.",
        "open_web_cas_zone_status": "third_party_suggests_cas_1q_but_not_officially_verified",
        "cas_zone_source_url": "https://www.klxksci.com/sci/5062.html",
        "warning_list_status": "not_detected_in_accessible_2025_warning_list_mirrors",
        "warning_source_url": "https://kjc.ahau.edu.cn/info/1031/10329.htm",
        "final_submission_action": "Use only as stretch route unless package-platform breadth is stronger; verify CAS/warning status officially.",
        "route_decision": "stretch_only",
    },
    {
        "priority": 3,
        "journal": "Molecular Cancer",
        "route_role": "cancer_application_route",
        "jif_2024": "33.9",
        "five_year_jif_2024": "35.9",
        "if20_50_status": "in_range_by_2year_jif",
        "metric_source_type": "publisher_official",
        "metric_source_url": "https://molecular-cancer.biomedcentral.com/",
        "metric_source_note": "Molecular Cancer homepage lists 2024 JIF 33.9 and 5-year JIF 35.9.",
        "open_web_cas_zone_status": "third_party_suggests_cas_1q_but_not_officially_verified",
        "cas_zone_source_url": "https://www.1mishu.com/sci/842694.html",
        "warning_list_status": "not_detected_in_accessible_2025_warning_list_mirrors",
        "warning_source_url": "https://kjc.ahau.edu.cn/info/1031/10329.htm",
        "final_submission_action": "Use as cancer-route fallback only if manuscript gains stronger disease story; verify CAS/warning status officially.",
        "route_decision": "fallback_if_cancer_story_strengthens",
    },
    {
        "priority": 4,
        "journal": "Nature Cancer",
        "route_role": "cancer_biology_stretch_route",
        "jif_2024": "28.5",
        "five_year_jif_2024": "28.6",
        "if20_50_status": "in_range_by_2year_jif",
        "metric_source_type": "publisher_official",
        "metric_source_url": "https://www.nature.com/natcancer/journal-impact",
        "metric_source_note": "Nature Cancer journal metrics page lists 2024 JIF 28.5; Nature Portfolio metrics also list 5-year JIF 28.6.",
        "open_web_cas_zone_status": "third_party_suggests_cas_1q_top_but_not_officially_verified",
        "cas_zone_source_url": "https://www.klxksci.com/zixun/8384.html",
        "warning_list_status": "not_detected_in_accessible_2025_warning_list_mirrors",
        "warning_source_url": "https://kjc.ahau.edu.cn/info/1031/10329.htm",
        "final_submission_action": "Not primary unless biological validation is strengthened; verify CAS/warning status officially.",
        "route_decision": "stretch_only",
    },
    {
        "priority": 5,
        "journal": "Nature Biomedical Engineering",
        "route_role": "engineering_translation_route",
        "jif_2024": "26.6",
        "five_year_jif_2024": "30.4",
        "if20_50_status": "in_range_by_2year_jif",
        "metric_source_type": "publisher_official",
        "metric_source_url": "https://www.nature.com/natbiomedeng/journal-impact",
        "metric_source_note": "Nature Biomedical Engineering metrics page lists 2024 JIF 26.6 and 5-year JIF 30.4.",
        "open_web_cas_zone_status": "not_open_verified_in_this_audit",
        "cas_zone_source_url": "NA",
        "warning_list_status": "not_detected_in_accessible_2025_warning_list_mirrors",
        "warning_source_url": "https://kjc.ahau.edu.cn/info/1031/10329.htm",
        "final_submission_action": "Only consider if engineering/deployment angle is rewritten; verify CAS/warning status officially.",
        "route_decision": "fallback_only",
    },
    {
        "priority": 6,
        "journal": "Nature Machine Intelligence",
        "route_role": "computational_algorithm_stretch_route",
        "jif_2024": "23.9",
        "five_year_jif_2024": "31.8",
        "if20_50_status": "in_range_by_2year_jif",
        "metric_source_type": "publisher_official",
        "metric_source_url": "https://www.nature.com/nature-portfolio/about/journal-metrics",
        "metric_source_note": "Nature Portfolio metrics list Nature Machine Intelligence JIF 23.9 and 5-year JIF 31.8.",
        "open_web_cas_zone_status": "not_open_verified_in_this_audit",
        "cas_zone_source_url": "NA",
        "warning_list_status": "not_detected_in_accessible_2025_warning_list_mirrors",
        "warning_source_url": "https://kjc.ahau.edu.cn/info/1031/10329.htm",
        "final_submission_action": "Not recommended unless a real ML contribution is added; verify CAS/warning status officially if kept.",
        "route_decision": "not_recommended_currently",
    },
]


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_tsv_atomic(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    fieldnames = list(rows[0].keys()) if rows else ["journal"]
    with tmp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    tmp_path.replace(path)


def classify_decision(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "JOURNAL_METRIC_AUDIT_EMPTY"
    if any(row["metric_source_type"] != "publisher_official" for row in rows):
        return "JOURNAL_METRIC_AUDIT_HAS_NONPUBLISHER_METRICS"
    needs_final_check = False
    for row in rows:
        cas_status = str(row["open_web_cas_zone_status"])
        warning_status = str(row["warning_list_status"])
        cas_is_official = cas_status == "officially_verified_current_cas_zone"
        warning_is_official = warning_status == "official_current_warning_status_verified"
        if not cas_is_official or not warning_is_official:
            needs_final_check = True
            break
    if needs_final_check:
        return "JOURNAL_METRIC_AUDIT_IF_VERIFIED_CAS_WARNING_NEEDS_FINAL_CHECK"
    return "JOURNAL_METRIC_AUDIT_READY"


def build_report(rows: list[dict[str, object]]) -> str:
    decision = classify_decision(rows)
    target_lines = []
    for row in rows:
        target_lines.append(
            f"- {row['journal']}: JIF {row['jif_2024']}, 5-year JIF "
            f"{row['five_year_jif_2024']}, route `{row['route_decision']}`; "
            f"CAS/warning boundary `{row['open_web_cas_zone_status']}` / "
            f"`{row['warning_list_status']}`."
        )
    return "\n".join(
        [
            "# Journal Metric, CAS-Zone, And Warning-List Audit",
            "",
            f"- Decision: `{decision}`",
            "- Audit date: `2026-05-02`",
            "- Metric basis: 2024 Journal Impact Factor and 2024 5-year Journal Impact Factor.",
            "",
            "## Target Summary",
            "",
            *target_lines,
            "",
            "## Interpretation Boundary",
            "",
            "The impact-factor rows use publisher or Springer Nature official metric pages where available. "
            "The CAS-zone rows use open-web third-party hints only when listed; they are not a substitute "
            "for the official CAS partition platform or the user's institutional library. The warning-list "
            "status means the journal was not detected in accessible 2025 warning-list mirror pages checked "
            "during planning, but final submission must still verify the official/current warning-list source.",
            "",
            "## Submission-Day Required Action",
            "",
            "Before final journal selection, verify the selected journal's latest JIF, CAS zone, and warning-list "
            "status again. If the target changes, rerun this audit and update the cover letter and journal board.",
            "",
        ]
    )


def build_outputs(root: Path) -> dict[str, object]:
    rows = [dict(row) for row in JOURNAL_ROWS]
    _write_tsv_atomic(root / AUDIT_PATH, rows)
    _write_text_atomic(root / REPORT_PATH, build_report(rows))
    return {
        "decision": classify_decision(rows),
        "n_journals": len(rows),
        "audit_path": AUDIT_PATH.as_posix(),
        "report_path": REPORT_PATH.as_posix(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)

    summary = build_outputs(Path(args.root).resolve())
    print(summary["decision"])
    print(f"Journals: {summary['n_journals']}")
    print(f"Audit: {summary['audit_path']}")
    print(f"Report: {summary['report_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
