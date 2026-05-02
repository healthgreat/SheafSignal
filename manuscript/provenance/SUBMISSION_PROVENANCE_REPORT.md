# Submission Provenance Audit

Decision: `SUBMISSION_PROVENANCE_PASS_WITH_EXTERNAL_AND_AUTHOR_PENDING`

- Provenance rows: 28
- Failures: 0
- External or author-pending rows: 3

## Rows Requiring Attention

- `submission_metadata_templates` `pending_author_action`: template exists but author metadata must be completed Artifact: `manuscript/submission_metadata/AUTHOR_METADATA_TEMPLATE.tsv`
- `github_public_release` `pending_external`: external publication/deposition still required Artifact: `release/archives/sheafsignal_github_release.zip`
- `zenodo_doi` `pending_external`: external publication/deposition still required Artifact: `metadata/datasets.tsv`

## Boundary

This audit checks local provenance and explicit external/author pending
status. It does not mint a DOI, publish GitHub, or complete author
metadata on behalf of the authors.
