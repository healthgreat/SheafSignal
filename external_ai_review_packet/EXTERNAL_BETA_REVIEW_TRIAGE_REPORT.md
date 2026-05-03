# External Beta Review Triage Report

- Decision: `EXTERNAL_BETA_REVIEW_NO_RETURNED_REVIEWS`
- Input directory: `external_ai_review_packet/returned_reviews`
- Returned review findings: `0`
- Fatal findings: `0`
- Major findings: `0`
- Minor findings: `0`

## Domain Counts

- none

## Top Parsed Findings

- none

## How To Use This

Place returned human or external-AI reviews in the input directory as `.md`, `.txt`, or `.tsv` files, then rerun:

```bash
python scripts/triage_external_beta_reviews.py
```

Fatal or major returned-review items should be transferred into the response matrix before a 20-50 IF submission decision.
Reviewer model metadata is written to `external_ai_review_packet/external_beta_review_reviewer_metadata.tsv` when returned reviews report it.

## Boundary

This triage is keyword-assisted and reviewer-facing. It does not replace human judgment, public GitHub release, Zenodo DOI, author confirmation, or final clean-clone reproduction.
