#!/usr/bin/env python
"""Build a polished SCI manuscript v2 for the SheafSignal submission package.

Author: SheafSignal contributors
Date: 2026-05-01
Purpose: convert the reference-resolved v1 draft and current evidence tables
into a tighter Nature Methods-style manuscript with an auditable claim tracker,
editorial audit, and changelog.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

OUTPUT_FILES = {
    "manuscript": "SCI_MANUSCRIPT_V2_POLISHED.md",
    "claim_tracked": "SCI_MANUSCRIPT_V2_POLISHED_claim_tracked.md",
    "editorial_audit": "SCI_MANUSCRIPT_V2_EDITORIAL_AUDIT.tsv",
    "changelog": "SCI_MANUSCRIPT_V2_CHANGELOG.tsv",
}


FORBIDDEN_PATTERNS = {
    "clinical_utility_positive": re.compile(
        r"\b(demonstrate|demonstrates|establish|establishes|prove|proves)\b"
        r".{0,60}\bclinical utility\b",
        re.IGNORECASE,
    ),
    "guaranteed_acceptance": re.compile(
        r"\b(guarantee|guaranteed|guarantees)\b.{0,50}\b(acceptance|publication)\b",
        re.IGNORECASE,
    ),
    "broad_superiority": re.compile(
        r"\b(superior|outperform|outperforms|better than)\b.{0,90}"
        r"\b(CellChat|CellPhoneDB|LIANA|NicheNet|niche-DE|CCC tools)\b",
        re.IGNORECASE,
    ),
    "therapeutic_recommendation": re.compile(
        r"\b(recommend|recommends|guide|guides)\b.{0,80}"
        r"\b(treatment|therapy|therapeutic)\b",
        re.IGNORECASE,
    ),
}


def _read_table(path: Path, sep: str = ",") -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep=sep)


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_table_atomic(path: Path, table: pd.DataFrame) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    table.to_csv(tmp_path, sep="\t", index=False)
    tmp_path.replace(path)


def _fmt(value: object, digits: int = 3) -> str:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return "NA"
    return f"{float(numeric):.{digits}g}"


def _one_row(
    table: pd.DataFrame, default: dict[str, object] | None = None
) -> dict[str, object]:
    if table.empty:
        return default or {}
    return table.iloc[0].to_dict()


def component_recovery_sentence(component_recovery: pd.DataFrame) -> str:
    if component_recovery.empty:
        return "Component-recovery simulations are pending."
    records = component_recovery.to_dict(orient="records")
    expected = []
    mixed = []
    for row in records:
        scenario = str(row.get("scenario", "unknown"))
        summary = (
            f"{scenario}: gradient {_fmt(row.get('gradient_ratio'))}, "
            f"curl {_fmt(row.get('curl_ratio'))}, "
            f"harmonic {_fmt(row.get('harmonic_ratio'))}"
        )
        if scenario == "mixed":
            mixed.append(summary)
        else:
            expected.append(summary)
    return (
        "The pure-flow controls recovered their expected dominant component "
        f"({'; '.join(expected)}), and the mixed graph distributed energy across "
        f"components ({'; '.join(mixed)})."
    )


def public_benchmark_sentence(public_summary: pd.DataFrame) -> str:
    if public_summary.empty:
        return "Public benchmark summaries are pending."
    completed = public_summary.loc[
        (public_summary["status"].astype(str) == "completed")
        & (public_summary["dataset_id"].astype(str) != "demo_synthetic")
    ].copy()
    if completed.empty:
        return "Public benchmark summaries are pending."
    parts = []
    for row in completed.to_dict(orient="records"):
        parts.append(
            f"{row['dataset_id']} ({row['modality']}; {int(row['n_cell_types'])} "
            f"cell-type states; top source {row['top_frustration_cell_type']}; "
            f"total sheaf energy {_fmt(row['total_sheaf_energy'])})"
        )
    return "The completed public benchmark set comprised " + "; ".join(parts) + "."


def comparator_sentence(tool_comparison: pd.DataFrame) -> str:
    if tool_comparison.empty:
        return "Comparator summaries are pending."
    completed = tool_comparison.loc[
        (tool_comparison["status"].astype(str).str.startswith("completed"))
        & (tool_comparison["dataset_id"].astype(str) != "demo_synthetic")
    ].copy()
    if completed.empty:
        return "Comparator summaries are pending."
    rows = []
    for tool in ["LRProductBaseline", "LIANA", "MechanisticTargetPrior", "NicheNet"]:
        subset = completed.loc[completed["tool"].astype(str) == tool]
        if subset.empty:
            continue
        rho = pd.to_numeric(
            subset.get("spearman_sheaf_energy_vs_tool_score", pd.Series(dtype=float)),
            errors="coerce",
        ).dropna()
        rho_text = (
            "NA" if rho.empty else f"{float(rho.min()):.3g}-{float(rho.max()):.3g}"
        )
        rows.append(
            f"{tool} across {subset['dataset_id'].nunique()} datasets, Spearman {rho_text}"
        )
    return "Aligned comparator evidence included " + "; ".join(rows) + "."


def myeloid_sentence(myeloid_summary: pd.DataFrame) -> str:
    if myeloid_summary.empty:
        return "GSE154778 Myeloid claim-readiness summaries are pending."
    row = _one_row(myeloid_summary)
    return (
        "Myeloid passed the pancreatic-cancer main-claim gate with minimum "
        f"lesion support of {int(row['min_lesion_n_cells'])} cells and "
        f"{int(row['min_lesion_n_samples'])} samples, bootstrap top-source "
        f"frequency {_fmt(row['bootstrap_top_frequency'])}, Primary and "
        f"Metastatic frustration scores of {_fmt(row['primary_frustration_score'])} "
        f"and {_fmt(row['metastatic_frustration_score'])}, median marker-score "
        f"margin {_fmt(row['median_marker_score_margin'])}, and low-margin "
        f"fraction {_fmt(row['low_margin_fraction_lt_0_05'])}."
    )


def sample_level_sentence(sample_stability: pd.DataFrame) -> str:
    if sample_stability.empty:
        return "Sample-level Myeloid robustness summaries are pending."
    parts = []
    for row in sample_stability.to_dict(orient="records"):
        parts.append(
            f"{row['lesion_type']}: top-source frequency "
            f"{_fmt(row['myeloid_top_frequency_adequate'])} among "
            f"{int(row['n_myeloid_adequate_samples'])} adequate samples"
        )
    return (
        "At sample level, Myeloid robustness was heterogeneous ("
        + "; ".join(parts)
        + ")."
    )


def sparse_warning_sentence(claim_gating: pd.DataFrame) -> str:
    if claim_gating.empty:
        return "Sparse-category claim-gating summaries are pending."
    unsupported = claim_gating.loc[
        claim_gating["claim_gate"]
        .astype(str)
        .isin(["qc_warning_only", "supplement_only"])
    ].copy()
    if unsupported.empty:
        return "No sparse categories were downgraded by the current gate."
    names = ", ".join(unsupported["cell_type"].astype(str).tolist())
    min_cells = pd.to_numeric(unsupported["min_lesion_n_cells"], errors="coerce").min()
    cell_word = "cell" if int(min_cells) == 1 else "cells"
    return (
        f"The same pre-specified gate downgraded {names} to supplementary or QC-only "
        f"interpretation; the smallest lesion support among downgraded categories was "
        f"{int(min_cells)} {cell_word}."
    )


def build_polished_manuscript(
    *,
    component_recovery: pd.DataFrame,
    public_summary: pd.DataFrame,
    tool_comparison: pd.DataFrame,
    myeloid_summary: pd.DataFrame,
    claim_gating: pd.DataFrame,
    sample_stability: pd.DataFrame,
) -> str:
    return f"""# SheafSignal maps communication frustration in tissue signaling networks

