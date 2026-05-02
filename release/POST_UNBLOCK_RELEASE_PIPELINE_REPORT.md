# Post-Unblock Release Pipeline Report

- Decision: `POST_UNBLOCK_PIPELINE_BLOCKED_GITHUB_TOKEN`
- Execute mode: `False`

## Gate Snapshot

- `active_release_blockers`: `7`
- `github_token_api`: `valid_missing_workflow_scope`
- `github_cli_auth`: `not_logged_in`
- `zenodo_token_file`: `pending`
- `zenodo_archive_sha256`: `pass`
- `author_blocking`: `2`
- `author_pending`: `8`

## Pipeline Plan

| Step | Phase | Run by default | Command |
|---|---|---|---|
| `preflight_external_auth` | `preflight` | `yes` | `python scripts/check_external_release_authorization.py` |
| `preflight_author_confirmation` | `preflight` | `yes` | `python scripts/check_author_confirmation_preflight.py` |
| `preflight_zenodo_upload` | `preflight` | `yes` | `python scripts/check_zenodo_upload_preflight.py` |
| `publish_github_release` | `external_release` | `yes` | `python scripts/publish_github_release_after_auth.py --create-release` |
| `finalize_zenodo_doi` | `metadata` | `yes_if_doi_provided` | `python scripts/finalize_zenodo_doi.py --doi <REAL_ZENODO_DOI>` |
| `rebuild_release_files` | `metadata` | `yes` | `python scripts/build_reproducibility_release.py && python scripts/package_release_archives.py` |
| `final_blocker_report` | `audit` | `yes` | `python scripts/check_release_metadata_placeholders.py && python scripts/check_final_submission_blockers.py --report-only` |
| `clean_export_preflight` | `audit` | `yes` | `python scripts/run_clean_clone_preflight.py` |
| `full_test_and_release_audit` | `audit` | `yes` | `python -m pytest -q && python scripts/release_audit.py` |
| `refresh_distance_report` | `reporting` | `yes` | `python scripts/build_if20_50_gap_report.py && python scripts/build_submission_unblocker_handoff.py` |

## Execution Results

- none

## Boundary

This pipeline only handles release mechanics and reproducibility audits. It does not infer author-owned facts, does not print secrets, and does not guarantee acceptance by any journal.
