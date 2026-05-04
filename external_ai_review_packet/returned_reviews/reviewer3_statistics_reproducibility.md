# Reviewer 3 — Statistics, Reproducibility, and Journal Fit

## 0. Reviewer metadata

- **reviewer_model_name:** Claude (Anthropic)
- **reviewer_model_version:** Claude Opus 4.7 (`claude-opus-4-7`)
- **review_timestamp_with_timezone:** 2026-05-04, Asia/Shanghai (UTC+08:00)
- **claimed_training_data_cutoff:** End of January 2026 (per system context)
- **external_references_consulted:** None beyond the supplied bundle. The public GitHub URL `https://github.com/healthgreat/SheafSignal` and the Zenodo DOI `10.5281/zenodo.20012189` listed in the routing document **were not fetched or independently verified**. Reproducibility findings are based only on the bundled audit reports and on cross-referencing those reports against each other.
- **Independence disclosure:** This is one of three reviews (R1/R2/R3) produced sequentially by **the same Claude instance**. They are correlated; treat the three as a single-reviewer panel with three perspectives, not three independent referees. The bundle's `triage_external_beta_reviews.py` should not weight them as independent.
- **Review mode:** Aggressive — Nature Methods first-round desk-reject / referee-stage rejection threshold.
- **Evidence boundary:** `[direct]`, `[inferred]`, `[speculation]` are marked.

---

## 1. Editorial decision

**Reject for any 20–50 IF submission until the public-release reproducibility chain is independently verifiable, the FDR family is pre-registered, and the simulation/comparator evaluation is done under matched conditions. Major revision required.**

The package contains a remarkable amount of release infrastructure — preflight scripts, claim-safety audits, manifest builders, journal-metric audits, post-unblock pipelines. But the actual *reproducibility of the science* cannot be evaluated from this bundle alone. The bundle's own evidence index lists 11 files I cannot inspect (including `CLEAN_CLONE_PREFLIGHT_REPORT.md`, `RELEASE_METADATA_PLACEHOLDER_REPORT.md`, and `GIT_RELEASE_READINESS_REPORT.md`); the dashboard from 2026-05-03 lists 7 active blockers and the IF20-50 distance report from 2026-05-04 lists 0 blockers; and the confirmatory permutation results are reported at p-values that hit the resolution floor. None of these alone is fatal; collectively they make the reproducibility claim — which is the manuscript's *primary asset* — impossible to verify externally.

---

## 2. Top 5 fatal or near-fatal statistics / reproducibility concerns

### F1. The "10,000-permutation confirmatory subset" reports p-values at the resolution floor; further precision is unobtainable from the design. **[direct + inferred]**

`CONFIRMATORY_PERMUTATION_STATUS.md` reports the four confirmatory tests with **identical** p-values:

```
global_metrics:curl_ratio                         p = 9.999e-05
node_frustration:Myeloid                          p = 9.999e-05
edge_sheaf_energy:Myeloid->Tumor/Epithelial       p = 9.999e-05
edge_curl:Myeloid->CAF/Fibroblast                 p = 9.999e-05
```

This number is `1 / (n + 1)` for `n = 10000`, which is the **minimum possible empirical p-value** when zero null permutations are more extreme than the observed test statistic. It does not mean p ≈ 1e-4; it means **p ≤ 1e-4 and the design cannot resolve further**. Reporting the same floor value for four separate tests, combined with `family FDR` values that simply scale that floor by m/k, is statistical theatre: the FDR numbers (1.998e-4 to 5.999e-4) are mechanical consequences of the floor, not measured quantities.

Additional concerns:

- The four tests are reported as a "family" but they overlap substantially: a node-frustration permutation null and an edge-sheaf-energy permutation null sharing the same input data are not independent, so BH-FDR over them is too liberal.
- A confirmatory subset that pre-specifies exactly the four tests **already known to be significant in the 1000-permutation pre-screen** is a circular pre-registration. The function of confirmatory testing is to test hypotheses that were proposed *before* seeing the data; here the hypothesis was selected *after* seeing the data ("smallest 1000-perm p-values were", per Round 2 hardening report), then re-tested at higher resolution.

