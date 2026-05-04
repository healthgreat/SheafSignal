# Reviewer 2 — Single-Cell, Spatial, and Biological Claims

## 0. Reviewer metadata

- **reviewer_model_name:** Claude (Anthropic)
- **reviewer_model_version:** Claude Opus 4.7 (`claude-opus-4-7`)
- **review_timestamp_with_timezone:** 2026-05-04, Asia/Shanghai (UTC+08:00)
- **claimed_training_data_cutoff:** End of January 2026 (per system context)
- **external_references_consulted:** None beyond the supplied bundle. Public GitHub and Zenodo links were not fetched. GEO accession metadata for GSE154778, GSE72056, GSE176078, GSE103322 was not re-verified against the original GEO submissions in this review.
- **Independence disclosure:** This is one of three reviews (R1/R2/R3) produced sequentially by **the same Claude instance**. They are correlated, not independent.
- **Review mode:** Aggressive — Nature Methods first-round desk-reject / referee-stage rejection threshold.
- **Evidence boundary:** `[direct]`, `[inferred]`, `[speculation]` are marked.

---

## 1. Editorial decision

**Reject as a Nature Methods / Nature Biotechnology / Nature Cancer submission. Major revision plus additional biological validation required for any 20–30 IF route.**

The biology in this manuscript is honest about its limitations — almost to a fault. The authors openly admit that the central PDAC GSE154778 case yields **no main-text biological claim**, that Visium is hotspot demonstration only, and that "computational sheaf-energy rankings are dataset-dependent, not the biological claim that a single cell type universally dominates tumor communication inconsistency". The problem for a high-impact methods journal is that **what remains is a method without a single positive biological example.** Five public datasets produce five different "top frustration sources" with no biological synthesis. A high-impact biology editor will read the discipline as caution; a high-impact methods editor will read it as the absence of a demonstrated biological win. Both are blockers.

---

## 2. Top 5 fatal or near-fatal biological / single-cell concerns

### F1. The cross-dataset story is fragmented and has no positive biological anchor. **[direct]**

From `SCI_MANUSCRIPT_V2_POLISHED.md` (lines 110–118) and `README.md` (lines 295–315):

| Dataset | Top frustration source (computational) |
|---|---|
| GSE72056 melanoma | CAF/Fibroblast |
| GSE154778 PDAC, pooled expression mode | CAF/Fibroblast (raw score) |
| GSE154778 PDAC, lesion-stratified | Myeloid (both Primary and Metastatic) |
| GSE154778 PDAC, expression-mode permutation | Myeloid (lower raw score, smaller p) |
| GSE176078 BRCA | Endothelial |
| GSE103322 HNSC | Endothelial |
| 10x Visium breast | hotspot only — no cell-type claim |

The flagship dataset (GSE154778, the only one used for "claim gating") contradicts itself between modes. CAF wins on raw score; Myeloid wins on p-value; the manuscript correctly declines to promote either. Across datasets, the "top source" alternates between CAF, Myeloid, and Endothelial with no biological pattern that the method *itself* explains. The claim gates correctly downgrade these to "computational rankings", but a Nature Methods biology referee will ask the obvious question: **if the method's primary output cannot be interpreted biologically on any of the five datasets the manuscript provides, what is the biological reader supposed to do with the method?**

The honest answer the manuscript gives — *"this pattern supports the method-level claim that computational sheaf-energy rankings are dataset-dependent"* (line 116) — is a methodological observation dressed as a biological one. It does not constitute a positive demonstration. There is no analogous "we confirmed this prediction by orthogonal experiment / public protein data / patient outcome" anywhere in the bundle.

**Required action:** Add at least one positive biological demonstration. Candidates: (a) take a published PDAC perturbation study (e.g., a CAF or macrophage depletion) and show SheafSignal predicts the affected interactions; (b) cross-reference Myeloid-as-frustration-source against published PDAC immune-axis literature with explicit hypotheses tested; (c) drop a cell type (e.g., remove macrophages from the input) and show the method recovers loss of the relevant signal in a non-trivial way.

