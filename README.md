# SheafSignal

SheafSignal is a prototype algorithm for cell-cell communication analysis.
It now implements a rank-one cellular sheaf layer over a cell-type graph:
vertex stalks represent pathway state, edge stalks represent communication
observations, and the primary Hodge decomposition is applied to the sheaf
coboundary residual. Communication-flow Hodge components remain secondary
diagnostics.

This repository currently contains a runnable methods package and public TME
benchmark workflow. It is intended for method development and benchmarking,
not for clinical decision making.

## Publication status

This is currently a 20-50 IF methods-manuscript hardening workspace, not a
submission-ready package. Round 2 hardening completed full GSE154778
`scanpy_full_v1` reannotation, sample-stratified 1000-permutation benchmarking,
the pre-specified GSE154778 10,000-permutation confirmatory subset, and formal
sheaf residual outputs, but Zenodo/GitHub release remains on hold until public
release metadata, author-owned fields, and DOI blockers are cleared. Acceptance in any
journal is not guaranteed. See:

- `docs/publication_strategy.md`
- `docs/benchmark_plan.md`
- `docs/github_release_checklist.md`
- `docs/github_zenodo_authorization_guide.md`
- `docs/reviewer_reproducibility_quickstart.md`
- `docs/data_and_code_availability_template.md`
- `release/EXTERNAL_RELEASE_AUTHORIZATION_REPORT.md`
- `release/EXTERNAL_RELEASE_AUTHORIZATION_STATUS.tsv`
- `release/GITHUB_RELEASE_PUBLICATION_REPORT.md`
- `release/GITHUB_URL_FINALIZATION_SUMMARY.md`
- `release/zenodo_deposition_metadata.json`
- `release/archive_manifest.tsv`
- `release/ZENODO_UPLOAD_PREFLIGHT_REPORT.md`
- `release/ZENODO_UPLOAD_PREFLIGHT_STATUS.tsv`
- `release/RELEASE_UNBLOCKER_RUNBOOK_ZH.md`
- `release/RELEASE_UNBLOCKER_MATRIX.tsv`
- `release/SUBMISSION_UNBLOCKER_HANDOFF_ZH.md`
- `release/SUBMISSION_UNBLOCKER_HANDOFF_ZH.tsv`
- `release/POST_UNBLOCK_RELEASE_PIPELINE_REPORT.md`
- `release/POST_UNBLOCK_RELEASE_PIPELINE_PLAN.tsv`
- `manuscript/SHEAFSIGNAL_20_50_IF_STATUS_BRIEF_ZH_2026-05-03.md`
- `manuscript/journal_metric_audit/JOURNAL_SUBMISSION_DAY_CHECK_TEMPLATE.tsv`
- `manuscript/journal_metric_audit/JOURNAL_SUBMISSION_DAY_CHECK_REPORT.md`
- `manuscript/submission_metadata/AUTHOR_CONFIRMATION_PACKET.md`
- `manuscript/submission_metadata/AUTHOR_CONFIRMATION_RESPONSE_TEMPLATE.tsv`
- `manuscript/submission_metadata/AUTHOR_CONFIRMATION_RESPONSE_APPLY_REPORT.md`
- `manuscript/submission_metadata/AUTHOR_CONFIRMATION_PREFLIGHT_REPORT.md`
- `manuscript/submission_metadata/AUTHOR_CONFIRMATION_PREFLIGHT_STATUS.tsv`
- `manuscript/SCI20_50_ACTION_BOARD.md`
- `manuscript/JOURNAL_TARGETS_20_50.tsv`
- `manuscript/SUBMISSION_READINESS_REPORT.md`
- `manuscript/SCI_MANUSCRIPT_V2_POLISHED.md`
- `manuscript/SCI_MANUSCRIPT_V2_EDITORIAL_AUDIT.tsv`
- `manuscript/figure_quality/MAIN_FIGURE_QUALITY_REPORT.md`
- `manuscript/supplementary_quality/SUPPLEMENTARY_ARTIFACT_REPORT.md`
- `benchmarks/results/BENCHMARK_RESULT_CONTRACT_REPORT.md`
- `manuscript/provenance/SUBMISSION_PROVENANCE_REPORT.md`
- `manuscript/method_reporting/METHOD_REPORTING_REPORT.md`
- `manuscript/submission_upload_package/`
- `external_ai_review_packet/ROUND2_HARDENING_STATUS_2026-05-02.md`
- `external_ai_review_packet/EXTERNAL_BETA_REVIEW_TRIAGE_REPORT.md`
- `external_ai_review_packet/external_beta_review_action_matrix.tsv`
- `external_ai_review_packet/shareable_review_bundle/SHAREABLE_REVIEW_BUNDLE_REPORT.md`

