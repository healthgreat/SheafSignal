#!/usr/bin/env bash
set -euo pipefail

# Long-running confirmatory run. Use tmux/nohup in WSL and disable Windows sleep.
python scripts/run_tme_benchmark.py \
  --dataset-id gse154778_pdac_scrna \
  --results-dir benchmarks/results/confirmatory_10000 \
  --n-permutations 10000

python scripts/build_pooled_fdr_audit.py \
  --results-root benchmarks/results/confirmatory_10000 \
  --output-dir benchmarks/results/confirmatory_10000/pooled_fdr

python scripts/build_confirmatory_permutation_subset.py
