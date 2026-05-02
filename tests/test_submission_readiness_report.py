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


def test_submission_report_summarizes_gates_comparators_and_archives():
    script = _load_script("build_submission_readiness_report")
    gates = pd.DataFrame(
        [
            {
                "gate_id": "G10",
                "current_status": "zenodo_ready_no_doi",
                "claim_allowed_now": "Release manifests exist.",
                "remaining_action": "Mint DOI.",
            },
            {
                "gate_id": "G12",
                "current_status": "near_ready_pending_doi",
                "claim_allowed_now": "20-50 route plausible.",
                "remaining_action": "Freeze submission package.",
            },
        ]
    )
    tool_comparison = pd.DataFrame(
        [
            {
                "tool": "LIANA",
                "dataset_id": "gse154778_pdac_scrna",
                "status": "completed_full_import",
                "spearman_sheaf_energy_vs_tool_score": 0.69,
            },
            {
                "tool": "NicheNet",
                "dataset_id": "gse154778_pdac_scrna",
                "status": "completed",
                "spearman_sheaf_energy_vs_tool_score": 0.75,
            },
        ]
    )
    archive_manifest = pd.DataFrame(
        [
            {
                "archive_target": "github",
                "archive_path": "release/archives/sheafsignal_github_release.zip",
                "size_mb": 1.234,
                "sha256": "a" * 64,
            }
        ]
    )

    report = script.build_report(
        gates=gates,
        tool_comparison=tool_comparison,
        archive_manifest=archive_manifest,
    )

    assert "Local readiness: `near_ready_pending_doi`" in report
    assert "Reproducibility release status: `zenodo_ready_no_doi`" in report
    assert "`LIANA`: completed for 1 datasets" in report
    assert "`NicheNet`: completed for 1 datasets" in report
    assert "Do not guarantee acceptance in any journal." in report
    assert "Zenodo DOI is still required before submission" in report
    assert "release/archive_manifest.tsv" in report
    assert "Post-decision response and transfer package" in report
    assert "manuscript/response_transfer/" in report
    assert "Figure legends and source map package" in report
    assert "manuscript/figure_legends/" in report
    assert "Main figure quality audit" in report
    assert "check_main_figure_quality.py" in report
    assert "Supplementary artifact audit" in report
    assert "check_supplementary_artifacts.py" in report
    assert "Benchmark result contract audit" in report
    assert "check_benchmark_result_contracts.py" in report
    assert "Submission provenance audit" in report
    assert "check_submission_provenance.py" in report
    assert "Method reporting and reviewer-risk audit" in report
    assert "check_method_reporting_readiness.py" in report
    assert "Manuscript-wide claim safety audit" in report
    assert "check_claim_safety.py" in report
    assert "Formal SCI manuscript v1" in report
    assert "SCI_MANUSCRIPT_V1_claim_tracked.md" in report
    assert "Verified reference package" in report
    assert "SCI_REFERENCE_GAP_REPORT.md" in report
    assert "Polished SCI manuscript v2" in report
    assert "SCI_MANUSCRIPT_V2_POLISHED_claim_tracked.md" in report
    assert "Submission upload package" in report
    assert "build_submission_upload_package.py" in report


def test_submission_report_main_writes_output_atomically(tmp_path):
    script = _load_script("build_submission_readiness_report")
    gates = tmp_path / "gates.tsv"
    tools = tmp_path / "tool_comparison.csv"
    archives = tmp_path / "archive_manifest.tsv"
    output = tmp_path / "manuscript" / "SUBMISSION_READINESS_REPORT.md"
    pd.DataFrame(
        [
            {
                "gate_id": "G12",
                "current_status": "near_ready_pending_doi",
                "claim_allowed_now": "Route plausible.",
                "remaining_action": "Mint DOI.",
            }
        ]
    ).to_csv(gates, sep="\t", index=False)
    pd.DataFrame(
        [
            {
                "tool": "MechanisticTargetPrior",
                "dataset_id": "demo",
                "status": "completed",
                "spearman_sheaf_energy_vs_tool_score": 0.5,
            }
        ]
    ).to_csv(tools, index=False)
    pd.DataFrame(
        [
            {
                "archive_target": "zenodo",
                "archive_path": "release/archives/sheafsignal_zenodo_upload.zip",
                "size_mb": 2.0,
                "sha256": "b" * 64,
            }
        ]
    ).to_csv(archives, sep="\t", index=False)

    exit_code = script.main(
        [
            "--gates",
            str(gates),
            "--tool-comparison",
            str(tools),
            "--archive-manifest",
            str(archives),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert output.exists()
    assert not output.with_suffix(output.suffix + ".tmp").exists()
    text = output.read_text(encoding="utf-8")
    assert "MechanisticTargetPrior" in text
    assert "sheafsignal_zenodo_upload.zip" in text