## Problem

Common cell-cell communication tools usually ask whether sender cell type A can
signal to receiver cell type B through ligand-receptor pairs. SheafSignal asks a
different question:

- Are the inferred communication edges consistent with pathway state over the
  whole tissue graph?
- Do local feedback loops create high curl energy?
- Which sender cell types contribute most to communication frustration?

## Inputs

The MVP accepts plain text tables:

- `expression.csv`: cells x genes expression matrix. The first column should be
  `cell_id`.
- `metadata.csv`: at least `cell_id` and `cell_type`.
- `ligand_receptor.csv`: at least `ligand` and `receptor`; optional `weight`.
- `pathway_genes.txt`: one target/pathway gene per line.

For real scRNA-seq or spatial transcriptomics data, run standard QC,
normalization, batch-effect assessment, and annotation checks before using this
MVP. If the input is raw counts, the default CLI applies CPM-per-10k plus
`log1p` normalization.

## Core outputs

The default output paths are:

- `results/sheaf_energy_by_edge.csv`
- `results/hodge_decomposition_scores.csv`
- `figures/communication_curl_network.pdf`

Optional permutation outputs:

- `results/sheaf_energy_permutation_pvalues.csv`
- `results/frustration_permutation_pvalues.csv`
- `results/global_permutation_pvalues.csv`

Important columns:

- `sheaf_energy`: edge-level inconsistency between LR flow and pathway gradient.
- `gradient_ratio`: proportion of net communication flow explained by node
  potentials.
- `curl_ratio`: proportion explained by local triangular feedback loops.
- `harmonic_ratio`: residual global circulation not explained by gradient or
  local triangles.
- `frustration_score`: sender-level share of total outgoing sheaf energy.

When `--n-permutations` is used, SheafSignal adds empirical p-values and
Benjamini-Hochberg FDR columns. The current null model shuffles cell-type
labels across cells while preserving the original label counts. This tests
whether observed frustration is stronger than expected from randomized
cell-type assignment; it does not replace biological validation or a
dataset-specific covariate model.

## Quick start

From WSL:

```bash
cd /mnt/e/4实验数据/10新算法/SheafSignal
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
sheafsignal run \
  --expression examples/demo_expression.csv \
  --metadata examples/demo_metadata.csv \
  --lr-db examples/demo_ligand_receptor.csv \
  --gene-set examples/demo_pathway_genes.txt \
  --project-dir .
```

Run with a small permutation test:

```bash
sheafsignal run \
  --expression examples/demo_expression.csv \
  --metadata examples/demo_metadata.csv \
  --lr-db examples/demo_ligand_receptor.csv \
  --gene-set examples/demo_pathway_genes.txt \
  --project-dir . \
  --n-permutations 100 \
  --random-seed 1
```

For multi-sample or spatial-section data, prefer stratified permutation:

```bash
sheafsignal run \
  --expression expression.csv \
  --metadata metadata.csv \
  --lr-db ligand_receptor.csv \
  --gene-set pathway_genes.txt \
  --project-dir . \
  --n-permutations 1000 \
  --permutation-strata-col sample_id
```

Run tests:

```bash
python -m pytest -q
```

If `pytest` is not available in your current Python environment:

```bash
pip install -e ".[dev]"
python -m pytest -q
```

## GitHub and data release

GitHub should contain the software, tests, demo data, metadata, and download
scripts. Large omics files and any protected clinical metadata should not be
committed directly. Public datasets should be listed in:

```text
metadata/datasets.tsv
```

Before making the repository public, run:

```bash
python scripts/release_audit.py
```

## Nature Methods oriented TME benchmark

The publication track is organized around tumor microenvironment communication
frustration. The fixed public benchmark manifest is:

```text
metadata/datasets.tsv
```

Validate and inspect the public downloads without downloading large files:

```bash
python scripts/download_public_datasets.py --validate-only
python scripts/download_public_datasets.py --dry-run
```

Run the reproducible smoke-test benchmark from a clean clone:

