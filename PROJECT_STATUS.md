# PROJECT_STATUS

## Current Dashboard

- Latest one-page status board: `manuscript/SHEAFSIGNAL_STATUS_DASHBOARD_2026-05-02.md`
- Machine-readable gate table: `manuscript/SHEAFSIGNAL_STATUS_GATES_2026-05-02.tsv`
- Current stage: 20-50 IF manuscript hardening candidate; not submission-ready.
- Current blocker pattern: scientific core, simulation baseline hardening, manuscript claim-language synchronization, Visium hotspot-only scope gating, primary scRNA comparator-scope locking, Python environment locking, and local Git freeze are substantially improved, but public GitHub remote/tag/release URL and Zenodo DOI remain open.

## Scientific Question

Can ligand-receptor communication be reframed as sheaf-valued flow over a cell-type graph to identify tumor microenvironment pathway inconsistency, feedback loops, and global communication circulation?

## Current Evidence

- Round 2 hardening supersedes earlier coarse-annotation claims for GSE154778.
- The core package now has a formal rank-one cellular sheaf API with restriction maps, coboundary residuals, sheaf energy, sheaf Laplacian export, and primary Hodge decomposition on `sheaf_residual`.
- GSE154778 full Scanpy reannotation is complete under `scanpy_full_v1`: 14,926 cells, 16 samples, Primary and Metastatic lesions.
- GSE154778 prepared inputs now point to `data/processed/gse154778_pdac_scrna_scanpy_full_v1/`.
- Round2 GSE154778 expression-mode benchmark uses 1000 sample-stratified permutations and provenance hashes under `benchmarks/results/round2_hardening/`.
- Round2 claim gating keeps Myeloid as `supplement_only`, not a main biological source claim: stratified/bootstrap/sample-level Myeloid support exists, but overall expression-mode top source is CAF/Fibroblast and sparse categories remain underpowered.
- The synthetic expression-to-LR-to-pathway ground-truth benchmark now compares SheafSignal with LR-flow, pathway-gradient, Hodge-only, graph-centrality, and graph-smoothness baselines; SheafSignal has the highest average precision across tested noise levels.
- Zenodo/GitHub final release remains intentionally held until scientific/statistical blockers are cleared. A local Git freeze commit now exists, but the public GitHub remote, immutable tag, and release URL are still pending.

