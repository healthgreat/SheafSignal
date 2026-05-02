# Data release policy

This folder is for local data staging. Large or sensitive data are ignored by
Git on purpose.

## What can be committed

- Small synthetic demo data.
- Dataset manifests with accession numbers, URLs, licenses, and checksums.
- Scripts that download public datasets from their official repositories.
- Processed toy examples that contain no human-identifiable information.

## What should not be committed

- Private clinical data.
- Protected metadata with dates, IDs, hospital numbers, or rare identifying
  combinations.
- Raw sequencing files, BAM/CRAM/FASTQ, or large H5AD/RDS files.
- Data from repositories whose license does not allow redistribution.

## Recommended public release pattern

1. Put code on GitHub.
2. Put large immutable analysis data on Zenodo, Figshare, GEO, SRA, Synapse, or
   another field-appropriate repository.
3. Add dataset accession/DOI/checksum to `metadata/datasets.tsv`.
4. Keep `scripts/download_public_datasets.py` as the reproducible entry point.

⚠️ Human participant data must be released only when allowed by consent,
IRB/ethics approval, institutional rules, and the original data license.
