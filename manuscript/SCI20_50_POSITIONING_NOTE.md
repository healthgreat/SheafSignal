# SheafSignal 20-50 SCI Positioning Note

## Current Position

SheafSignal is no longer only an MVP. It now has:

- a distinct mathematical object: sheaf-valued communication flow with Hodge decomposition;
- simulation component recovery;
- three public scRNA-seq TME benchmarks;
- one public spatial transcriptomics case;
- GSE154778 claim gating that keeps sparse cell types out of main claims;
- internal LRProductBaseline comparison;
- full LIANA imports for the three public scRNA-seq benchmarks;
- MechanisticTargetPrior ligand-target prior comparator for the three public scRNA-seq benchmarks;
- NicheNet/nichenetr-engine comparator imports for the three public scRNA-seq benchmarks using the project-curated TME prior matrix;
- reviewer-facing objection and response tables.

## Current Claim Boundary

Allowed now:

- SheafSignal detects pathway-consistency mismatch and feedback/circulation structure not captured by simple LR product intensity.
- Across public tumor datasets, the dominant frustration source is context-specific.
- In GSE154778, no cell type is currently promoted as a main biological source claim after expression-mode permutation/FDR hardening; earlier Myeloid prioritization is retained only as a hypothesis-generating QC signal.
- Current full LIANA comparator imports support that SheafSignal is benchmarkable against external CCC tools.
- MechanisticTargetPrior supports target-program prior benchmarking across public scRNA-seq datasets.
- NicheNet/nichenetr-engine imports support a mechanistic comparator analysis when described with the curated-prior boundary.

Not allowed yet:

- broad superiority over CellChat, CellPhoneDB, NicheNet, LIANA, or niche-DE;
- full pretrained NicheNet network benchmarking, because the current nichenetr run uses a project-curated TME prior matrix;
- universal biological generalization of PDAC Myeloid frustration to all tumors;
- clinical or therapeutic claims;
- strong spatial cell-type mechanism claims from marker-dominant Visium spots alone.

## Submission Logic

The realistic 20-50 SCI route is a computational methods manuscript, not a clinical medicine manuscript.

Primary target: Nature Methods. This is the best-aligned route because the
main contribution is a reusable method and mathematical object, not a clinical
claim. Nature Biotechnology is a stretch target; Molecular Cancer, Nature
Cancer, Nature Biomedical Engineering, and Nature Machine Intelligence require
additional journal-specific framing or validation. The detailed target order is
maintained in `manuscript/SCI20_50_ACTION_BOARD.md` and
`manuscript/JOURNAL_TARGETS_20_50.tsv`.

The first serious submission package should be prepared only after:

1. The NicheNet section is described as official nichenetr scoring with a project-curated TME ligand-target prior matrix.
2. The manuscript does not imply use of the full pretrained NicheNet network unless that resource is explicitly added later.
3. The LIANA full-comparator section is kept as one external benchmark, not broad CCC-tool superiority.
4. All manuscript figures and supplementary QC tables are generated from documented scripts.
5. Processed data objects are frozen and assigned a Zenodo DOI.
6. Reviewer objection table is regenerated and consistent with final evidence.

## Operating Rule

Do not oversell. The project should win by being mathematically distinct, reproducible, and unusually careful about claim gating.
