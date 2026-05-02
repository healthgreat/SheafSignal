# SheafSignal External AI Pre-Review Exposure Report

Date: 2026-05-01

Purpose: this report is written for adversarial pre-review by another AI or a
human coauthor before public release and journal submission. The goal is not to
market the manuscript, but to expose weak assumptions, overclaiming risks,
missing external actions, and likely reviewer objections.

## 1. Current Submission Status

Current local decision: `NO_GO`.

This is not because the local code/test evidence chain failed. The current
blocking items are external/publication actions:

1. Zenodo DOI has not been minted.
2. The minted DOI has not been inserted into Data Availability.
3. `metadata/datasets.tsv` still contains the pending Zenodo release marker.

Current local readiness from `manuscript/SUBMISSION_READINESS_REPORT.md`:

- Target route: 20-50 IF computational methods manuscript.
- Local readiness: `near_ready_pending_doi`.
- Reproducibility release status: `zenodo_ready_no_doi`.
- Nature Methods route remains high-risk; acceptance is not guaranteed.

Current technical verification:

- `python -m pytest`: 152 passed, 1 warning.
- `ruff check scripts tests`: passed.
- `scripts/release_audit.py`: passed.
- Main figure quality audit: passed for 5 main figures.
- Benchmark result contract audit: passed.
- Claim safety audit: passed with boundary notes.
- Method reporting audit: passed with boundary notes.
- Submission provenance audit: passed with external/author pending rows.

Latest release archive:

- GitHub archive: `release/archives/sheafsignal_github_release.zip`
- Zenodo archive: `release/archives/sheafsignal_zenodo_upload.zip`
- Zenodo archive size: 9.445 MB
- Zenodo archive SHA256:
  `6796cf09df995f212cea805ede6ead0d4edeb057a032d7a3d079067af5dc18fb`

## 2. Manuscript Core Claim

Proposed central claim:

> SheafSignal reframes cell-cell communication as a sheaf-valued flow over a
> biological graph and uses Hodge decomposition to quantify communication
> inconsistency, feedback/curl, and global circulation features that are not
> captured by communication-intensity tools alone.

This claim is currently the safest high-level framing. The manuscript should
not be framed as a clinical predictor, therapeutic guide, or broad proof that
one cell type drives all tumor microenvironment communication.

## 3. Evidence Currently Supporting The Claim

### 3.1 Algorithmic Evidence

Source: `benchmarks/results/component_recovery.csv`

Controlled simulations recover the intended dominant components:

- `gradient_chain`: gradient ratio approximately 1.0.
- `triangle_curl`: curl ratio 1.0.
- `harmonic_ring`: harmonic ratio 1.0.
- `mixed`: gradient/curl/harmonic components are all non-zero.

Boundary: this supports mathematical component recovery under controlled
ground truth. It does not prove biological truth in real tumors.

### 3.2 Public TME Benchmarks

Source: `benchmarks/results/public_tme_sheafsignal_summary.csv`

Completed real/public benchmark rows include:

- GSE72056 melanoma scRNA-seq: completed; top source `CAF/Fibroblast`.
- GSE154778 PDAC scRNA-seq: completed; top source `Myeloid`.
- GSE176078 breast cancer scRNA-seq: completed; top source `Tumor/Malignant`.
- 10x breast cancer Visium: completed; top source `T/NK`.

Boundary: these support context-specific computational frustration
architecture. They should not be overgeneralized into one universal cell-type
mechanism.

### 3.3 GSE154778 Claim Gating

Source:
`benchmarks/results/gse154778_pdac_scrna/qc/claim_gating_by_cell_type.csv`

The current main-claim eligible GSE154778 cell type is Myeloid:

- total Myeloid cells: 1819
- minimum lesion n cells: 497
- minimum lesion n samples: 6
- all lesion strata adequate: true
- bootstrap top frequency: 1.0
- manuscript use: `main_text_candidate`

Important boundary:

- CAF/Fibroblast has only 2 metastatic cells and is `qc_warning_only`.
- Endothelial, B/Plasma, Unknown are also `qc_warning_only`.
- Tumor/Epithelial and T/NK are adequate but not top-in-all-lesions; they remain
  supplement/context rather than main mechanism.

Safe sentence:

> Myeloid remains the main claim-gated computational signal in GSE154778,
> whereas sparse stromal and lymphoid categories are retained only as
> supplementary QC context.

Unsafe sentence:

> Metastatic CAF/Fibroblast is a biological frustration driver.

### 3.4 Sample-Level Myeloid Robustness

Source:
`benchmarks/results/gse154778_pdac_scrna/stability/sample_level_myeloid_stability_summary.csv`

Current sample-level result:

