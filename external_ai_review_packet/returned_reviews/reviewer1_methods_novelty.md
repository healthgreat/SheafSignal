# Reviewer 1 — Methods and Novelty

## 0. Reviewer metadata

- **reviewer_model_name:** Claude (Anthropic)
- **reviewer_model_version:** Claude Opus 4.7 (`claude-opus-4-7`)
- **review_timestamp_with_timezone:** 2026-05-04, Asia/Shanghai (UTC+08:00)
- **claimed_training_data_cutoff:** End of January 2026 (per system context)
- **external_references_consulted:** None beyond the supplied bundle. Public GitHub (`github.com/healthgreat/SheafSignal`) and the Zenodo DOI (`10.5281/zenodo.20012189`) listed in the routing document **were not fetched** — review is based only on the bundled markdown/TSV evidence.
- **Independence disclosure:** This review is one of three (R1/R2/R3) produced sequentially by **the same model instance**. The author should treat the three reviews as **correlated**, not independent. A genuine multi-model panel (e.g., GPT-4-class + Gemini-class + Claude) is not substituted by this output.
- **Review mode:** Aggressive — explicitly simulating Nature Methods first-round desk-reject / referee-stage rejection threshold, as requested.
- **Evidence boundary:** I separate `[direct]` (text I read in the bundle), `[inferred]` (reasonable derivation from the text), and `[speculation]` (cannot be verified from the bundle).

---

## 1. Editorial decision

**Reject (not ready for Nature Methods or Nature Biotechnology in current form). Strong major revision required for any 20–30 IF route.**

The package shows real engineering effort, honest claim gating, and round-on-round hardening. But the two pillars that a high-impact methods journal will scrutinize first — **mathematical novelty of the sheaf framing** and **algorithmic added value over GSP/Hodge baselines on a non-self-fulfilling task** — remain mathematically thin. The Round 2 "formal sheaf" fix is a *labelling* fix, not a *structural* one. A Nature Methods Associate Editor reading this package would, in my judgement, return it without sending out for review, citing insufficient methodological novelty and circular validation.

---

## 2. Top 5 fatal or near-fatal methods concerns

### F1. The "rank-one cellular sheaf" is mathematically degenerate and equivalent to a standard weighted directed graph with node potentials. **[direct + inferred]**

`ROUND2_HARDENING_STATUS_2026-05-02.md` defines the rank-one cellular sheaf as:

- vertex stalk = `R_pathway_state` (i.e., ℝ)
- edge stalk = `R_communication_observation` (i.e., ℝ)
- restriction maps: sender = `−1`, receiver = `+1`
- coboundary expected flow = `receiver_pathway − sender_pathway`
- primary residual = `sheaf_residual = flow_z − coboundary_expected_flow`

This is precisely the **standard graph coboundary operator δ⁰** acting on a scalar function over vertices, which is the central object of graph signal processing (Sandryhaila & Moura 2013), graph Hodge theory (Jiang et al. 2011 — already cited), and discrete exterior calculus on graphs (Lim 2020 — already cited). With ±1 restriction maps and ℝ stalks, the cellular-sheaf machinery collapses: the sheaf Laplacian equals the ordinary graph Laplacian, the coboundary is the ordinary gradient, and the "sheaf-valued flow" is a scalar edge function. There is **no nontrivial restriction-map structure left to exploit**. The "rank-one cellular sheaf" claim is technically correct but mathematically vacuous — it is the trivial sheaf on a graph.

The bundle's own `SHEAFSIGNAL_NOVELTY_OVERLAP_REPORT.md` already acknowledges this risk: *"Do not claim first-ever use of sheaves in biology"; "presents an integrated sheaf/Hodge workflow for CCC graphs"*. But the manuscript abstract (`SCI_MANUSCRIPT_V2_POLISHED.md` lines 17–19) still leads with *"models cell-cell communication as a sheaf-valued flow over a biological graph"*. A reviewer with a graph-signal-processing or applied-topology background will recognize within a paragraph that the sheaf framing adds no expressive power over a directed weighted graph. **This is the single most likely first-round desk-reject driver at Nature Methods.**

