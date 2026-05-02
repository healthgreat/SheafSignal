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


def _fixture_tables():
    public_summary = pd.DataFrame(
        [
            {
                "dataset_id": "gse154778_pdac_scrna",
                "modality": "scRNA-seq",
                "status": "completed",
                "top_frustration_cell_type": "Myeloid",
            },
            {
                "dataset_id": "demo_synthetic",
                "modality": "synthetic",
                "status": "completed",
                "top_frustration_cell_type": "Tumor",
            },
        ]
    )
    component_recovery = pd.DataFrame(
        [
            {
                "scenario": "triangle_curl",
                "gradient_ratio": 0.0,
                "curl_ratio": 1.0,
                "harmonic_ratio": 0.0,
            }
        ]
    )
    tool_comparison = pd.DataFrame(
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
    gates = pd.DataFrame(
        [
            {"gate_id": "G1", "current_status": "pass"},
            {"gate_id": "G2", "current_status": "pass"},
            {"gate_id": "G4", "current_status": "pass"},
            {"gate_id": "G10", "current_status": "zenodo_ready_no_doi"},
        ]
    )
    return public_summary, component_recovery, tool_comparison, gates


def test_submission_package_claim_map_preserves_boundaries():
    script = _load_script("build_nature_methods_submission_package")
    public_summary, _, tool_comparison, gates = _fixture_tables()
    claim_map = script.build_claim_evidence_map(public_summary, tool_comparison, gates)

    assert "main_text_allowed_with_boundary" in set(claim_map["manuscript_use"])
    assert claim_map["boundary"].str.contains("Do not").any()
    sparse = claim_map.loc[claim_map["claim_id"] == "C5"].iloc[0]
    assert sparse["manuscript_use"] == "supplement_qc_only"


def test_submission_package_text_does_not_guarantee_publication():
    script = _load_script("build_nature_methods_submission_package")
    public_summary, component_recovery, tool_comparison, _ = _fixture_tables()
    abstract = script.build_abstract(public_summary, tool_comparison)
    main_text = script.build_main_text_skeleton(
        public_summary,
        component_recovery,
        tool_comparison,
    )
    limitations = script.build_limitations()
    full_manuscript = script.build_full_manuscript_draft(
        public_summary,
        component_recovery,
        tool_comparison,
    )

    combined = "\n".join([abstract, main_text, limitations, full_manuscript])
    assert "Guaranteed acceptance" in combined or "guaranteed" in combined.lower()
    assert "clinical" in combined.lower()
    assert "project-curated" in combined
    assert "context-specific" in combined
    assert "must not claim broad superiority" in combined


def test_submission_package_main_writes_expected_files(tmp_path):
    script = _load_script("build_nature_methods_submission_package")
    public_summary, component_recovery, tool_comparison, gates = _fixture_tables()
    public_path = tmp_path / "public.csv"
    component_path = tmp_path / "component.csv"
    tool_path = tmp_path / "tool.csv"
    gates_path = tmp_path / "gates.tsv"
    public_summary.to_csv(public_path, index=False)
    component_recovery.to_csv(component_path, index=False)
    tool_comparison.to_csv(tool_path, index=False)
    gates.to_csv(gates_path, sep="\t", index=False)

    out_dir = tmp_path / "manuscript" / "nature_methods_package"
    exit_code = script.main(
        [
            "--output-dir",
            str(out_dir),
            "--public-summary",
            str(public_path),
            "--component-recovery",
            str(component_path),
            "--tool-comparison",
            str(tool_path),
            "--gates",
            str(gates_path),
        ]
    )

    assert exit_code == 0
    expected = set(script.OUTPUT_FILES.values())
    observed = {path.name for path in out_dir.iterdir()}
    assert expected.issubset(observed)
    claim_map = pd.read_csv(out_dir / "05_claim_evidence_map.tsv", sep="\t")
    assert "C7" in set(claim_map["claim_id"])
    assert (out_dir / "09_full_manuscript_draft.md").exists()
    assert (out_dir / "10_supplementary_information_draft.md").exists()


def test_submission_package_can_use_polished_v2_as_full_manuscript(tmp_path):
    script = _load_script("build_nature_methods_submission_package")
    public_summary, component_recovery, tool_comparison, gates = _fixture_tables()
    polished = tmp_path / "SCI_MANUSCRIPT_V2_POLISHED.md"
    polished.write_text(
        "# Polished V2\n\nThis is the current working manuscript.\n", encoding="utf-8"
    )
    out_dir = tmp_path / "nature_methods_package"

    paths = script.build_package(
        output_dir=out_dir,
        public_summary=public_summary,
        component_recovery=component_recovery,
        tool_comparison=tool_comparison,
        gates=gates,
        polished_manuscript_path=polished,
    )

    assert (
        paths["full_manuscript"].read_text(encoding="utf-8").startswith("# Polished V2")
    )