- Metastatic: Myeloid top frequency 0.833 across completed samples and 0.75
  across adequate samples.
- Primary: Myeloid top frequency 0.4 across completed samples and 0.429 across
  adequate samples.
- All samples: Myeloid top frequency 0.563 completed and 0.545 adequate.

Boundary: this supports a lesion-stratified Myeloid signal, especially in
metastatic samples, but it also shows patient/sample heterogeneity. Do not say
the signal is uniform across all patients.

### 3.5 Spatial Visium Evidence

Source:
`benchmarks/results/tenx_breast_visium/spatial/qc/spatial_hotspot_qc_summary.csv`

Current spatial QC:

- 3798 spots.
- Reference k neighbors: 6.
- Minimum Spearman across k settings: 0.9309.
- Minimum top-50 overlap across k settings: 0.86.

Boundary: this supports neighborhood-parameter stability of spatial hotspot
ranks. It does not prove single-cell-level cell identity or histology-validated
mechanism.

### 3.6 Comparator Evidence

Source: `benchmarks/results/tool_comparison.csv`

Completed comparator evidence:

- LRProductBaseline completed for 5 datasets.
- LIANA completed/imported for 3 public scRNA-seq datasets.
- NicheNet/nichenetr-engine style import completed for 3 public scRNA-seq
  datasets.
- MechanisticTargetPrior completed for 3 public scRNA-seq datasets.

Boundary:

- CellChat, CellPhoneDB, and niche-DE remain not run / external-tool pending.
- Current NicheNet evidence uses a bounded project-curated TME prior matrix and
  should not be described as a full pretrained NicheNet network benchmark unless
  that resource is explicitly added.
- Comparator results should be used to show non-redundancy / alignment /
  discordance, not broad superiority.

## 4. Likely Reviewer Objections

### 4.1 Novelty / Rebranding Risk

Likely objection:

> Is this just a ligand-receptor scoring method with graph/Hodge terminology?

Current mitigation:

- Sheaf-valued flow and Hodge decomposition primitives exist in code and
  methods.
- Controlled simulations recover gradient/curl/harmonic components.

Remaining risk:

- The manuscript must clearly compare against existing graph signal processing,
  Hodge decomposition, sheaf learning, and CCC literature.
- A high-impact reviewer may ask for a stronger literature overlap audit:
  "What exactly is new mathematically and biologically?"

Required defensive wording:

- Claim a distinct mathematical object and measured communication consistency.
- Do not claim the first ever use of sheaves/Hodge in biology unless a formal
  literature search supports it.

### 4.2 Biological Validation Risk

Likely objection:

> Public-data computational signal is not enough to make a cancer biology
> mechanism claim.

Current mitigation:

- The manuscript is framed as a methods manuscript, not a clinical or mechanistic
  cancer paper.
- Claim gating prevents sparse-cell overinterpretation.

Remaining risk:

- No wet-lab perturbation validation.
- No independent histology review for Visium hotspots.
- No matched clinical outcome validation.
- GSE154778 uses coarse marker-based annotation, not author-validated
  cell-type labels.

Safe boundary:

> These analyses nominate computational frustration hypotheses rather than
> proving causal tumor-microenvironment mechanisms.

### 4.3 GSE154778 Annotation Risk

Likely objection:

> The Myeloid result depends on coarse marker-based annotation.

Current mitigation:

- Myeloid markers are explicitly checked.
- Low-margin and Unknown cells are flagged.
- Sparse categories are excluded from main claims.

Remaining risk:

- No Scanpy/Seurat reclustering layer yet.
- No author annotation import yet.
- No independent expert cell-type curation.

Potential fix:

1. Search for author/third-party GSE154778 annotation.
2. Add optional Seurat/scanpy reannotation workflow.
3. Repeat Myeloid claim gate under alternative annotation.

### 4.4 Comparator Scope Risk

Likely objection:

> Why are CellChat, CellPhoneDB, and niche-DE listed but not completed?

Current mitigation:

- The manuscript does not claim those are completed.
- LIANA, LRProductBaseline, bounded NicheNet, and MechanisticTargetPrior are
  completed.

Remaining risk:

- Nature Methods reviewers may expect direct comparison with CellChat,
  CellPhoneDB, and/or niche-DE because they are widely known.
- If those tools remain absent, the text must be very precise: the comparator
  benchmark is not exhaustive.

Potential fix:

1. Add at least CellPhoneDB or CellChat for the three scRNA-seq datasets.
2. If niche-DE is not a direct CCC comparator, explain scope or move it to
   related-method discussion rather than benchmark claim.

### 4.5 Effect Size / Interpretability Risk

Likely objection:

> Gradient ratios dominate real datasets; curl ratios are small. Are feedback
> claims meaningful?

