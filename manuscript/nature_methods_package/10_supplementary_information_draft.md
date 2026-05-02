# Supplementary Information Draft

## Supplementary Methods

### Dataset Preparation

Public scRNA-seq and spatial transcriptomics datasets are listed in
`metadata/datasets.tsv`. Raw public datasets are downloaded from their original
repositories and are not redistributed through GitHub. Frozen processed
benchmark objects are prepared for Zenodo deposition.

### Annotation QC

GSE154778 uses coarse marker-based annotation for the first-pass benchmark.
Marker heatmaps, cell-type counts, annotation-confidence distributions and
frustration-confidence overlays are generated under
`benchmarks/results/gse154778_pdac_scrna/qc/`.

### Claim Gating

Cell-type-level biological claims require minimum cell and sample support.
Underpowered categories are demoted to supplement-only or QC-warning-only
interpretation. After expression-mode permutation/FDR hardening, GSE154778 has
no current cell-type-level main-text source candidate.

### Comparator Analyses

Comparator outputs for the primary scRNA-seq scope include LRProductBaseline,
full LIANA imports, MechanisticTargetPrior, bounded nichenetr-engine scoring,
CellChat and CellPhoneDB.
The only pending comparator scopes are demo/Visium/GSE103322 rows and
niche-DE; they are outside the primary comparator claim and must not be
represented as completed benchmarks for those scopes.

### Spatial Sensitivity

The Visium spatial case includes k-neighbor sensitivity and hotspot QC. These
analyses test spatial robustness of hotspot ranking, not histology-confirmed
cell-type mechanisms.

## Supplementary Tables

- `manuscript/SCI20_50_SUBMISSION_GATES.tsv`
- `manuscript/reviewer_objection_response_table.tsv`
- `manuscript/FINAL_SUBMISSION_BLOCKERS.tsv`
- `manuscript/nature_methods_package/05_claim_evidence_map.tsv`
- `manuscript/nature_methods_package/06_figure_plan.tsv`
- `manuscript/submission_metadata/SUBMISSION_SYSTEM_METADATA_CHECKLIST.tsv`
- `release/zenodo_upload_manifest.tsv`
- `release/archive_manifest.tsv`

## Reproducibility

Before submission, run:

```bash
python -m pytest
python scripts/release_audit.py
python scripts/check_final_submission_blockers.py
```

The final command must not report `NO_GO` at journal submission.
