# Zenodo Upload Preflight Report

- Decision: `ZENODO_UPLOAD_PREFLIGHT_READY_FOR_MANUAL_UPLOAD_DOI_PENDING`
- Passed checks: `14`
- Pending checks: `2`
- Blocking checks: `0`

## Blocking Checks

- none

## Pending Checks

- `zenodo_doi_placeholders_expected`: release/DATA_AVAILABILITY_STATEMENT_DRAFT.md;metadata/datasets.tsv. Action: Mint DOI and run scripts/finalize_zenodo_doi.py after upload.
- `zenodo_token_file`: D:\secrets\zenodo_token.txt does not exist.. Action: Use manual Zenodo web upload or save a token at this path for API upload.

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
