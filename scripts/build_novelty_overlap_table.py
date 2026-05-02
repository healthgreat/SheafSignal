#!/usr/bin/env python
"""Build the SheafSignal novelty and overlap matrix."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROWS = [
    {
        "comparison_class": "standard_ccc_tools",
        "representative_methods": "CellChat;CellPhoneDB;LIANA;NicheNet",
        "primary_object": "ligand-receptor or ligand-target communication evidence",
        "sheafsignal_difference": "adds edge-level consistency between LR flow and receiver pathway-state transition",
        "overlap_risk": "high if described as a better CCC score",
        "safe_claim": "complements intensity-focused CCC tools with a graph-consistency readout",
        "required_evidence": "head-to-head CellChat/CellPhoneDB/LIANA/NicheNet edge alignment",
        "citation_keys": "cellchat_jin_2021;cellphonedb_efremova_2020;liana_plus_dimitrov_2024;nichenet_browaeys_2020",
    },
    {
        "comparison_class": "graph_signal_processing",
        "representative_methods": "graph smoothness;graph Laplacian signals",
        "primary_object": "scalar signal over graph nodes or edges",
        "sheafsignal_difference": "uses sheaf-valued local consistency constraints on directed CCC edges",
        "overlap_risk": "moderate if sheaf restriction maps are not explained",
        "safe_claim": "adapts graph-consistency analysis to CCC pathway-state mismatch",
        "required_evidence": "formal methods subsection defining edge stalks, restrictions and mismatch energy",
        "citation_keys": "graph_signal_processing_shuman_2013",
    },
    {
        "comparison_class": "hodge_biology_omics",
        "representative_methods": "Hodge decomposition on rankings or biological graph flows",
        "primary_object": "decomposition of graph or simplicial flows",
        "sheafsignal_difference": "constructs the flow from ligand-receptor evidence versus pathway-state transitions",
        "overlap_risk": "moderate if novelty is claimed as Hodge decomposition itself",
        "safe_claim": "uses Hodge decomposition as the component layer of a CCC-specific sheaf flow",
        "required_evidence": "simulation recovery plus real-data component reporting with conservative biological interpretation",
        "citation_keys": "hodge_rank_jiang_2011;hodge_laplacians_lim_2020",
    },
    {
        "comparison_class": "cellular_sheaf_methods",
        "representative_methods": "cellular sheaves;sheaf neural networks;sheaf diffusion",
        "primary_object": "local-to-global consistency over graph-attached vector spaces",
        "sheafsignal_difference": "defines a domain-specific CCC sheaf energy tied to LR and pathway genes",
        "overlap_risk": "high if described as first sheaf method in biology without a formal literature audit",
        "safe_claim": "presents an integrated sheaf/Hodge workflow for CCC graphs",
        "required_evidence": "novelty table plus citations and no first-ever claim unless independently verified",
        "citation_keys": "cellular_sheaves_hansen_2019",
    },
    {
        "comparison_class": "niche_regression_or_de_methods",
        "representative_methods": "niche-DE;neighborhood regression;covariate-adjusted niche models",
        "primary_object": "gene-expression association with neighborhood or niche covariates",
        "sheafsignal_difference": "does not test differential expression from niche covariates; it evaluates edge-wise consistency between directed CCC observations and pathway-state transitions",
        "overlap_risk": "moderate if described as replacing niche differential expression",
        "safe_claim": "provides a graph-consistency layer complementary to regression-based niche effect models",
        "required_evidence": "scope boundary that niche-DE is related-method context, not a mandatory CCC comparator",
        "citation_keys": "niche_de_reference_required",
    },
    {
        "comparison_class": "spatial_neighborhood_or_domain_methods",
        "representative_methods": "spatial neighborhood enrichment;domain detection;spot-level program mapping",
        "primary_object": "spatial proximity, tissue domains, or spot-level expression programs",
        "sheafsignal_difference": "uses optional spatial adjacency only to define local communication neighborhoods and hotspot stability, not histology-validated cell-type sources",
        "overlap_risk": "moderate if Visium hotspots are interpreted as deconvolved cell-type mechanisms",
        "safe_claim": "extends sheaf-energy summaries to spatial hotspot demonstrations under explicit spot-level boundaries",
        "required_evidence": "Visium hotspot-only scope gate unless deconvolution or pathology annotation is added",
        "citation_keys": "spatial_transcriptomics_methods_reference_required",
    },
    {
        "comparison_class": "centrality_or_network_topology",
        "representative_methods": "degree;betweenness;PageRank;network motifs",
        "primary_object": "topological position or motif count",
        "sheafsignal_difference": "scores inconsistency of biological edge values rather than graph position alone",
        "overlap_risk": "low if not oversold as replacing network topology",
        "safe_claim": "reports a value-aware inconsistency metric orthogonal to pure topology",
        "required_evidence": "simulation and comparator discordance examples",
        "citation_keys": "network_biology_review_required",
    },
]


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def build_novelty_overlap_table(output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(ROWS)
    table_path = output_dir / "SHEAFSIGNAL_NOVELTY_OVERLAP_TABLE.tsv"
    report_path = output_dir / "SHEAFSIGNAL_NOVELTY_OVERLAP_REPORT.md"
    table.to_csv(table_path, sep="\t", index=False)
    unresolved = table["citation_keys"].astype(str).str.contains("required", case=False).sum()
    lines = [
        "# SheafSignal Novelty And Overlap Report",
        "",
        f"- Comparison classes: {len(table)}",
        f"- Rows with citation placeholders requiring author verification: {int(unresolved)}",
        "- Boundary: claim an integrated sheaf/Hodge CCC workflow, not broad first-ever novelty.",
        "- Reviewer-facing interpretation: SheafSignal is not a replacement for CCC, niche-DE, spatial domain detection, graph centrality, or Hodge methods; it composes CCC-derived observations with a domain-specific sheaf consistency residual.",
        "",
        "## Highest-Risk Overlaps",
        "",
    ]
    risk_rows = table.loc[table["overlap_risk"].astype(str).str.startswith("high")]
    for row in risk_rows.to_dict(orient="records"):
        lines.append(
            f"- `{row['comparison_class']}`: {row['overlap_risk']}. "
            f"Safe claim: {row['safe_claim']}."
        )
    lines.extend(
        [
            "",
            "## Claims To Avoid",
            "",
            "- Do not claim first-ever use of sheaves in biology without a separate formal literature audit.",
            "- Do not claim Hodge decomposition itself is new.",
            "- Do not claim SheafSignal replaces CellChat, CellPhoneDB, LIANA, NicheNet, niche-DE, spatial deconvolution, or graph centrality.",
            "- Do not interpret Visium hotspots as validated cell-type mechanisms without deconvolution or pathology support.",
            "",
            "## Safest One-Sentence Novelty Claim",
            "",
            "SheafSignal implements a domain-specific sheaf/Hodge workflow that converts CCC-derived ligand-receptor observations and pathway-state transitions into edge- and node-level graph-consistency residuals.",
            "",
        ]
    )
    _write_text_atomic(report_path, "\n".join(lines))
    return {"table": table_path, "report": report_path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="manuscript/novelty_overlap")
    args = parser.parse_args(argv)
    paths = build_novelty_overlap_table(Path(args.output_dir))
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
