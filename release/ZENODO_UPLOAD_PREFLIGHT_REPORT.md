# Zenodo Upload Preflight Report

- Decision: `ZENODO_UPLOAD_PREFLIGHT_READY_NO_DOI_PLACEHOLDERS`
- Passed checks: `16`
- Pending checks: `0`
- Blocking checks: `0`

## Blocking Checks

- none

## Pending Checks

- none

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
