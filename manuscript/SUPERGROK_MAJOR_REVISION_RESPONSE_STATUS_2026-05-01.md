# SheafSignal Major-Revision Response Status

Date: 2026-05-01

## Update: External CCC Comparators Completed

After the initial hardening pass, CellPhoneDB v5 and CellChat v2 were installed
and run for the three required public scRNA-seq datasets.

CellPhoneDB v5 was installed in the isolated D-drive conda environment
`sheafsignal-cellphonedb` and executed through the official Python API because
the pip package did not expose a CLI entrypoint.

CellPhoneDB completed full runs:

- `gse72056_melanoma_scrna`: CellPhoneDB v5, database `v5.0.0`,
  `iterations=1000`, `threshold=0.1`, `threads=4`, `debug_seed=42`,
  imported into `sheafsignal_vs_cellphonedb.csv`.
- `gse154778_pdac_scrna`: same settings, imported into
  `sheafsignal_vs_cellphonedb.csv`.
- `gse176078_brca_scrna`: same settings, imported into
  `sheafsignal_vs_cellphonedb.csv`.

CellChat completed full sidecar runs:

- `gse72056_melanoma_scrna`: CellChat `2.2.0.9001`, official GitHub
  `jinworks/CellChat`, imported into `sheafsignal_vs_cellchat.csv`.
- `gse154778_pdac_scrna`: same workflow, imported into
  `sheafsignal_vs_cellchat.csv`.
- `gse176078_brca_scrna`: same workflow, imported into
  `sheafsignal_vs_cellchat.csv`.

Current comparator boundary:

- CellPhoneDB is now completed and imported for the three required public
  scRNA-seq datasets.
- CellChat is now completed and imported for the three required public
  scRNA-seq datasets.
- The SuperGrok CellChat/CellPhoneDB structural blocker is cleared.
- CellPhoneDB smoke/subsample runs are explicitly marked
  `smoke_completed_pending_full` and are not counted as full comparator
  evidence.
- The broader comparator readiness matrix still lists `niche-DE` as pending
  because it is intentionally downgraded to related-method discussion rather
  than treated as a mandatory CCC comparator.

Validation after this update:

- Full test suite: 171 passed, 1 warning.
- Ruff: passed.
- Benchmark result contract: comparator coverage now includes
  `CellChat=3` and `CellPhoneDB=3`.

## Decision

The project remains `NO_GO` for final submission, but the reason has changed.
The major scientific hardening cycle removed several internal blockers
(claim language, GSE154778 reannotation readiness, sensitivity/FDR reporting,
novelty overlap table). Remaining blockers are now mostly external-release and
external-tool execution items.

## Completed In This Hardening Pass

1. Added GSE103322 HNSCC as an independent public TME replication dataset.
   - Raw GEO processed file downloaded.
   - SHA256 recorded in `metadata/datasets.tsv`.
   - Prepared `expression.csv`, `metadata.csv`, `profiles.csv` and
     `annotation_summary.csv`.
   - Entered `benchmarks/results/public_tme_sheafsignal_summary.csv` as
     `completed`.

2. Added comparator infrastructure for CellChat and CellPhoneDB.
   - CellPhoneDB input bundles generated for public scRNA-seq datasets.
   - CellPhoneDB v5 full runs are now completed and imported for GSE72056,
     GSE154778 and GSE176078.
   - CellChat v2 full sidecar runs are now completed and imported for
     GSE72056, GSE154778 and GSE176078.
   - The CellChat/CellPhoneDB SuperGrok hardening gate is no longer a blocker.

3. Added GSE154778 independent reannotation workflow.
   - Added `envs/reannotation_environment.yml`.
   - Installed/validated `scanpy`, `anndata`, `scrublet`, `leidenalg` and
     `igraph` in the D-drive Python environment.
   - Added executable workflow to build `.h5ad` from the GEO full-gene matrix.
   - Completed a real 500-cell full-gene Scanpy smoke run with QC,
     normalization, HVG, PCA, neighbors, Leiden resolution sweep, Scrublet and
     marker-based cluster labeling.

4. Added permutation/FDR hardening.
   - `run_tme_benchmark.py --n-permutations 100` now runs cell-level
     expression mode when available.
   - Generated `sheaf_energy_permutation_pvalues.csv`,
     `frustration_permutation_pvalues.csv` and
     `global_permutation_pvalues.csv` for completed benchmark datasets.
   - `build_sensitivity_panel.py` now reads the actual pipeline permutation
     output and reports no missing permutation/FDR rows.

5. Downgraded GSE154778 biological interpretation.
   - Earlier profile-level and lesion-stratified QC prioritized Myeloid.
   - The expression-mode permutation/FDR run shifted the leading computational
     source to CAF/Fibroblast.
   - Because CAF/Fibroblast remains lesion-support-limited and Myeloid is not
     stable across analysis mode, no GSE154778 cell type is currently promoted
     as a main biological source claim.
   - Manuscript-facing text now presents GSE154778 as a cautionary
     annotation/model-dependence example.

6. Updated hardening gates and tests.
   - Claim hardening report: 0 blocking risky claims.
   - Method reporting audit: 15 pass, 1 pending external.
   - Benchmark result contract audit: 9 pass.
   - Full test suite: 171 passed, 1 warning after external comparator
     hardening.
   - Ruff: passed.
   - Release audit: passed.

## Current Final Blockers

From `manuscript/NATURE_METHODS_GO_NO_GO_REPORT.md`:

1. Zenodo DOI has not been minted.
2. Data Availability and `metadata/datasets.tsv` still contain pending DOI
   placeholders.

GitHub public release and author metadata remain non-blocking submission-day
items in the local gate.

## Current Claim Boundary

The manuscript should not claim:

- Myeloid as a validated GSE154778 mechanism.
- CAF/Fibroblast as a validated GSE154778 mechanism.
- Any universal tumor cell-type source of communication frustration.
- Clinical utility, treatment guidance or therapeutic relevance.
- Broad superiority over CellChat, CellPhoneDB, LIANA, NicheNet or niche-DE.

Allowed current claim:

SheafSignal provides a reproducible sheaf/Hodge workflow for quantifying
edge-level communication inconsistency and component structure, with public
data demonstrating context-specific computational rankings and the importance
of explicit claim gates.

## Remaining Work For A 20-50 IF Route

1. Run full-scale GSE154778 Scanpy/Seurat-style reannotation, not only the
   500-cell smoke run.
2. Increase permutation runs from the current hardening smoke value (`100`) to
   the manuscript-freeze value selected in the statistical analysis plan.
3. Add LR-resource and pathway-resource sensitivity sweeps.
4. Freeze GitHub/Zenodo release only after the above outputs and manuscript
   text are stable.
