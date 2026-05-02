# External Release Authorization Report

- Decision: `EXTERNAL_RELEASE_AUTHORIZATION_BLOCKED`
- Passed checks: `4`
- Pending checks: `2`
- Blocking checks: `3`

## Blocking Checks

- `github_cli_auth`: `not_logged_in`. Action: Run gh auth login or authenticate gh with a valid token.
- `github_token_api`: `valid_missing_workflow_scope`. Action: Regenerate the GitHub token with repo and workflow scopes, then overwrite the local token file.
- `zenodo_doi_placeholders`: `pending`. Action: Mint DOI and run scripts/finalize_zenodo_doi.py.

## Interpretation Boundary

This report validates account and release-infrastructure readiness. It does not
print token contents, does not change GitHub or Zenodo state, and does not
guarantee journal acceptance.

## Next Command

```bash
python scripts/check_external_release_authorization.py
```
