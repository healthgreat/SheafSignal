from scripts.check_release_metadata_placeholders import (
    PlaceholderHit,
    classify_decision,
    classify_placeholder,
)


def test_pending_zenodo_release_is_blocking_identifier():
    category, severity, action = classify_placeholder(
        "metadata/datasets.tsv",
        "gse154778\tPENDING_ZENODO_RELEASE",
        "PENDING_ZENODO_RELEASE",
    )

    assert category == "zenodo_doi_pending"
    assert severity == "blocking"
    assert "Zenodo DOI" in action


def test_github_tbd_is_blocking_identifier():
    category, severity, action = classify_placeholder(
        "CITATION.cff",
        'repository-code: "https://github.com/TBD/SheafSignal"',
        "github.com/TBD",
    )

    assert category == "github_url_pending"
    assert severity == "blocking"
    assert "GitHub" in action


def test_submission_templates_are_author_owned_pending():
    category, severity, action = classify_placeholder(
        "manuscript/submission_metadata/AUTHOR_METADATA_TEMPLATE.tsv",
        "author_name\tTBD",
        "TBD",
    )

    assert category == "author_owned_submission_metadata"
    assert severity == "pending_author"
    assert "Authors" in action


def test_decision_blocks_on_external_identifiers():
    hits = [
        PlaceholderHit(
            file="metadata/datasets.tsv",
            line=1,
            token="PENDING_ZENODO_RELEASE",
            category="zenodo_doi_pending",
            severity="blocking",
            evidence="PENDING_ZENODO_RELEASE",
            required_action="Mint DOI.",
        )
    ]

    assert classify_decision(hits) == "RELEASE_METADATA_BLOCKED_EXTERNAL_IDENTIFIERS"


def test_decision_allows_author_pending_when_no_external_identifier_blockers():
    hits = [
        PlaceholderHit(
            file="manuscript/submission_metadata/AUTHOR_METADATA_TEMPLATE.tsv",
            line=1,
            token="TBD",
            category="author_owned_submission_metadata",
            severity="pending_author",
            evidence="TBD",
            required_action="Authors must fill.",
        )
    ]

    assert classify_decision(hits) == "RELEASE_METADATA_AUTHOR_FIELDS_PENDING"
