# GitHub Release Publication Report

- Decision: `GITHUB_RELEASE_BLOCKED`
- Blocking reason: GitHub token is valid but missing required scope(s): workflow

## Required Action

Regenerate the GitHub token with both `repo` and `workflow` scopes,
then rerun this script after committing local changes.

## Boundary

This report documents why GitHub publication did not run. It does not
print token contents, does not mint a Zenodo DOI, and does not guarantee
journal acceptance.
