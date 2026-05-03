import pandas as pd

from scripts.triage_external_beta_reviews import (
    build_action_matrix,
    classify_decision,
    collect_review_findings,
    collect_reviewer_metadata,
    parse_review_file,
    write_outputs,
)


def test_parse_markdown_review_classifies_fatal_and_domain(tmp_path):
    review = tmp_path / "reviewer_a.md"
    review.write_text(
        "- Reviewer: external_ai_a\n\n"
        "- Fatal concern: GitHub and Zenodo DOI are missing, so this is not ready.\n"
        "- Major concern: permutation FDR reporting must be clearer.\n",
        encoding="utf-8",
    )

    findings = parse_review_file(review)

    assert any(finding.severity == "fatal" for finding in findings)
    assert any(finding.domain == "reproducibility" for finding in findings)
    assert any(finding.domain == "statistics" for finding in findings)


def test_parse_tsv_review_preserves_structured_fields(tmp_path):
    review = tmp_path / "reviewer_b.tsv"
    review.write_text(
        "reviewer\tseverity\tdomain\tfinding\tsuggested_action\n"
        "expert1\tmajor\tmethods\tNovelty table must cite Hodge biology\tAdd citations\n",
        encoding="utf-8",
    )

    findings = parse_review_file(review)

    assert len(findings) == 1
    assert findings[0].reviewer == "expert1"
    assert findings[0].severity == "major"
    assert findings[0].domain == "methods"


def test_decision_prioritizes_fatal_then_major():
    assert classify_decision([]) == "EXTERNAL_BETA_REVIEW_NO_RETURNED_REVIEWS"
    fatal = pd.Series(
        {
            "source_file": "x",
            "reviewer": "r",
            "severity": "fatal",
            "domain": "reproducibility",
            "finding": "reject",
            "suggested_action": "fix",
            "blocks_20_50_if": "yes",
        }
    )
    from scripts.triage_external_beta_reviews import ReviewFinding

    finding = ReviewFinding(**fatal.to_dict())
    assert classify_decision([finding]) == "EXTERNAL_BETA_REVIEW_TRIAGED_FATAL_OR_REJECT_CONCERNS"


def test_collect_and_write_outputs(tmp_path):
    input_dir = tmp_path / "external_ai_review_packet" / "returned_reviews"
    input_dir.mkdir(parents=True)
    (input_dir / "README.md").write_text(
        "Do not place access tokens, private credentials, raw patient data, or non-public clinical material here.\n",
        encoding="utf-8",
    )
    (input_dir / "REVIEWER_METADATA_TEMPLATE.tsv").write_text(
        "reviewer_file\treviewer_model_name\n"
        "reviewer4_code_review.md\tTO_FILL\n",
        encoding="utf-8",
    )
    (input_dir / "review.md").write_text(
        "- Major concern: CellChat comparator scope must be described clearly.\n",
        encoding="utf-8",
    )

    findings = collect_review_findings(input_dir)
    outputs = write_outputs(tmp_path, findings, input_dir)
    matrix = build_action_matrix(findings)

    assert findings
    assert matrix[0]["priority"] == "P1"
    assert outputs["triage"].exists()
    assert outputs["action_matrix"].exists()
    assert outputs["reviewer_metadata"].exists()
    assert outputs["report"].exists()


def test_collect_reviewer_metadata_from_markdown(tmp_path):
    input_dir = tmp_path / "external_ai_review_packet" / "returned_reviews"
    input_dir.mkdir(parents=True)
    (input_dir / "reviewer4_code_review.md").write_text(
        "reviewer_model_name: ExternalAI\n"
        "reviewer_model_version: v1\n"
        "review_timestamp_with_timezone: 2026-05-04 08:00 +08:00\n"
        "claimed_training_data_cutoff: 2026-01\n"
        "external_references_consulted: none\n"
        "- Major concern: code path handling must be clearer.\n",
        encoding="utf-8",
    )

    rows = collect_reviewer_metadata(input_dir)

    assert len(rows) == 1
    assert rows[0].reviewer_model_name == "ExternalAI"
    assert rows[0].claimed_training_data_cutoff == "2026-01"
