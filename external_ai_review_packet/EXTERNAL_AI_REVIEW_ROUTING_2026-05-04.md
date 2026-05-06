# SheafSignal External AI Review Routing

Generated: 2026-05-04 08:05:00 +08:00

Round 3 update: 2026-05-06. The package now includes a higher-rank
LR-channel-specific sheaf implementation and a task-based comparator evaluation.
Ask reviewers to judge whether these changes remove the prior fatal objections
about rank-one/trivial sheaf framing and circular simulation.

## Purpose

Use this document when asking 2-3 independent external AI reviewers to critique
the SheafSignal manuscript package before journal submission.

The goal is not polishing. The goal is to expose rejection risks before a
20-50 IF submission attempt.

## What To Send

Send this archive to each external AI reviewer:

`external_ai_review_packet/shareable_review_bundle/sheafsignal_external_beta_review_bundle.zip`

For source-code review, also send:

`external_ai_review_packet/source_code_review_bundle/sheafsignal_source_code_review_bundle.zip`

and use:

`external_ai_review_packet/EXTERNAL_AI_CODE_REVIEW_PROMPT_2026-05-04.md`

Current bundle status:

- Decision: `SHAREABLE_REVIEW_BUNDLE_READY`
- Included files: `51`
- Missing required files: `0`
- SHA256: see `external_ai_review_packet/shareable_review_bundle/SHAREABLE_REVIEW_BUNDLE_REPORT.md`

Current source-code bundle status:

- Decision: see `external_ai_review_packet/source_code_review_bundle/SOURCE_CODE_REVIEW_BUNDLE_REPORT.md`
- Included files: `198`
- SHA256: `48e604772a814c14d98af0d28aa1a2f44842e69fa145453927d86bdba7a54b65`

Public references reviewers may use:

- GitHub: https://github.com/healthgreat/SheafSignal
- GitHub release: https://github.com/healthgreat/SheafSignal/releases/tag/v0.1.0
- Zenodo DOI: https://doi.org/10.5281/zenodo.20012189

## Reviewer 1: Methods And Novelty

Copy-paste prompt:

```text
You are Reviewer 1: a computational methods reviewer for a 20-50 IF biology
methods journal.

Review the attached SheafSignal beta-review bundle. Be strict. Focus on method
novelty, mathematical framing, algorithmic correctness, graph/sheaf/Hodge
overlap with prior work, and whether this is more than a graph-signal-processing
rebranding.

Use only evidence in the provided bundle plus the public GitHub/Zenodo links if
available. Separate direct evidence, reasonable inference, and speculation.

Return your review with these sections:
0. Reviewer metadata: model name/version, review timestamp/timezone, claimed
   training-data cutoff, and external references consulted.
1. Editorial decision: ready / major revision / reject / not ready.
2. Top 5 fatal or near-fatal methods concerns.
3. Does the rank-one cellular sheaf framing justify the manuscript's claims?
4. Does the Round 3 higher-rank LR-channel sheaf implementation remove the
   prior trivial-sheaf objection?
5. Does the task-based comparator evaluation reduce the circular benchmark
   objection, and is the product-baseline tie acceptable with downgraded claims?
6. Is the Hodge decomposition on sheaf_residual technically defensible?
7. What exact novelty claims must be downgraded?
8. What additional method experiments would most improve a 20-50 IF submission?
9. Best-fit journals and why.
```

## Reviewer 2: Single-Cell, Spatial, And Biological Claims

Copy-paste prompt:

```text
You are Reviewer 2: a single-cell and spatial transcriptomics reviewer for a
20-50 IF biomedical journal.

Review the attached SheafSignal beta-review bundle. Be strict. Focus on
annotation validity, sample-level robustness, GSE154778 Myeloid claim gating,
GSE72056/GSE176078/GSE103322 replication boundaries, Visium hotspot-only scope,
and whether the manuscript overinterprets computational signals as biology.

Use only evidence in the provided bundle plus the public GitHub/Zenodo links if
available. Separate direct evidence, reasonable inference, and speculation.

Return your review with these sections:
0. Reviewer metadata: model name/version, review timestamp/timezone, claimed
   training-data cutoff, and external references consulted.
1. Editorial decision: ready / major revision / reject / not ready.
2. Top 5 fatal or near-fatal biological or single-cell concerns.
3. Is the GSE154778 Myeloid claim appropriately bounded?
4. Are sparse cell types, Visium spot labels, and mechanism language handled safely?
5. What exact biological claims must be downgraded or removed?
6. What validation or sensitivity analyses would most improve a 20-50 IF submission?
7. Best-fit journals and why.
```

## Reviewer 3: Statistics, Reproducibility, And Journal Fit

Copy-paste prompt:

```text
You are Reviewer 3: a statistical and reproducibility reviewer for a 20-50 IF
methods journal.

Review the attached SheafSignal beta-review bundle. Be strict. Focus on
sample-stratified permutations, bootstrap confidence intervals, pooled FDR,
sensitivity analysis, comparator fairness, clean-clone reproducibility,
environment locking, GitHub/Zenodo release readiness, and journal fit.

Use only evidence in the provided bundle plus the public GitHub/Zenodo links if
available. Separate direct evidence, reasonable inference, and speculation.

Return your review with these sections:
0. Reviewer metadata: model name/version, review timestamp/timezone, claimed
   training-data cutoff, and external references consulted.
1. Editorial decision: ready / major revision / reject / not ready.
2. Top 5 fatal or near-fatal statistics/reproducibility concerns.
3. Are permutation/FDR/bootstrap analyses enough for the claims being made?
4. Is comparator coverage adequate for the stated manuscript scope?
5. Does the Round 3 task-based comparator evaluation satisfy the request for
   benchmarking beyond descriptive alignment?
6. Can the public GitHub/Zenodo release support reproducibility review?
7. What exact statistical or reproducibility claims must be downgraded?
8. Best-fit journals and why.
```

## How To Save Returned Reviews

Save returned reviews here:

`external_ai_review_packet/returned_reviews/`

Recommended filenames:

- `reviewer1_methods_novelty.md`
- `reviewer2_singlecell_spatial_claims.md`
- `reviewer3_statistics_reproducibility.md`
- `reviewer4_code_review.md` if a separate code reviewer is used.

After all reviews are saved, run:

```bash
python scripts/triage_external_beta_reviews.py
python scripts/build_live_gantt_status.py
python scripts/build_if20_50_gap_report.py
```

## Decision Rule

- If any reviewer returns `reject` or `not ready`, triage the points before
  submission unless the finding is demonstrably stale or outside manuscript
  scope.
- If two or more reviewers return `major revision`, pause journal submission and
  update the action matrix.
- If reviewers mainly identify wording or presentation issues, proceed to final
  journal-format and submission-day metric checks.

## Boundary

External AI review is risk reduction, not proof of acceptability. A positive AI
review does not guarantee acceptance by Nature Methods, Nature Biotechnology,
or any 20-50 IF journal.
