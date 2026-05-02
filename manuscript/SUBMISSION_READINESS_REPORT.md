# SheafSignal Submission Readiness Report

## Executive Status

- Target route: 20-50 IF computational methods manuscript.
- Local readiness: `hardening_not_submission_ready`.
- Reproducibility release status: `zenodo_ready_no_doi`.
- Current blocker pattern: comparator scope, Visium interpretation boundary,
  manuscript-language synchronization, environment lock, public GitHub release,
  and Zenodo DOI remain open before submission.
- Journal route board: `manuscript/SCI20_50_ACTION_BOARD.md`.
- Nature Methods draft package: `manuscript/nature_methods_package/`.
- Final blocker gate: `manuscript/NATURE_METHODS_GO_NO_GO_REPORT.md`.
- Submission metadata templates: `manuscript/submission_metadata/`.
- Nature Methods format audit: `manuscript/NATURE_METHODS_FORMAT_AUDIT_REPORT.md`.
- Presubmission inquiry package: `manuscript/presubmission_inquiry/`.
- Post-decision response and transfer package: `manuscript/response_transfer/`.
- Figure legends and source map package: `manuscript/figure_legends/`.
- Main figure quality audit: `manuscript/figure_quality/MAIN_FIGURE_QUALITY_REPORT.md`.
- Supplementary artifact audit: `manuscript/supplementary_quality/SUPPLEMENTARY_ARTIFACT_REPORT.md`.
- Benchmark result contract audit: `benchmarks/results/BENCHMARK_RESULT_CONTRACT_REPORT.md`.
- Submission provenance audit: `manuscript/provenance/SUBMISSION_PROVENANCE_REPORT.md`.
- Method reporting and reviewer-risk audit: `manuscript/method_reporting/METHOD_REPORTING_REPORT.md`.
- Manuscript-wide claim safety audit: `manuscript/CLAIM_SAFETY_AUDIT_REPORT.md`.
- Formal SCI manuscript v1: `manuscript/SCI_MANUSCRIPT_V1.md`.
- Formal SCI manuscript v1 claim tracker: `manuscript/SCI_MANUSCRIPT_V1_claim_tracked.md`.
- Verified reference package: `manuscript/references/`.
- Polished SCI manuscript v2: `manuscript/SCI_MANUSCRIPT_V2_POLISHED.md`.
- Submission upload package: `manuscript/submission_upload_package/`.

## Gate Summary

- `hardening_not_submission_ready`: 1
- `partial`: 1
- `pass`: 8
- `pass_with_boundary`: 1
- `zenodo_ready_no_doi`: 1

## Gate Details

- `G1` `pass`: SheafSignal reframes CCC as sheaf-valued flow with Hodge decomposition over biological graphs. Remaining: Keep methods text focused on sheaf/Hodge object, not only a new scoring heuristic.
- `G2` `pass`: Component recovery supports gradient/curl/harmonic separation on controlled simulations. Remaining: Add larger stress tests only if reviewer requests broader parameter coverage.
- `G3` `pass_with_boundary`: Public TME benchmarks show dataset-dependent computational sheaf-energy rankings. Remaining: Do not describe these rankings as validated real-tumor feedback/frustration architecture.
- `G4` `supplement_only`: GSE154778 Myeloid remains a lesion-stratified/sample-level computational hypothesis under Round2, not a main biological source claim. Remaining: Keep Myeloid out of the main biological mechanism narrative unless future validation changes the gate.
- `G5` `partial`: GSE154778 Myeloid signal has sample-level support but remains heterogeneous and analysis-mode dependent. Remaining: Frame as supplement-level computational signal, not uniform patient-level biology.
- `G6` `pass`: Visium hotspot ranks are stable across k-neighbor sensitivity settings. Remaining: Do not make histology-level mechanism claims without annotation review.
- `G7` `pass`: LRProductBaseline is completed and shows SheafSignal is not reducible to LR product intensity. Remaining: Use discordance examples, not superiority language.
- `G8` `pass`: Full LIANA imports exist for all three public scRNA-seq benchmarks. Remaining: Use LIANA as one external comparator; broad CCC-tool superiority still requires careful scope or additional tools.
- `G9` `pass_with_boundary`: NicheNet/nichenetr-engine imports and MechanisticTargetPrior outputs exist for all three public scRNA-seq benchmarks. Remaining: Current NicheNet run uses official nichenetr scoring with the project-curated TME prior matrix; do not imply full pretrained NicheNet network benchmarking.
- `G10` `zenodo_ready_no_doi`: GitHub/Zenodo release manifests and SHA256 checksums exist; release audit passes. Remaining: Create the Zenodo deposition, upload files listed in release/zenodo_upload_manifest.tsv, then insert the DOI before submission.
- `G11` `pass`: Reviewer objections are proactively mapped to current LIANA, NicheNet-engine, mechanistic-prior, sparse-cell, and public-data evidence boundaries. Remaining: Regenerate after any future comparator or manuscript-figure change.
- `G12` `hardening_not_submission_ready`: 20-50 SCI route remains plausible as a methods manuscript, but the package is still under hardening. Remaining: Do not promise acceptance; finish scientific boundaries, environment lock, GitHub release, Zenodo DOI, manuscript figures and journal-specific formatting before submission.

## Comparator Evidence

