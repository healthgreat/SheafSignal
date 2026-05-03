import zipfile

from scripts.package_external_code_review_bundle import (
    build_outputs,
    classify_decision,
    collect_source_files,
)


def _write(path, text="x\n"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_source_bundle_requires_source_and_tests(tmp_path):
    _write(tmp_path / "README.md")
    _write(tmp_path / "pyproject.toml")

    summary = build_outputs(tmp_path, create_archive=False)

    assert summary["decision"] == "SOURCE_CODE_REVIEW_BUNDLE_BLOCKED_MISSING_SOURCE_OR_TESTS"


def test_source_bundle_includes_code_and_excludes_data(tmp_path):
    for rel in ["README.md", "pyproject.toml", "Dockerfile", "Makefile", "LICENSE"]:
        _write(tmp_path / rel)
    _write(tmp_path / "src" / "sheafsignal" / "core.py")
    _write(tmp_path / "scripts" / "run.py")
    _write(tmp_path / "tests" / "test_core.py")
    _write(tmp_path / "data" / "raw" / "secret.csv")
    _write(tmp_path / "release" / "archives" / "large.zip")

    rows = collect_source_files(tmp_path)
    rels = {path.relative_to(tmp_path).as_posix() for path in rows}

    assert "src/sheafsignal/core.py" in rels
    assert "tests/test_core.py" in rels
    assert "data/raw/secret.csv" not in rels
    assert "release/archives/large.zip" not in rels

    summary = build_outputs(tmp_path)
    assert summary["decision"] == "SOURCE_CODE_REVIEW_BUNDLE_READY"
    archive = tmp_path / summary["archive"]
    with zipfile.ZipFile(archive) as handle:
        names = set(handle.namelist())
    assert "src/sheafsignal/core.py" in names
    assert "data/raw/secret.csv" not in names


def test_classify_ready_with_minimal_source_and_tests(tmp_path):
    for rel in ["README.md", "pyproject.toml", "Dockerfile"]:
        _write(tmp_path / rel)
    _write(tmp_path / "src" / "pkg" / "a.py")
    _write(tmp_path / "tests" / "test_a.py")

    from scripts.package_external_code_review_bundle import build_manifest

    assert classify_decision(build_manifest(tmp_path)) == "SOURCE_CODE_REVIEW_BUNDLE_READY"
