# SheafSignal SCI Manuscript V2 Claim Tracker

This tracker maps the polished manuscript's main claims to the current
evidence package and states the boundary that must be preserved during
journal revision.

| Claim ID | Claim | Evidence source | Allowed scope | Forbidden extension |
|---|---|---|---|---|
| `C1_method_object` | SheafSignal models communication as a sheaf-valued graph flow. | `src/sheafsignal and Methods text` | methodological formulation | do not claim clinical utility or therapeutic guidance |
| `C2_hodge_components` | Gradient, curl and harmonic components are recovered in controlled simulations. | `benchmarks/results/component_recovery.csv` | implementation validation | do not use simulations as disease biology evidence |
| `C3_public_context_specificity` | Public TME benchmarks show dataset-dependent computational sheaf-energy rankings. | `benchmarks/results/public_tme_sheafsignal_summary.csv` | public-data methods benchmark | do not claim a universal dominant source cell type or validated tumor mechanism |
| `C4_gse154778_mode_dependence` | GSE154778 cell-type source rankings are annotation- and analysis-mode-dependent under the current hardening run. | `benchmarks/results/gse154778_pdac_scrna/results/frustration_permutation_pvalues.csv`; `benchmarks/results/gse154778_pdac_scrna/reannotation/scanpy_reannotation_run_summary.csv` | cautionary computational sensitivity finding | do not present Myeloid or CAF/Fibroblast as a validated pancreatic-cancer mechanism or clinical biomarker |
| `C5_sparse_categories` | Sparse cell types are downgraded to supplement/QC interpretation. | `benchmarks/results/gse154778_pdac_scrna/qc/claim_gating_by_cell_type.csv` | evidence limitation and QC warning | do not force sparse categories into main mechanistic claims |
| `C6_comparators` | Comparator results support alignment and complementarity. | `benchmarks/results/tool_comparison.csv` | alignment, non-equivalence and bounded comparison | do not claim broad superiority over all CCC tools |
| `C7_spatial` | Spatial analysis demonstrates hotspot localization under spot-level boundaries. | `benchmarks/results/tenx_breast_visium/spatial and QC tables` | workflow demonstration | do not claim histology-confirmed single-cell mechanism |

## Author-Owned Pending Items

- Author names, affiliations, CRediT roles, competing interests and final
  ethics/data-use wording remain TBD.
- Zenodo DOI and public GitHub URL must be inserted before submission.
- The manuscript still requires journal-system formatting and final figure
  assembly after DOI and author metadata are frozen.
