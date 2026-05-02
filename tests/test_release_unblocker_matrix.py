from pathlib import Path
import importlib.util


def _load_script(name: str):
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_unblocker_flags_pending_zenodo(tmp_path):
    script = _load_script("build_release_unblocker_matrix")
    (tmp_path / "metadata").mkdir()
    (tmp_path / "release").mkdir()
    (tmp_path / "metadata" / "datasets.tsv").write_text(
        "dataset_id\tbenchmark_role\tzenodo_doi\n"
        "gse154778\tpublic_scrna_benchmark\tPENDING_ZENODO_RELEASE\n",
        encoding="utf-8",
    )
    (tmp_path / "release" / "DATA_AVAILABILITY_STATEMENT_DRAFT.md").write_text(
        "Current DOI status: `PENDING_ZENODO_RELEASE`.\n",
        encoding="utf-8",
    )

    rows = script.build_unblocker_rows(tmp_path)
    by_id = {row["gate_id"]: row for row in rows}

    assert by_id["G04_zenodo_doi"]["current_status"] == "blocking_pending"
    assert by_id["G02_public_github_repo"]["current_status"] == "pending_no_origin_remote"


def test_release_unblocker_writes_matrix_and_runbook(tmp_path):
    script = _load_script("build_release_unblocker_matrix")
    (tmp_path / "metadata").mkdir()
    (tmp_path / "release").mkdir()
    (tmp_path / "metadata" / "datasets.tsv").write_text(
        "dataset_id\tbenchmark_role\tzenodo_doi\n"
        "demo\tdemo\tNA\n",
        encoding="utf-8",
    )
    (tmp_path / "release" / "DATA_AVAILABILITY_STATEMENT_DRAFT.md").write_text(
        "Current DOI status: `https://doi.org/10.5281/zenodo.123`.\n",
        encoding="utf-8",
    )

    outputs = script.build_release_unblocker_outputs(tmp_path)

    matrix = outputs["matrix"].read_text(encoding="utf-8")
    runbook = outputs["runbook"].read_text(encoding="utf-8")
    assert "G01_github_auth" in matrix
    assert "RELEASE_NOT_READY_UNTIL_GITHUB_ZENODO_AUTHOR_CONFIRMATION" in runbook
    assert "gantt" in runbook
    assert "does not guarantee acceptance" in runbook


def test_release_unblocker_reads_author_confirmation_preflight(tmp_path):
    script = _load_script("build_release_unblocker_matrix")
    (tmp_path / "metadata").mkdir()
    (tmp_path / "release").mkdir()
    preflight = tmp_path / "manuscript" / "submission_metadata"
    preflight.mkdir(parents=True)
    (tmp_path / "metadata" / "datasets.tsv").write_text(
        "dataset_id\tbenchmark_role\tzenodo_doi\n"
        "demo\tdemo\tNA\n",
        encoding="utf-8",
    )
    (tmp_path / "release" / "DATA_AVAILABILITY_STATEMENT_DRAFT.md").write_text(
        "Current DOI status: `https://doi.org/10.5281/zenodo.123`.\n",
        encoding="utf-8",
    )
    (preflight / "AUTHOR_CONFIRMATION_PREFLIGHT_REPORT.md").write_text(
        "# Author Confirmation Preflight Report\n\n"
        "- Decision: `AUTHOR_CONFIRMATION_BLOCKED`\n",
        encoding="utf-8",
    )

    rows = script.build_unblocker_rows(tmp_path)
    by_id = {row["gate_id"]: row for row in rows}

    assert by_id["G07_author_confirmation"]["current_status"] == (
        "AUTHOR_CONFIRMATION_BLOCKED"
    )
