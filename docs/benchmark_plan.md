# Benchmark plan

## Goal

The benchmark must show that SheafSignal provides information that standard
cell-cell communication tools do not provide: network self-consistency,
feedback/curl, harmonic circulation, and cell-type-level frustration.

## Simulation benchmark

### Graph classes

1. Chain/tree graph:
   - expected: high `gradient_ratio`
   - expected: low `curl_ratio`
2. Triangle feedback graph:
   - expected: high `curl_ratio`
3. Ring with no filled triangles:
   - expected: high `harmonic_ratio`
4. Mixed graph:
   - expected: non-zero gradient, curl, and harmonic components

### Noise factors

- dropout
- library size variation
- cell-type imbalance
- missing ligand-receptor pairs
- spurious ligand-receptor pairs
- pathway gene set contamination
- batch effects
- cell-type annotation noise

### Metrics

- component recovery correlation
- false positive curl detection
- rank recovery of high-frustration source nodes
- runtime and memory
- stability across bootstrap resampling

## Real-data benchmark

### Required datasets

Fixed Nature Methods oriented TME benchmark set:

- GSE72056 melanoma scRNA-seq
- GSE154778 PDAC scRNA-seq
- GSE176078 breast cancer scRNA-seq
- 10x Genomics human breast cancer Visium spatial transcriptomics

### Comparator tools

- Internal baseline: `LRProductBaseline`, ligand expression x receptor
  expression edge strength, aligned to SheafSignal edge-level `sheaf_energy`
  as a dependency-light benchmark sanity check.
- CellChat
- CellPhoneDB
- NicheNet
- LIANA
- niche-DE when differential niche association is relevant

### Comparison philosophy

Do not claim SheafSignal replaces these methods. Instead, use their LR edges as
one possible input layer and show that SheafSignal adds a network-consistency
interpretation on top.

## Statistical testing

For each real dataset:

- cell-label permutation for global sheaf energy
- stratified cell-label permutation by sample or tissue section when available
- LR-pair permutation within expression-matched bins
- bootstrap confidence interval for edge sheaf energy
- Benjamini-Hochberg FDR across tested edges or cell types

Report effect sizes with confidence intervals, not only p-values.

## Output tables

Recommended benchmark outputs:

- `benchmarks/results/component_recovery.csv`
- `benchmarks/results/tool_comparison.csv`
- `benchmarks/results/public_tme_sheafsignal_summary.csv`
- `benchmarks/results/spatial_frustration_hotspots.csv`
- `manuscript/figure_manifest.tsv`

Each table should include dataset ID, random seed, command, software version,
and checksum of the input matrix.

The current smoke-test workflow is:

```bash
python scripts/download_public_datasets.py --validate-only
python scripts/download_public_datasets.py --dry-run
python scripts/prepare_public_datasets.py --include-demo
python scripts/run_tme_benchmark.py --include-demo
python scripts/make_publication_figures.py
```

First real-data adapter:

```bash
python scripts/download_public_datasets.py --dataset-id gse154778_pdac_scrna
python scripts/prepare_public_datasets.py --dataset-id gse154778_pdac_scrna
python scripts/run_tme_benchmark.py
```

The GSE154778 adapter reads `GSE154778_dgeMtx.csv.gz` as genes x cells,
transposes it to cells x genes, parses sample and lesion type from IDs such as
`P01:1` or `MET01:1`, and assigns coarse cell types from canonical marker
scores. This annotation is sufficient for a reproducible first benchmark, but
not sufficient as final biological evidence without manual review.

Second real-data adapter:

```bash
python scripts/download_public_datasets.py --dataset-id gse72056_melanoma_scrna
python scripts/prepare_public_datasets.py --dataset-id gse72056_melanoma_scrna --force
python scripts/run_tme_benchmark.py --include-demo
```