Current observation:

- Real public datasets show gradient ratios around 0.96 to 0.98.
- Curl ratios are present but small.
- Harmonic ratios are near zero in current real summaries.

Remaining risk:

- The manuscript should explain why small curl ratios can still identify
  biologically meaningful local inconsistencies, or reduce emphasis on feedback
  loops in real data.
- "feedback architecture" may sound stronger than the observed real-data curl
  magnitude supports.

Potential fix:

- Report edge-level and node-level sheaf energy as the main output.
- Treat curl as a secondary component, unless additional datasets show stronger
  curl/harmonic structure.

### 4.6 Spatial Interpretation Risk

Likely objection:

> Visium spots are not cells, and marker-dominant spot programs are not
> validated cell types.

Current mitigation:

- Spatial QC explicitly warns that it is hotspot localization context, not
  single-cell identity proof.

Remaining risk:

- Avoid stating that a spot-level T/NK signal proves T/NK cells are the
  biological source.

Potential fix:

- Add histology or spatial-domain annotation if available.
- Keep Visium as a methods demonstration, not a mechanism pillar.

### 4.7 Reproducibility / Public Release Risk

Likely objection:

> The DOI and public repository are not yet available.

Current mitigation:

- Release archives, manifests, checksums, and upload instructions exist.

Remaining risk:

- Zenodo DOI is not minted.
- GitHub public repository URL is still not final.
- Author metadata is incomplete.

Potential fix:

1. Fill author metadata and GitHub URL.
2. Create Zenodo draft.
3. Review draft.
4. Publish Zenodo DOI.
5. Run `scripts/finalize_zenodo_doi.py --doi <ZENODO_DOI>`.
6. Rebuild release/readiness reports.

### 4.8 Journal Fit Risk

Likely objection:

> This is useful but may not reach Nature Methods / 20-50 IF without broader
> validation or community adoption.

Current rationale:

- The method has a distinct mathematical framing and reproducible public-data
  benchmark package.
- The journal route board lists Nature Methods as the best aligned high-risk
  first submission, with other 20-50 IF fallback routes.

Remaining risk:

- "Top journal" fit depends on novelty clarity, comparator completeness,
  editorial timing, and perceived biological breadth.
- No acceptance can be guaranteed.

Potential fallback framing:

- Strong computational methods journal route if Nature Methods declines.
- Cancer application route only if biological validation is strengthened.

## 5. Claims Allowed vs Not Allowed

### Allowed Claims

1. SheafSignal reframes cell-cell communication as sheaf-valued flow over a
   biological graph.
2. Hodge decomposition separates gradient, curl, and harmonic components under
   controlled simulations.
3. SheafSignal reports communication inconsistency/frustration signals not
   reducible to ligand-receptor intensity alone.
4. Public TME benchmarks show context-specific computational frustration
   architecture across PDAC, melanoma, breast cancer, and Visium examples.
5. In GSE154778, Myeloid is the only main-claim candidate after evidence-tier
   gating.

### Not Allowed Claims

1. Guaranteed publication in a 20-50 IF journal.
2. Clinical utility, diagnosis, prognosis, or therapy guidance.
3. Broad superiority over all CCC tools.
4. Full pretrained NicheNet benchmarking.
5. Strong biological claims from sparse cell types.
6. Single-cell identity claims from Visium marker-dominant spots.
7. Universal Myeloid mechanism across all tumor types.

## 6. Highest-Priority Fixes Before Submission

### Must Fix Before Any Submission

1. Mint Zenodo DOI and insert it into Data Availability and
   `metadata/datasets.tsv`.
2. Publish or prepare the GitHub repository with the final release archive.
3. Complete author metadata, affiliations, CRediT roles, competing interests,
   ethics/data-use wording, and corresponding author information.
4. Run final blocker gate and ensure it no longer says `NO_GO`.

### Strongly Recommended Scientific Fixes

1. Add a formal novelty/overlap table against CCC, graph signal processing,
   Hodge, and sheaf-learning methods.
2. Add at least one more widely recognized CCC comparator if feasible:
   CellChat or CellPhoneDB is the strongest practical addition.
3. Validate GSE154778 Myeloid under an alternative annotation source or a
   lightweight independent reannotation workflow.
4. Add sensitivity analysis for ligand-receptor database choice, pathway/gene
   set choice, and edge construction thresholds.
5. Reduce emphasis on "feedback architecture" unless curl/harmonic results are
   made more compelling in real data.

### Manuscript Wording Fixes

1. Use "computational signal", "hypothesis-generating", and "claim-gated" for
   real-data biological interpretation.
2. Do not use "driver", "causal", "therapeutic target", or "clinical utility".
3. State explicitly that public datasets and processed objects are traceable,
   but the DOI is pending until Zenodo publication.
