# Source Code Review Bundle Report

- Decision: `SOURCE_CODE_REVIEW_BUNDLE_READY`
- Archive: `external_ai_review_packet/source_code_review_bundle/sheafsignal_source_code_review_bundle.zip`
- Archive SHA256: `3f08b5614378167b91c6a853dc640399aaef20e99f6f81beeb1609e24c67f905`
- Included files: `193`
- Source files under `src/`: `15`
- Script files under `scripts/`: `82`
- Test files under `tests/`: `80`

## What To Send

Send this source-code archive together with:
`external_ai_review_packet/EXTERNAL_AI_CODE_REVIEW_PROMPT_2026-05-04.md`

## What To Ask Reviewers To Report

- Model name and version used for the review.
- Review timestamp and timezone.
- Claimed training-data cutoff, if the model reports one.
- External references consulted, if any.
- Fatal / major / minor code-level concerns.

## Exclusions

The archive excludes raw data, processed omics objects, generated figures,
release archives, credentials, virtual environments, caches, and large matrices.

## Boundary

This bundle supports code review only. It does not guarantee correctness,
security, reproducibility, or journal acceptance.
