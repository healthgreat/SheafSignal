# Benchmark design

This folder should contain benchmark scripts and result tables for the
publication version of SheafSignal.

Minimum benchmark set for a high-impact methods paper:

1. Simulation with known ground truth:
   - pure gradient flow
   - local triangular feedback loop
   - global harmonic circulation
   - mixed signals with dropout and batch effects
2. Public scRNA-seq datasets:
   - multiple tissues and disease contexts
   - manually curated cell-type annotations
   - comparison with CellChat, CellPhoneDB, NicheNet, LIANA, and niche-DE when
     applicable
3. Public spatial transcriptomics datasets:
   - spatial neighbor graph
   - distance-aware communication edges
   - tissue region stratification
4. Ablation studies:
   - without sheaf mismatch term
   - without Hodge decomposition
   - pathway gene set size sensitivity
   - LR database sensitivity
5. Runtime and scalability:
   - cells/spots
   - cell types
   - LR pairs
   - memory use

For each benchmark, record dataset accession, command, software versions,
random seed, output checksum, and expected figure/table.

## Current publication benchmark entry point

```bash
python scripts/prepare_public_datasets.py --include-demo
python scripts/run_tme_benchmark.py --include-demo
python scripts/make_publication_figures.py
```

This writes:

```text
benchmarks/results/component_recovery.csv
benchmarks/results/tool_comparison.csv
benchmarks/results/public_tme_sheafsignal_summary.csv
benchmarks/results/spatial_frustration_hotspots.csv
manuscript/figure_manifest.tsv
```

The first three scenarios are ground-truth sanity checks:

- `gradient_chain`: should be gradient dominated
- `triangle_curl`: should be curl dominated
- `harmonic_ring`: should be harmonic dominated
