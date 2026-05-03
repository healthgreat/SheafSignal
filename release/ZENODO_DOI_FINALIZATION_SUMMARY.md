# Zenodo DOI Finalization Summary

DOI: https://doi.org/10.5281/zenodo.20012189

Updated public benchmark rows: gse72056_melanoma_scrna;gse154778_pdac_scrna;gse176078_brca_scrna;gse103322_hnsc_scrna;tenx_breast_visium

Next required commands:

```bash
python scripts/check_final_submission_blockers.py
python scripts/build_submission_readiness_report.py
python scripts/build_reproducibility_release.py
python scripts/package_release_archives.py
python -m pytest
python scripts/release_audit.py
```

Boundary: DOI finalization removes the Zenodo blocker only. It does not
guarantee journal acceptance and does not replace author metadata or final
journal-format checks.
