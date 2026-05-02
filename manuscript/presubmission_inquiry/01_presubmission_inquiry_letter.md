# Presubmission Inquiry Letter Draft

Dear Nature Methods Editors,

We would like to ask whether the manuscript "SheafSignal maps frustration in
cell communication networks" may be suitable for consideration as a methods
article in Nature Methods.

Current cell-cell communication workflows primarily rank sender-receiver
ligand-receptor interactions. SheafSignal addresses a different mathematical
question: whether inferred communication is self-consistent across a biological
graph. The method represents communication as a sheaf-valued flow and applies
Hodge decomposition to quantify pathway inconsistency, local feedback/curl and
global circulation.

The evidence package includes controlled recovery of gradient, curl and
harmonic components; public tumor microenvironment benchmarks across
gse72056_melanoma_scrna, gse154778_pdac_scrna and gse176078_brca_scrna as scRNA-seq sheaf-energy ranking cases; tenx_breast_visium as a spot-level spatial hotspot workflow demonstration; and comparator analyses using
LIANA (3 datasets), LRProductBaseline (4 datasets), MechanisticTargetPrior (3 datasets), NicheNet (3 datasets). The manuscript also includes programmatic
claim gating. For example, in GSE154778 pancreatic cancer, Myeloid is retained
only as a supplement-level computational hypothesis, while sparse categories
are restricted to supplementary quality-control context.

We position the study as a reproducible computational methods contribution. We
do not claim clinical utility, treatment prediction, or broad superiority over
all communication tools. Source code, small benchmark summaries and release
manifests are prepared for GitHub release, and frozen processed benchmark
objects are prepared for Zenodo deposition before submission.

We would appreciate your advice on whether this manuscript is within the scope
and interest of Nature Methods.

Sincerely,

TBD