Article type: Methods article

Authors: TBD

Affiliations: TBD

Correspondence: TBD

## Abstract

Cell-cell communication methods transform transcriptomes into candidate
ligand-receptor links, but they usually evaluate those links pairwise rather
than asking whether the resulting tissue-level communication network is
self-consistent. We present SheafSignal, a computational framework that models
cell-cell communication as a sheaf-valued flow over a biological graph and
uses Hodge decomposition to quantify edge-level frustration, directional
signal, local feedback-like structure and global circulation-like structure.
Controlled simulations recovered gradient, curl, harmonic and mixed-flow
components. In public tumor-microenvironment benchmarks spanning melanoma,
pancreatic cancer, breast cancer single-cell RNA-seq and breast Visium data,
SheafSignal identified context-specific frustration architectures rather than
a universal source cell type. In pancreatic cancer, pre-specified annotation,
sample-support and sparse-category gates retained Myeloid as the only
main-text cell-type-level computational signal. Comparisons with ligand-
receptor product scoring, LIANA, bounded nichenetr-engine scoring and a
mechanistic target-prior baseline showed alignment with existing communication
evidence while preserving a distinct inconsistency-focused readout.
SheafSignal provides a reproducible route for studying when inferred
communication is discordant with pathway-state structure, complementing
existing intensity-focused cell-cell communication tools.