The GSE72056 adapter reads
`GSE72056_melanoma_single_cell_revised_v2.txt.gz` as author metadata rows plus
genes x cells, transposes selected LR/marker/pathway genes to cells x genes, and
maps the author codes to coarse categories: Tumor/Malignant, T/NK, B/Plasma,
Myeloid, Endothelial, CAF/Fibroblast, and Unknown. The local processed-file
checksum is recorded in `metadata/datasets.tsv`.

The current GSE72056 profile benchmark uses 4,645 cells, 52 selected genes, and
7 author-annotated cell-type categories. `JCHAIN` is the only required marker
gene absent from the processed table. The current global decomposition is
gradient_ratio 0.9762, curl_ratio 0.0238, and harmonic_ratio approximately 0.
The top frustration source is CAF/Fibroblast with frustration score 0.4142.
This is not evidence that the PDAC Myeloid hypothesis generalizes across every
cancer type; instead, it supports the broader methods claim that SheafSignal can
recover cancer-context-specific computational sheaf-energy rankings from independent public
TME datasets.

Third real-data adapter:

```bash
python scripts/download_public_datasets.py --dataset-id gse176078_brca_scrna
python scripts/prepare_public_datasets.py --dataset-id gse176078_brca_scrna --force
python scripts/run_tme_benchmark.py --include-demo
```

The GSE176078 adapter reads
`GSE176078_Wu_etal_2021_BRCA_scRNASeq.tar.gz` directly. The archive contains
`count_matrix_sparse.mtx`, `count_matrix_genes.tsv`,
`count_matrix_barcodes.tsv`, and `metadata.csv`. The adapter streams the sparse
Matrix Market file and keeps only selected LR/marker/pathway genes rather than
materializing a full dense 100,064-cell matrix. Author `celltype_major`
annotations are mapped to Tumor/Malignant, Normal/Epithelial, T/NK, B/Plasma,
Myeloid, Endothelial, CAF/Fibroblast, and Perivascular.

The current GSE176078 profile benchmark uses 100,064 cells, 53 selected genes,
and 8 mapped author-annotated cell-type categories across ER+, HER2+, and TNBC
samples. The current global decomposition is gradient_ratio 0.9637, curl_ratio
0.0363, and harmonic_ratio approximately 0. The top frustration source is
Tumor/Malignant with frustration score 0.5237. Together with GSE154778 and
GSE72056, this creates a three-dataset public scRNA-seq benchmark where the top
frustration source is context-specific rather than forced to be universal.

Spatial case:

```bash
python scripts/download_public_datasets.py --dataset-id tenx_breast_visium
python scripts/prepare_public_datasets.py --dataset-id tenx_breast_visium --force --marker-margin 0
python scripts/run_tme_benchmark.py --include-demo
```

The 10x breast Visium adapter reads the filtered feature-barcode HDF5 matrix and
the spatial tarball containing `tissue_positions_list.csv`. It keeps selected
LR/marker/pathway genes, CPM-log1p normalizes spots, assigns marker-dominant
spot programs, and builds a spatial k-nearest-neighbor graph over in-tissue
spots. The spatial benchmark computes spot-neighbor LR/pathway sheaf mismatch
and writes:

- `benchmarks/results/spatial_frustration_hotspots.csv`
- `benchmarks/results/tenx_breast_visium/spatial/spatial_sheaf_edges.csv`
- `benchmarks/results/tenx_breast_visium/spatial/spatial_frustration_hotspots.csv`
- `benchmarks/results/tenx_breast_visium/spatial/spatial_hotspot_summary.csv`

The current Visium run uses 3,798 in-tissue spots, 53 selected genes, and 22,788
directed k-nearest-neighbor spot edges. The top hotspot is
`GGTAAATGTGCGTTAC-1`, with spot-level frustration score 0.00394. Marker-dominant
spot labels are not single-cell annotations; sparse programs such as T/NK,
Endothelial, or B/Plasma should be used only as QC context. The spatial main
claim should focus on local hotspot localization rather than cell-type-specific
mechanism.

Visium spatial QC and sensitivity are generated with:

```bash
python scripts/qc_tenx_visium_spatial.py
```

This writes:

- `benchmarks/results/tenx_breast_visium/spatial/qc/marker_spot_counts.csv`
- `benchmarks/results/tenx_breast_visium/spatial/qc/hotspot_marker_overlay.csv`
- `benchmarks/results/tenx_breast_visium/spatial/qc/k_neighbors_sensitivity.csv`
- `benchmarks/results/tenx_breast_visium/spatial/qc/spatial_hotspot_qc_summary.csv`
- supplement PDF versions of marker counts, hotspot scatter, marker overlay,
  and k-neighbor sensitivity

The current sensitivity run compares `k=4,6,8,10,12` against `k=6`. The minimum
Spearman correlation of spot-level frustration scores is 0.9309, and the
minimum top-50 hotspot overlap is 0.86. This supports hotspot localization
robustness across reasonable neighbor graph choices, while still requiring
spatial histology/annotation review before any biological mechanism claim.

A local 1000-cell smoke benchmark is supported with:

```bash
python scripts/prepare_public_datasets.py \
  --dataset-id gse154778_pdac_scrna \
  --max-cells 1000 \
  --force \
  --marker-margin 0
python scripts/run_tme_benchmark.py --include-demo
```

The full local benchmark should use compact profiles instead of a dense full
cells x genes CSV:

```bash
python scripts/prepare_public_datasets.py \
  --dataset-id gse154778_pdac_scrna \
  --profile-only \
  --force \
  --marker-margin 0
python scripts/run_tme_benchmark.py --include-demo
```

The same benchmark command now writes `LRProductBaseline` comparator outputs:

- `benchmarks/results/<dataset_id>/comparators/lr_product_baseline_edges.csv`
- `benchmarks/results/<dataset_id>/comparators/sheafsignal_vs_lr_product_baseline.csv`

This baseline is useful for showing whether high communication frustration is
just a restatement of high LR-product intensity. It is not a substitute for
external CellChat, CellPhoneDB, NicheNet, LIANA, or niche-DE runs.

External comparator handoff is standardized by:

```bash
python scripts/export_comparator_inputs.py --dataset-id gse154778_pdac_scrna
```

The exported bundle contains profile-level expression, LR pairs, cell-type
counts, a SheafSignal edge template, and an external-result template. After an
external CCC tool returns an edge table, import it with:

```bash
python scripts/import_external_comparator.py \
  --dataset-id gse154778_pdac_scrna \
  --tool LIANA \
  --input path/to/external_edges.csv \
  --sender-col sender \
  --receiver-col receiver \
  --score-col score
```

The importer aggregates duplicate ligand-receptor rows to directed cell-type
edges, aligns them to SheafSignal `sheaf_energy`, and updates
`benchmarks/results/tool_comparison.csv`.

LIANA has a direct runner because it can consume SheafSignal processed
cell-level `expression.csv` and `metadata.csv` files:

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

GSE72056 and GSE176078 are intentionally profile-first for lightweight
SheafSignal replication. For LIANA, they must first export selected-gene
cell-level expression:

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

This wrapper calls LIANA `rank_aggregate`, exports `score=1-magnitude_rank`
when available, and then reuses `import_external_comparator.py` so LIANA appears
in the same edge-aligned `tool_comparison.csv` schema as CellChat, CellPhoneDB,
NicheNet, and other external tools. Full manuscript runs should remove
`--max-cells`; any downsampled run is a smoke/sensitivity result only.

The current repository also provides two mechanistic comparator routes:

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

`MechanisticTargetPrior` is a transparent Python baseline. The R NicheNet route
uses `nichenetr::predict_ligand_activities()` with the project-curated TME
ligand-target prior matrix in `metadata/tme_ligand_target_prior.csv`; it should
not be described as a full pretrained NicheNet network benchmark.

External comparator execution readiness is generated by:

```bash
python scripts/check_external_comparator_readiness.py
```

