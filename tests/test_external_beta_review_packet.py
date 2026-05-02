from pathlib import Path

import pandas as pd

from scripts.build_external_beta_review_packet import (
    CHECKLIST_ROWS,
    EVIDENCE_ITEMS,
    CHECKLIST_PATH,
    EVIDENCE_INDEX_PATH,
    SUMMARY_PATH,
    build_outputs,
    classify_packet,
)


def test_checklist_contains_core_reviewer_domains():
    areas = {row["review_area"] for row in CHECKLIST_ROWS}

    assert {"Methods", "SingleCell", "Statistics", "Reproducibility", "JournalFit"}.issubset(
        areas
    )
    assert any(row["priority"] == "fatal_if_failed" for row in CHECKLIST_ROWS)


def test_packet_blocks_when_required_evidence_is_missing():
    rows = [{"required": "yes", "exists": "no"}]

    assert classify_packet(rows) == "BETA_REVIEW_PACKET_BLOCKED_MISSING_REQUIRED_EVIDENCE"


def test_packet_ready_when_required_evidence_exists():
    rows = [{"required": "yes", "exists": "yes"}, {"required": "no", "exists": "no"}]

    assert classify_packet(rows) == "BETA_REVIEW_PACKET_READY_LOCAL_EXTERNAL_REVIEWS_PENDING"


def test_build_outputs_writes_packet_when_evidence_files_exist(tmp_path: Path):
    for item in EVIDENCE_ITEMS:
        path = tmp_path / item["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".tsv":
            path.write_text("col\nvalue\n", encoding="utf-8")
        else:
            path.write_text("- Decision: `fixture_decision`\n", encoding="utf-8")

    summary = build_outputs(tmp_path)

    assert summary["decision"] == "BETA_REVIEW_PACKET_READY_LOCAL_EXTERNAL_REVIEWS_PENDING"
    assert (tmp_path / SUMMARY_PATH).exists()
    assert (tmp_path / EVIDENCE_INDEX_PATH).exists()
    assert (tmp_path / CHECKLIST_PATH).exists()

    evidence = pd.read_csv(tmp_path / EVIDENCE_INDEX_PATH, sep="\t")
    checklist = pd.read_csv(tmp_path / CHECKLIST_PATH, sep="\t")
    assert evidence["exists"].eq("yes").all()
    assert "review_area" in checklist.columns