4. Keep sparse-cell warnings in the Results, not only in Supplementary Methods.

## 7. Suggested Adversarial Prompt For Another AI

Copy the following prompt into another AI system together with this report and
the key project files.

```text
You are acting as a strict Nature Methods / high-impact computational biology
reviewer. Please perform an adversarial pre-review of the SheafSignal manuscript
package.

Your task is to find reasons this paper could be rejected before submission.
Do not praise the work unless it is necessary for balance. Focus on fatal flaws,
major revision requirements, unsupported claims, missing comparisons, missing
validation, weak statistics, unclear novelty, and reproducibility gaps.

Evaluate the project across these axes:
1. Mathematical novelty: is sheaf/Hodge analysis genuinely a new object here,
   or is it a relabeled scoring pipeline?
2. Biological validity: do the public TME results justify the biological
   wording, especially the GSE154778 Myeloid claim?
3. Annotation quality: is coarse marker-based annotation sufficient?
4. Comparator quality: are LIANA, LR baseline, bounded NicheNet, and
   MechanisticTargetPrior enough, or are CellChat/CellPhoneDB/niche-DE required?
5. Statistical rigor: are permutation, sensitivity, sample-level robustness,
   and multiple-testing boundaries sufficient?
6. Figure and table traceability: do all claims map to source data?
7. Reproducibility: are GitHub/Zenodo, checksums, scripts, and environment
   enough for public review?
8. Journal fit: should this go to Nature Methods first, or a lower-risk
   computational biology journal?

Please output:
- one-sentence editorial decision: reject / major revision / potentially
  competitive after fixes;
- top 5 fatal or near-fatal concerns;
- top 10 major revision requests;
- exact claims that must be downgraded;
- extra analyses that would most increase the chance of a 20-50 IF acceptance;
- whether the current package is ready for Zenodo/GitHub release.
```

## 8. Files The External Reviewer Should Inspect

Primary manuscript and package:

- `manuscript/SCI_MANUSCRIPT_V2_POLISHED.md`
- `manuscript/SCI_MANUSCRIPT_V2_POLISHED_claim_tracked.md`
- `manuscript/nature_methods_package/`
- `manuscript/figure_legends/03_figure_source_map.tsv`

Core audits:

- `manuscript/SUBMISSION_READINESS_REPORT.md`
- `manuscript/NATURE_METHODS_GO_NO_GO_REPORT.md`
- `manuscript/CLAIM_SAFETY_AUDIT_REPORT.md`
- `manuscript/method_reporting/REVIEWER_RISK_REPORT.md`
- `manuscript/method_reporting/METHOD_REPORTING_REPORT.md`
- `benchmarks/results/BENCHMARK_RESULT_CONTRACT_REPORT.md`
- `manuscript/figure_quality/MAIN_FIGURE_QUALITY_REPORT.md`
- `manuscript/provenance/SUBMISSION_PROVENANCE_REPORT.md`

Key results:

- `benchmarks/results/component_recovery.csv`
- `benchmarks/results/public_tme_sheafsignal_summary.csv`
- `benchmarks/results/tool_comparison.csv`
- `benchmarks/results/gse154778_pdac_scrna/qc/claim_gating_by_cell_type.csv`
- `benchmarks/results/gse154778_pdac_scrna/stability/sample_level_myeloid_stability_summary.csv`
- `benchmarks/results/tenx_breast_visium/spatial/qc/spatial_hotspot_qc_summary.csv`

Release evidence:

- `release/archive_manifest.tsv`
- `release/zenodo_upload_manifest.tsv`
- `release/ZENODO_DEPOSITION_INSTRUCTIONS.md`
- `release/ZENODO_API_UPLOAD_SUMMARY.md`

## 9. Bottom-Line Pre-Review Conclusion

This package is locally strong enough to justify serious pre-submission review
as a computational methods manuscript, but it is not yet submission-ready
because Zenodo DOI, GitHub public release, and author metadata remain external
blockers.

The highest scientific risks are:

1. novelty could be challenged as graph/Hodge rebranding unless the distinction
   from prior methods is made very explicit;
2. GSE154778 biology depends on coarse annotation and should remain
   hypothesis-generating;
3. comparator breadth is incomplete relative to the original list of CCC tools;
4. real-data curl/harmonic magnitudes may not fully justify strong feedback-loop
   language;
5. public-data-only evidence supports a methods paper better than a definitive
   cancer biology or clinical paper.

Recommended editorial stance before external submission:

> Continue, but do one adversarial review round before Zenodo publication and
> before locking the manuscript language. The current best route is a cautious
> 20-50 IF methods submission, not a guaranteed top-journal acceptance claim.
