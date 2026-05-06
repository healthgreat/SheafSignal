# Round 3 Higher-Rank Sheaf Response

- Decision: `ROUND3_READY_FOR_EXTERNAL_REREVIEW`
- Date: `2026-05-06`
- Scope: address the returned-review objections that SheafSignal was only a rank-one graph-coboundary residual and that the synthetic validation was circular.

## What Changed

- Implemented a higher-rank LR-channel-specific sheaf in `src/sheafsignal/sheaf.py`.
- Vertex stalks are `R^m`, where `m` is the number of valid ligand-receptor channels.
- Sender and receiver restriction coefficients are expression-scaled and LR-channel-specific, not constant `-1/+1`.
- Added LR-channel residual, LR-channel sheaf energy, edge-level higher-rank energy summary, and node-channel sheaf Laplacian outputs.
- The main pipeline now writes:
  - `results/lr_channel_sheaf_restrictions.csv`
  - `results/lr_channel_sheaf_edge_summary.csv`
  - `results/lr_channel_sheaf_laplacian.csv`
- Added tests that require higher-rank and channel-specific behavior in `tests/test_higher_rank_sheaf.py`.
- Added a task-based comparator evaluation scaffold and outputs:
  - `benchmarks/results/comparator_task_recovery.csv`
  - `benchmarks/results/comparator_task_recovery.md`

## Evidence Boundary

The rank-one scalar sheaf contract remains in the codebase for backward compatibility and provenance continuity. It should no longer be treated as the method novelty claim.

The current independent perturbation task reduces the circular-ground-truth objection because truth labels are predefined perturbation edges rather than residual-thresholded edges. However, the fair `FlowGradientOpposition_product` baseline ties SheafSignal on this task. Therefore the allowed claim is:

> SheafSignal now implements a higher-rank LR-channel sheaf object and can be evaluated on a non-residual-defined perturbation task.

The disallowed claim remains:

> SheafSignal is already proven superior to all simple LR-flow/pathway-gradient product baselines.

## What External Reviewers Should Check Next

1. Does the higher-rank LR-channel implementation remove the fatal "trivial rank-one sheaf" objection?
2. Are the restriction maps mathematically meaningful enough for the SheafSignal name?
3. Does the task-based comparator table reduce the circular benchmark concern?
4. Is the current product-baseline tie acceptable with downgraded claims, or does a 20-50 IF methods route require a harder task?
5. What exact manuscript wording must change before submission?

## Current Submission Meaning

This round makes the project stronger, but it is still not a final 20-50 IF submission package until external rereview confirms that the prior fatal objections are resolved or safely downgraded.