- `LRProductBaseline`: completed for 5 datasets (demo_synthetic;gse154778_pdac_scrna;gse176078_brca_scrna;gse72056_melanoma_scrna;tenx_breast_visium); Spearman range -0.0496-0.72
- `LIANA`: completed for 3 datasets (gse154778_pdac_scrna;gse176078_brca_scrna;gse72056_melanoma_scrna); Spearman range 0.0743-0.699
- `NicheNet`: completed for 3 datasets (gse154778_pdac_scrna;gse176078_brca_scrna;gse72056_melanoma_scrna); Spearman range 0.184-0.75
- `MechanisticTargetPrior`: completed for 3 datasets (gse154778_pdac_scrna;gse176078_brca_scrna;gse72056_melanoma_scrna); Spearman range 0.176-0.643

## Local Release Archives

- `github`: `release/archives/sheafsignal_github_release.zip` (checksum and size are recorded in `release/archive_manifest.tsv`)
- `zenodo`: `release/archives/sheafsignal_zenodo_upload.zip` (checksum and size are recorded in `release/archive_manifest.tsv`)

## Allowed Claims

- SheafSignal reframes cell-cell communication as sheaf-valued flow with Hodge decomposition.
- The method reports communication inconsistency plus curl-like and harmonic graph-flow diagnostics not reducible to simple LR intensity.
- Public TME benchmarks support dataset-dependent computational sheaf-energy rankings across public cancer datasets.
- GSE154778 Myeloid can be discussed only as a supplement-level, annotation- and analysis-dependent computational signal, with sparse cell types kept in supplement/QC.
- Full LIANA, bounded nichenetr-engine, and MechanisticTargetPrior comparators are available for the three public scRNA-seq benchmarks.

## Not Allowed

- Do not guarantee acceptance in any journal.
- Do not claim clinical utility, therapeutic recommendations, or treatment-response prediction.
- Do not claim full pretrained NicheNet network benchmarking unless that resource is explicitly added.
- Do not claim broad superiority over all CCC tools; CellChat and CellPhoneDB are complete only for the primary scRNA-seq scope, while demo/Visium/GSE103322 and niche-DE remain outside that comparator claim.
- Do not make strong biology claims from sparse cell types or marker-dominant Visium spot labels.

## Required Before Submission

1. Upload files listed in `release/zenodo_upload_manifest.tsv` or `release/archives/sheafsignal_zenodo_upload.zip` to Zenodo.
2. Insert the minted Zenodo DOI into the data availability statement and dataset manifest.
3. Use `release/zenodo_deposition_metadata.json` and `release/ZENODO_DEPOSITION_INSTRUCTIONS.md` for deposition.
4. After DOI minting, run `python scripts/finalize_zenodo_doi.py --doi <ZENODO_DOI>`.
5. Freeze manuscript figures and rerun `python -m pytest`, `python scripts/release_audit.py`, and `python scripts/build_reproducibility_release.py`.
6. Keep `manuscript/JOURNAL_TARGETS_20_50.tsv` and `manuscript/SCI20_50_ACTION_BOARD.md` synchronized with the final target journal.
7. Update `manuscript/nature_methods_package/` after final figures, author list, and Zenodo DOI are frozen.
8. Run `python scripts/check_final_submission_blockers.py --report-only`; final submission is not allowed while the report says `NO_GO`.
9. Fill author metadata, affiliations, CRediT roles, competing interests, and submission-system metadata templates before journal upload.
10. Run `python scripts/check_nature_methods_format.py --report-only` and resolve any `FORMAT_PENDING` items.
11. Use `manuscript/presubmission_inquiry/01_presubmission_inquiry_letter.md` for a Nature Methods presubmission inquiry if the authors want editorial triage before full submission.
12. Use `manuscript/response_transfer/` after editorial feedback, review, or rejection; do not transfer to another 20-50 IF target unless the journal-specific transfer gate is marked appropriate.
13. Review `manuscript/figure_legends/03_figure_source_map.tsv` before figure assembly so every captioned claim maps to a source table and a claim boundary.
14. Run `python scripts/check_main_figure_quality.py` after regenerating figures and before rebuilding the upload package.
15. Run `python scripts/check_supplementary_artifacts.py` after regenerating supplementary figures, tables, or support files.
16. Run `python scripts/check_benchmark_result_contracts.py` after regenerating benchmark summaries or comparator imports.
17. Run `python scripts/check_submission_provenance.py` after rebuilding manuscript, figure, upload, release, or quality-gate artifacts.
18. Run `python scripts/check_method_reporting_readiness.py` before final blocker checks so reviewer-risk boundaries are current.
19. Run `python scripts/check_claim_safety.py --report-only` before every submission or rebuttal and resolve any `blocking_positive_claim` rows.
20. Use `manuscript/SCI_MANUSCRIPT_V2_POLISHED.md` as the current working manuscript and `manuscript/SCI_MANUSCRIPT_V2_POLISHED_claim_tracked.md` to audit evidence-linked claims during revision.
21. Use `manuscript/references/SCI_MANUSCRIPT_V1_referenced.md` for the reference-resolved manuscript and keep `manuscript/references/SCI_REFERENCE_GAP_REPORT.md` at `REFERENCE_PLACEHOLDERS_RESOLVED`.
22. Keep `manuscript/SCI_MANUSCRIPT_V2_EDITORIAL_AUDIT.tsv` and `manuscript/SCI_MANUSCRIPT_V2_CHANGELOG.tsv` with the manuscript package so the v2 editorial changes remain auditable.
23. Use `manuscript/submission_upload_package/` for DOCX upload artifacts, but rerun `python scripts/build_submission_upload_package.py` after any manuscript, DOI, author metadata, or release-package change.
