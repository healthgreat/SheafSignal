# Shareable External Beta Review Bundle Report

- Decision: `SHAREABLE_REVIEW_BUNDLE_READY`
- Archive: `external_ai_review_packet/shareable_review_bundle/sheafsignal_external_beta_review_bundle.zip`
- Archive SHA256: `169d6f5d70d2e34f79e563608d43e1ba89a6fd27d0e5509580dca48042e28982`
- Included files: `31`
- Missing required files: `0`

## Missing Required Files

- none

## Reviewer Instructions

Send the archive to 2-3 external AI or human reviewers. Use the role-specific
prompts in `external_ai_review_packet/EXTERNAL_AI_REVIEW_ROUTING_2026-05-04.md`.
If using a single generic request, send the archive together with:
`Please judge novelty, reproducibility, statistics, claim boundaries, and journal fit.`
Returned `.md`, `.txt`, or `.tsv` reviews should be placed under
`external_ai_review_packet/returned_reviews/` and triaged with:

```bash
python scripts/triage_external_beta_reviews.py
```

## Boundary

This bundle is a review handoff. It does not contain raw data, processed omics objects,
release archives, access tokens, or any guarantee of journal acceptance.
