# Methods Skeleton

## Input Data

- Cell-by-gene expression matrix or spatial spot-by-gene matrix.
- Cell type or spot-program metadata.
- Ligand-receptor database.
- Pathway or target-gene set.
- Optional spatial coordinates.

## Preprocessing

- Use dataset-specific adapters for public scRNA-seq and Visium data.
- Aggregate selected LR, marker and pathway genes to cell-type profiles for the
  main benchmark path.
- Keep raw and processed large files out of Git; release frozen processed
  objects through Zenodo.

## Sheaf Energy

- Compute ligand-receptor sender-receiver flow.
- Compute pathway-state difference between sender and receiver profiles.
- Standardize both terms and calculate edge-level mismatch energy.

## Hodge Decomposition

- Collapse anti-parallel directed flows to canonical net pairwise flow.
- Decompose net edge flow into gradient, curl and harmonic components.
- Report gradient_ratio, curl_ratio and harmonic_ratio.

## Frustration Scoring

- Compute sender-level outgoing share of total sheaf energy.
- Use claim gating to restrict biological interpretation to supported cell
  types.

## Statistical Testing

- Use empirical permutation and Benjamini-Hochberg FDR where specified.
- Use stratified or sample-aware designs when sample identity is available.

## Comparator Analyses

- Internal LRProductBaseline: ligand expression times receptor expression.
- LIANA: full imports for public scRNA-seq benchmarks.
- NicheNet/nichenetr-engine: official nichenetr scoring with a project-curated
  tumor-microenvironment prior matrix.
- MechanisticTargetPrior: transparent ligand-target prior baseline.

## Software And Reproducibility

- Python package with pytest tests.
- R-side nichenetr dependency installed separately.
- Release manifests, SHA256 checksums and archives generated before submission.
