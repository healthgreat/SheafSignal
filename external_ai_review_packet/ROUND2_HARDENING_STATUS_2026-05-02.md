# SheafSignal Round 2 Hardening Status

Date: 2026-05-02

Update: the rank-one sheaf layer described below is now legacy/backward-compatible
output. The current method-facing response to returned reviews is the Round 3
higher-rank LR-channel sheaf report:
`external_ai_review_packet/ROUND3_HIGHER_RANK_SHEAF_RESPONSE_2026-05-06.md`.

## Completed In This Round

- Implemented an explicit rank-one cellular sheaf layer:
  - vertex stalk: `R_pathway_state`
  - edge stalk: `R_communication_observation`
  - restrictions: sender `-1`, receiver `+1`
  - coboundary expected flow: `receiver_pathway - sender_pathway`
  - primary residual: `sheaf_residual = flow_z - coboundary_expected_flow`
- Switched primary Hodge decomposition to `sheaf_residual`.
- Preserved secondary communication-flow Hodge fields as `communication_hodge_*`.
- Added generated sheaf contract outputs:
  - `cellular_sheaf_restrictions.csv`
  - `cellular_sheaf_laplacian.csv`
  - `provenance.json`
- Created isolated conda environment `sheafsignal-reannotation`.
- Completed full GSE154778 Scanpy reannotation:
  - 14,926 cells after filtering
  - 16 samples
  - lesion types: Metastatic and Primary
  - annotation version: `scanpy_full_v1`
- Froze Scanpy annotation into prepared inputs:
  - `data/processed/gse154778_pdac_scrna_scanpy_full_v1/expression.csv`
  - `data/processed/gse154778_pdac_scrna_scanpy_full_v1/metadata.csv`
  - `data/processed/gse154778_pdac_scrna_scanpy_full_v1/profiles.csv`
  - `data/processed/gse154778_pdac_scrna_scanpy_full_v1/annotation_summary.csv`
- Updated `metadata/datasets.tsv` so GSE154778 points to the frozen Scanpy-prepared inputs.
- Ran round2 GSE154778 benchmark with 1000 sample-stratified permutations:
  - output root: `benchmarks/results/round2_hardening/`
  - `permutation_strata_col=sample_id`
  - `annotation_version=scanpy_full_v1`
- Recomputed GSE154778 QC, lesion stratification, bootstrap stability, sample-level stability, and claim gating under the frozen annotation.
- Updated claim evidence map so GSE154778 Myeloid is `supplement_with_boundary`, not a main-text biological claim.
- Added a synthetic expression-to-LR-to-pathway ground-truth benchmark with AUROC/AP recovery metrics against LR-flow, pathway-gradient, Hodge-only, graph-centrality, and graph-smoothness baselines.

## Key Round2 Results

- Overall GSE154778 expression-mode top frustration cell type: `CAF/Fibroblast`.
- GSE154778 expression-mode Myeloid:
  - `frustration_score=0.1845`
  - `frustration_fdr=0.001998`
  - not expression-mode top source.
- Lesion-stratified top source:
  - Primary: Myeloid
  - Metastatic: Myeloid
- Sample-level Myeloid top frequency:
  - all completed samples: 0.80
  - adequate samples: 0.727
  - Primary adequate samples: 0.667
  - Metastatic adequate samples: 0.80
- Claim gate:
  - Myeloid `main_claim_ready=False`
  - Myeloid `claim_gate=supplement_only`
- Synthetic ground-truth benchmark:
  - SheafSignal AP: 1.00, 0.917, 0.867 at noise SD 0, 0.05, 0.10
  - LR-flow baseline AP: 0.587, 0.610, 0.610
  - Hodge-only baseline AP: 0.317, 0.317, 0.317
  - Graph-centrality baseline AP: 0.633, 0.633, 0.633
  - Graph-smoothness baseline AP: 0.633, 0.633, 0.633
  - output: `benchmarks/results/simulation/sheaf_ground_truth_recovery.csv`

## Interpretation Boundary

Round2 strengthens the computational evidence that Myeloid is a robust lesion-stratified/sample-level signal under `scanpy_full_v1`, but it also shows that the overall expression-mode top source is CAF/Fibroblast and that Metastatic CAF/Fibroblast is underpowered. Therefore, Myeloid remains a supplement-level computational hypothesis and cannot be promoted as a standalone main biological source claim.

## Remaining Open Items

- Define pooled FDR families across all datasets before manuscript finalization.
- Synchronize older manuscript drafts and README sections that still contain stale language.
- Keep Zenodo/GitHub final release on hold until scientific hardening is complete.
