from pathlib import Path
import importlib.util

import pandas as pd


def _load_script():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "check_visium_scope_gate.py"
    spec = importlib.util.spec_from_file_location("check_visium_scope_gate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_required_visium_outputs(root: Path) -> None:
    spatial = root / "benchmarks" / "results" / "tenx_breast_visium" / "spatial"
    qc = spatial / "qc"
    qc.mkdir(parents=True)
    pd.DataFrame([{"spot_id": "s1", "frustration_score": 0.1}]).to_csv(
        spatial / "spatial_frustration_hotspots.csv",
        index=False,
    )
    pd.DataFrame([{"dataset_id": "tenx_breast_visium", "status": "completed"}]).to_csv(
        spatial / "spatial_hotspot_summary.csv",
        index=False,
    )
    pd.DataFrame([{"marker_program": "Tumor", "n_spots": 10}]).to_csv(
        qc / "marker_spot_counts.csv",
        index=False,
    )
    pd.DataFrame(
        [
            {
                "k_neighbors": 4,
                "spearman_with_reference": 0.93,
                "top_50_overlap_with_reference": 0.86,
            }
        ]
    ).to_csv(qc / "k_neighbors_sensitivity.csv", index=False)
    pd.DataFrame(
        [
            {
                "dataset_id": "tenx_breast_visium",
                "min_spearman_across_k": 0.93,
                "min_top_50_overlap_across_k": 0.86,
                "interpretation_warning": (
                    "marker-dominant Visium spot programs; use as spatial hotspot "
                    "QC context, not as single-cell-level cell type proof"
                ),
            }
        ]
    ).to_csv(qc / "spatial_hotspot_qc_summary.csv", index=False)


def test_visium_scope_gate_flags_top_source_overclaim(tmp_path):
    script = _load_script()
    _write_required_visium_outputs(tmp_path)
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "draft.md").write_text(
        "tenx_breast_visium is Visium spatial transcriptomics with top source T/NK.\n",
        encoding="utf-8",
    )

    audit = script.build_visium_scope_audit(tmp_path)
    failures = audit.loc[audit["status"] == "fail"]

    assert "text_scope::visium_top_source" in set(failures["check_id"])


def test_visium_scope_gate_passes_hotspot_boundary_language(tmp_path):
    script = _load_script()
    _write_required_visium_outputs(tmp_path)
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "draft.md").write_text(
        "Visium is used as a spot-level hotspot workflow demonstration, not as a "
        "histology-confirmed single-cell mechanism.\n",
        encoding="utf-8",
    )

    audit = script.build_visium_scope_audit(tmp_path)
    report = script.build_visium_scope_report(audit)

    assert "fail" not in set(audit["status"])
    assert "VISIUM_SCOPE_PASS_HOTSPOT_ONLY" in report


def test_visium_scope_main_writes_outputs(tmp_path):
    script = _load_script()
    _write_required_visium_outputs(tmp_path)
    (tmp_path / "manuscript").mkdir()

    exit_code = script.main(["--root", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / "manuscript" / "visium_scope" / "VISIUM_SCOPE_AUDIT.tsv").exists()
    assert (tmp_path / "manuscript" / "visium_scope" / "VISIUM_SCOPE_REPORT.md").exists()
