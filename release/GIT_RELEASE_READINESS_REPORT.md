# Git Release Readiness Report

- Decision: `GIT_RELEASE_LOCAL_FREEZE_PASS_PUBLIC_REMOTE_PENDING`
- G11 gate status: `yellow`
- Branch: `codex/sheafsignal-hardening-release`
- Has local commit: `True`
- Configured remotes: `0`
- Exact tag on HEAD: `none`
- Non-ignored file count: `537`
- Oversized file threshold: `20 MB`
- Oversized file count: `0`

## Largest Non-Ignored Files

- `benchmarks/results/round2_hardening/tenx_breast_visium/spatial/spatial_sheaf_edges.csv`: 7.739 MB
- `benchmarks/results/tenx_breast_visium/spatial/spatial_sheaf_edges.csv`: 7.739 MB
- `benchmarks/results/gse154778_pdac_scrna/reannotation/scanpy_cell_annotations.csv`: 4.198 MB
- `benchmarks/results/gse176078_brca_scrna/comparators/cellphonedb_run/cellphonedb_meta.tsv`: 3.506 MB
- `benchmarks/results/round2_hardening/tenx_breast_visium/spatial/spatial_frustration_hotspots.csv`: 1.174 MB
- `benchmarks/results/tenx_breast_visium/spatial/spatial_frustration_hotspots.csv`: 1.174 MB
- `benchmarks/results/round2_hardening/spatial_frustration_hotspots.csv`: 1.165 MB
- `benchmarks/results/spatial_frustration_hotspots.csv`: 1.165 MB
- `benchmarks/results/gse154778_pdac_scrna/comparators/cellphonedb_run/cellphonedb_meta.tsv`: 0.359 MB
- `benchmarks/results/gse103322_hnsc_scrna/comparators/cellphonedb_run/cellphonedb_meta.tsv`: 0.219 MB

## Dirty Worktree Preview

- clean

## Interpretation Boundary

A local freeze commit is a reproducibility milestone, not a public release. G11 cannot become green until the repository has a public GitHub remote, an immutable release tag, and the release URL is written into manuscript and release metadata. Zenodo DOI minting remains intentionally held until the scientific and public-release gates are frozen.