```bash
python scripts/prepare_public_datasets.py --include-demo
python scripts/run_tme_benchmark.py --include-demo
python scripts/make_publication_figures.py
```

Run the first real-data adapter after downloading GSE154778:

```bash
python scripts/download_public_datasets.py --dataset-id gse154778_pdac_scrna
python scripts/prepare_public_datasets.py --dataset-id gse154778_pdac_scrna
python scripts/run_tme_benchmark.py
```

For local smoke testing on a small subset:

```bash
python scripts/prepare_public_datasets.py \
  --dataset-id gse154778_pdac_scrna \
  --max-cells 1000 \
  --force \
  --marker-margin 0
python scripts/run_tme_benchmark.py --include-demo
```

To replace the 1000-cell smoke-test subset with the full processed matrix,
rerun preparation with `--force` and omit `--max-cells`.

Preferred full GSE154778 benchmark path:

```bash
python scripts/prepare_public_datasets.py \
  --dataset-id gse154778_pdac_scrna \
  --profile-only \
  --force \
  --marker-margin 0
python scripts/run_tme_benchmark.py --include-demo
```

This profile-only mode reads only marker, LR, and pathway genes from the raw
processed matrix, then writes a compact cell-type profile table for benchmarking.

Run the second public scRNA-seq replication adapter for GSE72056 melanoma:

```bash
python scripts/download_public_datasets.py --dataset-id gse72056_melanoma_scrna
python scripts/prepare_public_datasets.py --dataset-id gse72056_melanoma_scrna --force
python scripts/run_tme_benchmark.py --include-demo
```

The GSE72056 adapter reads the GEO processed table as metadata rows plus genes x
cells, uses the author-provided malignant/non-malignant annotation codes, and
writes compact cell-type profiles. In the current run, GSE72056 has 4,645 cells,
52 selected LR/marker/pathway genes, and 7 cell-type categories. Its top
frustration source is CAF/Fibroblast, not Myeloid, so it should be interpreted
as cancer-context replication of the SheafSignal framework rather than
replication of the PDAC Myeloid-specific hypothesis.

Run the third public scRNA-seq replication adapter for GSE176078 breast cancer:

```bash
python scripts/download_public_datasets.py --dataset-id gse176078_brca_scrna
python scripts/prepare_public_datasets.py --dataset-id gse176078_brca_scrna --force
python scripts/run_tme_benchmark.py --include-demo
```

The GSE176078 adapter reads the GEO tar.gz archive without expanding it into a
dense matrix. It streams the Matrix Market count matrix, keeps only the selected
LR/marker/pathway genes, and uses author `celltype_major` annotations. In the
current run, GSE176078 has 100,064 cells, 53 selected genes, and 8 mapped
cell-type categories across ER+, HER2+, and TNBC samples. Its top frustration
source is Tumor/Malignant, so it should be used as another independent
cancer-context benchmark rather than a universal-source claim.

Run the public spatial Visium case:

```bash
python scripts/download_public_datasets.py --dataset-id tenx_breast_visium
python scripts/prepare_public_datasets.py --dataset-id tenx_breast_visium --force --marker-margin 0
python scripts/run_tme_benchmark.py --include-demo
```

The Visium adapter reads the 10x filtered HDF5 matrix and spatial coordinate
tarball, keeps selected LR/marker/pathway genes, and writes marker-dominant
spot metadata. `run_tme_benchmark.py` then computes spot-neighbor spatial sheaf
energy and exports hotspots to `benchmarks/results/spatial_frustration_hotspots.csv`.
In the current run, the spatial case has 3,798 in-tissue spots and 22,788
directed k-nearest-neighbor spot edges. Marker-dominant labels are spot-level
program summaries, not single-cell annotations, so sparse labels such as T/NK
or Endothelial must not be treated as strong mechanistic claims.

Run Visium spatial hotspot QC and k-neighbor sensitivity:

```bash
python scripts/qc_tenx_visium_spatial.py
```

This writes supplement-ready hotspot scatter, marker-program burden, and
`k_neighbors` sensitivity outputs under:

```text
benchmarks/results/tenx_breast_visium/spatial/qc/
```

The current `k=4,6,8,10,12` sensitivity check keeps hotspot rankings stable
against the `k=6` reference, with minimum Spearman correlation 0.9309 and
minimum top-50 hotspot overlap 0.86.

