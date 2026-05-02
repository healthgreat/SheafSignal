# Reviewer Risk Register

- Risks tracked: 11
- Open or boundary-note risks: 0

## RR1_algorithm_rebranding

- Status: `mitigated`
- Reviewer risk: Reviewer may argue that SheafSignal is only a ligand-receptor intensity score.
- Mitigation evidence: all required SheafSignal primitives found
- Residual boundary: Do not claim broad superiority; claim a distinct sheaf/Hodge object and measured consistency signals.

## RR2_simulation_ground_truth

- Status: `mitigated`
- Reviewer risk: Reviewer may ask whether gradient, curl, and harmonic components are identifiable.
- Mitigation evidence: component_recovery.csv covers gradient/curl/harmonic/mixed
- Residual boundary: Simulation supports component recovery, not biological truth.

## RR3_public_data_reproducibility

- Status: `external_pending`
- Reviewer risk: Reviewer may ask whether all public data and processed objects are traceable.
- Mitigation evidence: public_benchmark_rows=5
- Residual boundary: Zenodo DOI remains an external submission step until minted.

## RR4_comparator_scope

- Status: `mitigated`
- Reviewer risk: Reviewer may request external CCC comparator evidence beyond internal LR baseline.
- Mitigation evidence: LIANA=3;LRProductBaseline=5;MechanisticTargetPrior=3;NicheNet=3
- Residual boundary: CellChat, CellPhoneDB, and niche-DE are not claimed as completed unless their outputs are imported.

## RR5_sparse_cell_types

- Status: `mitigated`
- Reviewer risk: Reviewer may object that sparse cell types are overinterpreted.
- Mitigation evidence: main_claim_cell_types=
- Residual boundary: GSE154778 main text should not promote Myeloid, CAF/Fibroblast, or any other cell type as a validated source mechanism until annotation and expression-mode permutation/FDR gates agree.

## RR6_spatial_neighbor_choice

- Status: `mitigated`
- Reviewer risk: Reviewer may ask whether Visium hotspot ranking depends on arbitrary k.
- Mitigation evidence: min_spearman=0.9309;min_top50_overlap=0.8600
- Residual boundary: Spatial claims are hotspot-localization claims, not single-cell annotation proof.

## RR7_overclaiming

- Status: `mitigated`
- Reviewer risk: Reviewer may reject unsupported clinical utility, therapeutic, or broad-superiority claims.
- Mitigation evidence: CLAIM_SAFETY_AUDIT_REPORT.md
- Residual boundary: Keep the article framed as a reproducible methods manuscript.

## RR8_figure_traceability

- Status: `mitigated`
- Reviewer risk: Reviewer or editor may ask whether each figure maps to source data and safe claims.
- Mitigation evidence: MAIN_FIGURE_QUALITY_AUDIT.tsv
- Residual boundary: Automated audit does not replace final manual journal production review.

## RR9_supplementary_artifact_completeness

- Status: `mitigated`
- Reviewer risk: Reviewer or editor may ask whether supplementary figures, tables, and support files are complete and readable.
- Mitigation evidence: supplementary_artifacts=84
- Residual boundary: Artifact readability does not replace manual caption or journal production review.

## RR10_result_table_integrity

- Status: `mitigated`
- Reviewer risk: Reviewer may question whether benchmark result tables, metric ranges, and comparator file links are internally consistent.
- Mitigation evidence: benchmark_contract_checks=9
- Residual boundary: Contract checks support table integrity, not broader biological or clinical validity.

## RR11_artifact_provenance

- Status: `mitigated`
- Reviewer risk: Reviewer, editor, or coauthor may ask which script or source generated each submission artifact.
- Mitigation evidence: provenance_rows=28
- Residual boundary: Provenance audit does not complete external DOI, GitHub publication, or author metadata.
