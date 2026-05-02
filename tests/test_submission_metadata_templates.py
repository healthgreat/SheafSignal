from pathlib import Path
import importlib.util

import pandas as pd


def _load_script(name: str):
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_submission_metadata_templates_have_required_author_columns():
    script = _load_script("build_submission_metadata_templates")
    authors = script.author_template()

    assert list(authors.columns) == script.AUTHOR_COLUMNS
    assert authors.loc[0, "status"] == "tbd_by_authors"
    assert "Methodology" in authors.loc[0, "credit_roles"]


def test_submission_metadata_template_builder_writes_files(tmp_path):
    script = _load_script("build_submission_metadata_templates")
    outputs = script.build_templates(
        tmp_path / "manuscript" / "submission_metadata",
        tmp_path / "release",
    )

    assert outputs["authors"].exists()
    assert outputs["github_release"].exists()
    checklist = pd.read_csv(outputs["metadata_checklist"], sep="\t")
    assert "competing_interests" in set(checklist["item"])
    assert "release/archives/sheafsignal_github_release.zip" in outputs[
        "github_release"
    ].read_text(encoding="utf-8")


def test_final_blocker_gate_marks_tbd_author_metadata_pending(tmp_path):
    templates = _load_script("build_submission_metadata_templates")
    gate = _load_script("check_final_submission_blockers")
    templates.build_templates(
        tmp_path / "manuscript" / "submission_metadata",
        tmp_path / "release",
    )

    rows = gate.check_submission_metadata(tmp_path)
    table = pd.DataFrame(rows)

    assert "author_metadata::authors" in set(table["blocker_id"])
    assert set(table["severity"]) == {"pending"}
