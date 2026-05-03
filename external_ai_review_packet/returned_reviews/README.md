# Returned External Reviews

Place returned external AI or human review files in this directory.

Recommended filenames:

- `reviewer1_methods_novelty.md`
- `reviewer2_singlecell_spatial_claims.md`
- `reviewer3_statistics_reproducibility.md`
- `reviewer4_code_review.md`

Ask each reviewer to report:

- `reviewer_model_name`
- `reviewer_model_version`
- `review_timestamp_with_timezone`
- `claimed_training_data_cutoff`
- `external_references_consulted`

After adding review files, run:

```bash
python scripts/triage_external_beta_reviews.py
python scripts/build_live_gantt_status.py
python scripts/build_if20_50_gap_report.py
```

Do not place access tokens, private credentials, raw patient data, or non-public
clinical material in this directory.