## Introduction

Single-cell and spatial transcriptomics have made cell-cell communication
analysis a routine part of tissue profiling. Widely used methods including
CellChat, CellPhoneDB, NicheNet and LIANA prioritize candidate interactions by
combining ligand, receptor and, in some settings, downstream target evidence
[@cellchat_jin_2021; @cellphonedb_efremova_2020; @cellphonedb_troule_2025;
@nichenet_browaeys_2020; @nichenet_protocol_sangaram_2025;
@liana_plus_dimitrov_2024]. These approaches answer an essential question:
which sender-receiver pairs have plausible communication evidence? They do
not, by design, fully answer a different graph-level question: whether the
collection of inferred communication edges is self-consistent with tissue-wide
pathway-state change.

This distinction becomes important when communication is interpreted as a
network process rather than as an ordered list of ligand-receptor scores. A
high-scoring edge can be locally inconsistent with the receiver-state
transition, and a set of individually plausible edges can form feedback-like
or circulation-like structure that is not reducible to pairwise intensity.
Existing benchmarks have clarified how communication tools differ in their
resources and scoring assumptions [@ccc_comparison_dimitrov_2022], but a
method is still needed for quantifying inconsistency, feedback and circulation
directly on the inferred communication graph.

SheafSignal addresses this gap by changing the mathematical object under
analysis. For each directed sender-receiver edge, the method compares
ligand-receptor communication evidence with a receiver pathway-state
transition and treats the mismatch as sheaf energy, or communication
frustration. The resulting edge flow is then decomposed using graph Hodge
theory into gradient, curl and harmonic components [@hodge_rank_jiang_2011;
@hodge_laplacians_lim_2020], with cellular sheaves providing the language for
local-to-global consistency constraints [@cellular_sheaves_hansen_2019].
SheafSignal therefore asks not only where communication is strong, but where
it is inconsistent with the state changes it is expected to explain.

Here we evaluate SheafSignal as a reproducible methods framework. The study
uses controlled mathematical simulations, public tumor microenvironment
single-cell benchmarks, a public spatial transcriptomics demonstration,
external comparator alignments and explicit claim gates for sparse or
uncertain annotations. The central claim is methodological: SheafSignal
provides a graph-consistency view of cell-cell communication that complements,
but does not replace, established ligand-receptor prioritization.

## Results

### A sheaf-valued flow defines communication frustration

SheafSignal takes a cell-by-gene or profile-by-gene expression table,
cell-type annotations, ligand-receptor pairs and a pathway or target-gene set.
It builds a directed cell-type graph in which each sender-receiver edge carries
two quantities: communication evidence derived from sender ligand and receiver
receptor expression, and a pathway-state transition estimated in the receiver
context. Edge-level sheaf energy is the standardized mismatch between these
quantities. Node-level frustration scores summarize the share of outgoing
inconsistency contributed by each sender population, while global
gradient/curl/harmonic ratios summarize the structure of the resulting flow.

This design separates three outputs that are conflated in ordinary edge
ranking. A gradient-dominated flow is largely explainable by node potentials;
curl captures local feedback-like inconsistency around triangular motifs; and
harmonic energy represents residual circulation-like structure that is neither
node-potential nor local-triangle flow. The output therefore complements
ligand-receptor intensity by making network self-consistency measurable.

### Simulations validate the Hodge component implementation

