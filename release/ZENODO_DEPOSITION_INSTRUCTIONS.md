# Zenodo Deposition Upload Instructions

## Upload Target

- Upload archive: `release/archives/sheafsignal_zenodo_upload.zip`
- Archive size: `27.157 MB`
- Archive SHA256: `e2ad6b3d705788329a420cfc234326b233ea8547a228751ab35c0f934f3c4ede`
- Deposition metadata JSON: `release/zenodo_deposition_metadata.json`
- Frozen files represented in `release/zenodo_upload_manifest.tsv`: 40

## Steps

1. Create a new Zenodo deposition for a dataset.
2. Use the metadata from `release/zenodo_deposition_metadata.json`.
3. Upload `release/archives/sheafsignal_zenodo_upload.zip`.
4. Confirm the archive checksum equals `e2ad6b3d705788329a420cfc234326b233ea8547a228751ab35c0f934f3c4ede`.
5. Publish the Zenodo record and copy the DOI.
6. Run:

```bash
python scripts/finalize_zenodo_doi.py --doi <ZENODO_DOI>
python scripts/check_final_submission_blockers.py
```

## Boundary

Do not submit the manuscript while `NATURE_METHODS_GO_NO_GO_REPORT.md` says
`NO_GO`. This instruction file does not mint a DOI and does not guarantee
journal acceptance.
