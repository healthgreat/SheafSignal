# Round 3 Returned AI Review Triage

- Timestamp: 2026-05-02 22:05:00
- Review source: internal multi-agent AI review returned in the Codex workspace
- Decision: `RETURNED_REVIEWS_TRIAGED_SCIENCE_HARDENED_RELEASE_BLOCKED`

## Summary

Five AI reviewer responses were returned across methods novelty, single-cell
evidence, statistics, high-impact framing and reproducibility. Several fatal
comments were based on stale snapshots and are no longer true in the current
tracked repository. They are still useful because they identify the exact
failure modes that journal reviewers will look for.

## Current Open Blockers

- Public GitHub remote, immutable tag and release URL remain missing.
- Zenodo DOI remains intentionally unminted until author metadata and public
  release metadata are finalized.
- Author-owned metadata remain incomplete: author names, affiliations, ORCIDs
  when available, CRediT roles, competing interests and ethics/data-use text.
- Final clean-clone reproduction must be rerun from the public GitHub release
  after DOI and URL insertion.
- Human or truly independent external reviewer responses are still not filed;
  the current returned critiques are internal AI-agent reviews.

## Stale Or Resolved Findings

- Formal sheaf implementation, restriction outputs, sheaf residual and sheaf
  Laplacian outputs are now implemented.
- Primary Hodge decomposition is now applied to `sheaf_residual`, with
  communication-flow Hodge retained only as a secondary diagnostic.
- GSE154778 now uses frozen `scanpy_full_v1` prepared inputs, not the old
  coarse-only route.
- GSE154778 now has a pre-specified 10,000-permutation confirmatory subset.
- GSE154778 QC, lesion-stratified analysis, bootstrap stability, sample-level
  stability and claim gating have been regenerated against frozen
  `scanpy_full_v1` inputs.
- CellChat and CellPhoneDB are complete for the three primary public scRNA-seq
  comparator benchmarks; demo, Visium, GSE103322 and niche-DE remain outside
  primary comparator-completeness claims.

## Boundary Decisions

- The pooled 10,000-permutation GSE154778 summary ranks CAF/Fibroblast highest
  by raw node frustration score, but CAF/Fibroblast remains `qc_warning_only`
  because metastatic lesion support is sparse.
- Myeloid remains `supplement_only` / `supplement_context`: it is a
  lesion-stratified computational hypothesis, not a validated biological
  source or mechanism.
- Real-data curl/harmonic components remain graph-decomposition diagnostics,
  not validated biological feedback loops.

## Next Required Action

The shortest route to a credible 20-50 IF submission candidate is now an
external-release cycle: public GitHub, author metadata, Zenodo DOI, DOI/URL
insertion, then public clean-clone reproduction.
