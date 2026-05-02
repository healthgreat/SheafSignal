# GitHub Public Release Instructions

## Upload Target

- Source/code archive: `release/archives/sheafsignal_github_release.zip`
- Archive checksum: see `release/archive_manifest.tsv`
- Large processed benchmark objects: upload to Zenodo, not GitHub

## Steps

1. Create or select the public GitHub repository for SheafSignal.
2. Upload the repository source files or unpack
   `release/archives/sheafsignal_github_release.zip`.
3. Confirm `.gitignore` excludes raw data, processed large matrices, and local
   archives.
4. Create a versioned release tag such as `v0.1.0`.
5. Link the Zenodo DOI in README, `metadata/datasets.tsv`, and the manuscript
   data availability statement.
6. Re-run:

```bash
python scripts/release_audit.py
python scripts/check_final_submission_blockers.py
```

## Boundary

Do not publish private clinical data, controlled-access raw reads, local
credentials, or generated archives that are intentionally ignored by Git.