`run_tme_benchmark.py` also writes an internal conventional CCC baseline named
`LRProductBaseline`. This is not a replacement for CellChat, CellPhoneDB,
NicheNet, or LIANA. It exports ligand-expression x receptor-expression edge
strength and aligns it with SheafSignal `sheaf_energy` so the benchmark can
separate ordinary communication intensity from pathway-consistency frustration.

Comparator outputs are written under:

```text
benchmarks/results/<dataset_id>/comparators/
```

Export comparator handoff bundles for all completed public benchmarks:

```bash
python scripts/export_comparator_inputs.py --all-completed-public
```

This writes `cell_type_profiles.csv`, `ligand_receptor_pairs.csv`,
`sheafsignal_edge_template.csv`, and `external_comparator_template.csv` under:

```text
benchmarks/results/<dataset_id>/comparator_inputs/
```

After running an external CCC tool, import its edge table with:

```bash
python scripts/import_external_comparator.py \
  --dataset-id gse154778_pdac_scrna \
  --tool LIANA \
  --input path/to/external_edges.csv \
  --sender-col sender \
  --receiver-col receiver \
  --score-col score
```

LIANA can also be run directly from SheafSignal processed `expression.csv` and
`metadata.csv` files:

```bash
conda env create -f envs/liana_environment.yml
conda activate sheafsignal-liana

python scripts/run_liana_comparator.py \
  --dataset-id gse154778_pdac_scrna \
  --max-cells 5000 \
  --min-cells 20 \
  --n-perms 1000 \
  --n-jobs 4
```

GSE72056 and GSE176078 are profile-first adapters by default. Before running
LIANA on those datasets, export selected-gene cell-level expression tables:

```bash
python scripts/prepare_public_datasets.py \
  --dataset-id gse72056_melanoma_scrna \
  --write-selected-expression \
  --force

python scripts/prepare_public_datasets.py \
  --dataset-id gse176078_brca_scrna \
  --write-selected-expression \
  --force
```

The direct LIANA runner writes raw LIANA output, a standardized external edge
table, and SheafSignal-aligned comparator outputs under:

```text
benchmarks/results/<dataset_id>/comparators/liana_run/
benchmarks/results/<dataset_id>/comparators/sheafsignal_vs_liana.csv
```

For manuscript-grade runs, run LIANA without `--max-cells` unless memory limits
force a documented sensitivity run. Long external comparator jobs should be
started in `tmux` or `nohup` because interrupted network or compute sessions can
leave incomplete external tool outputs.

Mechanistic comparator routes are also provided:

```bash
python scripts/run_mechanistic_prior_comparator.py \
  --dataset-id gse154778_pdac_scrna

Rscript scripts/run_nichenet_prior_comparator.R \
  --dataset-id gse154778_pdac_scrna

python scripts/import_external_comparator.py \
  --dataset-id gse154778_pdac_scrna \
  --tool NicheNet \
  --input benchmarks/results/gse154778_pdac_scrna/comparators/nichenet_prior_run/nichenet_prior_raw_edges.csv \
  --sender-col sender \
  --receiver-col receiver \
  --score-col score \
  --ligand-col ligand \
  --receptor-col receptor \
  --aggregate max
```

Install the R-side NicheNet dependency with:

```bash
Rscript envs/install_nichenetr.R
```

The NicheNet route uses the official `nichenetr` scoring engine with the
project-curated TME ligand-target prior matrix. Do not describe it as a full
pretrained NicheNet network benchmark unless that resource is explicitly added.

Check whether external comparator execution is currently blocked or ready:

```bash
python scripts/check_external_comparator_readiness.py
```

This writes:

```text
benchmarks/results/external_comparator_environment_status.csv
benchmarks/results/external_comparator_execution_plan.csv
benchmarks/results/external_comparator_gate_summary.csv
manuscript/external_comparator_gate_summary.tsv
```

Build the reviewer-facing objection and gate table:

```bash
python scripts/build_reviewer_objection_table.py
```

Current status: `LRProductBaseline`, full LIANA, `MechanisticTargetPrior`, and
bounded NicheNet/nichenetr-engine, CellPhoneDB, and CellChat imports are
complete for the three primary public scRNA-seq benchmarks. Demo data, Visium,
GSE103322, and niche-DE remain outside the primary comparator-completeness
claim, so broad CCC-tool-superiority claims are still out of scope.

Build the GitHub/Zenodo reproducibility release manifests:

```bash
python scripts/build_reproducibility_release.py
python scripts/release_audit.py
```

