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
            },
            {
                "scenario": "triangle_curl",
                "gradient_ratio": 0.0,
                "curl_ratio": 1.0,
                "harmonic_ratio": 0.0,
            },
        ]
    )


def _public_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "dataset_id": "gse154778_pdac_scrna",
                "status": "completed",
                "n_cell_types": 7,
                "n_edges": 42,
                "top_frustration_cell_type": "Myeloid",
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
                "primary_frustration_score": 0.38,
                "metastatic_frustration_score": 0.81,
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
                "spearman_sheaf_energy_vs_tool_score": 0.7,
            },
            {
                "dataset_id": "gse154778_pdac_scrna",
                "tool": "NicheNet",
                "status": "completed_external_import",
                "spearman_sheaf_energy_vs_tool_score": 0.75,
            },
        ]
    )


def test_main_legends_use_existing_numbers_and_boundaries():
    script = _load_script("build_figure_legend_package")

    text = script.build_main_legends(
        component_recovery=_component_recovery(),
        public_summary=_public_summary(),
        myeloid_summary=_myeloid_summary(),
        tool_comparison=_tool_comparison(),
    )

    assert "gradient_chain: gradient 1.000" in text
    assert "gse154778_pdac_scrna with 7 cell-type states, 42 edges" in text
    assert "min lesion support of 497 cells and 6 samples" in text
    assert "LIANA: 1 datasets, Spearman 0.700-0.700" in text
    assert "must not be captioned as broad superiority" in text


def test_source_map_preserves_claim_boundaries():
    script = _load_script("build_figure_legend_package")

    source_map = script.build_source_map()
    fig5 = source_map.loc[source_map["display_item"] == "Figure 5"].iloc[0]
    fig4 = source_map.loc[source_map["display_item"] == "Figure 4"].iloc[0]

    assert fig5["claim_ids"] == "C6"
    assert "broad superiority" in fig5["boundary"]
    assert "Sparse categories remain supplement/QC" in fig4["boundary"]
    assert {"display_item", "claim_ids", "source_files", "boundary"}.issubset(source_map.columns)


def test_figure_legend_package_writes_expected_files(tmp_path):
    script = _load_script("build_figure_legend_package")
    figure_plan = tmp_path / "figure_plan.tsv"
    figure_manifest = tmp_path / "figure_manifest.tsv"
    component = tmp_path / "component.csv"
    public = tmp_path / "public.csv"
    myeloid = tmp_path / "myeloid.csv"
    tools = tmp_path / "tools.csv"

    pd.DataFrame(
        [
            {
                "figure": "Figure 1",
                "purpose": "SheafSignal concept",
                "source": "src/sheafsignal",
                "status": "planned",
            }
        ]
    ).to_csv(figure_plan, sep="\t", index=False)
    pd.DataFrame(
        [
            {
                "figure_id": "fig1_component_recovery",
                "path": "figures/publication_figure_component_recovery.pdf",
                "source_results_dir": "benchmarks/results",
            },
            {
                "figure_id": "supp_qc",
                "path": "benchmarks/results/qc.pdf",
                "source_results_dir": "benchmarks/results",
            },
        ]
    ).to_csv(figure_manifest, sep="\t", index=False)
    _component_recovery().to_csv(component, index=False)
    _public_summary().to_csv(public, index=False)
    _myeloid_summary().to_csv(myeloid, index=False)
    _tool_comparison().to_csv(tools, index=False)

    out_dir = tmp_path / "manuscript" / "figure_legends"
    exit_code = script.main(
        [
            "--output-dir",
            str(out_dir),
            "--figure-plan",
            str(figure_plan),
            "--figure-manifest",
            str(figure_manifest),
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
    observed = {path.name for path in out_dir.iterdir()}
    assert expected.issubset(observed)
    assert not any(path.name.endswith(".tmp") for path in out_dir.iterdir())
    source_map = pd.read_csv(out_dir / "03_figure_source_map.tsv", sep="\t")
    assert "Figure 1" in set(source_map["display_item"])
