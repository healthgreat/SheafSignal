import zipfile

from scripts.package_external_beta_review_bundle import (
    OPTIONAL_FILES,
    REQUIRED_FILES,
    build_bundle_manifest,
    build_outputs,
    classify_decision,
    evidence_index_required_files,
)


def _write(path, text="- Decision: `ok`\n"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_bundle_blocks_when_required_file_missing(tmp_path):
    rows = build_bundle_manifest(tmp_path)

    assert classify_decision(rows) == "SHAREABLE_REVIEW_BUNDLE_BLOCKED_MISSING_REQUIRED_FILES"


def test_bundle_ready_and_archive_contains_required_files(tmp_path):
    for rel in REQUIRED_FILES:
        _write(tmp_path / rel)
    for rel in OPTIONAL_FILES[:2]:
        _write(tmp_path / rel)

    summary = build_outputs(tmp_path)
    archive = tmp_path / summary["archive"]

    assert summary["decision"] == "SHAREABLE_REVIEW_BUNDLE_READY"
    assert summary["missing_required"] == 0
    assert archive.exists()
    with zipfile.ZipFile(archive) as handle:
        names = set(handle.namelist())
    assert set(REQUIRED_FILES).issubset(names)
    assert "data/raw/example.h5ad" not in names


def test_bundle_includes_required_files_declared_by_evidence_index(tmp_path):
    for rel in REQUIRED_FILES:
        _write(tmp_path / rel)
    evidence_only = "manuscript/evidence_only_required.md"
    index = (
        tmp_path
        / "external_ai_review_packet"
        / "beta_review_packet_2026-05-02"
        / "02_EVIDENCE_FILE_INDEX.tsv"
    )
    _write(
        index,
        "category\tlabel\tpath\twhy\trequired\texists\tsize_bytes\tsha256\n"
        f"extra\tExtra evidence\t{evidence_only}\tNeeded\tyes\tyes\t1\tabc\n",
    )
    _write(tmp_path / evidence_only, "extra evidence\n")

    summary = build_outputs(tmp_path)

    assert evidence_index_required_files(tmp_path) == [evidence_only]
    assert summary["decision"] == "SHAREABLE_REVIEW_BUNDLE_READY"
    with zipfile.ZipFile(tmp_path / summary["archive"]) as handle:
        names = set(handle.namelist())
    assert evidence_only in names


def test_bundle_blocks_when_evidence_index_required_file_is_missing(tmp_path):
    for rel in REQUIRED_FILES:
        _write(tmp_path / rel)
    missing = "manuscript/missing_required_evidence.md"
    index = (
        tmp_path
        / "external_ai_review_packet"
        / "beta_review_packet_2026-05-02"
        / "02_EVIDENCE_FILE_INDEX.tsv"
    )
    _write(
        index,
        "category\tlabel\tpath\twhy\trequired\texists\tsize_bytes\tsha256\n"
        f"extra\tMissing evidence\t{missing}\tNeeded\tyes\tno\t0\tNA\n",
    )

    rows = build_bundle_manifest(tmp_path)

    assert classify_decision(rows) == "SHAREABLE_REVIEW_BUNDLE_BLOCKED_MISSING_REQUIRED_FILES"
    assert any(row.rel_path == missing and row.included == "no" for row in rows)


def test_bundle_no_archive_mode_writes_report_and_manifest(tmp_path):
    for rel in REQUIRED_FILES:
        _write(tmp_path / rel)

    summary = build_outputs(tmp_path, create_archive=False)

    assert summary["decision"] == "SHAREABLE_REVIEW_BUNDLE_READY"
    assert summary["archive"] == "not_created"
    assert (
        tmp_path
        / "external_ai_review_packet"
        / "shareable_review_bundle"
        / "SHAREABLE_REVIEW_BUNDLE_REPORT.md"
    ).exists()
