# GSE103322 Replication Supplement Report

- Decision: `GSE103322_REPLICATION_EXPLORATORY_READY_RERUN_RECOMMENDED`
- Dataset: `gse103322_hnsc_scrna`
- Cells / samples / patients: `5902` / `103` / `21`
- Cell types: `8`
- Lesion types: `LymphNode;Primary`
- Current top node frustration cell type: `Endothelial`
- Current top node frustration FDR: `0.2376237623762376`
- Global curl ratio / FDR: `0.0371630707932562` / `0.0396039603960396`
- Current permutation grade: n=`100`, strata=`missing_or_unstratified`
- LRProductBaseline Spearman: `0.24265208475734792`
- CellChat status: `missing_dependency`

## Interpretation

GSE103322 is useful as an independent HNSCC public-data workflow replication, but the current outputs are exploratory. The existing permutation tables use 100 permutations and are not sample-stratified, even though metadata contains sample and patient identifiers. Therefore GSE103322 should not be used for main-text biological source claims or primary comparator-completeness claims.

## Required Upgrade For Supplement-Grade Replication

Run `benchmarks/results/gse103322_hnsc_scrna/replication/run_gse103322_replication_1000_commands.sh` to regenerate a 1000-permutation, sample-stratified GSE103322 supplement candidate. Keep the primary comparator claim restricted to GSE72056/GSE154778/GSE176078 unless full external comparator imports are completed for GSE103322.
