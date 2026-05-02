# SheafSignal method note

## Biological object

SheafSignal models cell-cell communication as a flow on a biological graph:

- nodes: cell types or spatial neighborhoods
- directed edges: ligand-receptor communication from sender to receiver
- node signal: pathway or target-gene activation state
- edge signal: ligand-receptor communication strength

The key modeling assumption is that a communication edge should be locally
consistent with the pathway state change it claims to induce. A strong outgoing
LR signal with no compatible receiver pathway response receives high sheaf
energy.

## Edge-level sheaf energy

Let `x_i` be the pathway score of node `i`, and `f_ij` be the LR communication
flow from sender `i` to receiver `j`.

The MVP uses:

```text
g_ij = x_j - x_i
e_ij = w_ij * (z(log1p(f_ij)) - z(g_ij))^2
```

where `w_ij` is the communication strength scaled to `[0, 1]`. This makes weak
edges contribute less to total frustration.

## Hodge decomposition

Directed LR edges can be anti-parallel. For graph Hodge decomposition, the MVP
first collapses each unordered cell-type pair into a canonical net flow:

```text
F_{a,b} = flow(a -> b) - flow(b -> a), where a < b
```

The net flow is decomposed into:

```text
F = B^T phi + C^T psi + h
```

where:

- `B` is the node-edge incidence matrix.
- `C` is the triangle-edge boundary matrix.
- `B^T phi` is the gradient component.
- `C^T psi` is the curl component.
- `h` is the harmonic residual.

The ratios are squared-energy proportions:

```text
gradient_ratio = ||gradient||^2 / ||F||^2
curl_ratio = ||curl||^2 / ||F||^2
harmonic_ratio = ||harmonic||^2 / ||F||^2
```

## Statistical layer

The current implementation includes a first statistical layer:

- cell-label permutation for edge `sheaf_energy`
- cell-label permutation for cell-type `frustration_score`
- global permutation summaries for total sheaf energy and Hodge ratios
- Benjamini-Hochberg FDR correction across tested edges or cell types

The null model shuffles `cell_type` labels across cells while preserving label
counts. This is a useful first sanity check, but it assumes cell-level
exchangeability. In patient-derived datasets, publication analyses should
usually stratify permutations by sample, batch, tissue section, or disease
group. The CLI supports this with `--permutation-strata-col`.

The next statistical layer should add:

- LR-pair permutation within expression-matched bins
- bootstrap confidence intervals over cells or spatial spots
- patient-level or sample-level bootstrap
- stratified permutation for clinical covariates and spatial regions

For biological interpretation, p-values should be treated as exploratory unless
the null model and multiple-testing plan are pre-registered.