**Required action:** Either (a) implement a non-trivial sheaf — higher-rank stalks, non-orthogonal restriction maps, or context-dependent restrictions per ligand-receptor channel — and demonstrate that this richer object captures something the rank-one trivial sheaf cannot; or (b) drop "sheaf-valued" from the title and abstract and reframe as *"a graph-Hodge consistency residual for CCC"*. Option (b) is honest but loses the methods-journal hook.

### F2. The "sheaf residual" is `z(LR_flow) − (path_recv − path_send)` — i.e., a graph-smoothness residual already studied for over a decade. **[direct]**

From `README.md` lines 845–849:

```
sheaf_energy(edge) = edge_weight * (z(log1p(flow)) − z(pathway_receiver − pathway_sender))^2
```

This is the squared mismatch between a normalized edge signal and a normalized vertex-gradient signal — i.e., the **non-smooth component** of an edge function with respect to a node potential. The same quantity appears under multiple names in prior art:

- **Graph signal processing** "non-smoothness energy" / Dirichlet energy of edge residuals (Ortega et al. 2018, *Proc. IEEE*).
- **Hodge rank aggregation** residual (Jiang et al. 2011 — Math. Program. — already in the manuscript reference list).
- **Frustration in signed/weighted graphs** (Aref & Wilson 2019 — *J. Complex Networks*).
- **Network smoothness regularization** in graph-based semi-supervised learning (Zhou et al. 2003; Belkin & Niyogi 2004).

The novelty must be redefined as **the application** (LR-flow vs pathway-state on a CCC graph), not the **method**. The current manuscript framing ("a computational framework that models cell-cell communication as a sheaf-valued flow… and uses Hodge decomposition to quantify edge-level frustration") will not survive a methods reviewer's first pass.

**Required action:** Restate the contribution as *"applying graph-Hodge consistency to CCC residuals"* and let novelty rest on the **biological/data-analysis pipeline**, not on the mathematical object.

### F3. The synthetic ground-truth simulation looks circular. **[inferred from `ROUND2_HARDENING_STATUS_2026-05-02.md`; the actual `sheaf_ground_truth_recovery.csv` is missing from the bundle]**

Round 2 reports SheafSignal AP = 1.00 / 0.917 / 0.867 at noise SD 0 / 0.05 / 0.10, against an LR-flow baseline AP ≈ 0.6, a Hodge-only baseline AP ≈ 0.32, and centrality/smoothness baselines AP ≈ 0.63. AP = 1.00 at zero noise is the canonical signature of a method recovering its own definition.

Without the simulation generator code or the recovery CSV, I cannot verify, but the AP gap pattern is **consistent with the synthetic ground truth being constructed from `flow − coboundary_pathway` directly**. If the simulator generates inconsistent edges by injecting `flow_z − (path_recv − path_send)` deviations and SheafSignal scores by computing exactly that quantity, then AP = 1.00 is **definitional, not empirical**. Note also that `sheaf_ground_truth_recovery.csv` is listed as *required* in `02_EVIDENCE_FILE_INDEX.tsv` but **is not present in this review bundle** (see §F5 below) — a referee cannot independently verify the ground-truth construction.

**Required action:** (a) Restore the simulation CSV to the review bundle; (b) describe the data-generating process (DGP) of the synthetic benchmark in mathematical detail; (c) add a non-self-fulfilling task — e.g., recovering simulated **biological perturbations** that propagate through a known pathway, where the ground truth is *the perturbation*, not *the residual definition*; (d) include "leakage tests" where SheafSignal is denied access to either LR or pathway, and show degradation matches expectation.

### F4. Hodge decomposition is computed on collapsed antiparallel net flow, with curl basis restricted to complete cell-type triangles — both choices destroy structure the framework exists to capture. **[direct]**

From `README.md` lines 851–858 and 873–878:

> "For Hodge decomposition, anti-parallel directed edges are collapsed into a canonical pairwise net flow… The current curl space is generated from complete cell-type triangles in the communication graph… Hodge decomposition uses pairwise net flow, so it emphasizes directional imbalance rather than total bidirectional communication."

Two structural problems:

1. **Antiparallel collapse**: in real CCC, A→B and B→A are biologically distinct (e.g., a TGFB ligand from CAF to T-cell vs an IL-2 ligand from T-cell to CAF). Collapsing them to a single net pairwise flow throws away the very direction-dependent biology that motivates a sheaf framework. The manuscript admits this in the limitations section but does not quantify the information loss.
2. **Triangle-only curl basis**: with K cell-types, the curl basis has at most C(K,3) elements, of which only a subset corresponds to triangles realized in the data. For K = 7–8 (the per-dataset cell-type counts in `SCI_MANUSCRIPT_V2_POLISHED.md`), this is at most 35–56 dimensions, with realized triangles likely much fewer. Reporting a "small curl/harmonic ratio" on real data and calling it a finding ("real datasets are dominated by gradient components" — `ROUND1_MULTI_AGENT_REVIEW_SUMMARY_2026-05-02.md` consensus issue 6) is **near-tautological** when the curl basis is so low-dimensional.

**Required action:** (a) Replace antiparallel collapse with a directed Hodge decomposition (e.g., magnetic Laplacian or directed graph Hodge as in Schaub et al. 2020); (b) extend the curl basis to higher-order simplices (4-cycles, 5-cycles) or admit that the gradient/curl/harmonic split on a small dense graph is information-poor; (c) report the dimension of the curl basis explicitly per dataset.

### F5. The bundle is internally inconsistent — 11/22 required evidence files are missing. **[direct, programmatically verified]**

The shareable bundle's own `02_EVIDENCE_FILE_INDEX.tsv` lists 22 files as `required=yes`. Of these, the following 11 are physically absent from the zip:

- `manuscript/SHEAFSIGNAL_STATUS_DASHBOARD_2026-05-02.md` (the 2026-05-03 file is present instead — a date drift)
- `manuscript/SHEAFSIGNAL_STATUS_GATES_2026-05-02.tsv`
- `manuscript/FINAL_SUBMISSION_BLOCKERS.tsv`
- `benchmarks/results/simulation/sheaf_ground_truth_recovery.csv` ← **the key methods evidence**
- `benchmarks/results/gse154778_pdac_scrna/reannotation/GSE154778_REANNOTATION_READINESS_REPORT.md`
- `manuscript/figure_quality/MAIN_FIGURE_QUALITY_REPORT.md`
- `envs/ENVIRONMENT_LOCK_REPORT.md`
- `release/clean_clone_preflight/CLEAN_CLONE_PREFLIGHT_REPORT.md`
- `release/GIT_RELEASE_READINESS_REPORT.md`
- `release/RELEASE_METADATA_PLACEHOLDER_REPORT.md`
- `manuscript/nature_methods_package/10_supplementary_information_draft.md`

Yet `EXTERNAL_AI_REVIEW_ROUTING_2026-05-04.md` declares `Decision: SHAREABLE_REVIEW_BUNDLE_READY`, `Included files: 35`, `Missing required files: 0`. This is a verifiable contradiction in the project's own packaging audit. It implies either (a) the integrity-check script does not actually check filesystem presence against the index, or (b) the bundle was built from a different source-of-truth than the index. Both are concerning for a manuscript whose central pitch is **reproducibility hardening**.

**Required action:** Fix the bundle generator so the integrity report actually verifies presence; add a unit test in `scripts/package_external_beta_review_bundle.py` that checks every `required=yes` row in the index resolves to a file with the expected SHA256; then resend.

---

## 3. Does the rank-one cellular sheaf framing justify the manuscript's claims?

**No, not in its current form.**

A cellular sheaf with ℝ stalks and ±1 restriction maps is the **trivial sheaf** on the underlying graph: it carries no information beyond the graph topology and node values. The "sheaf coboundary" `δp(e) = p_target − p_source` is the standard graph gradient (Lim 2020, eq. 2.3). The "sheaf Laplacian" `L = δ*δ` is the standard combinatorial graph Laplacian. The "sheaf residual" is the residual of an edge signal against a node-gradient potential — a graph-smoothness object.

For the sheaf framing to do real work, at least **one** of the following must hold:

- Stalks of dimension > 1 (e.g., one dimension per pathway, per LR pair, or per cellular state).
- Restriction maps that are **not** ±1 (e.g., learned or biology-derived linear maps that encode "what arrives at the receiver is a context-modulated version of what the sender emits").
- Restriction maps **per LR channel**, so that consistency means "all LR channels at edge `e` agree on the same receiver-stalk vector".

