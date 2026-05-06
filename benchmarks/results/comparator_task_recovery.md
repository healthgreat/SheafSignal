# Task-Based Comparator Evaluation Report

- Decision: `TASK_BASED_COMPARATOR_EVALUATION_READY`
- Output table: `benchmarks/results/comparator_task_recovery.csv`
- Primary task: `independent_perturbation`
- Boundary: primary simulation truth labels are predefined perturbation edges, not residual-thresholded edges.

## Top Methods By Noise Level

| noise_sd | method | average_precision | auroc | baseline_family |
|---|---|---:|---:|---|
| 0.0 | `SheafSignal_sheaf_energy` | 1.0000 | 1.0000 | `sheaf_residual` |
| 0.0 | `FlowGradientOpposition_product` | 1.0000 | 1.0000 | `flow_gradient_product` |
| 0.0 | `HigherRankLRChannelSheaf_energy` | 1.0000 | 1.0000 | `higher_rank_lr_channel_sheaf` |
| 0.05 | `SheafSignal_sheaf_energy` | 1.0000 | 1.0000 | `sheaf_residual` |
| 0.05 | `FlowGradientOpposition_product` | 1.0000 | 1.0000 | `flow_gradient_product` |
| 0.05 | `HigherRankLRChannelSheaf_energy` | 1.0000 | 1.0000 | `higher_rank_lr_channel_sheaf` |
| 0.1 | `SheafSignal_sheaf_energy` | 1.0000 | 1.0000 | `sheaf_residual` |
| 0.1 | `FlowGradientOpposition_product` | 1.0000 | 1.0000 | `flow_gradient_product` |
| 0.1 | `HigherRankLRChannelSheaf_energy` | 1.0000 | 1.0000 | `higher_rank_lr_channel_sheaf` |

## Interpretation Boundary

This task-based comparison reduces the circular-ground-truth concern, but it does not by itself prove that the higher-rank sheaf is superior to every simple LR-flow/pathway-gradient product baseline. That claim must be supported by harder perturbation tasks or downgraded.
