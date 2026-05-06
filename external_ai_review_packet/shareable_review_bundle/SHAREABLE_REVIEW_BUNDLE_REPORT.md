# Shareable External Beta Review Bundle Report

- Decision: `SHAREABLE_REVIEW_BUNDLE_READY`
- Archive: `external_ai_review_packet/shareable_review_bundle/sheafsignal_external_beta_review_bundle.zip`
- Archive SHA256: `1e67dac000982b1854273d30f3cacba19eb47d995bc6e9874cc2188ba2c0789d`
- Included files: `51`
- Missing required files: `0`

## Missing Required Files

- none

## Reviewer Instructions

Send the archive to 2-3 external AI or human reviewers. Use the role-specific
prompts in `external_ai_review_packet/EXTERNAL_AI_REVIEW_ROUTING_2026-05-04.md`.
For code-level review, also send the source-code archive reported in
`external_ai_review_packet/source_code_review_bundle/SOURCE_CODE_REVIEW_BUNDLE_REPORT.md`
with `external_ai_review_packet/EXTERNAL_AI_CODE_REVIEW_PROMPT_2026-05-04.md`.
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