- The MVP accepts expression, metadata, ligand-receptor, and pathway gene inputs.
- The CLI can produce sheaf energy, Hodge decomposition scores, and communication network figures on demo data.
- The method has a clear mathematical distinction from standard ligand-receptor scoring.
- The repository now has a Nature Methods oriented public TME benchmark manifest covering melanoma, PDAC, breast cancer scRNA-seq, and breast cancer Visium.
- The smoke-test workflow writes standardized benchmark and figure-manifest outputs without committing large public datasets.
- GSE154778 now has a dataset-specific adapter for the GEO processed `GSE154778_dgeMtx.csv.gz` file, including sample parsing and coarse marker-based cell-type annotation.
- GSE154778 has been downloaded and checksum-verified locally; the full 14,926-cell matrix now runs through a compact profile-only path without exporting a dense full expression CSV.
- In the current full GSE154778 coarse-marker benchmark, Myeloid is the top frustration source, but this remains a computational signal requiring annotation review.
- GSE154778 annotation QC now generates supplement-ready marker heatmap, cell-count, confidence, and frustration-overlay tables/figures.
- The benchmark workflow now writes an internal `LRProductBaseline` comparator that aligns conventional ligand-receptor product edge strength against SheafSignal `sheaf_energy`.
- External comparator handoff is now standardized: `export_comparator_inputs.py` writes compact profile-level inputs, and `import_external_comparator.py` imports CellChat/CellPhoneDB/NicheNet/LIANA-style edge tables into the common alignment schema.
- GSE154778 bootstrap stability is implemented; in the current 100-bootstrap run, Myeloid is the top frustration source in 100/100 resamples under fixed coarse marker annotations, with median frustration score 0.8741 and 2.5%-97.5% interval 0.8273-0.9154.
- GSE154778 lesion-stratified analysis is implemented; Myeloid remains the top frustration source in both Metastatic and Primary subsets, with explicit low-count warnings for sparse cell types.
- GSE154778 claim gating is implemented; Myeloid is the only `main_claim` candidate, while sparse non-Myeloid categories are demoted to QC-warning or supplement-only interpretation.
- GSE154778 sample-level pseudobulk robustness is implemented; it shows heterogeneity, with stronger Myeloid top-source frequency in Metastatic samples than in Primary samples.
- GSE72056 melanoma has been downloaded, checksum-verified, prepared from author metadata rows plus genes x cells, and benchmarked as a second public TME scRNA-seq replication dataset.
- In the current GSE72056 author-annotation benchmark, CAF/Fibroblast is the top frustration source. This supports cancer-context-specific SheafSignal replication, not cross-cancer generalization of the PDAC Myeloid hypothesis.
- GSE176078 breast cancer has been downloaded, checksum-verified, prepared by streaming the Matrix Market archive for selected genes, and benchmarked as a third public TME scRNA-seq replication dataset.
- In the current GSE176078 author-annotation benchmark, Tumor/Malignant is the top frustration source across mapped ER+/HER2+/TNBC profiles. This strengthens the methods claim that SheafSignal detects context-specific frustration architecture across independent public datasets.
- `download_public_datasets.py` now uses resumable `.part` downloads with `aria2c` when available, writes `logs/download.log`, and only promotes completed downloads to final paths.
- 10x breast Visium has been downloaded, checksum-verified for both HDF5 and spatial tarball, prepared as selected-gene marker-dominant spot profiles, and benchmarked as the first spatial hotspot case.
- The current Visium spatial run exports 3,798 in-tissue spots and 22,788 directed spot-neighbor edges to `spatial_frustration_hotspots.csv`. Marker-dominant spot labels are QC context, not single-cell-level biological proof.
- Visium hotspot QC and `k_neighbors` sensitivity are implemented. The current `k=4,6,8,10,12` run has minimum Spearman correlation 0.9309 and minimum top-50 hotspot overlap 0.86 against the `k=6` reference.
- Visium interpretation is now programmatically gated by `scripts/check_visium_scope_gate.py`; the current decision is `VISIUM_SCOPE_PASS_HOTSPOT_ONLY`, so Visium can be used only as a spot-level hotspot workflow demonstration unless future deconvolution/histology evidence is added.
- Comparator handoff bundles are now exported for all four real public benchmarks. `LRProductBaseline` is complete, LIANA smoke imports are complete for the three public scRNA-seq benchmarks, and CellChat, CellPhoneDB, NicheNet, niche-DE, plus full-scale LIANA remain explicit gates.
- A direct LIANA runner is now implemented in `scripts/run_liana_comparator.py` with a reproducible environment file at `envs/liana_environment.yml`; this is ready to execute once the LIANA environment is created.
- External comparator readiness is now audited by `scripts/check_external_comparator_readiness.py`. GSE154778, GSE72056, and GSE176078 now have selected-gene cell-level `expression.csv` inputs for LIANA; the isolated `sheafsignal-liana` environment is available for reproducible LIANA execution.
- The `sheafsignal-liana` conda environment has been updated successfully with LIANA 1.7.1, scanpy 1.11.5, anndata 0.12.11, and editable SheafSignal.
- GSE154778 now has a full-cell selected-gene LIANA input covering 14,926 metadata cells and 51 SheafSignal/CCC-relevant genes, avoiding the earlier 1,000-cell prepared-subset limitation.
- Full LIANA comparator imports are complete for GSE154778 PDAC, GSE72056 melanoma, and GSE176078 breast cancer scRNA-seq benchmarks. The imported external edge tables write `liana_edges.csv` and `sheafsignal_vs_liana.csv` for all three public scRNA-seq datasets.
- External LIANA gate status is now `satisfied_liana_full`: 3/3 public scRNA-seq datasets have `completed_full_import`. CellChat, CellPhoneDB, NicheNet, and niche-DE remain pending, so broad CCC-tool superiority is still not allowed.
- Comparator interpretation is now programmatically gated by `scripts/check_comparator_scope_gate.py`; the current decision is `COMPARATOR_SCOPE_PASS_PRIMARY_SCRNA`, meaning LRProductBaseline, LIANA, MechanisticTargetPrior, bounded NicheNet/nichenetr-engine, CellPhoneDB and CellChat are complete for the three primary scRNA-seq benchmarks, while demo/Visium/GSE103322/niche-DE remain outside the main comparator claim.
- A transparent `MechanisticTargetPrior` comparator is now implemented and completed for GSE154778, GSE72056, and GSE176078. It scores sender ligand, receiver receptor, and receiver target-program activity using `metadata/tme_ligand_target_prior.csv`.
- Official `nichenetr` 2.2.1.1 is installed in the D-drive R library, and `scripts/run_nichenet_prior_comparator.R` runs `nichenetr::predict_ligand_activities()` with the project-curated TME prior matrix for all three public scRNA-seq benchmarks.
- Mechanistic comparator gate status is now `pass_with_boundary`: NicheNet/nichenetr-engine imports exist for all three public scRNA-seq datasets, but the manuscript must state that the current run uses the project-curated prior matrix rather than a full pretrained NicheNet network.
- Reviewer-facing objection and response tables are generated programmatically; they now distinguish full LIANA evidence, MechanisticTargetPrior evidence, and bounded nichenetr-engine evidence.
- Reproducibility release manifests are now generated under `release/`: GitHub-target files, Zenodo-target processed objects, SHA256 sums, a release summary, and a data-availability statement draft.
- G10 reproducibility status is now `zenodo_ready_no_doi`: the upload manifest and checksums exist, but no Zenodo DOI has been minted yet.
- A 20-50 IF journal-specific action board is now generated under `manuscript/`. It ranks Nature Methods as the primary method-aligned target, keeps Nature Biotechnology as a high-risk stretch, and explicitly states that journal acceptance cannot be guaranteed.
- A Nature Methods first-submission scaffold is now generated under `manuscript/nature_methods_package/`, including title page, abstract draft, cover letter draft, main text skeleton, methods skeleton, claim-evidence map, figure plan, and submission checklist.
- The Nature Methods package now also includes a full manuscript draft and supplementary information draft generated from the current benchmark and claim-gating tables.
- A local Nature Methods format audit is implemented and currently reports `FORMAT_LOCALLY_READY` for title length, 150-word abstract, main-text length, display-item count, Data Availability, Code Availability, and required support files.
- A Nature Methods presubmission inquiry package is now generated under `manuscript/presubmission_inquiry/`, including an editor-facing one-page summary, inquiry letter, editorial triage risk audit, novelty/evidence matrix, and claim-boundary note.
- A post-decision response and transfer package is now generated under `manuscript/response_transfer/`, including a route decision tree, editorial-rejection template, reviewer-response skeleton, journal-transfer table, target-specific rewrite actions, and do-not-claim checklist.
- Evidence-linked figure legends and source maps are now generated under `manuscript/figure_legends/`; every main figure is mapped to source files, allowed claims, and forbidden overclaims before journal upload.
- Automated main-figure quality auditing is implemented under `manuscript/figure_quality/`; it checks that the five main-figure PDFs are renderable, one-page, non-empty, and linked to source-map claim boundaries.
- Supplementary artifact auditing is implemented under `manuscript/supplementary_quality/`; it checks all `supp_` manifest entries for file existence, readable PDF/CSV/TSV/JSON/text content, source directory presence, and global supplementary claim boundary coverage.
- Benchmark result contract auditing is implemented under `benchmarks/results/`; it checks simulation recovery, public TME summary, comparator linked files, GSE154778 Myeloid-only claim gate, and Visium spatial sensitivity metric ranges.
- Submission provenance auditing is implemented under `manuscript/provenance/`; it maps key submission, figure, benchmark, upload, release, and quality-gate artifacts to generator scripts or explicit author/external pending ownership.
- Zenodo API upload automation is implemented in `scripts/upload_zenodo_deposition.py`; it supports dry-run, draft upload, and explicit publish/finalization while refusing unsafe `TBD` metadata for publication.
- Python environment locking is implemented by `scripts/build_environment_lock.py`; the current decision is `ENVIRONMENT_LOCK_PASS` with 216 exact locked requirements and zero warnings under `D:\BioSoft\python\Python311\python.exe`.
- Release metadata placeholder auditing is implemented by `scripts/check_release_metadata_placeholders.py`; the current decision is `RELEASE_METADATA_BLOCKED_EXTERNAL_IDENTIFIERS`, separating pending GitHub URL, Zenodo DOI, and author-owned fields from code/scientific blockers.
- IF 20-50 distance reporting is implemented by `scripts/build_if20_50_gap_report.py`; the current decision is `IF20_50_SCIENTIFICALLY_HARDENED_BUT_RELEASE_BLOCKED`, with overall readiness 78.0%, scientific/method hardening 95.1%, and submission infrastructure 44.5%.
- Journal metric auditing is implemented by `scripts/build_journal_metric_audit.py`; publisher JIF values are tied to official metric pages, while CAS zone and warning-list status remain final official checks on the submission day.
- External beta-review packet generation is implemented by `scripts/build_external_beta_review_packet.py`; the current decision is `BETA_REVIEW_PACKET_READY_LOCAL_EXTERNAL_REVIEWS_PENDING`, meaning the handoff package is ready but no independent returned reviews are filed yet.
- Local clean-export reproduction preflight is implemented by `scripts/run_clean_clone_preflight.py`; the current decision is `CLEAN_CLONE_PREFLIGHT_PASS_LOCAL_EXPORT` for commit `9ccf5f3`, covering core pytest, CLI demo, expected output checks, and release audit from a Git-tracked export.
- Method-reporting and reviewer-risk auditing is implemented under `manuscript/method_reporting/`; it checks algorithm primitives, simulation recovery, public dataset manifest completeness, comparator scope, sparse-cell claim gating, Visium sensitivity, figure traceability, references, and release archives.
- A manuscript-wide claim safety audit is now generated as `manuscript/CLAIM_SAFETY_AUDIT.tsv` and `manuscript/CLAIM_SAFETY_AUDIT_REPORT.md`, scanning all manuscript-facing files for unsupported clinical, therapeutic, guaranteed-publication, broad-superiority, and full-pretrained-NicheNet claims.
- A formal SCI manuscript v1 is now generated as `manuscript/SCI_MANUSCRIPT_V1.md`, with a claim-tracked companion, title/abstract/keywords file, Nature Methods cover letter draft, and author-side todo list.
- A verified reference package is now generated under `manuscript/references/`, including publisher-verified DOI metadata, BibTeX, placeholder mapping, a reference-resolved manuscript, and a reference gap report.
- A polished SCI manuscript v2 is now generated as `manuscript/SCI_MANUSCRIPT_V2_POLISHED.md`, with a v2 claim tracker, editorial audit, and changelog that preserve the Myeloid-only main claim, sparse-category QC downgrade, bounded NicheNet scope, and no-clinical-utility boundary.
- A submission upload package is now generated under `manuscript/submission_upload_package/`, including DOCX versions of the v2 main manuscript, Nature Methods cover letter, supplementary information, five main-figure PDFs, upload manifest, preflight checklist, DOCX text-extraction check, and automated DOCX-to-PDF layout check.
- The main figure package is now generated as five uploadable PDFs: concept schematic, simulation component recovery, public TME summary, GSE154778 Myeloid claim gate, and comparator alignment.
- Final submission blocker gating is now implemented. The current go/no-go report is `NO_GO` because Zenodo DOI deposition, GitHub public release URL/tag, author metadata, and final Nature Methods formatting are not yet complete.
- Zenodo deposition preparation is now scripted. `release/zenodo_deposition_metadata.json` and `release/ZENODO_DEPOSITION_INSTRUCTIONS.md` identify the exact upload archive, checksum, and DOI-finalization command.
- Submission metadata templates are now generated under `manuscript/submission_metadata/`; author names, affiliations, CRediT roles, competing interests, and institutional ethics wording remain author-owned pending items.

