from pathlib import Path
import importlib.util

import pandas as pd


def _load_script():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "build_polished_sci_manuscript_v2.py"
    spec = importlib.util.spec_from_file_location(
        "build_polished_sci_manuscript_v2", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_polished_manuscript_keeps_boundaries_and_resolved_references():
    script = _load_script()
    manuscript = script.build_polished_manuscript(
        component_recovery=pd.DataFrame(
            [
                {
                    "scenario": "gradient_chain",
                    "gradient_ratio": 1,
                    "curl_ratio": 0,
                    "harmonic_ratio": 0,
                },
                {
                    "scenario": "mixed",
                    "gradient_ratio": 0.4,
                    "curl_ratio": 0.3,
                    "harmonic_ratio": 0.3,
                },
            ]
        ),
        public_summary=pd.DataFrame(
            [
                {
                    "dataset_id": "gse154778_pdac_scrna",
                    "status": "completed",
                    "modality": "scRNA-seq",
                    "n_cell_types": 7,
                    "top_frustration_cell_type": "Myeloid",
                    "total_sheaf_energy": 36.1,
                }
            ]
        ),
        tool_comparison=pd.DataFrame(
            [
                {
                    "dataset_id": "gse154778_pdac_scrna",
                    "tool": "LIANA",
                    "status": "completed_full_import",
                    "spearman_sheaf_energy_vs_tool_score": 0.69,
                }
            ]
        ),
        myeloid_summary=pd.DataFrame(
            [
                {
                    "min_lesion_n_cells": 497,
                    "min_lesion_n_samples": 6,
                    "bootstrap_top_frequency": 1,
                    "primary_frustration_score": 0.38,
                    "metastatic_frustration_score": 0.81,
                    "median_marker_score_margin": 0.35,
                    "low_margin_fraction_lt_0_05": 0.07,
                }
            ]
        ),
        claim_gating=pd.DataFrame(
            [
                {
                    "cell_type": "CAF/Fibroblast",
                    "claim_gate": "qc_warning_only",
                    "min_lesion_n_cells": 2,
                }
            ]
        ),
        sample_stability=pd.DataFrame(
            [
                {
                    "lesion_type": "Metastatic",
                    "myeloid_top_frequency_adequate": 0.75,
                    "n_myeloid_adequate_samples": 4,
                }
            ]
        ),
    )

    assert "[REF:" not in manuscript
    assert "not a full pretrained NicheNet network benchmark" in manuscript
    assert "does not claim clinical" in manuscript
    normalized = " ".join(manuscript.split())
    assert "guaranteed journal acceptance" in normalized
    assert "broad superiority" in manuscript
    assert "Myeloid passed the pancreatic-cancer main-claim gate" in manuscript
    assert (
        "smallest lesion support among downgraded categories was 2 cells" in manuscript
    )


def test_editorial_audit_flags_pending_items_without_blocking_valid_boundaries():
    script = _load_script()
    manuscript = (
        "Authors: TBD\n"
        "This uses not a full pretrained NicheNet network benchmark.\n"
        "Sparse categories are QC-only.\n"
        "This manuscript does not claim clinical utility.\n"
    )

    audit = script.build_editorial_audit(manuscript)

    statuses = dict(zip(audit["audit_id"], audit["status"]))
    assert statuses["references_no_placeholder"] == "pass"
    assert statuses["boundary_statement_present"] == "pass"
    assert statuses["nichenet_boundary_present"] == "pass"
    assert statuses["sparse_category_boundary_present"] == "pass"
    assert statuses["forbidden_positive_claims_absent"] == "pass"
    assert statuses["author_metadata_pending"] == "pending_author_action"
    assert statuses["zenodo_and_github_pending"] == "pending_author_action"


def test_build_package_writes_all_v2_outputs(tmp_path):
    script = _load_script()
    (tmp_path / "benchmarks" / "results" / "gse154778_pdac_scrna" / "qc").mkdir(
        parents=True
    )
    (tmp_path / "benchmarks" / "results" / "gse154778_pdac_scrna" / "stability").mkdir(
        parents=True
    )
    pd.DataFrame(
        [
            {
                "scenario": "gradient_chain",
                "gradient_ratio": 1,
                "curl_ratio": 0,
                "harmonic_ratio": 0,
            },
            {
                "scenario": "mixed",
                "gradient_ratio": 0.4,
                "curl_ratio": 0.3,
                "harmonic_ratio": 0.3,
            },
        ]
    ).to_csv(
        tmp_path / "benchmarks" / "results" / "component_recovery.csv", index=False
    )
    pd.DataFrame(
        [
            {
                "dataset_id": "gse154778_pdac_scrna",
                "status": "completed",
                "modality": "scRNA-seq",
                "n_cell_types": 7,
                "top_frustration_cell_type": "Myeloid",
                "total_sheaf_energy": 36.1,
            }
        ]
    ).to_csv(
        tmp_path / "benchmarks" / "results" / "public_tme_sheafsignal_summary.csv",
        index=False,
    )
    pd.DataFrame(
        [
            {
                "dataset_id": "gse154778_pdac_scrna",
                "tool": "LIANA",
                "status": "completed_full_import",
                "spearman_sheaf_energy_vs_tool_score": 0.69,
            }
        ]
    ).to_csv(tmp_path / "benchmarks" / "results" / "tool_comparison.csv", index=False)
    pd.DataFrame(
        [
            {
                "min_lesion_n_cells": 497,
                "min_lesion_n_samples": 6,
                "bootstrap_top_frequency": 1,
                "primary_frustration_score": 0.38,
                "metastatic_frustration_score": 0.81,
                "median_marker_score_margin": 0.35,
                "low_margin_fraction_lt_0_05": 0.07,
            }
        ]
    ).to_csv(
        tmp_path
        / "benchmarks"
        / "results"
        / "gse154778_pdac_scrna"
        / "qc"
        / "myeloid_claim_readiness_summary.csv",
        index=False,
    )
    pd.DataFrame(
        [
            {
                "cell_type": "CAF/Fibroblast",
                "claim_gate": "qc_warning_only",
                "min_lesion_n_cells": 2,
            }
        ]
    ).to_csv(
        tmp_path
        / "benchmarks"
        / "results"
        / "gse154778_pdac_scrna"
        / "qc"
        / "claim_gating_by_cell_type.csv",
        index=False,
    )
    pd.DataFrame(
        [
            {
                "lesion_type": "Metastatic",
                "myeloid_top_frequency_adequate": 0.75,
                "n_myeloid_adequate_samples": 4,
            }
        ]
    ).to_csv(
        tmp_path
        / "benchmarks"
        / "results"
        / "gse154778_pdac_scrna"
        / "stability"
        / "sample_level_myeloid_stability_summary.csv",
        index=False,
    )

    paths = script.build_package(root=tmp_path, output_dir=tmp_path / "manuscript")

    for path in paths.values():
        assert path.exists()
    audit = pd.read_csv(paths["editorial_audit"], sep="\t")
    assert set(audit["status"]) >= {"pass", "pending_author_action"}
    assert "C4_gse154778_myeloid" in paths["claim_tracked"].read_text(encoding="utf-8")