### F2. Annotations are coarse, single-source, and never validated against an independent reference. **[direct + inferred]**

`ROUND2_HARDENING_STATUS_2026-05-02.md` reports the GSE154778 reannotation as `scanpy_full_v1` with 14,926 cells, 16 samples, ~7 cell-type categories. The bundle provides no:

- Comparison against the **author-published annotations** of Lin et al. (the original GSE154778 paper), even though those exist.
- Comparison against an **independent automated reference** (Azimuth, CellTypist, scANVI).
- Per-cell-type marker confidence panels.
- Doublet rates per cluster (DoubletFinder / Scrublet outputs).
- Lesion-vs-batch confounding analysis (sample composition by lesion type).

For coarse types like "Myeloid" and "CAF/Fibroblast", this matters in cancer biology because the *subtype* is the biology:

- Myeloid in PDAC includes monocytes, macrophages (M1, M2, TAM-1, TAM-2 polarization), DCs, neutrophils, MDSCs. "Myeloid frustration" averaged across these is a low-resolution claim.
- CAFs in PDAC are explicitly heterogeneous (iCAF, myCAF, apCAF — Elyada et al. 2019, Öhlund et al. 2017). A "CAF top frustration source" averaged across iCAF and myCAF is biologically uninformative.
- "Tumor/Epithelial" in PDAC mixes ductal, acinar, and PanIN-derived populations.

The manuscript's claim gating correctly stops biological interpretation at this resolution, but a single-cell referee will ask: **why was the analysis run at this resolution at all?** The biology of CCC in PDAC happens between iCAF and TAM2 at minimum, not between "CAF" and "Myeloid".

**Required action:** Run at least one dataset (GSE154778) at finer cell-state resolution (≥ 12–15 subtypes), with annotation cross-checked against an independent reference (Azimuth or the original publication). Show whether SheafSignal's frustration ranking changes meaningfully under finer annotation. If the ranking is unstable across annotation depth, that is itself a finding the manuscript must report.

### F3. The "Endothelial top" finding in BRCA and HNSC is biologically suspicious and likely an artifact of cell counts and LR-database coverage. **[inferred]**

In tumor scRNA-seq, endothelial cells typically constitute 1–5% of captured cells (lower for HNSC FFPE, slightly higher for BRCA fresh tissue). They have:

- The smallest absolute cell counts of the major tumor compartments.
- Sparse expression of common LR pairs (most CCC databases are skewed toward cytokines/chemokines/growth factors that are immune- and stromal-centric).
- Distinct, highly regulated angiogenesis-axis ligands (VEGF, ANGPT, DLL4) that are over-represented in some LR databases.

A computational frustration score concentrated in endothelial cells is therefore consistent with **(a) low-cell-count denominator effects, (b) LR-database bias toward angiogenesis pairs, or (c) failure of the pathway-state estimate to converge in a small, highly specialized population.** Without:

- Per-cell-type cell counts in the bundle (not provided).
- Per-cell-type LR-pair coverage (not provided).
- Per-cell-type pathway-score variance (not provided).

…the "Endothelial top" result in two of the five datasets is **not interpretable**. The manuscript correctly does not promote this as biology, but it also does not flag the artifact risk.

**Required action:** Report per-cell-type cell counts and per-cell-type expressed-LR-pair counts for every dataset. Re-run with cell-count-balanced subsampling (e.g., downsample each cell type to min(N_celltype) and re-rank). If "Endothelial top" survives this, it merits further investigation; if it doesn't, the manuscript should explicitly state the artifact.

### F4. The Visium analysis is presented at the right scope (hotspot only) but contributes no biological information at that scope. **[direct]**