Build the 20-50 IF journal action board and submission-readiness report:

```bash
python scripts/build_journal_target_board.py
python scripts/apply_journal_submission_day_check.py
python scripts/build_nature_methods_submission_package.py
python scripts/build_submission_metadata_templates.py
python scripts/apply_author_confirmation_response.py
python scripts/build_presubmission_inquiry_package.py
python scripts/build_response_transfer_package.py
python scripts/build_figure_legend_package.py
python scripts/check_main_figure_quality.py
python scripts/check_supplementary_artifacts.py
python scripts/check_benchmark_result_contracts.py
python scripts/check_submission_provenance.py
python scripts/check_method_reporting_readiness.py
python scripts/upload_zenodo_deposition.py --dry-run
python scripts/build_formal_sci_manuscript.py
python scripts/build_reference_package.py
python scripts/build_polished_sci_manuscript_v2.py
python scripts/build_submission_upload_package.py
python scripts/package_external_beta_review_bundle.py
python scripts/triage_external_beta_reviews.py
python scripts/check_claim_safety.py --report-only
python scripts/build_zenodo_deposition_package.py
python scripts/build_submission_unblocker_handoff.py
python scripts/build_post_unblock_release_pipeline.py
python scripts/check_final_submission_blockers.py --report-only
python scripts/build_submission_readiness_report.py
```

This writes:

```text
release/release_file_inventory.tsv
release/github_release_manifest.tsv
release/zenodo_upload_manifest.tsv
release/github_sha256sums.txt
release/zenodo_sha256sums.txt
release/REPRODUCIBILITY_RELEASE_SUMMARY.md
release/DATA_AVAILABILITY_STATEMENT_DRAFT.md
manuscript/JOURNAL_TARGETS_20_50.tsv
manuscript/SCI20_50_ACTION_BOARD.md
manuscript/nature_methods_package/
manuscript/submission_metadata/
manuscript/FINAL_SUBMISSION_BLOCKERS.tsv
manuscript/NATURE_METHODS_GO_NO_GO_REPORT.md
release/zenodo_deposition_metadata.json
release/ZENODO_DEPOSITION_INSTRUCTIONS.md
release/GITHUB_RELEASE_INSTRUCTIONS.md
manuscript/SUBMISSION_READINESS_REPORT.md
manuscript/NATURE_METHODS_FORMAT_AUDIT.tsv
manuscript/NATURE_METHODS_FORMAT_AUDIT_REPORT.md
manuscript/presubmission_inquiry/
manuscript/response_transfer/
manuscript/figure_legends/
manuscript/figure_quality/
manuscript/supplementary_quality/
manuscript/method_reporting/
manuscript/SCI_MANUSCRIPT_V1.md
manuscript/SCI_MANUSCRIPT_V1_claim_tracked.md
manuscript/SCI_MANUSCRIPT_V2_POLISHED.md
manuscript/SCI_MANUSCRIPT_V2_POLISHED_claim_tracked.md
manuscript/SCI_MANUSCRIPT_V2_EDITORIAL_AUDIT.tsv
manuscript/SCI_MANUSCRIPT_V2_CHANGELOG.tsv
manuscript/submission_upload_package/
manuscript/SCI_TITLE_ABSTRACT_KEYWORDS.md
manuscript/SCI_COVER_LETTER_NatureMethods.md
manuscript/references/
manuscript/CLAIM_SAFETY_AUDIT.tsv
manuscript/CLAIM_SAFETY_AUDIT_REPORT.md
benchmarks/results/BENCHMARK_RESULT_CONTRACT_AUDIT.tsv
benchmarks/results/BENCHMARK_RESULT_CONTRACT_REPORT.md
manuscript/provenance/SUBMISSION_PROVENANCE_AUDIT.tsv
manuscript/provenance/SUBMISSION_PROVENANCE_REPORT.md
```

The Nature Methods package includes a full manuscript draft and supplementary
information draft:

```text
manuscript/nature_methods_package/09_full_manuscript_draft.md
manuscript/nature_methods_package/10_supplementary_information_draft.md
```

Run the local Nature Methods format audit:

```bash
python scripts/check_nature_methods_format.py --report-only
```

Build the Nature Methods presubmission inquiry package:

```bash
python scripts/build_presubmission_inquiry_package.py
```

Build the post-decision reviewer-response and journal-transfer package:

```bash
python scripts/build_response_transfer_package.py
```

