# SheafSignal 20-50 SCI Journal Action Board

## Decision

The first submission target is `Nature Methods`. It is the best-aligned 20-50
IF route because SheafSignal is a method-first contribution: a new
sheaf-valued communication-flow object, Hodge decomposition, simulations,
public tumor microenvironment benchmarks, external comparator alignments, and
reproducible software/data packaging.

This board does not guarantee acceptance. It defines the strongest defensible
submission route and the claims that must stay out of the manuscript.

## Submission Order

1. `Nature Methods` as the primary methods target.
2. `Nature Biotechnology` only as a high-risk stretch if the package is framed
   as a broadly reusable platform.
3. `Molecular Cancer` only if the manuscript gains stronger cancer-biology
   validation; the current GSE154778 cell-type source ranking is not stable
   enough for a Myeloid-centered mechanism paper.
4. `Nature Cancer` only if biological validation becomes stronger.
5. `Nature Biomedical Engineering` only if the engineering/translation angle is
   strengthened.
6. `Nature Machine Intelligence` is not recommended unless a real ML primitive
   is added.

## Required Non-Negotiable Actions

1. Mint Zenodo DOI for the processed benchmark objects and archive manifests.
2. Keep GSE154778 main-text biology as an annotation/model-dependence caution:
   neither Myeloid nor CAF/Fibroblast is currently a validated source claim.
3. State that NicheNet evidence uses the official nichenetr scoring engine with
   a project-curated TME prior matrix, not a full pretrained NicheNet network.
4. Avoid broad superiority language over CellChat, CellPhoneDB, LIANA, NicheNet,
   and niche-DE.
5. Re-run `python -m pytest`, `python scripts/release_audit.py`,
   `python scripts/build_reproducibility_release.py`, and
   `python scripts/build_submission_readiness_report.py` after any file change.

## Target Details

### 1. Nature Methods

- 2024 JIF: 32.1; 5-year JIF: 51.7.
- Role: `primary_methods_target`.
- Fit score: 5/5.
- Current position: `best_aligned_high_risk_first_submission`.
- Why it fits: Best fit for a reusable biological method with a new mathematical object, simulation validation, public benchmarks, and software release.
- Must have before submission: Zenodo DOI; frozen figures; clear methods text; no overclaiming beyond LIANA and bounded nichenetr-engine evidence.
- Boundary: Do not claim clinical utility, full pretrained NicheNet benchmarking, or broad superiority over all CCC tools.
- Metric source: https://www.nature.com/nmeth/journal-impact

### 2. Nature Biotechnology

- 2024 JIF: 41.7; 5-year JIF: 59.5.
- Role: `stretch_methods_platform_target`.
- Fit score: 4/5.
- Current position: `stretch_target_not_most_likely`.
- Why it fits: Possible only if the manuscript is framed as a broadly reusable biotechnology/computational platform with strong external benchmarks.
- Must have before submission: Stronger user-facing package polish; possibly additional external CCC comparators or independent application breadth.
- Boundary: Do not present a public-only TME case study as a validated biotechnology platform without broad adoption or prospective validation.
- Metric source: https://www.nature.com/nbt/journal-impact

### 3. Molecular Cancer

- 2024 JIF: 33.9; 5-year JIF: 35.9.
- Role: `cancer_application_route`.
- Fit score: 3/5.
- Current position: `possible_after_stronger_cancer_story`.
- Why it fits: Strong IF fit, but the current package is a method-first public-data study rather than a definitive cancer-mechanism paper.
- Must have before submission: sharper tumor-microenvironment biological narrative, independent annotation validation, and no GSE154778 cell-type mechanism claim unless reannotation and expression-mode permutation/FDR gates agree.
- Boundary: Do not turn sparse cell-type or Visium marker-spot findings into strong cancer mechanism conclusions.
- Metric source: https://molecular-cancer.biomedcentral.com/about

### 4. Nature Cancer

- 2024 JIF: 28.5; 5-year JIF: 28.6.
- Role: `cancer_biology_stretch_route`.
- Fit score: 3/5.
- Current position: `not_primary_without_biology_validation`.
- Why it fits: Good disease-field visibility, but likely requires stronger cancer biology, histology, clinical, or perturbation validation than available now.
- Must have before submission: External biological validation or a much deeper public cancer atlas story; journal-specific disease relevance.
- Boundary: Do not imply clinical or therapeutic relevance from computational frustration scores alone.
- Metric source: https://www.nature.com/natcancer/journal-impact

### 5. Nature Biomedical Engineering

- 2024 JIF: 26.6; 5-year JIF: 30.4.
- Role: `engineering_translation_route`.
- Fit score: 3/5.
- Current position: `fallback_only_if_engineering_angle_strengthens`.
- Why it fits: In IF range and method-oriented, but SheafSignal currently lacks engineering or translational validation.
- Must have before submission: Clear deployable workflow, robust software documentation, and stronger evidence that the method changes biological interpretation.
- Boundary: Do not frame as a biomedical engineering tool with clinical deployment readiness.
- Metric source: https://www.nature.com/natbiomedeng/journal-impact

### 6. Nature Machine Intelligence

- 2024 JIF: 23.9; 5-year JIF: 31.8.
- Role: `computational_algorithm_stretch_route`.
- Fit score: 2/5.
- Current position: `not_recommended_unless_ml_novelty_added`.
- Why it fits: Within the target IF range, but SheafSignal is currently a mathematical bioinformatics method rather than a machine-intelligence contribution.
- Must have before submission: A stronger AI/ML primitive and ML benchmark suite, not only sheaf/Hodge bioinformatics.
- Boundary: Do not relabel a sheaf/Hodge method as machine intelligence without an actual ML contribution.
- Metric source: https://www.nature.com/nature-portfolio/about/journal-metrics
