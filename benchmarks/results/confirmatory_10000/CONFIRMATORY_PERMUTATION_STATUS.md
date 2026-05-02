# Confirmatory 10,000-Permutation Subset Status

- Decision: `CONFIRMATORY_10000_COMPLETED`
- Target dataset: `gse154778_pdac_scrna`
- Target permutations: `10000`
- Current role: `completed_statistical_strengthening_not_mechanism_validation`

## Target Tests

- `global_metrics:curl_ratio`: current p=0.0009990009990009, family FDR=0.0039960039960036, current n=1000, confirmatory p=9.999000099990002e-05, confirmatory FDR=0.0003999600039996, confirmatory n=10000, confirmatory status `completed_10000`.
- `node_frustration:Myeloid`: current p=0.0009990009990009, family FDR=0.0019980019980018, current n=1000, confirmatory p=9.999000099990002e-05, confirmatory FDR=0.0001999800019998, confirmatory n=10000, confirmatory status `completed_10000`.
- `edge_sheaf_energy:Myeloid->Tumor/Epithelial`: current p=0.0009990009990009, family FDR=0.0059940059940053, current n=1000, confirmatory p=9.999000099990002e-05, confirmatory FDR=0.0005999400059994, confirmatory n=10000, confirmatory status `completed_10000`.
- `edge_curl:Myeloid->CAF/Fibroblast`: current p=0.0009990009990009, family FDR=0.0019980019980018, current n=1000, confirmatory p=9.999000099990002e-05, confirmatory FDR=0.0001999800019998, confirmatory n=10000, confirmatory status `completed_10000`.

## Pooled Top-Source Boundary

- The pooled confirmatory summary ranks `CAF/Fibroblast` highest by raw node frustration score (`0.4305969571078318`). This pooled ranking is not automatically a manuscript claim.
- Claim gate for `CAF/Fibroblast`: `qc_warning_only`; manuscript use: `supplement_qc_only`; reason: we pre-specified minimum cell/sample support and excluded underpowered categories from biological claims.
- Myeloid remains bounded by the frozen claim gate as `supplement_only` / `supplement_context`; this supports a lesion-stratified computational hypothesis, not a main biological-driver claim.

## Interpretation Boundary

This file pre-specifies the smallest confirmatory subset for a higher-resolution 10,000-permutation pass. The current state is not allowed to promote Myeloid, curl-like, or edge-level real-data signals into biological mechanism claims. A completed 10,000-permutation run may improve statistical defensibility, but it still does not create clinical, therapeutic, or causal evidence.

## Run Command

Use `benchmarks/results/confirmatory_10000/run_confirmatory_10000_commands.sh`. Because this is a long-running computation, run it in WSL with `tmux` or `nohup`, keep Windows sleep disabled, and keep the current 1000-permutation outputs unchanged as the baseline evidence.
