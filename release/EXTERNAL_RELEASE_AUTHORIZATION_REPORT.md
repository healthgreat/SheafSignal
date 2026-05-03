# External Release Authorization Report

- Decision: `EXTERNAL_RELEASE_AUTHORIZATION_PARTIAL_METADATA_BLOCKED`
- Passed checks: `7`
- Pending checks: `1`
- Blocking checks: `1`

## Blocking Checks

- `zenodo_doi_placeholders`: `pending`. Action: Mint DOI and run scripts/finalize_zenodo_doi.py.

## Interpretation Boundary

This report validates account and release-infrastructure readiness. It does not
print token contents, does not change GitHub or Zenodo state, and does not
guarantee journal acceptance.

## Next Command

```bash
python scripts/check_external_release_authorization.py
```
