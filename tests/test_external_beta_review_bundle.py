import zipfile

from scripts.package_external_beta_review_bundle import (
    OPTIONAL_FILES,
    REQUIRED_FILES,
    build_bundle_manifest,
    build_outputs,
    classify_decision,
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
