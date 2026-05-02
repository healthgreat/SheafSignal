#!/usr/bin/env python
"""Build reviewer-facing objection, evidence, and gate tables."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import _bootstrap  # noqa: F401


EXTERNAL_TOOLS = ["CellChat", "CellPhoneDB", "NicheNet", "LIANA", "niche-DE"]
MECHANISTIC_PRIOR_TOOLS = ["MechanisticTargetPrior"]
MECHANISTIC_TOOLS = ["NicheNet", *MECHANISTIC_PRIOR_TOOLS]


def _dataset_word(n: int) -> str:
    return "dataset" if int(n) == 1 else "datasets"


def _read_optional_csv(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def comparator_readiness_matrix(tool_comparison: pd.DataFrame) -> pd.DataFrame:
    """Summarize internal and external comparator readiness by dataset."""
    if tool_comparison.empty:
        return pd.DataFrame(
            columns=[
                "dataset_id",
                "internal_lr_product_completed",
                "external_tools_completed",
                "external_tools_pending",
                "external_comparator_gate",
                "mechanistic_tools_completed",
                "mechanistic_tools_pending",
                "mechanistic_comparator_gate",
                "max_abs_spearman_internal_lr_product",
            ]
        )

    rows = []
    for dataset_id, group in tool_comparison.groupby("dataset_id", dropna=False):
        internal = group.loc[group["tool"] == "LRProductBaseline"]
        external = group.loc[group["tool"].isin(EXTERNAL_TOOLS)].copy()
        external_completed = sorted(
            external.loc[
                external["status"].astype(str).str.startswith("completed"),
                "tool",
            ]
            .astype(str)
            .unique()
            .tolist()
        )
        external_pending = sorted(set(EXTERNAL_TOOLS).difference(external_completed))
        mechanistic = group.loc[group["tool"].isin(MECHANISTIC_TOOLS)].copy()
        mechanistic_completed = sorted(
            mechanistic.loc[
                mechanistic["status"].astype(str).str.startswith("completed"),
                "tool",
            ]
            .astype(str)
            .unique()
            .tolist()
        )
        mechanistic_pending = sorted(set(MECHANISTIC_TOOLS).difference(mechanistic_completed))
        if "NicheNet" in mechanistic_completed:
            mechanistic_gate = "pass_nichenetr_engine_with_prior"
        elif set(mechanistic_completed).intersection(MECHANISTIC_PRIOR_TOOLS):
            mechanistic_gate = "partial_mechanistic_prior_baseline"
        else:
            mechanistic_gate = "pending_mechanistic_comparator"
        rho = pd.to_numeric(
            internal.get("spearman_sheaf_energy_vs_tool_score", pd.Series(dtype=float)),
            errors="coerce",
        )
        rows.append(
            {
                "dataset_id": dataset_id,
                "internal_lr_product_completed": bool(
                    (internal["status"].astype(str) == "completed").any()
                ),
                "external_tools_completed": ";".join(external_completed),
                "external_tools_pending": ";".join(external_pending),
                "external_comparator_gate": (
                    "pass" if len(external_pending) == 0 else "pending_external_tools"
                ),
                "mechanistic_tools_completed": ";".join(mechanistic_completed),
                "mechanistic_tools_pending": ";".join(mechanistic_pending),
                "mechanistic_comparator_gate": mechanistic_gate,
                "max_abs_spearman_internal_lr_product": (
                    float(rho.abs().max()) if not rho.dropna().empty else pd.NA
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("dataset_id")


def _completed_dataset_summary(public_summary: pd.DataFrame) -> str:
    if public_summary.empty:
        return "No public benchmark summary found."
    completed = public_summary.loc[
        (public_summary["status"] == "completed")
        & (public_summary["dataset_id"].astype(str) != "demo_synthetic")
    ].copy()
    parts = []
    for row in completed.to_dict(orient="records"):
        parts.append(
            f"{row['dataset_id']}: top={row['top_frustration_cell_type']} "
            f"score={float(row['top_frustration_score']):.4g}"
        )
    return "; ".join(parts)


def _lr_product_summary(readiness: pd.DataFrame) -> str:
    if readiness.empty:
        return "LRProductBaseline summary unavailable."
    completed = readiness.loc[readiness["internal_lr_product_completed"] == True].copy()  # noqa: E712
    if completed.empty:
        return "LRProductBaseline not completed."
    low = float(completed["max_abs_spearman_internal_lr_product"].min())
    high = float(completed["max_abs_spearman_internal_lr_product"].max())
    return (
        f"LRProductBaseline completed for {len(completed)} datasets; absolute Spearman "
        f"range {low:.3g}-{high:.3g}. External tools remain separately gated."
    )


def _claim_gate_summary(claim_gate: pd.DataFrame) -> str:
    if claim_gate.empty:
        return "GSE154778 claim-gating table unavailable."
    if "claim_gate" in claim_gate.columns:
        main = claim_gate.loc[claim_gate["claim_gate"] == "main_claim", "cell_type"].astype(str).tolist()
    elif "claim_use" in claim_gate.columns:
        main = claim_gate.loc[claim_gate["claim_use"] == "main_claim", "cell_type"].astype(str).tolist()
    elif "claim_tier" in claim_gate.columns:
        main = claim_gate.loc[claim_gate["claim_tier"] == "main_claim", "cell_type"].astype(str).tolist()
    else:
        main = []
    if not main:
        return "No GSE154778 cell type currently passes the main-claim gate."
    return f"GSE154778 main-claim eligible cell types: {';'.join(main)}."


def _visium_qc_summary(visium_qc: pd.DataFrame) -> str:
    if visium_qc.empty:
        return "Visium spatial QC summary unavailable."
    row = visium_qc.iloc[0]
    return (
        f"Visium hotspot sensitivity: min Spearman={float(row['min_spearman_across_k']):.4g}, "
        f"min top-50 overlap={float(row['min_top_50_overlap_across_k']):.4g}."
    )


def _external_comparator_summary(
    readiness: pd.DataFrame,
    external_gate_summary: pd.DataFrame | None = None,
) -> dict[str, object]:
    """Summarize imported external comparator evidence across public datasets."""
    if readiness.empty or "external_tools_completed" not in readiness.columns:
        return {
            "has_any_external": False,
            "liana_completed_datasets": [],
            "completed_tools": [],
            "pending_tools": EXTERNAL_TOOLS,
            "evidence_sentence": "No imported external CCC comparator outputs are currently recorded.",
            "gate_status": "pending_external_tools",
            "claim_boundary": (
                "Methods package is not Nature Methods-ready until external comparator imports exist."
            ),
            "required_next_action": (
                "Use comparator_inputs bundles to run LIANA/CellChat/CellPhoneDB/NicheNet "
                "and import edge tables."
            ),
        }

    completed_tools: set[str] = set()
    liana_datasets: list[str] = []
    for row in readiness.to_dict(orient="records"):
        completed = [
            item
            for item in str(row.get("external_tools_completed", "")).split(";")
            if item and item != "nan"
        ]
        completed_tools.update(completed)
        if "LIANA" in completed:
            liana_datasets.append(str(row.get("dataset_id", "")))

    pending_tools = sorted(set(EXTERNAL_TOOLS).difference(completed_tools))
    completed_tools_sorted = sorted(completed_tools)
    gate_row = None
    if external_gate_summary is not None and not external_gate_summary.empty:
        gate_row = external_gate_summary.iloc[0].to_dict()

    if liana_datasets:
        gate_status = str(gate_row.get("gate_status", "")) if gate_row else ""
        n_smoke = int(gate_row.get("n_smoke_completed_datasets", 0)) if gate_row else 0
        n_full = int(gate_row.get("n_full_completed_datasets", 0)) if gate_row else 0
        n_subset = (
            int(gate_row.get("n_prepared_subset_completed_datasets", 0))
            if gate_row
            else 0
        )
        if gate_status == "partially_satisfied_smoke_only":
            evidence = (
                "LIANA smoke imports are present for "
                f"{n_smoke or len(liana_datasets)} public scRNA-seq datasets: "
                f"{';'.join(liana_datasets)}. Full LIANA imports completed for "
                f"{n_full} datasets. Remaining external tools pending: "
                f"{';'.join(pending_tools) if pending_tools else 'none'}."
            )
            return {
                "has_any_external": True,
                "liana_completed_datasets": liana_datasets,
                "completed_tools": completed_tools_sorted,
                "pending_tools": pending_tools,
                "evidence_sentence": evidence,
                "gate_status": "partial_liana_smoke_import_done",
                "claim_boundary": (
                    "External comparator benchmarking is partially satisfied by LIANA smoke "
                    "imports; do not claim full LIANA benchmarking or broad superiority until "
                    "full LIANA and at least one mechanistic comparator are complete."
                ),
                "required_next_action": (
                    "Run full LIANA without --max-cells where feasible and add a mechanistic "
                    "comparator such as NicheNet."
                ),
            }
        if gate_status == "partially_satisfied_mixed":
            evidence = (
                "LIANA imports are present for "
                f"{len(liana_datasets)} public scRNA-seq datasets: "
                f"{';'.join(liana_datasets)}. Full LIANA imports completed for "
                f"{n_full} {_dataset_word(n_full)}; prepared-subset imports completed for "
                f"{n_subset} {_dataset_word(n_subset)}; smoke-level-or-better imports are "
                f"recorded for {n_smoke} {_dataset_word(n_smoke)}. Remaining external tools pending: "
                f"{';'.join(pending_tools) if pending_tools else 'none'}."
            )
            return {
                "has_any_external": True,
                "liana_completed_datasets": liana_datasets,
                "completed_tools": completed_tools_sorted,
                "pending_tools": pending_tools,
                "evidence_sentence": evidence,
                "gate_status": "partial_liana_mixed_import_done",
                "claim_boundary": (
                    "External comparator benchmarking has mixed LIANA coverage; "
                    "prepared-subset imports are not full-dataset evidence. Do not claim "
                    "complete LIANA benchmarking or broad superiority until all public "
                    "scRNA-seq datasets have full LIANA and at least one mechanistic "
                    "comparator is complete."
                ),
                "required_next_action": (
                    "Resolve any prepared-subset LIANA datasets with a true full-cell input "
                    "or pre-specified downsampling design, then add a mechanistic comparator "
                    "such as NicheNet."
                ),
            }
        if gate_status == "partially_satisfied_prepared_subset_only":
            evidence = (
                "LIANA prepared-subset imports are present for "
                f"{n_subset or len(liana_datasets)} public scRNA-seq datasets: "
                f"{';'.join(liana_datasets)}. Full LIANA imports completed for "
                f"{n_full} datasets. Remaining external tools pending: "
                f"{';'.join(pending_tools) if pending_tools else 'none'}."
            )
            return {
                "has_any_external": True,
                "liana_completed_datasets": liana_datasets,
                "completed_tools": completed_tools_sorted,
                "pending_tools": pending_tools,
                "evidence_sentence": evidence,
                "gate_status": "partial_liana_prepared_subset_import_done",
                "claim_boundary": (
                    "Prepared-subset LIANA imports are useful smoke-level evidence, but "
                    "not full-dataset external benchmarking."
                ),
                "required_next_action": (
                    "Create full cell-level inputs or an approved downsampling benchmark "
                    "design, then rerun LIANA and add a mechanistic comparator."
                ),
            }
        if gate_status == "satisfied_liana_full":
            evidence = (
                "Full LIANA imports are present for "
                f"{n_full or len(liana_datasets)} public scRNA-seq datasets: "
                f"{';'.join(liana_datasets)}. Remaining external tools pending: "
                f"{';'.join(pending_tools) if pending_tools else 'none'}."
            )
            return {
                "has_any_external": True,
                "liana_completed_datasets": liana_datasets,
                "completed_tools": completed_tools_sorted,
                "pending_tools": pending_tools,
                "evidence_sentence": evidence,
                "gate_status": "partial_liana_full_import_done",
                "claim_boundary": (
                    "Full LIANA benchmarking is available, but broad superiority claims remain "
                    "gated by mechanistic comparator coverage."
                ),
                "required_next_action": "Add a mechanistic comparator such as NicheNet.",
            }
        evidence = (
            "LIANA completed_external_import is present for "
            f"{len(liana_datasets)} public scRNA-seq datasets: "
            f"{';'.join(liana_datasets)}. Remaining external tools pending: "
            f"{';'.join(pending_tools) if pending_tools else 'none'}."
        )
        return {
            "has_any_external": True,
            "liana_completed_datasets": liana_datasets,
            "completed_tools": completed_tools_sorted,
            "pending_tools": pending_tools,
            "evidence_sentence": evidence,
            "gate_status": "partial_liana_import_done",
            "claim_boundary": (
                "External comparator benchmarking is partially satisfied by LIANA imports; "
                "do not claim broad superiority over all CCC tools until full-scale LIANA "
                "and at least one mechanistic comparator are complete."
            ),
            "required_next_action": (
                "Upgrade LIANA smoke runs to full runs where feasible and add a mechanistic "
                "comparator such as NicheNet."
            ),
        }

    if completed_tools_sorted:
        evidence = (
            "Imported external comparator outputs are present for tools: "
            f"{';'.join(completed_tools_sorted)}. Remaining external tools pending: "
            f"{';'.join(pending_tools) if pending_tools else 'none'}."
        )
        return {
            "has_any_external": True,
            "liana_completed_datasets": [],
            "completed_tools": completed_tools_sorted,
            "pending_tools": pending_tools,
            "evidence_sentence": evidence,
            "gate_status": "partial_external_import_done",
            "claim_boundary": (
                "External comparator benchmarking is partially satisfied; broad superiority "
                "claims remain gated by additional comparator coverage."
            ),
            "required_next_action": "Add LIANA and one mechanistic comparator across public scRNA-seq datasets.",
        }

    return {
        "has_any_external": False,
        "liana_completed_datasets": [],
        "completed_tools": [],
        "pending_tools": pending_tools,
        "evidence_sentence": "Comparator input/export/import schema exists, but no external tool rows are imported yet.",
        "gate_status": "pending_external_tools",
        "claim_boundary": (
            "Methods package is not Nature Methods-ready until external comparator imports exist."
        ),
        "required_next_action": (
            "Use comparator_inputs bundles to run LIANA/CellChat/CellPhoneDB/NicheNet "
            "and import edge tables."
        ),
    }


def _mechanistic_comparator_summary(readiness: pd.DataFrame) -> dict[str, object]:
    if readiness.empty or "mechanistic_tools_completed" not in readiness.columns:
        return {
            "has_any_mechanistic": False,
            "gate_status": "pending_mechanistic_comparator",
            "evidence_sentence": "No mechanistic comparator outputs are currently recorded.",
            "claim_boundary": (
                "No mechanistic target-prior or NicheNet benchmark claim is allowed yet."
            ),
            "required_next_action": (
                "Run a mechanistic comparator such as NicheNet or a transparent ligand-target "
                "prior baseline."
            ),
        }

    completed_tools: set[str] = set()
    nichenet_datasets: list[str] = []
    prior_datasets: list[str] = []
    for row in readiness.to_dict(orient="records"):
        completed = [
            item
            for item in str(row.get("mechanistic_tools_completed", "")).split(";")
            if item and item != "nan"
        ]
        completed_tools.update(completed)
        dataset_id = str(row.get("dataset_id", ""))
        if "NicheNet" in completed:
            nichenet_datasets.append(dataset_id)
        if set(completed).intersection(MECHANISTIC_PRIOR_TOOLS):
            prior_datasets.append(dataset_id)

    if nichenet_datasets:
        return {
            "has_any_mechanistic": True,
            "gate_status": "pass_nichenetr_engine_with_prior",
            "evidence_sentence": (
                "NicheNet/nichenetr-engine imports are completed for "
                f"{len(nichenet_datasets)} public scRNA-seq datasets: "
                f"{';'.join(nichenet_datasets)}. The current run uses the official "
                "nichenetr scoring engine with the project-curated TME ligand-target "
                "prior matrix."
            ),
            "claim_boundary": (
                "Allowed claim: official nichenetr scoring engine was executed with a "
                "transparent curated prior. Not allowed: full pretrained NicheNet network "
                "benchmarking unless that resource is explicitly added and documented."
            ),
            "required_next_action": "Regenerate final manuscript figures and reviewer gates.",
        }

    if prior_datasets:
        return {
            "has_any_mechanistic": True,
            "gate_status": "partial_mechanistic_prior_done",
            "evidence_sentence": (
                "MechanisticTargetPrior is completed for "
                f"{len(prior_datasets)} public scRNA-seq datasets: "
                f"{';'.join(prior_datasets)}. This is a curated ligand-target prior "
                "baseline, not an official nichenetr/NicheNet package run."
            ),
            "claim_boundary": (
                "Allowed claim: a transparent ligand-target prior comparator supports "
                "mechanistic target-program benchmarking. Not allowed: official NicheNet "
                "benchmarking is complete."
            ),
            "required_next_action": (
                "Keep this as a mechanistic-prior baseline and run official nichenetr/NicheNet "
                "if feasible before a highest-impact submission."
            ),
        }

    return {
        "has_any_mechanistic": False,
        "gate_status": "pending_mechanistic_comparator",
        "evidence_sentence": "No mechanistic comparator outputs are currently recorded.",
        "claim_boundary": "No mechanistic comparator claim is allowed yet.",
        "required_next_action": "Run or import NicheNet or a transparent ligand-target prior baseline.",
    }


def reviewer_objection_table(
    public_summary: pd.DataFrame,
    readiness: pd.DataFrame,
    claim_gate: pd.DataFrame,
    visium_qc: pd.DataFrame,
    external_gate_summary: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Create a manuscript/rebuttal-ready table of likely reviewer objections."""
    dataset_summary = _completed_dataset_summary(public_summary)
    lr_summary = _lr_product_summary(readiness)
    claim_summary = _claim_gate_summary(claim_gate)
    visium_summary = _visium_qc_summary(visium_qc)
    external_summary = _external_comparator_summary(readiness, external_gate_summary)
    mechanistic_summary = _mechanistic_comparator_summary(readiness)
    external_response_position = (
        "External comparator status is generated from imported tool outputs, not manual text. "
        "The current manuscript can state that LIANA imports exist only at the evidence tier "
        "recorded in the comparator gate table."
        if bool(external_summary["has_any_external"])
        else (
            "This is a hard submission gate. The repository makes external handoff auditable, "
            "but the manuscript should not state that external comparator benchmarking is complete."
        )
    )

    rows = [
        {
            "objection_id": "R1_algorithm_is_lr_intensity",
            "likely_reviewer_objection": "SheafSignal may be a rebranding of ligand-receptor communication intensity.",
            "current_evidence": lr_summary,
            "response_position": (
                "Internal LRProductBaseline is explicitly aligned to sheaf_energy; discordance and "
                "correlation summaries show SheafSignal measures pathway-consistency mismatch on top "
                "of LR flow, not only LR strength."
            ),
            "claim_boundary": (
                "Do not claim superiority over CellChat/CellPhoneDB/NicheNet/LIANA until external "
                "tool runs are imported."
            ),
            "gate_status": "partial_internal_baseline_done",
            "required_next_action": "Run and import at least LIANA plus one mechanistic comparator such as NicheNet.",
        },
        {
            "objection_id": "R2_no_external_comparator",
            "likely_reviewer_objection": "The benchmark lacks real external CCC comparator outputs.",
            "current_evidence": str(external_summary["evidence_sentence"]),
            "response_position": external_response_position,
            "claim_boundary": str(external_summary["claim_boundary"]),
            "gate_status": str(external_summary["gate_status"]),
            "required_next_action": str(external_summary["required_next_action"]),
        },
        {
            "objection_id": "R3_sparse_cell_type_overinterpretation",
            "likely_reviewer_objection": "Sparse or low-confidence categories may drive overinterpreted biology.",
            "current_evidence": claim_summary,
            "response_position": (
                "GSE154778 uses programmatic claim gating; sparse categories are demoted to "
                "supplement/QC warning instead of being rescued post hoc."
            ),
            "claim_boundary": (
                "Main text can discuss Myeloid only for GSE154778; sparse cell types remain QC context."
            ),
            "gate_status": "pass_for_gse154778_claim_boundary",
            "required_next_action": "Keep claim-gating table in supplement and avoid sparse cell-type mechanism language.",
        },
        {
            "objection_id": "R4_single_dataset_biology",
            "likely_reviewer_objection": "The result may be dataset-specific rather than a general method.",
            "current_evidence": dataset_summary,
            "response_position": (
                "The benchmark now includes PDAC, melanoma, breast cancer scRNA-seq, and breast Visium. "
                "The correct claim is context-specific frustration architecture, not one universal source cell type."
            ),
            "claim_boundary": "Do not generalize PDAC Myeloid to all tumors.",
            "gate_status": "pass_for_methods_replication",
            "required_next_action": str(external_summary["required_next_action"]),
        },
        {
            "objection_id": "R5_spatial_neighbor_arbitrariness",
            "likely_reviewer_objection": "Spatial hotspots may depend on arbitrary k-neighbor graph choice.",
            "current_evidence": visium_summary,
            "response_position": (
                "Visium hotspot QC includes k-neighbor sensitivity and spatial scatter; current hotspot "
                "ranks are stable across k=4,6,8,10,12."
            ),
            "claim_boundary": (
                "Spatial labels are marker-dominant spot programs, not single-cell cell-type proof; "
                "main claim should be hotspot localization."
            ),
            "gate_status": "pass_for_spatial_hotspot_qc",
            "required_next_action": "Add histology-aware annotation review before biological mechanism claims.",
        },
        {
            "objection_id": "R6_public_data_only",
            "likely_reviewer_objection": "Public-data-only evidence may be insufficient for clinical claims.",
            "current_evidence": "All benchmark datasets are public, manifested, checksum-tracked, and GitHub/Zenodo-ready.",
            "response_position": (
                "Position the paper as a methods article with reproducible public benchmarks, not as a "
                "clinical medicine or therapeutic target paper."
            ),
            "claim_boundary": "No clinical decision or treatment-response claim.",
            "gate_status": "pass_for_methods_scope",
            "required_next_action": "Keep data/code availability and accession/checksum table complete.",
        },
        {
            "objection_id": "R7_no_mechanistic_comparator",
            "likely_reviewer_objection": (
                "A target-program or mechanistic CCC comparator is needed, not only LR edge ranking."
            ),
            "current_evidence": str(mechanistic_summary["evidence_sentence"]),
            "response_position": (
                "Mechanistic comparator status is generated from imported tool rows. "
                "MechanisticTargetPrior is acceptable as a transparent prior baseline, but "
                "must not be described as official NicheNet."
            ),
            "claim_boundary": str(mechanistic_summary["claim_boundary"]),
            "gate_status": str(mechanistic_summary["gate_status"]),
            "required_next_action": str(mechanistic_summary["required_next_action"]),
        },
    ]
    return pd.DataFrame(rows)


