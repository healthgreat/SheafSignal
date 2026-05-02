# External Comparator Inputs: gse176078_brca_scrna

These files are compact, profile-level inputs for external
cell-cell communication comparator tools. They are not raw
single-cell matrices.

## Files

- `cell_type_profiles.csv`: cell type x selected genes mean expression.
- `ligand_receptor_pairs.csv`: ligand-receptor pairs used by SheafSignal.
- `cell_type_counts.csv`: cell type counts, including lesion strata when available.
- `sheafsignal_edge_template.csv`: SheafSignal edge-level metrics for alignment.
- `external_comparator_template.csv`: expected schema for imported external results.

## External Result Schema

Fill or export a table with at least these columns:

```text
sender,receiver,score
```

Optional ligand-receptor-level columns:

```text
ligand,receptor
```

Then align it with:

```bash
python scripts/import_external_comparator.py \
  --dataset-id gse176078_brca_scrna \
  --tool LIANA \
  --input path/to/external_edges.csv \
  --sender-col sender \
  --receiver-col receiver \
  --score-col score
```

Interpretation boundary: external comparator scores represent
communication intensity or tool-specific confidence, whereas
SheafSignal `sheaf_energy` represents inconsistency between
communication flow and pathway-state gradients.
