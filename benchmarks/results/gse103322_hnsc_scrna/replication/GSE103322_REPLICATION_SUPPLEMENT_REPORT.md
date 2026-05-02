# GSE103322 Replication Supplement Report

- Decision: `GSE103322_REPLICATION_SUPPLEMENT_READY`
- Dataset: `gse103322_hnsc_scrna`
- Result source: `gse103322_replication_1000`
- Cells / samples / patients: `5902` / `103` / `21`
- Cell types: `8`
- Lesion types: `LymphNode;Primary`
- Current top node frustration cell type: `Endothelial`
- Current top node frustration FDR: `0.1332001332001332`
- Global curl ratio / FDR: `0.0125320901706762` / `0.0039960039960039`
- Current permutation grade: n=`1000`, strata=`sample_id_stratified`
- LRProductBaseline Spearman: `0.24265208475734792`
- CellChat status: `missing_dependency`

## Interpretation

GSE103322 can now be used as a supplement-grade HNSCC public-data replication for workflow generality and descriptive graph-component stability. It still must remain outside primary comparator-completeness claims unless full external comparator imports are completed for this dataset.

## Required Upgrade For Supplement-Grade Replication

If the decision is already `GSE103322_REPLICATION_SUPPLEMENT_READY`, no rerun is needed for the current supplement-grade statistical gate. Keep the primary comparator claim restricted to GSE72056/GSE154778/GSE176078 unless full external comparator imports are completed for GSE103322. Otherwise run `benchmarks/results/gse103322_hnsc_scrna/replication/run_gse103322_replication_1000_commands.sh`.
