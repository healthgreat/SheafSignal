#!/usr/bin/env bash
set -euo pipefail

# Long-running supplement-grade rerun. Use tmux/nohup in WSL and disable Windows sleep.
python scripts/run_tme_benchmark.py \
  --dataset-id gse103322_hnsc_scrna \
  --results-dir benchmarks/results/gse103322_replication_1000 \
  --n-permutations 1000

python scripts/build_pooled_fdr_audit.py \
  --results-root benchmarks/results/gse103322_replication_1000 \
  --output-dir benchmarks/results/gse103322_replication_1000/pooled_fdr

python scripts/build_gse103322_replication_supplement.py