We first tested whether the implementation recovers known graph-flow
structure. The simulation panel included pure gradient, pure curl, pure
harmonic and mixed-flow scenarios. {component_recovery_sentence(component_recovery)}
These controls validate the decomposition layer and define the interpretation
of the reported ratios. They are mathematical checks, not biological evidence.

### Public tumor benchmarks show context-specific frustration architecture

We next ran the same workflow across public tumor microenvironment datasets.
{public_benchmark_sentence(public_summary)} The top sender contributing
frustration differed across datasets: CAF/Fibroblast in melanoma, Myeloid in
pancreatic cancer, Tumor/Malignant in breast cancer single-cell data and T/NK
in the breast Visium demonstration. This pattern supports the method-level
claim that communication frustration is context-specific, not the biological
claim that a single cell type universally dominates tumor communication
inconsistency.

### Claim-gated pancreatic cancer analysis retains Myeloid as the main signal

GSE154778 pancreatic cancer was used as the detailed claim-gated case because
it includes primary and metastatic lesions and a complete public processed
matrix. The first-pass annotation is deliberately described as coarse
marker-based annotation. We therefore required minimum lesion-level cell
support, sample support, marker confidence and robustness evidence before any
cell-type-level result could enter the main narrative.

{myeloid_sentence(myeloid_summary)} {sample_level_sentence(sample_stability)}
This supports a Myeloid frustration signal as a computational hypothesis, not
as a confirmed mechanism. {sparse_warning_sentence(claim_gating)} These
downstream categories remain useful QC signals, but they are not used for
lesion-specific mechanism claims.

### Comparator alignment shows complementarity rather than broad superiority

SheafSignal was compared with conventional and external communication evidence
after aligning outputs at the sender-receiver edge level. {comparator_sentence(tool_comparison)}
The comparator panel shows that SheafSignal is not merely a relabelled
ligand-receptor product score, while also showing that it remains connected to
recognized communication evidence. The intended conclusion is complementarity:
existing tools prioritize communication evidence, whereas SheafSignal asks
whether those graph-level flows are consistent with pathway-state structure.

The NicheNet-related comparator is intentionally bounded. It uses the official
nichenetr scoring engine with a project-curated tumor-microenvironment prior
matrix, not a full pretrained NicheNet network benchmark. For this reason, the
manuscript does not claim broad superiority over NicheNet, CellChat,
CellPhoneDB, LIANA or niche-DE.

### Spatial analysis localizes hotspots with spot-level boundaries

The breast Visium case demonstrates how the framework extends to spatial
profiles. SheafSignal was run on spot-level profiles and spatial neighborhoods,
with k-neighbor sensitivity checks and spot-level QC. Because Visium spots can
contain mixed cell states and the current labels are marker-dominant rather
than histology-validated single-cell identities, these results are positioned
as hotspot localization and workflow demonstration. They are not presented as
histology-confirmed cell-type mechanisms.

## Discussion

SheafSignal reframes cell-cell communication analysis around consistency
rather than intensity alone. By representing communication as a sheaf-valued
flow and decomposing that flow with Hodge theory, the method reports where
communication edges are discordant with pathway-state transitions and whether
the resulting network structure is dominated by directional, local
feedback-like or global circulation-like components. This provides an
interpretive layer that is absent from pairwise ligand-receptor ranking.

The public benchmarks illustrate the practical value of this reframing.
Different tumor datasets showed different dominant frustration sources,
arguing against a universal cell-type explanation and in favor of dataset- and
context-specific analysis. The pancreatic cancer case also illustrates why
claim gating is necessary for high-impact computational biology: Myeloid
passes the current evidence gate, but sparse stromal and lymphoid categories
do not. The result is therefore a prioritized computational hypothesis for
follow-up, not a clinical or mechanistic proof.

The comparator analyses support the same boundary. Alignment with LIANA,
ligand-receptor product scoring, a mechanistic target-prior baseline and
bounded nichenetr-engine scoring indicates that SheafSignal remains connected
to established communication evidence. Discordance is also expected, because
SheafSignal measures inconsistency relative to pathway-state structure rather
than communication strength alone. The manuscript therefore avoids broad
superiority language and treats comparator evidence as a test of alignment,
non-equivalence and interpretability.

