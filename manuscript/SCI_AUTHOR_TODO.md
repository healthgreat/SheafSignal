# SCI Manuscript V1 Author Todo

## Blocking Before Submission

1. Fill author list, affiliations, ORCID identifiers and corresponding author
   information.
2. Fill CRediT author contributions.
3. Confirm competing interests.
4. Confirm institutional wording for ethics and public-data use.
5. Create the public GitHub release.
6. Upload the Zenodo archive and insert the DOI into `metadata/datasets.tsv`,
   Data Availability and release files.
7. Freeze final figures and update figure panel labels.
8. Run:

```bash
python scripts/check_claim_safety.py --report-only
python scripts/check_final_submission_blockers.py --report-only
python -m pytest
python scripts/release_audit.py
```

## Writing Tasks

1. Replace `[REF: ...]` placeholders with verified references.
2. Convert Markdown to journal-formatted DOCX or submission-system text.
3. Review whether Figure 1 needs a professionally drawn conceptual panel.
4. Review all figure legends against `manuscript/figure_legends/03_figure_source_map.tsv`.
5. Keep all clinical and therapeutic wording inside boundary statements only.
