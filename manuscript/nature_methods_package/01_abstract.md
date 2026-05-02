# Abstract Draft

Cell-cell communication methods prioritize ligand-receptor activity but rarely
test whether inferred signals are self-consistent across a tissue graph. We
present SheafSignal, a method that represents communication as a sheaf-valued
flow and uses Hodge decomposition to quantify pathway inconsistency, local
feedback and global circulation. Controlled simulations recover gradient, curl,
harmonic and mixed flow structure. Across public tumor microenvironment
benchmarks (gse72056_melanoma_scrna (scRNA-seq, highest computational source
CAF/Fibroblast); gse154778_pdac_scrna (scRNA-seq, highest computational source
CAF/Fibroblast after expression-mode permutation/FDR hardening);
gse176078_brca_scrna (scRNA-seq, highest computational source Endothelial);
gse103322_hnsc_scrna (scRNA-seq, highest computational source Endothelial);
tenx_breast_visium (Visium spatial transcriptomics, highest computational
source Endothelial)), dominant computational frustration rankings are
context-specific rather than universal. Comparator analyses include ligand-receptor product
baselines, full LIANA imports, bounded nichenetr-engine scoring with a
project-curated prior and a transparent mechanistic target-prior baseline. In
pancreatic cancer, claim gating shows that earlier profile-level Myeloid
prioritization is not stable enough for a standalone biological source claim
under the current expression-mode permutation/FDR hardening. SheafSignal provides a reproducible framework for studying
communication inconsistency rather than communication intensity alone.

Boundary: this abstract draft makes no clinical, therapeutic, or guaranteed
publication claim.