Build evidence-linked figure legends and source maps:

```bash
python scripts/build_figure_legend_package.py
```

Run automated main-figure PDF quality audit:

```bash
python scripts/check_main_figure_quality.py
```

Run supplementary artifact readability audit:

```bash
python scripts/check_supplementary_artifacts.py
```

Run benchmark result contract audit:

```bash
python scripts/check_benchmark_result_contracts.py
```

Run submission artifact provenance audit:

```bash
python scripts/check_submission_provenance.py
```

Run a Zenodo API upload dry-run. Real upload requires a Zenodo personal access
token in `ZENODO_ACCESS_TOKEN`, completed creator metadata, and an explicit
publish confirmation:

```bash
python scripts/upload_zenodo_deposition.py --dry-run
```

Run method-reporting and reviewer-risk audit:

```bash
python scripts/check_method_reporting_readiness.py
```

Build the formal SCI manuscript v1:

```bash
python scripts/build_formal_sci_manuscript.py
```

Build the verified reference package and reference-resolved manuscript:

```bash
python scripts/build_reference_package.py
```

Build the polished SCI manuscript v2 and editorial audit:

```bash
python scripts/build_polished_sci_manuscript_v2.py
```

Build DOCX upload artifacts and a submission preflight checklist:

```bash
python scripts/build_submission_upload_package.py
```

This also runs a lightweight DOCX-to-PDF layout check when `soffice` and
PyMuPDF are available, writing:

```text
manuscript/submission_upload_package/DOCX_LAYOUT_CHECK.tsv
```

The upload package also copies the five generated main-figure PDFs into:

```text
manuscript/submission_upload_package/main_figures/
manuscript/submission_upload_package/main_figure_upload_manifest.tsv
```

Run manuscript-wide claim safety audit:

```bash
python scripts/check_claim_safety.py --report-only
```

For the final submission gate, omit `--report-only`. The command should return
success only after blocking items such as the Zenodo DOI have been resolved:

```bash
python scripts/check_final_submission_blockers.py
```

After Zenodo publishes the DOI, update all DOI-dependent files with:

```bash
python scripts/finalize_zenodo_doi.py --doi <ZENODO_DOI>
```

The release builder does not mint a DOI. Before submission, upload the files
listed in `release/zenodo_upload_manifest.tsv` to Zenodo and insert the DOI into
the manuscript data-availability statement.

Export compact profile-level inputs for CellChat, CellPhoneDB, NicheNet, LIANA,
or other external CCC tools:

```bash
python scripts/export_comparator_inputs.py --dataset-id gse154778_pdac_scrna
```

This writes:

```text
benchmarks/results/gse154778_pdac_scrna/comparator_inputs/
```

After an external tool has produced an edge table, import and align it:

```bash
python scripts/import_external_comparator.py \
  --dataset-id gse154778_pdac_scrna \
  --tool LIANA \
  --input path/to/liana_edges.csv \
  --sender-col sender \
  --receiver-col receiver \
  --score-col score
```

If an external score is rank-like where smaller is better, add
`--score-ascending`.

Generate GSE154778 annotation QC supplement figures:

```bash
python scripts/qc_gse154778_annotation.py
```

QC outputs are written to:

```text
benchmarks/results/gse154778_pdac_scrna/qc/
```

Run a bootstrap stability check for the GSE154778 Myeloid frustration
hypothesis:

```bash
python scripts/bootstrap_gse154778_stability.py --n-bootstraps 100 --random-seed 1
```

For a quick local smoke test, reduce `--n-bootstraps` to 20. The bootstrap is
performed over cells while keeping the current frozen annotation version fixed;
it tests computational stability, not independent biological validity. In the
current 100-bootstrap run on `scanpy_full_v1`, Myeloid remains the top
frustration source in 100/100 resamples, with median frustration score 0.9176
and a 2.5%-97.5% bootstrap interval of 0.9110-0.9241.

Stability outputs are written to:

```text
benchmarks/results/gse154778_pdac_scrna/stability/
```

Run GSE154778 lesion-stratified SheafSignal analysis:

```bash
python scripts/stratify_gse154778_lesion.py
```

This runs Primary and Metastatic profiles separately and writes:

```text
benchmarks/results/gse154778_pdac_scrna/stratified/
```

The current stratified result keeps Myeloid as the top frustration source in
both Primary and Metastatic subsets. Low-count cell-type warnings are included
in the output tables and must be respected in manuscript interpretation.

