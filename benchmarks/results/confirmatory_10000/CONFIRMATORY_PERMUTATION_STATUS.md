# Confirmatory 10,000-Permutation Subset Status

- Decision: `CONFIRMATORY_10000_READY_NOT_RUN`
- Target dataset: `gse154778_pdac_scrna`
- Target permutations: `10000`
- Current role: `pre-specified_confirmatory_subset_local_ready`

## Target Tests

- `global_metrics:curl_ratio`: current p=0.0009990009990009, family FDR=0.0039960039960036, current n=1000, confirmatory status `ready_not_run`.
- `node_frustration:Myeloid`: current p=0.0009990009990009, family FDR=0.0019980019980018, current n=1000, confirmatory status `ready_not_run`.
- `edge_sheaf_energy:Myeloid->Tumor/Epithelial`: current p=0.0009990009990009, family FDR=0.0059940059940053, current n=1000, confirmatory status `ready_not_run`.
- `edge_curl:Myeloid->CAF/Fibroblast`: current p=0.0009990009990009, family FDR=0.0019980019980018, current n=1000, confirmatory status `ready_not_run`.

## Interpretation Boundary

This file pre-specifies the smallest confirmatory subset for a higher-resolution 10,000-permutation pass. The current state is not allowed to promote Myeloid, curl-like, or edge-level real-data signals into biological mechanism claims. A completed 10,000-permutation run may improve statistical defensibility, but it still does not create clinical, therapeutic, or causal evidence.

## Run Command

Use `benchmarks/results/confirmatory_10000/run_confirmatory_10000_commands.sh`. Because this is a long-running computation, run it in WSL with `tmux` or `nohup`, keep Windows sleep disabled, and keep the current 1000-permutation outputs unchanged as the baseline evidence.