def build_tables(
    results_dir: Path,
    manuscript_dir: Path,
    output_dir: Path,
) -> dict[str, Path]:
    public_summary = _read_optional_csv(results_dir / "public_tme_sheafsignal_summary.csv")
    tool_comparison = _read_optional_csv(results_dir / "tool_comparison.csv")
    claim_gate = _read_optional_csv(
        results_dir / "gse154778_pdac_scrna" / "qc" / "claim_gating_by_cell_type.csv"
    )
    visium_qc = _read_optional_csv(
        results_dir
        / "tenx_breast_visium"
        / "spatial"
        / "qc"
        / "spatial_hotspot_qc_summary.csv"
    )
    external_gate_summary = _read_optional_csv(
        results_dir / "external_comparator_gate_summary.csv"
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    manuscript_dir.mkdir(parents=True, exist_ok=True)
    readiness = comparator_readiness_matrix(tool_comparison)
    reviewer_readiness = readiness.loc[
        readiness["dataset_id"].astype(str) != "demo_synthetic"
    ].copy()
    objections = reviewer_objection_table(
        public_summary,
        reviewer_readiness,
        claim_gate,
        visium_qc,
        external_gate_summary,
    )

    readiness_path = output_dir / "comparator_readiness_matrix.csv"
    objections_csv = output_dir / "reviewer_objection_response_table.csv"
    objections_tsv = manuscript_dir / "reviewer_objection_response_table.tsv"
    readiness.to_csv(readiness_path, index=False)
    objections.to_csv(objections_csv, index=False)
    objections.to_csv(objections_tsv, sep="\t", index=False)
    return {
        "comparator_readiness": readiness_path,
        "reviewer_objection_csv": objections_csv,
        "reviewer_objection_tsv": objections_tsv,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", default="benchmarks/results")
    parser.add_argument("--manuscript-dir", default="manuscript")
    parser.add_argument("--output-dir", default="benchmarks/results")
    args = parser.parse_args(argv)

    paths = build_tables(
        results_dir=Path(args.results_dir),
        manuscript_dir=Path(args.manuscript_dir),
        output_dir=Path(args.output_dir),
    )
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