`VISIUM_SCOPE_REPORT.md` constrains the Visium section to "spot-level spatial hotspot workflow demonstration with k-neighbor sensitivity and marker-program QC", and the manuscript respects this. Good discipline. But the consequence is that the Visium section becomes **an algorithmic stability check, not a biological result**: it shows hotspots are stable across k = 4–12 (Spearman ≥ 0.93, top-50 overlap ≥ 0.86 — `README.md` lines 346–349) but says nothing about *what those hotspots are biologically*.

For a 20–50 IF venue, the spatial section either earns its space by:

- Adding deconvolution (e.g., cell2location, RCTD, CARD) so spot labels are meaningful.
- Adding an orthogonal validation (H&E pathology overlay, IHC for predicted ligand or receptor protein).
- Adding a perturbation or longitudinal axis.

…or it does not belong in the manuscript at all. The current "Visium = workflow demonstration" framing is honest but uninformative for a methods journal that values demonstration over claim discipline.

**Required action:** Either drop the Visium section to the supplement and reframe as a "future-work software extension demonstration", or add deconvolution + at least one orthogonal validation. The middle ground (current state) reads as filler.

### F5. The pathway/target-gene set is undefined and represents a hidden parameter. **[direct]**

`README.md` line 109 says inputs include `pathway_genes.txt: one target/pathway gene per line`. `SCI_MANUSCRIPT_V2_POLISHED.md` Methods section (line 219) says "Receiver pathway state is summarized from target-gene activity" without specifying which gene set was used for any of the five datasets. There is no:

- Per-dataset pathway gene-set source (Hallmark? KEGG? a custom PDAC list?).
- Sensitivity to gene-set choice.
- Discussion of how pathway-set heterogeneity affects cross-dataset comparisons.

This is a major omission. **The pathway gradient is half of the residual definition.** If the pathway sets differ between datasets, the cross-dataset "top frustration source" comparison is comparing different residual definitions across datasets. A reviewer will demand sensitivity analysis with at least 3 standard sources (Hallmark, KEGG, Reactome).

**Required action:** Document the exact pathway gene set used per dataset, justify the choice, and provide a sensitivity analysis showing how rankings change with alternative gene-set sources.

---

## 3. Is the GSE154778 Myeloid claim appropriately bounded?

**Yes, the bounding is appropriate and the claim discipline is exemplary — but the bounded claim is so narrow that it stops contributing to the manuscript's case.**

The bundle's claim gating (`CONFIRMATORY_PERMUTATION_STATUS.md`, `ROUND2_HARDENING_STATUS_2026-05-02.md`, `ROUND3_RETURNED_REVIEW_TRIAGE_2026-05-02.md`) explicitly:

- Sets Myeloid claim gate to `supplement_only` / `supplement_context`.
- States Myeloid is "a lesion-stratified computational hypothesis, not a validated biological source or mechanism".
- Notes that pooled expression-mode top-source is CAF/Fibroblast, not Myeloid (`frustration_score=0.4306`, BH-FDR=0.0157 vs Myeloid `frustration_score=0.1845`, BH-FDR=0.0002).
- Notes that CAF/Fibroblast is itself QC-warning-only because "metastatic lesion support is sparse".

This is correct boundary-setting. **However**, observe what is *not* claimed anywhere:

- A specific testable biological hypothesis ("Myeloid TAMs in metastatic PDAC drive frustrated TGFB→TGFBR signaling on CAFs", or similar).
- A mechanism the SheafSignal output uniquely points to that an existing tool would not.
- A reason a follow-up wet-lab experiment should target Myeloid rather than CAF.

The result is a cell type that is `supplement_only`, plus a method that produced the supplement, plus no biological prediction. From the reader's perspective, the GSE154778 example exists primarily to demonstrate the claim-gating workflow, not the biological inference. This is fine for a reproducibility paper but thin for a methods-journal biological case study.

**Suggestion:** Either drop GSE154778 to a supplementary case-study and replace the main-text biological example with a dataset where SheafSignal does generate a positive testable prediction; or strengthen GSE154778 by integrating it with bulk PDAC TCGA / clinical outcomes (e.g., does Myeloid frustration correlate with response to anti-PD-1 in published cohorts?).