**Required action:** (a) Report whether any null permutation matched or exceeded the observed statistic (yes/no, count). If `count = 0`, report `p < 1/(n+1)` rather than the floor value. (b) Document the test family pre-registration timestamp, hash, and which tests were chosen before vs after the 1000-perm pass. (c) For genuinely confirmatory hypotheses, run independent permutations with `n ≥ 10⁵` so the resolution floor is below 0.001 / m_tests with comfortable margin. (d) Drop the framing "10,000-permutation confirmatory subset" and replace with "high-resolution re-evaluation of the four 1000-perm-significant tests".

### F2. The CAF/Fibroblast vs Myeloid p-value flip is a high-leverage signal that is not diagnosed in the bundle. **[direct + inferred]**

From `SCI_MANUSCRIPT_V2_POLISHED.md` lines 130–137 and `ROUND2_HARDENING_STATUS_2026-05-02.md`:

| Cell type | Raw frustration score | Empirical p (10,000 perms) | BH-FDR |
|---|---|---|---|
| CAF/Fibroblast | 0.4306 | 0.0118 | 0.0157 |
| Myeloid | 0.1845 | 9.999e-05 | 0.0002 |

CAF has 2.3× the raw score of Myeloid but a p-value 100× larger and an FDR 80× larger. This is mathematically possible only if **the null distribution under sample-stratified permutation is much narrower for Myeloid than for CAF**. With 16 PDAC samples (Round 2 report), narrow-null behaviour for Myeloid is most plausibly explained by:

- A small number of high-leverage samples driving the Myeloid score.
- Or the Myeloid label-shuffle preserving a structural property (e.g., consistent within-sample Myeloid abundance) that makes the permuted nulls cluster.

The bundle does not include leave-one-sample-out (LOSO) diagnostics for Myeloid, sample-level frustration variance, or the empirical null-distribution width per cell type. These are essential for interpreting the p-value flip. Without them, the headline statistic "Myeloid empirical p = 9.999e-05 with sample-stratified permutation" is at risk of being driven by 1–3 samples.

