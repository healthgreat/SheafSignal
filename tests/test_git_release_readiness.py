from scripts.check_git_release_readiness import (
    GitSnapshot,
    build_audit_rows,
    build_report,
    classify_release_state,
)


def _snapshot(**overrides):
    base = {
        "has_commit": True,
        "branch": "codex/sheafsignal-hardening-release",
        "remote_count": 1,
        "exact_tag": "v0.1.0-hardening",
        "dirty_paths": tuple(),
        "file_scope": (("README.md", 1024),),
        "oversized_files": tuple(),
    }
    base.update(overrides)
    return GitSnapshot(**base)


def test_no_commit_blocks_release():
    decision, gate_status = classify_release_state(_snapshot(has_commit=False))

    assert decision == "GIT_RELEASE_BLOCKED_NO_COMMIT"
    assert gate_status == "red"


def test_local_commit_without_remote_is_yellow_freeze_candidate():
    decision, gate_status = classify_release_state(
        _snapshot(remote_count=0, exact_tag="")
    )

    assert decision == "GIT_RELEASE_LOCAL_FREEZE_PASS_PUBLIC_REMOTE_PENDING"
    assert gate_status == "yellow"


def test_oversized_file_blocks_even_with_remote_and_tag():
    decision, gate_status = classify_release_state(
        _snapshot(
            file_scope=(("large.csv", 25 * 1024 * 1024),),
            oversized_files=(("large.csv", 25 * 1024 * 1024),),
        )
    )

    assert decision == "GIT_RELEASE_BLOCKED_FILE_SCOPE"
    assert gate_status == "red"


def test_audit_rows_include_g11_decision():
    rows = build_audit_rows(_snapshot(remote_count=0, exact_tag=""), max_mb=20.0)

    decision_rows = [row for row in rows if row["check_id"] == "g11_decision"]
    assert len(decision_rows) == 1
    assert decision_rows[0]["status"] == "yellow"
    assert "PUBLIC_REMOTE_PENDING" in decision_rows[0]["evidence"]


def test_report_documents_boundary_between_commit_and_public_release():
    report = build_report(_snapshot(remote_count=0, exact_tag=""), max_mb=20.0)

    assert "A local freeze commit is a reproducibility milestone" in report
    assert "Zenodo DOI minting remains intentionally held" in report