## What This Project Can Prove

- On benchmark datasets, SheafSignal can report communication features that are not directly captured by standard CCC tools.
- Hodge components can summarize gradient-like, curl-like, and harmonic communication structure.

## What This Project Cannot Prove

- It cannot claim biological discovery from synthetic examples alone.
- It cannot claim superiority over established CCC tools without benchmark comparisons.
- It cannot infer clinical decisions or therapeutic targets without external validation.

## Key Outputs

- `results/sheaf_energy_by_edge.csv`
- `results/hodge_decomposition_scores.csv`
- `figures/communication_curl_network.pdf`
- `benchmarks/results/component_recovery.csv`
- `benchmarks/results/tool_comparison.csv`
- `benchmarks/results/public_tme_sheafsignal_summary.csv`
- `benchmarks/results/spatial_frustration_hotspots.csv`
- `benchmarks/results/<dataset_id>/comparator_inputs/`
- `benchmarks/results/<dataset_id>/comparators/sheafsignal_vs_lr_product_baseline.csv`
- `benchmarks/results/gse154778_pdac_scrna/stability/`
- `benchmarks/results/gse154778_pdac_scrna/stratified/`
- `benchmarks/results/gse154778_pdac_scrna/qc/claim_gating_by_cell_type.csv`
- `benchmarks/results/gse154778_pdac_scrna/qc/myeloid_claim_readiness_summary.csv`
- `benchmarks/results/gse72056_melanoma_scrna/comparators/sheafsignal_vs_lr_product_baseline.csv`
- `benchmarks/results/gse176078_brca_scrna/comparators/sheafsignal_vs_lr_product_baseline.csv`
- `benchmarks/results/tenx_breast_visium/spatial/spatial_frustration_hotspots.csv`
- `benchmarks/results/tenx_breast_visium/spatial/spatial_hotspot_summary.csv`
- `benchmarks/results/tenx_breast_visium/spatial/qc/k_neighbors_sensitivity.csv`
- `benchmarks/results/tenx_breast_visium/spatial/qc/spatial_hotspot_qc_summary.csv`
- `manuscript/visium_scope/VISIUM_SCOPE_AUDIT.tsv`
- `manuscript/visium_scope/VISIUM_SCOPE_REPORT.md`
- `manuscript/comparator_scope/COMPARATOR_SCOPE_AUDIT.tsv`
- `manuscript/comparator_scope/COMPARATOR_SCOPE_REPORT.md`
- `envs/requirements-py311-lock.txt`
- `envs/requirements-core-lock.txt`
- `envs/environment_lock_audit.tsv`
- `envs/environment_lock_summary.tsv`
- `envs/ENVIRONMENT_LOCK_REPORT.md`
- `benchmarks/results/comparator_input_exports.csv`
- `benchmarks/results/comparator_readiness_matrix.csv`
- `benchmarks/results/reviewer_objection_response_table.csv`
- `manuscript/reviewer_objection_response_table.tsv`
- `scripts/run_liana_comparator.py`
- `scripts/check_external_comparator_readiness.py`
- `envs/liana_environment.yml`
- `benchmarks/results/external_comparator_environment_status.csv`
- `benchmarks/results/external_comparator_execution_plan.csv`
- `benchmarks/results/external_comparator_gate_summary.csv`
- `manuscript/external_comparator_gate_summary.tsv`
- `benchmarks/results/gse154778_pdac_scrna/comparators/sheafsignal_vs_liana.csv`
- `benchmarks/results/gse72056_melanoma_scrna/comparators/sheafsignal_vs_liana.csv`
- `benchmarks/results/gse176078_brca_scrna/comparators/sheafsignal_vs_liana.csv`
- `benchmarks/results/gse154778_pdac_scrna/comparators/sheafsignal_vs_mechanistictargetprior.csv`
- `benchmarks/results/gse72056_melanoma_scrna/comparators/sheafsignal_vs_mechanistictargetprior.csv`
- `benchmarks/results/gse176078_brca_scrna/comparators/sheafsignal_vs_mechanistictargetprior.csv`
- `benchmarks/results/gse154778_pdac_scrna/comparators/sheafsignal_vs_nichenet.csv`
- `benchmarks/results/gse72056_melanoma_scrna/comparators/sheafsignal_vs_nichenet.csv`
- `benchmarks/results/gse176078_brca_scrna/comparators/sheafsignal_vs_nichenet.csv`
- `metadata/tme_ligand_target_prior.csv`
- `scripts/run_nichenet_prior_comparator.R`
- `envs/install_nichenetr.R`
- `scripts/build_reproducibility_release.py`
- `release/release_file_inventory.tsv`
- `release/github_release_manifest.tsv`
- `release/zenodo_upload_manifest.tsv`
- `release/github_sha256sums.txt`
- `release/zenodo_sha256sums.txt`
- `release/REPRODUCIBILITY_RELEASE_SUMMARY.md`
- `release/DATA_AVAILABILITY_STATEMENT_DRAFT.md`
- `release/archive_manifest.tsv`
- `manuscript/SCI20_50_SUBMISSION_GATES.tsv`
- `manuscript/SCI20_50_POSITIONING_NOTE.md`
- `manuscript/JOURNAL_TARGETS_20_50.tsv`
- `manuscript/SCI20_50_ACTION_BOARD.md`
- `manuscript/SUBMISSION_READINESS_REPORT.md`
- `manuscript/nature_methods_package/00_title_page.md`
- `manuscript/nature_methods_package/01_abstract.md`
- `manuscript/nature_methods_package/02_cover_letter_draft.md`
- `manuscript/nature_methods_package/03_main_text_skeleton.md`
- `manuscript/nature_methods_package/04_methods_skeleton.md`
- `manuscript/nature_methods_package/05_claim_evidence_map.tsv`
- `manuscript/nature_methods_package/06_figure_plan.tsv`
- `manuscript/nature_methods_package/07_submission_checklist.tsv`
- `manuscript/nature_methods_package/08_claim_boundaries_and_limitations.md`
- `manuscript/nature_methods_package/09_full_manuscript_draft.md`
- `manuscript/nature_methods_package/10_supplementary_information_draft.md`
- `manuscript/FINAL_SUBMISSION_BLOCKERS.tsv`
- `manuscript/NATURE_METHODS_GO_NO_GO_REPORT.md`
- `scripts/check_final_submission_blockers.py`
- `release/zenodo_deposition_metadata.json`
- `release/ZENODO_DEPOSITION_INSTRUCTIONS.md`
- `release/GITHUB_RELEASE_INSTRUCTIONS.md`
- `release/GIT_RELEASE_READINESS_REPORT.md`
- `release/RELEASE_METADATA_PLACEHOLDER_REPORT.md`
- `manuscript/IF20_50_DISTANCE_REPORT.md`
- `manuscript/journal_metric_audit/JOURNAL_METRIC_AUDIT.tsv`
- `manuscript/journal_metric_audit/JOURNAL_METRIC_AUDIT_REPORT.md`
- `external_ai_review_packet/beta_review_packet_2026-05-02/00_README_FOR_REVIEWERS.md`
- `external_ai_review_packet/beta_review_packet_2026-05-02/01_BETA_REVIEW_PACKET_STATUS.md`
- `external_ai_review_packet/beta_review_packet_2026-05-02/02_EVIDENCE_FILE_INDEX.tsv`
- `external_ai_review_packet/beta_review_packet_2026-05-02/03_REVIEWER_CHECKLIST.tsv`
- `external_ai_review_packet/beta_review_packet_2026-05-02/04_AI_REVIEW_PROMPT.md`
- `external_ai_review_packet/beta_review_packet_2026-05-02/05_REVIEW_FORM_TEMPLATE.md`
- `release/clean_clone_preflight/CLEAN_CLONE_PREFLIGHT_REPORT.md`
- `scripts/build_zenodo_deposition_package.py`
- `scripts/finalize_zenodo_doi.py`
- `manuscript/submission_metadata/AUTHOR_METADATA_TEMPLATE.tsv`
- `manuscript/submission_metadata/AFFILIATIONS_TEMPLATE.tsv`
- `manuscript/submission_metadata/AUTHOR_CONTRIBUTIONS_CREDIT_TEMPLATE.tsv`
- `manuscript/submission_metadata/SUBMISSION_SYSTEM_METADATA_CHECKLIST.tsv`
- `manuscript/submission_metadata/COMPETING_INTERESTS_TEMPLATE.md`
- `manuscript/submission_metadata/ETHICS_AND_DATA_USE_STATEMENT.md`
- `scripts/build_submission_metadata_templates.py`
- `manuscript/NATURE_METHODS_FORMAT_AUDIT.tsv`
- `manuscript/NATURE_METHODS_FORMAT_AUDIT_REPORT.md`
- `scripts/check_nature_methods_format.py`
- `manuscript/presubmission_inquiry/00_one_page_editor_summary.md`
- `manuscript/presubmission_inquiry/01_presubmission_inquiry_letter.md`
- `manuscript/presubmission_inquiry/02_editorial_triage_risk_audit.tsv`
- `manuscript/presubmission_inquiry/03_novelty_evidence_matrix.tsv`
- `manuscript/presubmission_inquiry/04_editor_claim_boundary_note.md`
- `scripts/build_presubmission_inquiry_package.py`
- `manuscript/response_transfer/00_decision_tree.md`
- `manuscript/response_transfer/01_editorial_rejection_response_template.md`
- `manuscript/response_transfer/02_reviewer_response_skeleton.md`
- `manuscript/response_transfer/03_transfer_package_by_journal.tsv`
- `manuscript/response_transfer/04_target_specific_rewrite_actions.tsv`
- `manuscript/response_transfer/05_do_not_claim_checklist.md`
- `scripts/build_response_transfer_package.py`
- `manuscript/figure_legends/00_figure_legend_inventory.tsv`
- `manuscript/figure_legends/01_main_figure_legends.md`
- `manuscript/figure_legends/02_supplementary_figure_legends.md`
- `manuscript/figure_legends/03_figure_source_map.tsv`
- `manuscript/figure_legends/04_figure_claim_boundary_checklist.tsv`
- `scripts/build_figure_legend_package.py`
- `manuscript/figure_quality/MAIN_FIGURE_QUALITY_AUDIT.tsv`
- `manuscript/figure_quality/MAIN_FIGURE_QUALITY_REPORT.md`
- `scripts/check_main_figure_quality.py`
- `manuscript/supplementary_quality/SUPPLEMENTARY_ARTIFACT_AUDIT.tsv`
- `manuscript/supplementary_quality/SUPPLEMENTARY_ARTIFACT_REPORT.md`
- `scripts/check_supplementary_artifacts.py`
- `benchmarks/results/BENCHMARK_RESULT_CONTRACT_AUDIT.tsv`
- `benchmarks/results/BENCHMARK_RESULT_CONTRACT_REPORT.md`
- `scripts/check_benchmark_result_contracts.py`
- `manuscript/provenance/SUBMISSION_PROVENANCE_AUDIT.tsv`
- `manuscript/provenance/SUBMISSION_PROVENANCE_REPORT.md`
- `scripts/check_submission_provenance.py`
- `scripts/upload_zenodo_deposition.py`
- `release/ZENODO_API_UPLOAD_SUMMARY.json`
- `release/ZENODO_API_UPLOAD_SUMMARY.md`
- `manuscript/method_reporting/METHOD_REPORTING_AUDIT.tsv`
- `manuscript/method_reporting/METHOD_REPORTING_REPORT.md`
- `manuscript/method_reporting/REVIEWER_RISK_REGISTER.tsv`
- `manuscript/method_reporting/REVIEWER_RISK_REPORT.md`
- `scripts/check_method_reporting_readiness.py`
- `manuscript/CLAIM_SAFETY_AUDIT.tsv`
- `manuscript/CLAIM_SAFETY_AUDIT_REPORT.md`
- `scripts/check_claim_safety.py`
- `manuscript/SCI_TITLE_ABSTRACT_KEYWORDS.md`
- `manuscript/SCI_MANUSCRIPT_V1.md`
- `manuscript/SCI_MANUSCRIPT_V1_claim_tracked.md`
- `manuscript/SCI_MANUSCRIPT_V2_POLISHED.md`
- `manuscript/SCI_MANUSCRIPT_V2_POLISHED_claim_tracked.md`
- `manuscript/SCI_MANUSCRIPT_V2_EDITORIAL_AUDIT.tsv`
- `manuscript/SCI_MANUSCRIPT_V2_CHANGELOG.tsv`
- `manuscript/submission_upload_package/SheafSignal_main_manuscript_v2.docx`
- `manuscript/submission_upload_package/SheafSignal_cover_letter_NatureMethods.docx`
- `manuscript/submission_upload_package/SheafSignal_supplementary_information.docx`
- `manuscript/submission_upload_package/submission_upload_manifest.tsv`
- `manuscript/submission_upload_package/submission_upload_preflight_checklist.tsv`
- `manuscript/submission_upload_package/main_figure_upload_manifest.tsv`
- `manuscript/submission_upload_package/main_figures/`
- `manuscript/submission_upload_package/DOCX_TEXT_EXTRACTION_CHECK.md`
- `manuscript/submission_upload_package/DOCX_LAYOUT_CHECK.tsv`
- `manuscript/SCI_COVER_LETTER_NatureMethods.md`
- `manuscript/SCI_AUTHOR_TODO.md`
- `scripts/build_formal_sci_manuscript.py`
- `scripts/build_polished_sci_manuscript_v2.py`
- `scripts/build_submission_upload_package.py`
- `manuscript/references/SCI_REFERENCES_VERIFIED.tsv`
- `manuscript/references/SCI_REFERENCES.bib`
- `manuscript/references/SCI_REFERENCE_PLACEHOLDER_MAP.tsv`
- `manuscript/references/SCI_REFERENCES.md`
- `manuscript/references/SCI_REFERENCE_GAP_REPORT.md`
- `manuscript/references/SCI_MANUSCRIPT_V1_referenced.md`
- `scripts/build_reference_package.py`
- `manuscript/figure_manifest.tsv`
- `benchmarks/results/gse154778_pdac_scrna/qc/`
- `docs/benchmark_plan.md`
- `docs/publication_strategy.md`