**Required action:** Add LOSO Myeloid frustration ranking (drop each of 16 samples, re-rank, report the distribution of Myeloid rank). If the rank distribution is concentrated (Myeloid stays top in ≥ 14/16 LOSO runs), the signal is robust. If it shifts substantially (Myeloid drops below #3 in ≥ 4/16 LOSO runs), the manuscript must report this as a high-leverage finding, not a confirmatory signal. The bundle reports "Myeloid top in 100/100 cell-bootstraps" — which is **not** the same as sample-level robustness because cells within a sample are not exchangeable units of variation.

### F3. The pooled FDR family is not pre-specified anywhere in the visible documentation. **[direct]**

Round 1 review explicitly flagged this (`round1_review_response_matrix.tsv` row "Statistics MAJOR — Global multiple-testing family is undefined"). Round 2 status (`fixed_round2_pooled_fdr_audit_script_added`) reports that a pooled FDR audit script was added (`scripts/build_pooled_fdr_audit.py` — visible in the source manifest, not in this content bundle). However, the bundle contains no:

- Definition of which test family BH is applied across.
- Whether per-dataset FDR, pooled-across-datasets FDR, or per-test-class FDR is used for the manuscript-facing numbers.
- A pre-registered exploratory vs confirmatory split.

Different choices change the reported FDR by 10–100×. Without a documented family, the FDR claims throughout the manuscript (e.g., "BH-FDR=0.0002") are **not interpretable** because the multiple-testing correction depends on the family Mass.

**Required action:** Add to Methods a paragraph specifying:
1. The exact test family for each BH-corrected statistic in the manuscript.
2. Whether the family was pre-registered (timestamp / commit hash).
3. The exploratory vs confirmatory boundary.
4. A supplementary table listing every BH-corrected p-value, the family it belongs to, family size m, and the per-test BH threshold at α = 0.05.

### F4. Comparator alignment is reported as point-estimate Spearman without confidence intervals or matched-condition evaluation. **[direct]**

From `SCI_MANUSCRIPT_V2_POLISHED.md` line 145:

> "LRProductBaseline across 4 datasets, Spearman -0.0496 to 0.72; LIANA across 3 datasets, Spearman 0.0743 to 0.699; MechanisticTargetPrior across 3 datasets, Spearman 0.176 to 0.643; NicheNet across 3 datasets, Spearman 0.184 to 0.75."

Issues:

1. **No confidence intervals** on the Spearman correlations. With n = number of edges per dataset (likely 30–100 directed cell-type edges given 7–8 cell types), Spearman 0.07 has a 95% CI roughly (-0.2, 0.4), and Spearman 0.18 has a CI roughly (-0.1, 0.45). These are not different from zero or from each other. Reporting bare ρ values without CIs invites overinterpretation.
2. **No matched-condition comparison.** SheafSignal was run with sample-stratified permutations and 10⁴ perms; LIANA was run with `--n-perms 1000` (`README.md` line 399). NicheNet uses a "project-curated TME ligand-target prior matrix, not a full pretrained NicheNet network benchmark" (`README.md` line 458–460). Each comparator was run under tool-specific defaults, not matched conditions. The Spearman alignment is therefore a comparison of **method × configuration**, not method.
3. **No formal test of (non-)equivalence.** The manuscript claims "alignment with existing communication evidence while preserving a distinct inconsistency-focused readout" (abstract line 31–32). A formal claim of non-equivalence requires a permutation test that the SheafSignal vs comparator difference is greater than expected from noise. None is reported.
4. **Comparator scope is partial.** `COMPARATOR_SCOPE_REPORT.md` correctly notes that "demo, Visium, GSE103322 and niche-DE remain outside primary comparator-completeness claims". The boundary-setting is appropriate. But for a 20–50 IF venue, comparator coverage is what reviewers judge — partial coverage means partial defensibility.

**Required action:** (a) Add bootstrap 95% CI to every Spearman value. (b) Run SheafSignal and at least LIANA under **identical permutation budgets and identical inputs** for at least one dataset, and report a paired comparison on a held-out task. (c) Add a formal non-equivalence test (e.g., bootstrap test of `1 - |ρ|` for each pair). (d) State explicitly which comparator-method-dataset cells are completed and which are not, in a single table at the start of the comparator section.

### F5. The bundle is internally inconsistent about whether the public release is complete; clean-clone reproducibility cannot be externally verified. **[direct, programmatically verified]**

There is a contradiction between two reports in this bundle:

| Source | Date | Report on release readiness |
|---|---|---|
| `manuscript/SHEAFSIGNAL_STATUS_DASHBOARD_2026-05-03.md` | 2026-05-03 | "Submission infrastructure index: 44.5%. Final local decision: NO_GO for formal submission. Current live blocker: GitHub token has `repo` but not `workflow` scope; push rejected. Active release blockers: 7." |
| `manuscript/IF20_50_DISTANCE_REPORT.md` | 2026-05-04 | "Submission infrastructure index: 100.0%. Live release blocking gates: 0 of 7. Decision: IF20_50_SUBMISSION_CANDIDATE_AFTER_FINAL_FORMAT_CHECK. Clean-export reproduction preflight: local_clean_export_pass." |

The 24-hour gap between the dashboard and the distance report is consistent with the GitHub workflow-scope blocker being resolved overnight. But the bundle does not include:

- `release/clean_clone_preflight/CLEAN_CLONE_PREFLIGHT_REPORT.md` (required per the index, **not in the bundle**).
- `release/GIT_RELEASE_READINESS_REPORT.md` (required per the index, **not in the bundle**).
- `release/RELEASE_METADATA_PLACEHOLDER_REPORT.md` (required per the index, **not in the bundle**).
- `manuscript/FINAL_SUBMISSION_BLOCKERS.tsv` (required per the index, **not in the bundle**).

So the only evidence that the public release transitioned from "blocked" to "ready" is a single line in a derived report (`IF20_50_DISTANCE_REPORT.md`). I cannot verify whether:

- The repository at `github.com/healthgreat/SheafSignal` actually contains the release-tagged code claimed.
- The Zenodo DOI `10.5281/zenodo.20012189` actually resolves to a deposition matching the claimed SHA256.
- A clean-clone reproduction was actually performed against the public URL or only against a local export.

For a reproducibility-centric methods paper, this is the most consequential gap. **A reviewer at any 20+ IF venue will fetch the GitHub URL and the Zenodo record before sending the manuscript out for review.** If those resources do not match the manuscript's claims, the desk-reject is automatic.

**Required action:** (a) Restore the four missing reproducibility audits to the review bundle. (b) Provide a verifiable transcript of the clean-clone preflight: clone the public URL into a fresh container, install the locked environment from `envs/requirements-py311-lock.txt`, run `pytest -q`, run `make_publication_figures.py`, and attach the stdout/stderr log + final manifest hash to the bundle. (c) Confirm Zenodo DOI resolution publicly and provide the matching SHA256 in the manuscript Data Availability section.

---

## 3. Are permutation / FDR / bootstrap analyses enough for the claims being made?

**No, not at the current claim level. They are sufficient for "exploratory, hypothesis-generating, computational" claims, which the manuscript correctly applies. But three holes remain even at that level.**

What is sufficient:
- Sample-stratified permutation at n=1000 for the per-dataset main analyses is a defensible default.
- Bootstrap stability of Myeloid as the top frustration source over cell resampling (100/100, median 0.9176, 95% interval 0.9110–0.9241) is appropriately reported as **computational stability**, not biological robustness.
- BH-FDR is the right correction family in principle.

What is not sufficient:
- **The pre-specification of the confirmatory subset is post-hoc.** See F1 — the four tests selected for 10⁴ perms are exactly the four most significant tests at 10³ perms. This is not pre-registration.
- **Sample-level robustness diagnostics are missing.** See F2 — leave-one-sample-out across 16 samples is the natural unit of variation for a multi-patient, multi-lesion dataset.
- **The pooled FDR family is not specified.** See F3 — without it, every BH-corrected number in the manuscript is non-interpretable.

What would be appropriate at *true confirmatory* level (not currently claimed):
- Pre-registered hypotheses with timestamp before the analysis.
- Independent dataset for confirmation (not a re-perm of the same data).
- Effect sizes with CIs, not just p-values.
- Sample-level mixed-effect models on the residual rather than label permutation alone.

---

## 4. Is comparator coverage adequate for the stated manuscript scope?

**Partially. The scope-gating is rigorous, but the comparator analysis itself is descriptive rather than evaluative.**

The scope gate (`COMPARATOR_SCOPE_REPORT.md`) restricts primary comparator claims to GSE72056, GSE154778, and GSE176078 with LRProductBaseline, LIANA, MechanisticTargetPrior, bounded NicheNet, CellPhoneDB, and CellChat. This is honest scope-setting.

However:

1. The current manuscript text (lines 142–156) summarises only LRProductBaseline, LIANA, MechanisticTargetPrior, and NicheNet alignments. CellPhoneDB and CellChat — explicitly mentioned in the scope gate as completed — are not in the manuscript Spearman summary. Either include them in the summary, or explain why they were excluded from the Results paragraph.
2. The comparator section makes only a non-equivalence claim ("not merely a relabelled ligand-receptor product score"). It makes no **superiority claim** — which is correct — but it also does not run any task on which comparators can be **evaluated** (recovery of a known LR pair, prediction of a held-out perturbation, agreement with a curated ground truth). Without an evaluation task, the comparator section is correlation reporting, not benchmarking.
3. NicheNet is bounded to "nichenetr scoring engine with project-curated TME prior matrix, not a full pretrained NicheNet network benchmark" (`README.md` line 458–460). This is honest, but it means the NicheNet alignment numbers are **NicheNet-the-engine, not NicheNet-the-method-as-published**. A reviewer with a CCC background will register that this is a custom configuration, not a like-for-like comparison.

**Required action:** Either (a) expand the comparator section to include a task-based evaluation (recovery of a curated CCC interaction, held-out prediction, etc.), or (b) explicitly retitle the section as "Comparator alignment (descriptive)" and reduce the manuscript-level interpretation accordingly.

---

## 5. Can the public GitHub / Zenodo release support reproducibility review?

**Cannot be determined from this bundle.**

The bundle contains:
- A claim that GitHub URL (`github.com/healthgreat/SheafSignal`) and Zenodo DOI (`10.5281/zenodo.20012189`) are minted and inserted (`IF20_50_DISTANCE_REPORT.md`, `EXTERNAL_AI_REVIEW_ROUTING_2026-05-04.md`).
- An `EXTERNAL_RELEASE_AUTHORIZATION_REPORT.md` with `Decision: EXTERNAL_RELEASE_AUTHORIZATION_READY`, `Passed checks: 8`, `Pending checks: 1`.
- A `POST_UNBLOCK_RELEASE_PIPELINE_REPORT.md` with `Decision: POST_UNBLOCK_PIPELINE_BLOCKED_GITHUB_TOKEN`, `active_release_blockers: 7`.
- A dashboard with the GitHub workflow-scope problem unresolved as of 2026-05-03.
- A distance report with everything resolved as of 2026-05-04.

The bundle does **not** contain:
- The clean-clone preflight report.
- The release metadata placeholder report (which would confirm DOI placeholders are replaced).
- The Git release readiness report.
- The actual final-blocker tsv.
- A log of any externally-verifiable test that the public URLs work.

**Required for confidence:** A clean-clone reviewer reproducibility test from outside the author's machine. The bundle's `docs/reviewer_reproducibility_quickstart.md` is referenced but not included. The bundle's GitHub release authorization scripts are referenced but not runnable from this content alone.

A practical test for reviewers: clone `https://github.com/healthgreat/SheafSignal` at the v0.1.0 tag, verify SHA256 matches the source-code review bundle hash (`3f08b5614378167b91c6a853dc640399aaef20e99f6f81beeb1609e24c67f905` per the routing document), install the locked environment, run `pytest -q`, and run the demo. If any step fails, reproducibility claims are not externally verifiable.

I have not performed this test in this review.

---

## 6. What exact statistical or reproducibility claims must be downgraded?

| Current claim (location) | Required action |
|---|---|
| `CONFIRMATORY_PERMUTATION_STATUS.md`: confirmatory p-values reported as `9.999e-05` | Replace with `< 1/(n+1) for n=10000 — resolution floor`. State the count of null permutations matching/exceeding the observed statistic. |
| `SCI_MANUSCRIPT_V2_POLISHED.md` line 134–137: "BH-FDR=0.0002 with 10,000 sample-stratified permutations" | Add: "(BH-FDR is at the resolution floor of the 10,000-permutation design; the test family used for BH correction is [explicit family])". |
| `SCI_MANUSCRIPT_V2_POLISHED.md` line 145: "Spearman -0.0496 to 0.72" without CIs | Add bootstrap 95% CIs for every Spearman; state the `n` (number of edges) per dataset. |
| `IF20_50_DISTANCE_REPORT.md`: "Overall readiness index: 98.0%" and "Submission infrastructure index: 100.0%" | These are internal indices with no defined formula. Either drop them from external-facing documents or add the formula in an audit appendix. They will be misread as success probabilities. |
| `README.md` lines 753–755: "Myeloid remains the top frustration source in 100/100 resamples, with median frustration score 0.9176 and a 2.5%-97.5% bootstrap interval of 0.9110-0.9241" | Reframe explicitly: "100/100 cell-level bootstrap resamples maintain Myeloid as top, but cell-level bootstrap does not address sample-level robustness; see leave-one-sample-out diagnostic in [supplement]." |
| `EXTERNAL_AI_REVIEW_ROUTING_2026-05-04.md`: "Decision: SHAREABLE_REVIEW_BUNDLE_READY", "Missing required files: 0" | Fix the bundle generator to actually verify file presence. As shipped, 11 of 22 files declared `required=yes` in the bundle's own index are absent. (See bundle integrity finding flagged across all three reviews.) |
| Comparator alignment paragraph (lines 142–156): "shows alignment with existing communication evidence while preserving a distinct inconsistency-focused readout" | Add: "Alignment is assessed by Spearman correlation under tool-specific default configurations; matched-condition comparator evaluation is not provided." |

---

## 7. Best-fit journals and why

**At current state (without F1–F5 fixes):**
- **Bioinformatics** (OUP) — accepts methods with documented limitations and clean reproducibility once the public release is verified.
- **PLOS Computational Biology** — accepts honest methods with descriptive comparator analysis.
- **Briefings in Bioinformatics** — methods reviews + applied methods.

**Reachable with statistics + reproducibility hardening (F1, F2, F3, F5):**
- **Genome Biology** (~12 IF) — strong on reproducibility; will accept descriptive comparators if statistics are tight.
- **Cell Reports Methods** (~5 IF) — accepts a methods paper with cancer-context replication once stats are pre-registered.
- **Nucleic Acids Research** (general track) — possible if the comparator section adds a recovery task.

**Stretch targets in `IF20_50_DISTANCE_REPORT.md`:**
- **Nature Methods (32.1 IF)** — *not appropriate*. The reproducibility chain is not externally verifiable from this bundle. The confirmatory permutation framing is post-hoc. Nature Methods will run a clean-clone test from your GitHub URL and check that the manuscript's reported numbers regenerate; if any step fails, it is a desk-reject.
- **Nature Biotechnology (41.7 IF)** — *not appropriate*. Same reason, plus no translational utility.
- **Molecular Cancer (33.9 IF)** — same as Reviewer 2's verdict — only viable as a PDAC biology paper, and only after the F1–F2 statistics fixes.

**Editor's-eye verdict:** Present-state reproducibility fits **Bioinformatics or PLOS Comp Bio** once GitHub/Zenodo are externally verified. The 20–50 IF route requires F1 (resolution-floor honesty), F3 (FDR family pre-registration), and F5 (verifiable clean-clone reproduction) at minimum.

---

## Final remark

The reproducibility infrastructure investment in this project is unusual in volume — preflight scripts, claim-safety audits, manifest builders, journal-metric audits, multi-round triage. The amount of process is substantial. But process is not evidence: a reviewer at a high-impact venue checks whether **the public-facing claims regenerate from the public-facing artifacts**, not whether the project has a long audit trail. Three concrete changes would convert most of this audit infrastructure into a defensible 20–30 IF reproducibility submission:

1. Bundle integrity: ship every file the index says is shipped.
2. FDR family pre-registration: a single methods paragraph + an audit table.
3. External clean-clone verification: clone-from-public-URL → install-locked-env → pytest → demo, with the log committed to the public release.

The science (Reviewer 1, Reviewer 2 territory) needs more work; the reproducibility (this reviewer's territory) needs less, but it needs the right kind.