This writes environment, execution-plan, and manuscript gate tables:

- `benchmarks/results/external_comparator_environment_status.csv`
- `benchmarks/results/external_comparator_execution_plan.csv`
- `benchmarks/results/external_comparator_gate_summary.csv`
- `manuscript/external_comparator_gate_summary.tsv`

All completed public benchmark comparator bundles are exported with:

```bash
python scripts/export_comparator_inputs.py --all-completed-public
```

Current exported datasets:

- GSE154778 PDAC scRNA-seq
- GSE72056 melanoma scRNA-seq
- GSE176078 breast cancer scRNA-seq
- 10x breast Visium marker-dominant spot programs

Reviewer-facing comparator and claim gates are generated with:

```bash
python scripts/build_reviewer_objection_table.py
```

This writes:

- `benchmarks/results/comparator_readiness_matrix.csv`
- `benchmarks/results/reviewer_objection_response_table.csv`
- `manuscript/reviewer_objection_response_table.tsv`

The current comparator state is stronger than the initial handoff stage:
`LRProductBaseline`, full LIANA, `MechanisticTargetPrior`, bounded
NicheNet/nichenetr-engine, CellPhoneDB, and CellChat imports are complete for
the three primary public scRNA-seq benchmarks. Pending rows for demo data,
Visium, GSE103322, or niche-DE are outside the primary comparator claim scope;
broad CCC-tool-superiority language is still not allowed.

The current full GSE154778 profile benchmark uses 14,926 cells, 51 selected
marker/LR/pathway genes, and 4 frozen `scanpy_full_v1` cell-type states. The
10,000-permutation confirmatory run ranks pooled CAF/Fibroblast highest by raw
node frustration score, but the claim gate keeps CAF/Fibroblast as
QC-warning-only because metastatic lesion support is sparse. Myeloid remains a
lesion-stratified supplement-level computational hypothesis, not a main
biological source claim.

Annotation QC for the GSE154778 hypothesis is generated with:

```bash
python scripts/qc_gse154778_annotation.py
```

This writes marker heatmap, cell-type counts, annotation confidence, and
frustration-overlay tables/figures under
`benchmarks/results/gse154778_pdac_scrna/qc/`.

Bootstrap stability for the GSE154778 frustration-source hypothesis is generated
with:

```bash
python scripts/bootstrap_gse154778_stability.py --n-bootstraps 100 --random-seed 1
```

For rapid checks, use `--n-bootstraps 20`. The current 100-bootstrap result
keeps Myeloid as the top frustration source in 100/100 resamples, with median
frustration score 0.8741 and a 2.5%-97.5% bootstrap interval of 0.8273-0.9154.
This supports computational stability under fixed coarse marker annotations,
but it is not an independent biological validation of the annotation or
mechanism.

Lesion-stratified GSE154778 analysis is generated with:

```bash
python scripts/stratify_gse154778_lesion.py
```

The current stratified analysis keeps Myeloid as the top frustration source in
both Metastatic and Primary subsets. Metastatic Myeloid frustration score is
0.8112; Primary Myeloid frustration score is 0.3776. Several low-count cell
types are flagged, including Metastatic CAF/Fibroblast, Endothelial, B/Plasma,
Unknown, and Primary Unknown. These flags limit biological interpretation and
should be reported explicitly.

Claim gating and sample-level robustness are generated with:

```bash
python scripts/sample_level_gse154778_stability.py
python scripts/qc_gse154778_claim_gating.py
```

The current hardening gate no longer promotes Myeloid as a `main_claim`
candidate because expression-mode permutation/FDR analysis changes the leading
computational source. Sparse categories remain demoted to `qc_warning_only`,
and the output explicitly records the review-response sentence: "we
pre-specified minimum cell/sample support and
excluded underpowered categories from biological claims." Sample-level
pseudobulk analysis supports stronger robustness in Metastatic samples
than in Primary samples, so the final manuscript claim should be lesion-level
and hypothesis-level rather than universal across every sample.