Several limitations are central to the current study. First, all disease
examples are based on public data and should be interpreted as computational
and hypothesis-generating. Second, some annotations are coarse, especially in
GSE154778 and the Visium case, so cell-type claims require explicit QC and
should not be overextended. Third, the current comparator set does not exhaust
all CCC tools or all possible NicheNet resources. Fourth, SheafSignal itself
does not provide evidence for clinical utility, treatment guidance or
therapeutic recommendations.

Future work should extend the framework to larger simulation stress tests,
additional public and private validation cohorts, fuller external tool
execution, and experimental perturbation of prioritized frustration sources.
The present study establishes the mathematical formulation, open software,
public-data benchmark suite and claim-safety framework needed for that next
stage.

## Methods

### Inputs and preprocessing

SheafSignal accepts expression data, cell annotations, ligand-receptor pairs
and pathway or target-gene sets. Single-cell data are summarized to cell-type
or sample-by-cell-type profiles for graph-level analysis after dataset-specific
preparation. Spatial data are analyzed at spot-profile level with explicit
spot-level interpretation boundaries. Public dataset accession, download,
checksum and preparation metadata are tracked in the dataset manifest.

### Communication flow and sheaf energy

For each directed sender-receiver pair, sender ligand expression and receiver
receptor expression define communication evidence. Receiver pathway state is
summarized from target-gene activity. Both quantities are standardized before
their mismatch is calculated. This mismatch is reported as edge-level sheaf
energy, with sender-level frustration scores computed from outgoing sheaf
energy.

### Hodge decomposition

The edge flow is decomposed into gradient, curl and harmonic components using
graph Hodge decomposition. Gradient energy captures the portion explainable by
node potentials, curl captures local feedback-like triangular structure, and
harmonic energy captures residual global circulation-like structure. Component
ratios are reported as fractions of total flow energy.

### Claim gating

The GSE154778 pancreatic cancer analysis used a pre-specified evidence-tier
gate. A category was eligible for main-text interpretation only when it had
adequate cell support and sample support within lesion strata, acceptable
marker confidence and robustness evidence. Sparse or low-confidence categories
were downgraded to supplementary QC interpretation before biological
discussion.

### Comparator analyses

Comparator outputs were aligned at the sender-receiver edge level. The current
panel includes a ligand-receptor product baseline, LIANA imports,
MechanisticTargetPrior scoring and bounded nichenetr-engine scoring with a
project-curated tumor-microenvironment prior matrix. The comparison tests
alignment and complementarity, not broad tool superiority.

### Reproducibility and availability

All source code, tests, dataset manifests, figure manifests, release manifests,
claim-safety audits and manuscript-supporting tables are generated within the
repository. Large processed objects are prepared for Zenodo deposition, while
code and small result tables are prepared for GitHub release.

## Data Availability

Raw public data remain available from the original GEO and 10x Genomics
sources listed in `metadata/datasets.tsv`. Frozen processed objects are
prepared for Zenodo deposition. The Zenodo DOI must be inserted after the
deposition is published.

## Code Availability

Source code, tests, benchmark scripts and small result tables are prepared for
public GitHub release. The final repository URL must be inserted after public
release.

## Acknowledgements

TBD.

## Author Contributions

TBD.

## Competing Interests

TBD.

## Boundary Statement

