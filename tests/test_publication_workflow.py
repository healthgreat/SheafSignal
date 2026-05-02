from pathlib import Path
import importlib.util
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def _load_script(name: str):
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_publication_benchmark_scripts_write_standard_outputs(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(root)

    prepare = _load_script("prepare_public_datasets")
    benchmark = _load_script("run_tme_benchmark")
    figures = _load_script("make_publication_figures")

    results_dir = tmp_path / "benchmarks" / "results"
    figures_dir = tmp_path / "figures"
    figure_manifest = tmp_path / "manuscript" / "figure_manifest.tsv"

    assert prepare.main(["--include-demo", "--results-dir", str(results_dir)]) == 0
    assert benchmark.main(["--include-demo", "--results-dir", str(results_dir)]) == 0
    assert (
        figures.main(
            [
                "--results-dir",
                str(results_dir),
                "--figures-dir",
                str(figures_dir),
                "--manifest-out",
                str(figure_manifest),
            ]
        )
        == 0
    )

    expected = [
        results_dir / "component_recovery.csv",
        results_dir / "tool_comparison.csv",
        results_dir / "public_tme_sheafsignal_summary.csv",
        results_dir / "spatial_frustration_hotspots.csv",
        figures_dir / "publication_figure1_sheafsignal_concept.pdf",
        figures_dir / "publication_figure2_component_recovery.pdf",
        figures_dir / "publication_figure3_tme_summary.pdf",
        figures_dir / "publication_figure4_gse154778_claim_gating.pdf",
        figures_dir / "publication_figure5_comparator_alignment.pdf",
        figure_manifest,
    ]
    for path in expected:
        assert path.exists()

    summary = pd.read_csv(results_dir / "public_tme_sheafsignal_summary.csv")
    assert "demo_synthetic" in set(summary["dataset_id"])
    tool_table = pd.read_csv(results_dir / "tool_comparison.csv")
    tools = set(tool_table["tool"])
    assert {"CellChat", "NicheNet", "LIANA"}.issubset(tools)
    assert "LRProductBaseline" in tools

    baseline = tool_table.loc[
        (tool_table["dataset_id"] == "demo_synthetic")
        & (tool_table["tool"] == "LRProductBaseline")
    ].iloc[0]
    assert baseline["status"] == "completed"
    assert Path(baseline["aligned_edge_table"]).exists()
    manifest = pd.read_csv(figure_manifest, sep="\t")
    assert {
        "fig1_sheafsignal_concept",
        "fig2_component_recovery",
        "fig3_tme_summary",
        "fig4_gse154778_claim_gating",
        "fig5_comparator_alignment",
    }.issubset(set(manifest["figure_id"]))


def test_conda_environment_files_install_project_root_editable():
    root = Path(__file__).resolve().parents[1]
    for env_file in [
        root / "envs" / "environment.yml",
        root / "envs" / "liana_environment.yml",
    ]:
        text = env_file.read_text(encoding="utf-8")
        lines = [line.strip() for line in text.splitlines()]
        assert "- -e .." in text
        assert "- -e ." not in lines
