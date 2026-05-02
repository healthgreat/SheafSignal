# Main Figure Legends Draft

## Figure 1. SheafSignal formulation of communication frustration.

Schematic of the SheafSignal workflow. Ligand-receptor evidence is represented
as a directed sender-receiver communication flow, receiver pathway state is
represented on graph nodes, and sheaf energy quantifies mismatch between the
edge signal and node-state transition. Hodge decomposition separates the flow
into gradient, curl and harmonic components. This figure supports the
mathematical-object claim only; it does not claim clinical utility or broad
superiority over existing communication tools.

Source evidence: `src/sheafsignal`, `manuscript/nature_methods_package/05_claim_evidence_map.tsv`,
`figures/publication_figure1_sheafsignal_concept.pdf`.

## Figure 2. Controlled recovery of Hodge communication components.

Simulation benchmark showing recovery of pre-specified gradient, curl,
harmonic and mixed flow structure. gradient_chain: gradient 1.000, curl 0.000, harmonic 0.000; triangle_curl: gradient 0.000, curl 1.000, harmonic 0.000; harmonic_ring: gradient 0.000, curl 0.000, harmonic 1.000; mixed: gradient 0.446, curl 0.286, harmonic 0.268.
These simulations validate component separation under controlled settings and
should not be interpreted as biological validation.

Source evidence: `benchmarks/results/component_recovery.csv`,
`figures/publication_figure2_component_recovery.pdf`.

## Figure 3. Public tumor microenvironment benchmarks.

Summary of completed public tumor microenvironment benchmarks analyzed with
the same SheafSignal workflow. The panel is intended to compare dataset-level
sheaf-energy summaries and top computational rankings under each dataset's
annotation and processing version. It supports dataset-dependent computational
readouts, not a universal source-cell mechanism across cancers.

Source evidence: `benchmarks/results/public_tme_sheafsignal_summary.csv`,
`figures/publication_figure3_tme_summary.pdf`.

## Figure 4. GSE154778 Myeloid claim gating and robustness.

GSE154778 pancreatic cancer analysis with evidence-tier gating, lesion
stratification, annotation QC and sample-level robustness checks. Under the
Round2 full Scanpy annotation, Myeloid remains a lesion-stratified and
sample-level computational signal, but it is not main-claim ready because the
overall expression-mode top source is CAF/Fibroblast. Sparse stromal and
lymphoid categories remain supplementary/QC context and are not used for main
mechanistic claims.

Source evidence: `benchmarks/results/gse154778_pdac_scrna/qc/`,
`benchmarks/results/gse154778_pdac_scrna/stability/`,
`benchmarks/results/gse154778_pdac_scrna/stratified/`.

## Figure 5. Comparator alignment and complementarity.

Edge-level SheafSignal results are aligned against ligand-receptor product
baseline, LIANA, bounded nichenetr-engine scoring with a project-curated TME
prior, and MechanisticTargetPrior outputs. LIANA: 3 datasets, Spearman 0.074-0.699; LRProductBaseline: 4 datasets, Spearman -0.050-0.720; MechanisticTargetPrior: 3 datasets, Spearman 0.176-0.643; NicheNet: 3 datasets, Spearman 0.184-0.750.
This figure supports benchmarkability and complementarity; it must not be captioned as broad superiority over all cell-cell communication tools.

Source evidence: `benchmarks/results/tool_comparison.csv`,
`benchmarks/results/*/comparators/sheafsignal_vs_*.csv`.