Run the claim-gating and sample-level robustness checks:

```bash
python scripts/sample_level_gse154778_stability.py
python scripts/qc_gse154778_claim_gating.py
```

These write:

```text
benchmarks/results/gse154778_pdac_scrna/stability/sample_level_*.csv
benchmarks/results/gse154778_pdac_scrna/qc/claim_gating_by_cell_type.csv
benchmarks/results/gse154778_pdac_scrna/qc/myeloid_claim_readiness_summary.csv
```

The current claim gate does not allow any GSE154778 cell type to be promoted as
a validated main-text biological source. Myeloid remains a supplement-level,
lesion-stratified computational hypothesis, while pooled CAF/Fibroblast
frustration is QC-warning-only because metastatic support is underpowered.
Sample-level analysis shows heterogeneity, especially in Primary tumors, so the
manuscript wording must not claim that any cell type is top in every sample.

Standard benchmark outputs:

```text
benchmarks/results/component_recovery.csv
benchmarks/results/tool_comparison.csv
benchmarks/results/public_tme_sheafsignal_summary.csv
benchmarks/results/spatial_frustration_hotspots.csv
manuscript/figure_manifest.tsv
```

The public scRNA-seq/spatial datasets are manifested but not committed. After
download and dataset-specific preparation, frozen processed matrices should be
released on Zenodo and linked back through `metadata/datasets.tsv`.

GSE154778 currently uses the frozen `scanpy_full_v1` annotation and associated
claim gates. Publication-grade interpretation should still manually inspect
marker expression and, if possible, compare against author or third-party
annotations before any biological mechanism language is strengthened.

Recommended release pattern:

1. Publish source code on GitHub.
2. Archive a versioned release on Zenodo to obtain a DOI.
3. Deposit large processed benchmark data on Zenodo/Figshare/GEO/SRA as
   appropriate.
4. Record every accession, DOI, license, and checksum in
   `metadata/datasets.tsv`.

⚠️ Do not upload private clinical data, protected participant metadata, or
controlled-access raw data to GitHub unless release is explicitly permitted by
consent, IRB/ethics approval, institutional rules, and original data licenses.

## Method sketch

For each directed sender-receiver cell-type edge, SheafSignal computes an LR
communication flow:

```text
flow(sender -> receiver) = sum_ligand_receptor weight * ligand_sender * receptor_receiver
```

It also computes a pathway score for each cell type from the target gene set.
The edge sheaf energy is a weighted mismatch between standardized LR flow and
standardized pathway gradient:

```text
sheaf_energy(edge) = edge_weight * (z(log1p(flow)) - z(pathway_receiver - pathway_sender))^2
```

For Hodge decomposition, anti-parallel directed edges are collapsed into a
canonical pairwise net flow. The net edge flow is decomposed into:

```text
flow = gradient + curl + harmonic
```

The current curl space is generated from complete cell-type triangles in the
communication graph.

## Statistical assumptions

The current permutation test assumes exchangeability of cell labels under the
null. For real studies, this assumption can be violated by patient identity,
batch, spatial region, tissue section, or disease group. Publication analyses
should use stratified permutation or mixed-effect/bootstrap designs when those
covariates are present.

Multiple testing correction is done with Benjamini-Hochberg FDR across tested
edges or cell types. Treat p-values as exploratory unless the null model,
tested hypotheses, and FDR scope are defined before looking at the results.

## Current limitations

- The MVP aggregates cells to cell-type means. Spatial neighbor graphs and
  single-cell local sheaves are planned extensions.
- Hodge decomposition uses pairwise net flow, so it emphasizes directional
  imbalance rather than total bidirectional communication.
- Ligand-receptor activity is expression based and does not yet model receptor
  complex stoichiometry, downstream target priors, or ligand secretion.
- The current permutation test is label-shuffle based; stratified permutation,
  patient-level bootstrap, and pathway/LR database uncertainty are planned.

## Repository map

```text
src/sheafsignal/          Python package
examples/                 small synthetic demo data
tests/                    unit and pipeline tests
docs/                     method, benchmark, publication, and release notes
metadata/datasets.tsv     public dataset manifest
scripts/                  reproducibility and release helper scripts
workflow/                 Snakemake entry point
benchmarks/               benchmark design and future benchmark outputs
manuscript/               manuscript planning workspace
```