This is a computational methods manuscript. It does not claim clinical
utility, treatment guidance, treatment-response prediction, guaranteed journal
acceptance or broad superiority over established cell-cell communication
tools.
"""


def build_claim_tracker() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "claim_id": "C1_method_object",
                "claim": "SheafSignal models communication as a sheaf-valued graph flow.",
                "evidence_source": "src/sheafsignal and Methods text",
                "allowed_scope": "methodological formulation",
                "forbidden_extension": "do not claim clinical utility or therapeutic guidance",
            },
            {
                "claim_id": "C2_hodge_components",
                "claim": "Gradient, curl and harmonic components are recovered in controlled simulations.",
                "evidence_source": "benchmarks/results/component_recovery.csv",
                "allowed_scope": "implementation validation",
                "forbidden_extension": "do not use simulations as disease biology evidence",
            },
            {
                "claim_id": "C3_public_context_specificity",
                "claim": "Public TME benchmarks show context-specific frustration architectures.",
                "evidence_source": "benchmarks/results/public_tme_sheafsignal_summary.csv",
                "allowed_scope": "public-data methods benchmark",
                "forbidden_extension": "do not claim a universal dominant source cell type",
            },
            {
                "claim_id": "C4_gse154778_myeloid",
                "claim": "Myeloid is the only GSE154778 main-text cell-type-level computational signal.",
                "evidence_source": "benchmarks/results/gse154778_pdac_scrna/qc/myeloid_claim_readiness_summary.csv",
                "allowed_scope": "claim-gated computational hypothesis",
                "forbidden_extension": "do not present as validated mechanism or clinical biomarker",
            },
            {
                "claim_id": "C5_sparse_categories",
                "claim": "Sparse cell types are downgraded to supplement/QC interpretation.",
                "evidence_source": "benchmarks/results/gse154778_pdac_scrna/qc/claim_gating_by_cell_type.csv",
                "allowed_scope": "evidence limitation and QC warning",
                "forbidden_extension": "do not force sparse categories into main mechanistic claims",
            },
            {
                "claim_id": "C6_comparators",
                "claim": "Comparator results support alignment and complementarity.",
                "evidence_source": "benchmarks/results/tool_comparison.csv",
                "allowed_scope": "alignment, non-equivalence and bounded comparison",
                "forbidden_extension": "do not claim broad superiority over all CCC tools",
            },
            {
                "claim_id": "C7_spatial",
                "claim": "Spatial analysis demonstrates hotspot localization under spot-level boundaries.",
                "evidence_source": "benchmarks/results/tenx_breast_visium/spatial and QC tables",
                "allowed_scope": "workflow demonstration",
                "forbidden_extension": "do not claim histology-confirmed single-cell mechanism",
            },
        ]
    )


def build_claim_tracked_markdown(claims: pd.DataFrame) -> str:
    lines = [
        "# SheafSignal SCI Manuscript V2 Claim Tracker",
        "",
        "This tracker maps the polished manuscript's main claims to the current",
        "evidence package and states the boundary that must be preserved during",
        "journal revision.",
        "",
        "| Claim ID | Claim | Evidence source | Allowed scope | Forbidden extension |",
        "|---|---|---|---|---|",
    ]
    for row in claims.to_dict(orient="records"):
        lines.append(
            f"| `{row['claim_id']}` | {row['claim']} | `{row['evidence_source']}` | "
            f"{row['allowed_scope']} | {row['forbidden_extension']} |"
        )
    lines.extend(
        [
            "",
            "## Author-Owned Pending Items",
            "",
            "- Author names, affiliations, CRediT roles, competing interests and final",
            "  ethics/data-use wording remain TBD.",
            "- Zenodo DOI and public GitHub URL must be inserted before submission.",
            "- The manuscript still requires journal-system formatting and final figure",
            "  assembly after DOI and author metadata are frozen.",
            "",
        ]
    )
    return "\n".join(lines)


def build_changelog() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "change_id": "V2_001",
                "section": "Whole manuscript",
                "change": "Rewrote v1 from result-list style into a tighter gap-method-validation-boundary narrative.",
                "reason": "Improve Nature Methods editorial fit while preserving evidence boundaries.",
            },
            {
                "change_id": "V2_002",
                "section": "Abstract",
                "change": "Added explicit distinction between communication intensity and communication inconsistency.",
                "reason": "Make the method contribution clear in the first paragraph.",
            },
            {
                "change_id": "V2_003",
                "section": "Results",
                "change": "Separated method definition, simulations, public benchmarks, GSE154778 claim gating, comparators and spatial boundaries.",
                "reason": "Keep each evidence layer interpretable and auditable.",
            },
            {
                "change_id": "V2_004",
                "section": "Discussion",
                "change": "Strengthened limitation language for public-data, coarse annotation, bounded NicheNet and clinical-utility boundaries.",
                "reason": "Reduce reviewer risk from overclaiming.",
            },
            {
                "change_id": "V2_005",
                "section": "Claim tracker",
                "change": "Added a manuscript-specific claim map with forbidden extensions.",
                "reason": "Support high-impact revision discipline and reviewer response.",
            },
        ]
    )


def build_editorial_audit(manuscript: str) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    unresolved_refs = re.findall(r"\[REF:[^\]]+\]", manuscript, flags=re.IGNORECASE)
    rows.append(
        {
            "audit_id": "references_no_placeholder",
            "status": "pass" if not unresolved_refs else "fail",
            "evidence": f"unresolved_placeholders={len(unresolved_refs)}",
            "required_action": "Resolve all [REF: ...] placeholders.",
        }
    )
    rows.append(
        {
            "audit_id": "boundary_statement_present",
            "status": "pass" if "does not claim clinical" in manuscript else "fail",
            "evidence": "Boundary Statement section",
            "required_action": "Keep clinical and therapeutic boundaries explicit.",
        }
    )
    rows.append(
        {
            "audit_id": "nichenet_boundary_present",
            "status": (
                "pass"
                if "not a full pretrained NicheNet network benchmark" in manuscript
                else "fail"
            ),
            "evidence": "Comparator Results section",
            "required_action": "State bounded nichenetr-engine scope.",
        }
    )
    rows.append(
        {
            "audit_id": "sparse_category_boundary_present",
            "status": (
                "pass"
                if "sparse" in manuscript.lower() and "qc-only" in manuscript.lower()
                else "fail"
            ),
            "evidence": "GSE154778 claim-gated Results section",
            "required_action": "Keep sparse categories out of main mechanistic claims.",
        }
    )
    forbidden_hits = []
    for name, pattern in FORBIDDEN_PATTERNS.items():
        if pattern.search(manuscript):
            forbidden_hits.append(name)
    rows.append(
        {
            "audit_id": "forbidden_positive_claims_absent",
            "status": "pass" if not forbidden_hits else "fail",
            "evidence": (
                ";".join(forbidden_hits)
                if forbidden_hits
                else "no forbidden positive claim patterns"
            ),
            "required_action": "Rewrite any guarantee, broad-superiority, clinical-utility or therapeutic-guidance wording.",
        }
    )
    rows.append(
        {
            "audit_id": "author_metadata_pending",
            "status": (
                "pending_author_action" if "Authors: TBD" in manuscript else "pass"
            ),
            "evidence": "Authors: TBD",
            "required_action": "Authors must fill names, affiliations, CRediT roles and competing interests.",
        }
    )
    rows.append(
        {
            "audit_id": "zenodo_and_github_pending",
            "status": "pending_author_action",
            "evidence": "Data Availability and Code Availability still require final DOI/URL insertion.",
            "required_action": "Mint Zenodo DOI and publish GitHub repository before final submission.",
        }
    )
    return pd.DataFrame(rows)


def build_package(
    *,
    root: Path,
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {key: output_dir / filename for key, filename in OUTPUT_FILES.items()}
    component_recovery = _read_table(root / "benchmarks/results/component_recovery.csv")
    public_summary = _read_table(
        root / "benchmarks/results/public_tme_sheafsignal_summary.csv"
    )
    tool_comparison = _read_table(root / "benchmarks/results/tool_comparison.csv")
    myeloid_summary = _read_table(
        root
        / "benchmarks/results/gse154778_pdac_scrna/qc/myeloid_claim_readiness_summary.csv"
    )
    claim_gating = _read_table(
        root
        / "benchmarks/results/gse154778_pdac_scrna/qc/claim_gating_by_cell_type.csv"
    )
    sample_stability = _read_table(
        root / "benchmarks/results/gse154778_pdac_scrna/stability/"
        "sample_level_myeloid_stability_summary.csv"
    )
    manuscript = build_polished_manuscript(
        component_recovery=component_recovery,
        public_summary=public_summary,
        tool_comparison=tool_comparison,
        myeloid_summary=myeloid_summary,
        claim_gating=claim_gating,
        sample_stability=sample_stability,
    )
    claims = build_claim_tracker()
    _write_text_atomic(paths["manuscript"], manuscript)
    _write_text_atomic(paths["claim_tracked"], build_claim_tracked_markdown(claims))
    _write_table_atomic(paths["editorial_audit"], build_editorial_audit(manuscript))
    _write_table_atomic(paths["changelog"], build_changelog())
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-dir", default="manuscript")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    paths = build_package(root=root, output_dir=root / args.output_dir)
    for path in paths.values():
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
