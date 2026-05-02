# Nature Methods Final Submission Go/No-Go Report

Decision: `NO_GO`

- Blocking items: 3
- Pending non-blocking items: 9
- Passed checks: 113

## Blocking Items

- `checklist::Zenodo DOI minted`: blocking_pending. Action: Upload release/archives/sheafsignal_zenodo_upload.zip and record DOI.
- `zenodo_doi::data_availability_statement`: pending. Action: Insert the minted DOI into the data availability statement.
- `zenodo_doi::dataset_manifest`: pending. Action: Mint Zenodo DOI and replace PENDING_ZENODO_RELEASE in metadata/datasets.tsv.

## Pending Items

- `author_metadata::affiliations`: tbd_by_authors. Action: Fill all affiliations.
- `author_metadata::authors`: tbd_by_authors. Action: Fill all author names, emails, ORCIDs when available, corresponding author status, and conflict statements.
- `author_metadata::competing_interests`: tbd_by_authors. Action: Replace TBD with final competing interests statement.
- `author_metadata::credit_roles`: tbd_by_authors. Action: Assign authors to CRediT roles.
- `author_metadata::ethics_data_use`: tbd_by_authors. Action: Confirm final ethics/data-use wording with authors or institution.
- `author_metadata::submission_system_checklist`: tbd_by_authors. Action: Complete submission-system metadata checklist.
- `checklist::Conflict of interest and author contributions`: tbd_by_authors. Action: Authors must fill journal submission metadata.
- `checklist::GitHub repository public release`: pending. Action: Use release/archives/sheafsignal_github_release.zip or tracked repository contents.
- `checklist::Nature Methods formatting checked`: pending_submission_day_check. Action: Check current official author instructions before upload.

## Interpretation Boundary

This report checks local readiness. It does not guarantee journal acceptance.
A final submission still requires author metadata, journal-format checking,
and the Zenodo DOI if listed as blocking.