---

## 4. Sparse cell types, Visium spot labels, and mechanism language

### Sparse cell types
Handled correctly via claim gates in `qc_gse154778_claim_gating.py` and `READMEFile.md` (lines 743–800 of `README.md`). The note that "low-count cell-type warnings are included in the output tables and must be respected in manuscript interpretation" is sound. The manuscript text (lines 122–140 of `SCI_MANUSCRIPT_V2_POLISHED.md`) reflects this discipline.

### Visium spot labels
Handled correctly via `VISIUM_SCOPE_REPORT.md` and `qc_tenx_visium_spatial.py`. Spot labels are described as "marker-dominant rather than histology-validated single-cell identities". The k-neighbor sensitivity (k = 4–12, Spearman ≥ 0.93) is methodological, not biological. The boundary is correct; my concern in F4 above is whether the section earns its space at this scope.

### Mechanism language
Mostly handled, but one instance to flag in `SCI_MANUSCRIPT_V2_POLISHED.md` line 174: *"the method reports… whether the fitted graph-flow structure is dominated by directional, local curl-like or global circulation-like components"*. The phrase "global circulation-like components" risks being read as referring to **physiological circulation** (blood flow) rather than **graph-theoretic harmonic circulation**. Rewrite to "global graph-circulation-like components (in the graph-theoretic sense, not vascular)" or similar. The same applies to `README.md` line 105: *"local feedback loops create high curl energy"* — "feedback loops" suggests biological feedback regulation; clarify that this is a graph-curl object.

The Discussion paragraph at lines 198–205 of the manuscript handles overclaim risk well. No further action needed there.

---

## 5. What exact biological claims must be downgraded or removed?

| Current text (location) | Required action |
|---|---|
| Abstract line 21–24: "SheafSignal identified context-specific computational rankings rather than a universal source cell type." | Acceptable, but the abstract should explicitly say **none of the rankings is biologically validated**. Otherwise readers may infer the rankings are biologically meaningful. |
| Lines 110–118 (public benchmarks paragraph): the per-dataset "highest computational source" list. | Add per-cell-type cell counts and per-cell-type LR-pair counts immediately after each "highest" claim, so readers see the denominator. Without these, "Endothelial top" in BRCA/HNSC reads stronger than the data supports (see F3). |
| Line 174: "global circulation-like components" | Disambiguate: graph-theoretic harmonic circulation, not vascular circulation. |
| Line 105 in README: "local feedback loops create high curl energy" | Disambiguate: graph-curl, not biological feedback regulation. |
| Discussion line 178–187: pancreatic cancer paragraph | Currently honest. Recommend adding one sentence: "We do not consider GSE154778 a biological case study; it is presented as a demonstration of why claim gating is necessary in CCC method development." That sentence would make the discipline visible to readers and protect against over-citation in follow-up literature. |
| GSE176078 BRCA "highest computational source Endothelial" (line 111) | Suspicious; likely artifact (F3). Either justify with cell-count and LR-coverage numbers or move to supplement with explicit caveat. |
| GSE103322 HNSC "highest computational source Endothelial" (line 111) | Same as above. |
| Spatial section lines 158–166: hotspot localization framing | Acceptable scope, but add: "spatial hotspots reported here are algorithmic stability artifacts of the spot-neighbor graph and are not interpreted as cellular communication mechanisms." |

---

## 6. What validation or sensitivity analyses would most improve a 20–50 IF submission?

In rough order of impact:

1. **One positive biological demonstration.** A single dataset where SheafSignal generates a **specific, falsifiable prediction** that is then orthogonally supported (protein, IHC, perturbation, patient outcome). The manuscript currently has zero. Without one, the method's biological utility is asserted, not shown.
2. **Annotation-resolution sensitivity.** Re-run GSE154778 at coarse (7), medium (12–15, sub-typed), and fine (≥ 25) resolutions. Show whether the frustration ranking is stable across resolution. If not, this defines the resolution at which the method is interpretable.
3. **Independent annotation cross-check on GSE154778.** Compare `scanpy_full_v1` annotations to the original Lin et al. annotations and to Azimuth/CellTypist references. Quantify agreement (ARI, NMI) per cell type. The current bundle does not show this.
4. **Cell-count- and LR-coverage-balanced re-ranking.** Subsample each cell type to a common N and re-rank frustration. Address F3 directly.
5. **Pathway-set sensitivity.** Run with at least Hallmark, KEGG, and Reactome pathway sources. Show ranking stability or document the dependence.
6. **LR-database sensitivity.** Run with CellChatDB, OmniPath, and Connectome-DB LR pair lists. Same logic.
7. **Sample-leverage diagnostic on the Myeloid signal.** Leave-one-sample-out frustration ranking on GSE154778 (16 samples). If Myeloid is driven by ≤ 3 samples, that needs to be in the manuscript. (See Reviewer 3 §F3 for the parallel statistical concern.)
8. **Visium deconvolution.** If Visium stays in the manuscript, run cell2location or RCTD and re-define hotspots in deconvolved space. Otherwise drop.
9. **Comparator under matched conditions for a biological task.** Existing comparator analysis is alignment-only (Spearman). Add a task: "predict a held-out perturbation effect" or "predict a known LR pair from the literature" and run SheafSignal vs LIANA vs CellChat under identical inputs. Without this, the comparator section is descriptive, not evaluative.

---

## 7. Best-fit journals and why

**At current state (no positive biological demonstration):**
- **Bioinformatics** (OUP, ~5–6 IF) — accepts methods with honest limitations and good benchmarking.
- **NAR Genomics & Bioinformatics** — same tier.
- **PLOS Computational Biology** — accepts well-disciplined methods papers without strong biological case.
- **F1000Research** with refereeing — possible if open peer review is acceptable.

**Reachable after positive biological case (F1, F2, plus #1 and #3 from §6):**
- **Genome Biology** (~12 IF) — methods + biology, will demand at least one positive demonstration.
- **Cell Reports Methods** (~5 IF, Cell Press) — fits a method paper with cancer-context replication.
- **Bioinformatics Advances** — newer OUP venue, similar standards.
- **Briefings in Bioinformatics** (~10 IF) — survey/methods overlap.

**Stretch targets named in `IF20_50_DISTANCE_REPORT.md`:**
- **Nature Methods (32.1 IF)** — *not appropriate at current state*. The biology section provides no positive demonstration, the method's central object is mathematically thin (see Reviewer 1 §F1), and the cross-dataset behaviour does not converge on any biological pattern. A biology referee will return it without sending out for review.
- **Nature Cancer (28.5 IF)** — *not appropriate*. The PDAC case is explicitly bounded as non-biological. There is no cancer-mechanistic finding to anchor the submission.
- **Nature Biotechnology (41.7 IF)** — *not appropriate*. No translational utility, no clinical claim, no validated biomarker.
- **Molecular Cancer (33.9 IF)** — possible only if the manuscript is rewritten as a PDAC biology paper with SheafSignal as the analysis tool — and only after the F1 biological demonstration is added.

**Editor's-eye verdict:** Present-state biology fits **PLOS Comp Bio or Bioinformatics**. The 20–50 IF route requires at least one positive biological demonstration (§6 #1) plus annotation hardening. Without those, the manuscript is a careful methods workflow paper, not a high-impact biological methods paper.

---

## Final remark

The manuscript's claim discipline is genuinely admirable — the project openly downgrades its own headline cell type (Myeloid), keeps Visium narrowly scoped, and refuses to convert computational ranking into biological mechanism. This kind of discipline is uncommon and improves the literature. But the same discipline, applied to **all five datasets**, leaves the manuscript without a single demonstrated biological win. A methods reviewer at a 20–50 IF journal does not penalize honesty, but they do penalize the absence of a positive case. Add the positive case (one validated biological example), and most of the present biology critique resolves.
