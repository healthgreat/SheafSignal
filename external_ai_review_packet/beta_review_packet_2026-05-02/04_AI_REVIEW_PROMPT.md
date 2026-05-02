# Copy-Paste Prompt For External AI Review

You are acting as a critical methods-journal reviewer for the SheafSignal manuscript package.
Do not be polite for its own sake. Identify fatal and near-fatal weaknesses first.
Use only the evidence files provided by the authors, and clearly separate direct evidence,
reasonable inference, and speculation.

The current target is a 20-50 IF methods manuscript route, with Nature Methods as a stretch/primary
methods fit and safer fallback routes if the evidence does not support that level.

Please answer these checklist items:

- [Methods] Does the implemented rank-one cellular sheaf object justify the manuscript's sheaf-valued method framing? Evidence: src/sheafsignal/sheaf.py; manuscript/novelty_overlap/SHEAFSIGNAL_NOVELTY_OVERLAP_REPORT.md
- [Methods] Is Hodge decomposition correctly applied to sheaf_residual for the primary frustration result? Evidence: manuscript/SHEAFSIGNAL_STATUS_GATES_2026-05-02.tsv; benchmarks/results/BENCHMARK_RESULT_CONTRACT_REPORT.md
- [Simulation] Does the simulation benchmark prove added information beyond LR score, pathway gradient, Hodge-only, centrality, and graph-smoothness baselines? Evidence: benchmarks/results/simulation/sheaf_ground_truth_recovery.csv
- [SingleCell] Is GSE154778 annotation validation sufficient after scanpy_full_v1, and is the Myeloid claim correctly downgraded? Evidence: benchmarks/results/gse154778_pdac_scrna/reannotation/GSE154778_REANNOTATION_READINESS_REPORT.md; manuscript/CLAIM_SAFETY_AUDIT_REPORT.md
- [Statistics] Are sample-stratified permutations, pooled FDR, and bootstrap/stability outputs enough for descriptive computational claims? Evidence: manuscript/SHEAFSIGNAL_STATUS_GATES_2026-05-02.tsv; benchmarks/results/BENCHMARK_RESULT_CONTRACT_REPORT.md
- [Comparators] Is the completed primary scRNA comparator scope enough, and are unsupported broad-superiority claims absent? Evidence: manuscript/comparator_scope/COMPARATOR_SCOPE_REPORT.md; manuscript/CLAIM_SAFETY_AUDIT_REPORT.md
- [Spatial] Is the Visium section safely limited to hotspot demonstration without cell-type source claims? Evidence: manuscript/visium_scope/VISIUM_SCOPE_REPORT.md
- [Reproducibility] Would a reviewer be able to reproduce the core demo from a clean public clone after GitHub/Zenodo are inserted? Evidence: envs/ENVIRONMENT_LOCK_REPORT.md; release/clean_clone_preflight/CLEAN_CLONE_PREFLIGHT_REPORT.md; release/GIT_RELEASE_READINESS_REPORT.md
- [Submission] Are GitHub URL, Zenodo DOI, author metadata, and submission-day checks correctly treated as blockers? Evidence: manuscript/FINAL_SUBMISSION_BLOCKERS.tsv; release/RELEASE_METADATA_PLACEHOLDER_REPORT.md
- [JournalFit] Given the current evidence, is Nature Methods still the best first route, or should the package be aimed at another 20-50 IF journal? Evidence: manuscript/IF20_50_DISTANCE_REPORT.md; manuscript/journal_metric_audit/JOURNAL_METRIC_AUDIT_REPORT.md

Return your review in this structure:

1. Editorial decision: accept / minor / major / reject / not ready.
2. Top 5 fatal or near-fatal concerns.
3. Required fixes before any 20-50 IF submission.
4. Claims that must be downgraded or removed.
5. Best-fit journals and why.
6. Short final verdict on distance to submission readiness.