## Next 3 Actions

1. Treat full LIANA plus bounded NicheNet/nichenetr-engine evidence as comparator support, not broad superiority over all CCC tools.
2. Keep the NicheNet methods text explicit that the current run uses a project-curated TME ligand-target prior matrix.
3. Create the Zenodo deposition from `release/zenodo_upload_manifest.tsv`, insert the DOI, then rerun `python scripts/check_final_submission_blockers.py` until it no longer returns `NO_GO`.
4. If the first journal rejects or requests transfer, use `manuscript/response_transfer/03_transfer_package_by_journal.tsv` before rewriting the manuscript.
5. Before final figure assembly, compare all captions against `manuscript/figure_legends/03_figure_source_map.tsv` and keep unsupported claims out of figure legends.
6. After regenerating figures, rerun `python scripts/check_main_figure_quality.py` before rebuilding the upload package.
7. After regenerating supplement files, rerun `python scripts/check_supplementary_artifacts.py` and resolve any failing artifact rows.
8. After regenerating benchmark summaries or comparator imports, rerun `python scripts/check_benchmark_result_contracts.py`.
9. After rebuilding submission-facing artifacts, rerun `python scripts/check_submission_provenance.py`.
10. Before Zenodo publication, replace `TBD` creator/GitHub metadata, set `ZENODO_ACCESS_TOKEN`, run `python scripts/upload_zenodo_deposition.py --dry-run`, then publish only with the explicit confirmation flag.
11. Before final blocker checks, rerun `python scripts/check_method_reporting_readiness.py` and resolve any `fail` rows.
12. Before every submission, rebuttal, or transfer, rerun `python scripts/check_claim_safety.py --report-only` and resolve any `blocking_positive_claim` rows.
13. Use `manuscript/SCI_MANUSCRIPT_V2_POLISHED.md` as the current working SCI draft and revise it against `manuscript/SCI_MANUSCRIPT_V2_POLISHED_claim_tracked.md`.
14. Use `manuscript/references/SCI_MANUSCRIPT_V1_referenced.md` after reference-placeholder replacement and keep `manuscript/references/SCI_REFERENCE_GAP_REPORT.md` resolved.
15. Use `manuscript/submission_upload_package/submission_upload_preflight_checklist.tsv` as the last local upload checklist after Zenodo DOI, GitHub URL, and author metadata are completed.