Hansen & Ghrist's foundational cellular sheaf work (cited as `cellular_sheaves_hansen_2019`) explicitly motivates the formalism by these higher-rank, non-trivial-restriction settings. The current implementation does not use that machinery; it uses sheaf vocabulary on top of a graph-Laplacian computation. The manuscript's title, abstract, and Introduction lead with sheaf-valued language and will not survive sheaf-aware referees.

A **rescue path** that preserves "sheaf" wording with mathematical substance: define stalks as **R^|LR_pairs|** (one dimension per LR channel at each cell type), restriction maps as **diagonal matrices encoding the channel-specific receptor expression**, and the consistency residual as the **per-channel mismatch between sender-emitted and receiver-effective channel vectors**. That is a non-trivial sheaf, and the resulting decomposition is genuinely sheaf-Laplacian-based (cf. Hansen & Gebhart 2020). Whether this is implementable in the current codebase is unverified.

---

## 4. Is the Hodge decomposition on `sheaf_residual` technically defensible?

**Defensible as a computation, not as a methodological contribution.**

- **Computation**: applying graph Hodge decomposition (Jiang et al. 2011) to any edge signal — including `sheaf_residual` — is mathematically well-defined. The simulation panel reported in `SCI_MANUSCRIPT_V2_POLISHED.md` (gradient_chain → 100% gradient, triangle_curl → 100% curl, harmonic_ring → 100% harmonic) confirms the implementation correctness of the decomposition layer.

- **Contribution**: switching the input of the decomposition from `flow_z` (Round 1) to `sheaf_residual = flow_z − (path_recv − path_send)` (Round 2) is a meaningful modeling choice but **does not constitute a new decomposition method**. The mathematical machinery is unchanged. What changed is *what edge signal is decomposed*, which is at best an applied modelling choice and not a methodological novelty for a methods journal.

- **A more concerning aspect**: the residual itself already **subtracts the gradient component** (`path_recv − path_send` is exactly a gradient on the node potential). So computing a Hodge decomposition on `sheaf_residual` and then reporting a "gradient ratio" is at risk of confusion: the gradient that survives in the residual is the part of `flow_z` not aligned with the pathway gradient. This is interpretable, but the manuscript needs to spell it out clearly, otherwise readers will conflate "gradient-dominated residual" with "gradient-dominated communication", which means very different things. The current Discussion does not make this distinction sharp.

---

## 5. What exact novelty claims must be downgraded?

| Current claim (location) | Required downgrade |
|---|---|
| Title: "SheafSignal maps communication frustration in tissue signaling networks" | Acceptable, but "sheaf" should not appear in the title unless §3 rescue path is implemented. Suggest: *"A graph-Hodge consistency residual for cell–cell communication analysis"*. |
| Abstract: "models cell-cell communication as a sheaf-valued flow over a biological graph" (lines 17–19, `SCI_MANUSCRIPT_V2_POLISHED.md`) | Drop "sheaf-valued"; replace with "models inferred CCC as an edge flow over a cell-type graph and applies Hodge decomposition to a pathway-consistency residual". |
| Introduction: "SheafSignal addresses this gap by changing the mathematical object under analysis." (line 60) | The mathematical object is **not** changed — it is still a graph edge signal. Reword to: "SheafSignal changes the *quantity* under analysis from edge intensity to edge–pathway consistency residual." |
| "cellular sheaves providing the language for local-to-global consistency constraints" (line 67) | Either implement the §3 rescue (stalks > 1, non-trivial restrictions) or remove the cellular-sheaf citation. Citing Hansen & Ghrist for a rank-one trivial sheaf is overreach. |
| Round 2 "formal rank-one cellular sheaf API" claim | Rename to "graph-coboundary residual API" in code and docs. The current API does not implement the cellular-sheaf primitives that justify the name. |

---

## 6. Method experiments most likely to improve a 20–50 IF submission

In rough order of impact:

1. **Implement a non-trivial sheaf (highest priority).** Stalks with dimension equal to number of LR pairs per cell type; restriction maps encoded by receptor-side expression; demonstrate that the resulting sheaf Laplacian recovers structure that the rank-one Laplacian misses. Without this, the methods-journal hook is brittle.
2. **Non-self-fulfilling simulation.** Generate synthetic single-cell data with a **known biological perturbation** (e.g., knock down a ligand in one cell type, propagate downstream pathway changes) and show SheafSignal recovers the perturbation source, edge, or pathway better than CellChat / LIANA / a Hodge-only baseline. AP = 1.00 on a residual-recovery task is not convincing; recovery of an upstream perturbation is.
3. **Comparator under matched conditions.** Re-run LIANA, CellChat, NicheNet on the simulation in #2, with identical permutation budgets and identical evaluation tasks. Report AP, AUROC, FDR-controlled discovery counts, plus 95% CIs. Without matched-condition comparators, the "alignment" Spearman numbers (0.07–0.75) are descriptive only.
4. **Directed Hodge decomposition.** Replace antiparallel collapse with a magnetic-Laplacian or signed-edge approach (Schaub et al. 2020; Furutani et al. 2019). This addresses F4 directly and is a small mathematical extension that produces a defensible methodological delta.
5. **Higher-order simplicial decomposition.** Extend the curl basis to 4-cycles and 5-cycles. With the current 7–8 cell-type graphs, the curl basis is too low-dimensional to interpret "low curl ratio" as a finding.
6. **Sensitivity to LR-database and pathway-set choice.** All current results depend on the LR-pair list and the "target/pathway gene set". Run with at least 3 LR databases (CellChatDB, OmniPath, Connectome) and 3 pathway-set sources (Hallmark, KEGG, Reactome). Without this, "pathway-state transition" is a hidden parameter.
7. **Ablation: residual without Hodge decomposition.** Show that the Hodge split actually adds information beyond the raw `sheaf_energy` ranking on biological tasks. The manuscript currently uses Hodge ratios as descriptive diagnostics; reviewers will ask whether the decomposition is load-bearing for any biological claim.

---

## 7. Best-fit journals and why

**At current state (no further methodological hardening):**
- **Bioinformatics** (OUP) — 5–6 IF range, accepts applied algorithms with modest novelty if reproducibility and benchmarking are clean. Realistic primary target.
- **NAR Genomics & Bioinformatics** — similar tier, tolerant of applied workflows.
- **PLOS Computational Biology** — 4–5 IF, accepts honest applied methods. Would tolerate the current scope.

**Reachable after Round 2 rescue (non-trivial sheaf + perturbation simulation):**
- **Cell Reports Methods** (~5 IF, Cell Press) — honest fit for a CCC methodological extension with cancer-context replication.
- **Briefings in Bioinformatics** — methods reviews + workflows; accepts well-reproduced applied methods.
- **Genome Biology** — 12 IF, possible if the perturbation simulation is convincing and biological validation lands.

**Stretch targets explicitly named in `IF20_50_DISTANCE_REPORT.md`:**
- **Nature Methods (32.1 IF)** — *not appropriate at current state*. The "what is mathematically new" question is unanswered. Probability of desk-reject in my judgement: high.
- **Nature Biotechnology (41.7 IF)** — *not appropriate*. Method scope is too narrow; no demonstrated translational utility.
- **Nature Cancer / Nature Biomedical Engineering** — methodology is too detached from a specific cancer biology question or a device-class result to fit either remit.
- **Molecular Cancer (33.9 IF)** — possible only if recast as a **PDAC biology paper** with SheafSignal as a tool, and only if the GSE154778 Myeloid story can be biologically validated, which the bundle explicitly says it cannot.

**Editor's-eye verdict:** present-state best fit is **Bioinformatics or PLOS Comp Bio**. A 20–50 IF route is not currently defensible without the F1/F2/F3 fixes above.

---

## Final remark

The package shows unusually disciplined claim gating, claim-safety auditing, and review-cycle hygiene. Round 1 → Round 2 hardening is real engineering progress, and the boundary statements throughout (`CLAIM_SAFETY_AUDIT_REPORT.md`, `VISIUM_SCOPE_REPORT.md`, `COMPARATOR_SCOPE_REPORT.md`, `NOVELTY_OVERLAP_REPORT.md`) are exemplary in tone — the project clearly takes overclaiming seriously. The reason this review is still a reject is unrelated to discipline: **the central methodological object does not yet justify the methods-journal framing**. Fix that, and a credible 20-IF-tier submission is in reach. Don't fix it, and Nature Methods is not the right venue.
