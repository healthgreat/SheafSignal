# Zenodo Deposition Upload Instructions

## Upload Target

- Upload archive: `release/archives/sheafsignal_zenodo_upload.zip`
- Archive size: `105.300 MB`
- Archive SHA256: `c27421a6b6d12c706ee6d8dc1e61cdc86503c09105711f045f6e244f1aecd163`
- Deposition metadata JSON: `release/zenodo_deposition_metadata.json`
- Frozen files represented in `release/zenodo_upload_manifest.tsv`: 45

## Steps

1. Create a new Zenodo deposition for a dataset.
2. Use the metadata from `release/zenodo_deposition_metadata.json`.
3. Upload `release/archives/sheafsignal_zenodo_upload.zip`.
4. Confirm the archive checksum equals `c27421a6b6d12c706ee6d8dc1e61cdc86503c09105711f045f6e244f1aecd163`.
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
