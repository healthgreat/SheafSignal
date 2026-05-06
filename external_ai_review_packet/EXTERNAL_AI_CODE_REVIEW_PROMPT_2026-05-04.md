# SheafSignal External AI Code Review Prompt

Generated: 2026-05-04 08:00:00 +08:00

## What To Send

Send the source-code review archive:

`external_ai_review_packet/source_code_review_bundle/sheafsignal_source_code_review_bundle.zip`

Use this prompt with an external AI reviewer that can inspect source code.

## Copy-Paste Prompt

```text
You are acting as an external code reviewer for the SheafSignal project, a
Python methods package for sheaf/Hodge-based cell-cell communication analysis.

Review the attached source-code bundle. Do not focus on manuscript polish.
Focus on code-level correctness, reproducibility, package hygiene, tests,
failure modes, security/privacy risks, file-path robustness, and whether the
implementation matches the stated scientific claims.

Use only the files in the source bundle, plus public GitHub/Zenodo links if
provided by the authors. Clearly separate:
- direct evidence from code,
- reasonable inference,
- speculation.

Before the review findings, report:
- reviewer_model_name:
- reviewer_model_version:
- review_timestamp_with_timezone:
- claimed_training_data_cutoff:
- external_references_consulted:

Return your review in this exact structure:

1. Editorial code-readiness decision:
   ready / minor issues / major revision / not ready

2. Top 5 fatal or near-fatal code concerns:
   Focus on bugs that could invalidate results, break clean-clone
   reproducibility, leak private files, mishandle paths, silently reuse stale
   outputs, or make tests misleading.

3. Algorithm implementation review:
   Check formal sheaf API, Hodge targets, residual construction, permutation
   logic, FDR logic, provenance hashing, and source/test consistency. In
   particular, decide whether the Round 3 higher-rank LR-channel sheaf code
   (LR-channel vertex stalks, expression-scaled restriction maps, node-channel
   Laplacian, and task-based comparator evaluation) removes the prior
   rank-one/trivial-sheaf and circular-benchmark fatal objections.

4. Reproducibility review:
   Check environment locking, CLI entry points, test coverage, deterministic
   seeds, clean-clone assumptions, generated-output handling, and relative
   paths.

5. Security and privacy review:
   Check whether code could include raw data, processed omics objects, patient
   privacy material, access tokens, absolute local secrets, or unsafe network
   behavior in review/release bundles.

6. Required fixes before any 20-50 IF submission:
   Separate P0 blockers, P1 major fixes, and P2 optional improvements.

7. Claims that code does not support:
   Identify any manuscript or README-level claims that the code cannot
   support.

8. Suggested tests:
   Name exact tests that should be added or strengthened.

9. Short final verdict:
   State whether this codebase is defensible for external methods-review,
   and what remains most likely to trigger reviewer criticism.
```

## Returned Review Filename

Save the returned review as:

`external_ai_review_packet/returned_reviews/reviewer4_code_review.md`

Then run:

```bash
python scripts/triage_external_beta_reviews.py
```

## Boundary

External AI code review is a risk-reduction step. It is not formal software
verification, security certification, or peer review.
