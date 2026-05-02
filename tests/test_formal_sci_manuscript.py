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


def _component_recovery() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "scenario": "gradient_chain",
                "gradient_ratio": 1.0,
                "curl_ratio": 0.0,
                "harmonic_ratio": 0.0,
            }
        ]
    )


def _public_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "dataset_id": "gse154778_pdac_scrna",
                "status": "completed",
                "modality": "scRNA-seq",
                "n_cell_types": 7,
                "n_edges": 42,
                "top_frustration_cell_type": "Myeloid",
                "total_sheaf_energy": 36.09,
            }
        ]
    )


def _myeloid_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "min_lesion_n_cells": 497,
                "min_lesion_n_samples": 6,
                "bootstrap_top_frequency": 1.0,
                "primary_frustration_score": 0.378,
                "metastatic_frustration_score": 0.811,
                "median_marker_score_margin": 0.355,
            }
        ]
    )


def _tool_comparison() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "dataset_id": "gse154778_pdac_scrna",
                "tool": "LIANA",
                "status": "completed_external_import",
                "spearman_sheaf_energy_vs_tool_score": 0.699,
            }
        ]
    )


def test_formal_manuscript_contains_required_sections_and_boundaries():
    script = _load_script("build_formal_sci_manuscript")

    manuscript = script.build_manuscript(
        component_recovery=_component_recovery(),
        public_summary=_public_summary(),
        myeloid_summary=_myeloid_summary(),
        tool_comparison=_tool_comparison(),
    )

    assert "## Introduction" in manuscript
    assert "## Results" in manuscript
    assert "## Methods" in manuscript
    assert "## Data Availability" in manuscript
    assert "497 cells" in manuscript
    assert "LIANA: 1 datasets" in manuscript
    assert "does not claim clinical" in manuscript
    assert "broad superiority" in manuscript


def test_claim_tracked_companion_maps_claim_ids():
    script = _load_script("build_formal_sci_manuscript")
    tracked = script.build_claim_tracked("# Draft\n")

    assert "C1: SheafSignal" in tracked
    assert "C6: External comparator evidence exists" in tracked
    assert "benchmarks/results/tool_comparison.csv" in tracked


def test_formal_manuscript_package_writes_expected_files(tmp_path):
    script = _load_script("build_formal_sci_manuscript")
    component = tmp_path / "component.csv"
    public = tmp_path / "public.csv"
    myeloid = tmp_path / "myeloid.csv"
    tools = tmp_path / "tools.csv"
    _component_recovery().to_csv(component, index=False)
    _public_summary().to_csv(public, index=False)
    _myeloid_summary().to_csv(myeloid, index=False)
    _tool_comparison().to_csv(tools, index=False)

    exit_code = script.main(
        [
            "--output-dir",
            str(tmp_path / "manuscript"),
            "--component-recovery",
            str(component),
            "--public-summary",
            str(public),
            "--myeloid-summary",
            str(myeloid),
            "--tool-comparison",
            str(tools),
        ]
    )

    assert exit_code == 0
    expected = set(script.OUTPUT_FILES.values())
    observed = {path.name for path in (tmp_path / "manuscript").iterdir()}
    assert expected.issubset(observed)
    assert not any(path.name.endswith(".tmp") for path in (tmp_path / "manuscript").iterdir())
