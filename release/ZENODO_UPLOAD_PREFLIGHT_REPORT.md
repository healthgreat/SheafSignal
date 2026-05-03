# Zenodo Upload Preflight Report

- Decision: `ZENODO_UPLOAD_PREFLIGHT_READY_FOR_API_UPLOAD_DOI_PENDING`
- Passed checks: `15`
- Pending checks: `1`
- Blocking checks: `0`

## Blocking Checks

- none

## Pending Checks

- `zenodo_doi_placeholders_expected`: release/DATA_AVAILABILITY_STATEMENT_DRAFT.md;metadata/datasets.tsv. Action: Mint DOI and run scripts/finalize_zenodo_doi.py after upload.

## Next Commands

```bash
python scripts/upload_zenodo_deposition.py --dry-run
python scripts/finalize_zenodo_doi.py --doi <ZENODO_DOI>
python scripts/check_final_submission_blockers.py --report-only
```

## Boundary

This report checks Zenodo upload readiness. It does not upload files,
does not mint a DOI, does not print token contents, and does not
guarantee journal acceptance.
