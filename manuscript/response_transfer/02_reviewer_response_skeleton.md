# Reviewer Response Skeleton

## Cover Response

We thank the reviewers for their detailed assessment. We have revised the
manuscript to clarify the mathematical contribution of SheafSignal, strengthen
benchmark transparency, and sharpen the boundaries of biological interpretation.

## Response Table Template

| Comment ID | Reviewer Comment | Response Strategy | Manuscript Change | Evidence File | Status |
|---|---|---|---|---|---|
| R1.1 | TBD | Clarify sheaf-valued flow versus pairwise LR scoring. | Abstract, Figure 1, Methods. | `manuscript/nature_methods_package/05_claim_evidence_map.tsv` | pending |
| R1.2 | TBD | Add or cite benchmark/sensitivity evidence. | Results or Supplement. | `benchmarks/results/` | pending |
| R2.1 | TBD | Downgrade unsupported biology claims. | Results, Discussion, Limitations. | `benchmarks/results/gse154778_pdac_scrna/qc/claim_gating_by_cell_type.csv` | pending |
| R2.2 | TBD | Clarify comparator boundary. | Methods, Supplementary Methods. | `benchmarks/results/tool_comparison.csv` | pending |

## Response Rules

- Every response must name the exact file or figure that changed.
- Null or weak results should be disclosed, not hidden.
- Sparse cell types remain supplementary/QC unless they pass the pre-specified
  evidence-tier filter.
- If a reviewer asks for clinical interpretation, answer that the current study
  is computational and hypothesis-generating.
