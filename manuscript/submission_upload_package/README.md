# SheafSignal Submission Upload Package

This folder contains local DOCX upload artifacts generated from auditable
Markdown/TSV sources. The DOCX files are convenience upload products; the
authoritative sources remain the Markdown manuscript, claim tracker, benchmark
tables and release manifests.

## Files

- `SheafSignal_main_manuscript_v2.docx`
- `SheafSignal_cover_letter_NatureMethods.docx`
- `SheafSignal_supplementary_information.docx`
- `submission_upload_manifest.tsv`
- `submission_upload_preflight_checklist.tsv`
- `main_figure_upload_manifest.tsv`
- `DOCX_TEXT_EXTRACTION_CHECK.md`
- `DOCX_LAYOUT_CHECK.tsv`
- `manuscript/figure_quality/MAIN_FIGURE_QUALITY_AUDIT.tsv` remains the
  source quality gate for the copied main-figure PDFs.
- `manuscript/supplementary_quality/SUPPLEMENTARY_ARTIFACT_AUDIT.tsv` remains
  the readability gate for supplementary figures, tables, and support files.
- `benchmarks/results/BENCHMARK_RESULT_CONTRACT_AUDIT.tsv` remains the
  result-table contract gate for benchmark summaries and comparator links.
- `manuscript/provenance/SUBMISSION_PROVENANCE_AUDIT.tsv` remains the
  provenance gate for submission-facing artifacts.
- `manuscript/method_reporting/METHOD_REPORTING_AUDIT.tsv` remains the
  method-reporting gate for reviewer-facing manuscript claims.

## Current Boundary

This package does not make the manuscript submission-ready by itself. Zenodo
DOI, public GitHub URL, author metadata, affiliations, CRediT roles, competing
interests and final journal-system checks remain required.

## Preflight Snapshot

- Rows requiring attention: 2
- Final go/no-go source: `manuscript/NATURE_METHODS_GO_NO_GO_REPORT.md`
