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


def _write_minimal_package(root: Path) -> None:
    package = root / "manuscript" / "nature_methods_package"
    metadata = root / "manuscript" / "submission_metadata"
    package.mkdir(parents=True)
    metadata.mkdir(parents=True)
    (package / "00_title_page.md").write_text(
        "# SheafSignal maps frustration in cell communication networks\n",
        encoding="utf-8",
    )
    (package / "01_abstract.md").write_text(
        "# Abstract Draft\n\n"
        "SheafSignal maps communication frustration with Hodge decomposition.\n",
        encoding="utf-8",
    )
    (package / "09_full_manuscript_draft.md").write_text(
        "# Full Manuscript Draft\n\n"
        "## Introduction\n\nText.\n\n"
        "## Results\n\nText.\n\n"
        "## Discussion\n\nText.\n\n"
        "## Data Availability\n\nText.\n\n"
        "## Code Availability\n\nText.\n",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {"figure": "Figure 1", "purpose": "x"},
            {"figure": "Figure 2", "purpose": "x"},
        ]
    ).to_csv(package / "06_figure_plan.tsv", sep="\t", index=False)
    (package / "08_claim_boundaries_and_limitations.md").write_text(
        "boundaries\n",
        encoding="utf-8",
    )
    (metadata / "AUTHOR_METADATA_TEMPLATE.tsv").write_text("author\nTBD\n", encoding="utf-8")
    (metadata / "COMPETING_INTERESTS_TEMPLATE.md").write_text("TBD\n", encoding="utf-8")


def test_nature_methods_format_audit_passes_minimal_package(tmp_path):
    script = _load_script("check_nature_methods_format")
    _write_minimal_package(tmp_path)

    audit = script.build_format_audit(tmp_path)

    assert set(audit["status"]) == {"pass"}
    assert audit.loc[audit["check_id"] == "title_length", "observed"].iloc[0] <= 75
    assert audit.loc[audit["check_id"] == "abstract_word_count", "observed"].iloc[0] <= 150


def test_nature_methods_format_audit_flags_long_title_and_missing_code(tmp_path):
    script = _load_script("check_nature_methods_format")
    _write_minimal_package(tmp_path)
    package = tmp_path / "manuscript" / "nature_methods_package"
    (package / "00_title_page.md").write_text("# " + "A" * 80 + "\n", encoding="utf-8")
    text = (package / "09_full_manuscript_draft.md").read_text(encoding="utf-8")
    (package / "09_full_manuscript_draft.md").write_text(
        text.replace("## Code Availability\n\nText.\n", ""),
        encoding="utf-8",
    )

    audit = script.build_format_audit(tmp_path)
    issues = set(audit.loc[audit["status"] != "pass", "check_id"])

    assert "title_length" in issues
    assert "has_code_availability" in issues


def test_nature_methods_format_audit_main_writes_outputs(tmp_path):
    script = _load_script("check_nature_methods_format")
    _write_minimal_package(tmp_path)

    exit_code = script.main(["--root", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / "manuscript" / "NATURE_METHODS_FORMAT_AUDIT.tsv").exists()
    report = tmp_path / "manuscript" / "NATURE_METHODS_FORMAT_AUDIT_REPORT.md"
    assert "FORMAT_LOCALLY_READY" in report.read_text(encoding="utf-8")
