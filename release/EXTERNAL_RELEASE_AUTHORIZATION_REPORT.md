# External Release Authorization Report

- Decision: `EXTERNAL_RELEASE_AUTHORIZATION_READY`
- Passed checks: `8`
- Pending checks: `1`
- Blocking checks: `0`

## Blocking Checks

- none

## Interpretation Boundary

This report validates account and release-infrastructure readiness. It does not
print token contents, does not change GitHub or Zenodo state, and does not
guarantee journal acceptance.

## Next Command

```bash
python scripts/check_external_release_authorization.py
```
