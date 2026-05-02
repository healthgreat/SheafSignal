# SheafSignal Round 1 Multi-Agent Review Summary

Date: 2026-05-02

Scope: Internal multi-agent adversarial review for a 20-50 IF computational biology methods manuscript.

Reviewers:

- Methods Reviewer: Reject / major revision; confidence 38/100.
- Single-cell/spatial Reviewer: Reject / major revision; confidence 32/100.
- Statistics Reviewer: Reject / major revision; confidence 42/100.
- Reproducibility Reviewer: Reject for clean-clone reproducibility; confidence 38/100.
- High-impact Editor: Reject / do not submit now; confidence 38/100.

## Overall Verdict

Do not submit now.

The current package is a serious local methods prototype with real engineering progress, comparator imports, release manifests, and multiple benchmark layers. However, all five independent reviewers converged on the same conclusion: the manuscript is not yet defensible for a 20-50 IF journal because the remaining problems are structural, not cosmetic.

## Consensus Fatal Issues

1. Method novelty is not yet mathematically protected.
   The current implementation can be attacked as LR product scoring plus pathway mismatch plus standard graph Hodge decomposition. Reviewers found no fully implemented stalks, restriction maps, sheaf coboundary, or sheaf Laplacian. The manuscript must either implement a formal sheaf object or downgrade wording to an integrated graph-consistency/Hodge workflow.

2. GSE154778 full independent annotation is incomplete.
   The completed Scanpy reannotation is a 500-cell smoke run from sample P03 Primary, not the full 14,926-cell PDAC dataset. This cannot validate lesion-stratified or Myeloid-centered claims.

3. Several GSE154778 result tables appear generated from different annotation states.
   Metadata and stratified result tables disagree on cell-type counts, especially Myeloid and Unknown. This creates a stale-output/provenance risk that must be fixed before any manuscript-facing claim.

4. Real-data statistical support is weak.
   Current manuscript-facing outputs use 100 permutations; node-level and edge-level FDR support is not strong enough. Myeloid in GSE154778 remains hypothesis-generating, not a main claim.

5. Sample-level evidence is heterogeneous.
   Myeloid top-frequency differs between Primary and Metastatic samples. Cell-level bootstrap is not enough; sample-level/pseudobulk uncertainty is required.

6. Real-data curl/harmonic signals are small.
   Real datasets are dominated by gradient components. Any wording such as "feedback architecture", "circulation architecture", or strong biological mechanism should be removed or restricted to mathematical decomposition language.

7. Reproducibility is not public-release ready.
   GitHub is not a committed public release, Zenodo DOI is not minted, metadata still contains TBD/PENDING_ZENODO_RELEASE fields, and lockfiles are insufficient for clean-clone reproduction.

8. Manuscript-facing documents are inconsistent.
   Some files say CellChat/CellPhoneDB are pending, while comparator tables contain completed imports. Some claim maps still allow GSE154778 Myeloid main-text wording despite newer downgrade summaries.

## Priority Repair Order

1. Freeze claim language immediately.
   Remove main-claim language for GSE154778 Myeloid and real-data feedback/frustration architecture until reanalysis supports it.

2. Complete full GSE154778 reannotation.
   Run Scanpy or Seurat on all cells with QC, normalization, HVG, PCA, neighbors, Leiden resolution sweep, doublet detection, marker validation, and annotation sensitivity.

3. Add provenance hashing.
   Every result table should record metadata hash, annotation version, LR database version, pathway set version, and command provenance.

4. Re-run all GSE154778 outputs from one frozen annotation.
   Regenerate SheafSignal, stratified, claim gating, stability, permutation, bootstrap, and QC outputs.

5. Upgrade statistics.
   Use sample/lesion-stratified permutations, at least 1000 permutations for manuscript runs, pooled FDR families, sample-level CIs, and leave-one-sample-out stability.

6. Protect method novelty.
   Either implement formal sheaf primitives or downgrade the claim. Add simulations from synthetic expression to LR flow/pathway response with known consistency/inconsistency ground truth and ablations against LR-only, pathway-only, Hodge-only, centrality, and graph smoothness baselines.

7. Synchronize all documents.
   Update README, benchmark plan, claim evidence map, submission readiness report, manuscript, and release reports so they describe the same state.

8. Only after scientific hardening, mint DOI and publish GitHub.
   Do not mint a final Zenodo DOI while scientific blockers remain.

## Current Journal Interpretation

Current state: not submission-ready for 20-50 IF.

Near-term realistic state after repair: credible methods-journal candidate, likely presubmission inquiry rather than direct Nature Methods submission.

Strict Nature Methods route remains possible only if the method-novelty issue is solved formally and the real-data claims are made conservative, statistically hardened, and reproducible.

