# Shareable External Beta Review Bundle Report

- Decision: `SHAREABLE_REVIEW_BUNDLE_READY`
- Archive: `external_ai_review_packet/shareable_review_bundle/sheafsignal_external_beta_review_bundle.zip`
- Archive SHA256: `7c771fea7511770ec4261cfb8fd0d45784b8489e8fbbad82c9dcae6712d7ba37`
- Included files: `30`
- Missing required files: `0`

## Missing Required Files

- none

## Reviewer Instructions

Send the archive to an external AI or human reviewer together with the request:
`Please judge novelty, reproducibility, statistics, claim boundaries, and journal fit.`
Returned `.md`, `.txt`, or `.tsv` reviews should be placed under
`external_ai_review_packet/returned_reviews/` and triaged with:

```bash
python scripts/triage_external_beta_reviews.py
```

## Boundary

This bundle is a review handoff. It does not contain raw data, processed omics objects,
release archives, access tokens, or any guarantee of journal acceptance.
