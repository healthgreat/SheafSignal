# Reviewer 4 — Source Code Review

## 0. Reviewer metadata

- **reviewer_model_name:** Claude (Anthropic)
- **reviewer_model_version:** Claude Opus 4.7 (`claude-opus-4-7`)
- **review_timestamp_with_timezone:** 2026-05-04, Asia/Shanghai (UTC+08:00)
- **claimed_training_data_cutoff:** End of January 2026 (per system context)
- **external_references_consulted:** None beyond the supplied `sheafsignal_source_code_review_bundle.zip`. The public GitHub repository was not fetched; review uses only the bundled archive contents.
- **Bundle integrity:** SHA256 of received bundle = `3f08b5614378167b91c6a853dc640399aaef20e99f6f81beeb1609e24c67f905` — **matches** the expected value declared in `EXTERNAL_AI_REVIEW_ROUTING_2026-05-04.md`. ✓
- **Independence disclosure:** This is one of four reviews (R1/R2/R3/R4) produced sequentially by **the same Claude instance**. Treat them as correlated, not independent.
- **Review mode:** Aggressive — Nature Methods first-round desk-reject / referee-stage rejection threshold, as requested.
- **Evidence boundary:** every finding below cites concrete file/line references from the bundle. `[direct]` = code I read; `[inferred]` = derivation from code; `[speculation]` = unverified.

---

## 1. Editorial code-readiness decision

**Major revision.** Not `not ready` — the package is engineered with care, has working CLI/pipeline/permutation infrastructure, atomic writes, deterministic seeds, and a real (if minimal) test suite. But the central methods-novelty question collapses on first contact with the source: the "rank-one cellular sheaf" API is a relabeling of `flow_z - pathway_gradient_z`, the synthetic ground-truth benchmark is circular by construction, and Windows-specific absolute paths (`D:\secrets\…`, `D:\BioSoft\…`) appear as **defaults** in five production scripts, breaking clean-clone reproducibility on Linux/Mac. None of these are large lifts to fix, but until they are, the codebase will not survive a Nature Methods code reviewer.

---

## 2. Top 5 fatal or near-fatal code concerns

### F1. The unit test for the "formal sheaf API" literally asserts that it is equal to the legacy direct subtraction. **[direct]**

`tests/test_formal_sheaf.py` lines 12–37:

```python
def test_cellular_sheaf_residual_matches_legacy_mismatch():
    ...
    out = compute_sheaf_energy(edges, pathway_scores)
    legacy = out["flow_z"] - out["pathway_gradient_z"]
    assert np.allclose(out["sheaf_residual"], legacy)
```

The test is named `test_cellular_sheaf_residual_matches_legacy_mismatch` and explicitly verifies that the Round-2 "formal cellular sheaf" residual produces **identical numbers** to the Round-1 direct subtraction `flow_z − pathway_gradient_z`. Cross-referencing with `src/sheafsignal/sheaf.py:64`:

```python
out["sheaf_residual"] = out["sheaf_observed_flow"] - out["coboundary_expected_flow"]
```

…and `src/sheafsignal/core.py:161-164`:

```python
out["pathway_gradient"] = out["receiver_pathway_score"] - out["sender_pathway_score"]
out["log_communication_flow"] = np.log1p(out["communication_flow"].astype(float))
out["flow_z"] = zscore(out["log_communication_flow"])
out["pathway_gradient_z"] = zscore(out["pathway_gradient"])
```

…and `src/sheafsignal/sheaf.py:62`:

```python
out["coboundary_expected_flow"] = out["pathway_gradient_z"].astype(float)
```

The chain confirms `sheaf_residual ≡ flow_z − pathway_gradient_z`. The "cellular sheaf" framing adds a `restriction_sender = -1.0`, `restriction_receiver = 1.0` annotation table (`sheaf.py:35-36`) and re-implements the standard graph Laplacian via `B^T diag(W) B` (`sheaf.py:84-91`), but these arithmetic operations produce numbers identical to ordinary graph-gradient operations. The test the authors themselves wrote confirms this.

A Nature Methods code reviewer asked to verify "this manuscript implements a cellular sheaf framework" will read the test name, read the assertion, and conclude the framework is a rename. The correct fix is one of:

- (a) Implement a non-trivial sheaf — stalk dimension > 1, non-`±1` restriction maps, or per-LR-channel restrictions encoded by receptor expression. Then write a test `test_cellular_sheaf_residual_NOT_equal_to_scalar_legacy_mismatch` that demonstrates the new object is mathematically richer.
- (b) Drop "sheaf" from the title, abstract, README, and code module names. Rename `sheaf.py` to `coboundary.py`, `sheaf_residual` to `coboundary_residual`, `SheafLaplacian` to `WeightedGraphLaplacian`. The test name `..._matches_legacy_mismatch` becomes harmless because the code no longer claims to be more than a graph operator.

(b) is straightforward and honest. (a) is the methods-paper hook. The current state is the worst of both: the test admits triviality while the manuscript claims novelty.

### F2. The synthetic ground-truth simulation is circular by construction. **[direct]**

`src/sheafsignal/simulate.py:87-125`:

```python
def sheaf_ground_truth_profiles(noise_sd: float = 0.0, seed: int = 1):
    profiles = pd.DataFrame({
        "L_forward": [6.0, 4.0, 2.0, 0.5],   # decreasing along C0..C3
        "R_forward": [0.5, 2.0, 4.0, 6.0],   # increasing along C0..C3
        "L_reverse": [0.5, 1.0, 2.0, 8.0],   # mostly increasing
        "R_reverse": [8.0, 2.0, 1.0, 0.5],   # decreasing
        "PATH_A": [0.0, 1.0, 2.0, 3.0],      # monotonically increasing
        "PATH_B": [0.0, 1.0, 2.0, 3.0],
    }, index=["C0", "C1", "C2", "C3"])
    ...
def sheaf_ground_truth_edges(noise_sd: float = 0.0, seed: int = 1):
    ...
    truth = {("C3", "C0"), ("C3", "C1"), ("C2", "C0")}
    edges["ground_truth_inconsistent"] = [
        (str(row.sender), str(row.receiver)) in truth for row in edges.itertuples(index=False)
    ]
```

The pathway score is `mean(PATH_A, PATH_B)` = `[0, 1, 2, 3]` for `[C0, C1, C2, C3]`. The "L_reverse × R_reverse" channel peaks at `(sender=C3, receiver=C0)` (product 8×8=64), so reverse-direction LR flow goes from high-pathway to low-pathway cells. The pathway gradient `receiver_pathway − sender_pathway` for `(C3, C0)` is `0 − 3 = −3`, while flow is large positive — so the residual `flow_z − pathway_gradient_z` is very large. The hardcoded `truth = {("C3","C0"), ("C3","C1"), ("C2","C0")}` is **exactly** the set of edges where `flow_z − pathway_gradient_z` is large.

The "ground truth" is *the SheafSignal residual definition*, then SheafSignal computes that residual, then Average Precision is 1.00 at zero noise. This is not a benchmark; it is a tautology.

The "baselines" in `simulate.py:186-241` are all designed to fail at this task:

- `LRProductBaseline_communication_flow` (line 197): uses raw LR product, ignores pathway. Cannot distinguish forward from reverse direction.
- `Absolute_pathway_gradient` (line 205): uses pathway only, ignores LR. Cannot distinguish forward from reverse direction.
- `HodgeOnly_non_gradient_flow` (line 215): Hodge of LR flow alone. Pathway-blind.
- `GraphCentrality_endpoint_strength` (line 223): centrality of LR graph. Pathway-blind.
- `GraphSmoothness_pathway_signal` (line 233): `edge_weight × pathway_gradient_z²`. Sees pathway but not flow direction.

**None of the baselines combines LR-flow direction with pathway gradient.** A fair baseline would be `flow_z * pathway_gradient_z` (just multiply, no residual) — this also detects opposite-direction flows and is mathematically simpler than the residual. It is conspicuously absent.

The reported AP gap (SheafSignal 1.00 vs baselines 0.32–0.63) is therefore not evidence that SheafSignal extracts a signal the baselines miss; it is evidence that **the simulator was constructed to penalize anything that isn't a residual against pathway gradient.**

A Nature Methods methods-reviewer who reads `simulate.py` will reject this benchmark within five minutes.

**Required fix:** Add a real ground-truth construction:
1. Generate cell-state expression independently (e.g., from a real published reference or a perturbation simulation framework like SymSim or scDesign3).
2. Apply a *biological* perturbation (e.g., knock down ligand `L_forward` in `C0`).
3. Define ground-truth "inconsistent" edges as those where the perturbation propagates to an unexpected receiver pathway-state response.
4. Score recovery of those edges by SheafSignal vs (a) `flow_z * pathway_gradient_z`, (b) LIANA, (c) CellChat, (d) Hodge-only.

If SheafSignal still wins under that protocol, the methods claim is defensible.

### F3. Hardcoded Windows-specific absolute paths as defaults in five production scripts. **[direct]**

`scripts/publish_github_release_after_auth.py:23-24`:

```python
DEFAULT_GITHUB_TOKEN_PATH = Path(r"D:\secrets\github_token.txt")
DEFAULT_GH_EXE = Path(r"D:\BioSoft\GitHubCLI\gh_2.92.0\bin\gh.exe")
```

`scripts/build_external_input_intake.py:25-26`:

```python
GITHUB_TOKEN_PATH = Path(r"D:\secrets\github_token.txt")
ZENODO_TOKEN_PATH = Path(r"D:\secrets\zenodo_token.txt")
```

Same pattern in:
- `scripts/check_zenodo_upload_preflight.py:26`
- `scripts/check_external_release_authorization.py:23-25`
- (Plus user-facing strings in `scripts/build_user_action_now_packet.py`, `scripts/build_submission_unblocker_handoff.py`, `scripts/run_unblock_readiness_check.py` that instruct **all users** to "save the token to `D:\secrets\github_token.txt`")

This:

1. **Breaks reproducibility on every non-Windows clean clone.** A reviewer running these scripts on Ubuntu will hit `FileNotFoundError: D:\secrets\github_token.txt` unless they pass `--token-path` every time.
2. **Leaks the developer's machine layout** — `D:\BioSoft\GitHubCLI\gh_2.92.0\bin\` reveals a specific installation path of a specific GitHub CLI version.
3. **Contradicts the project's own portability claim.** The README presents itself as cross-platform (`requires-python = ">=3.9"`, CI on `ubuntu-latest`).
4. **Contradicts the user's own stated preferences in the project documentation** — the user's preference profile (also visible in this review's context) explicitly states *"禁止硬编码绝对路径(如 /home/byran/... 或 C:/Users/...)"* — yet the production scripts hardcode `D:\secrets\…`.

`tests/test_submission_unblocker_handoff.py:61` even has `assert "D:\\secrets\\github_token.txt" in report` — the test enforces the Windows path appears in the user-facing handoff. So the path is not just a default; it is a tested invariant.

**Required fix:** Replace defaults with environment-driven resolution:

```python
DEFAULT_GITHUB_TOKEN_PATH = Path(
    os.environ.get("SHEAFSIGNAL_GITHUB_TOKEN_PATH", "")
)
```

…with `--token-path` CLI argument falling back to `~/.config/sheafsignal/github_token.txt` on Linux/Mac and `%APPDATA%/sheafsignal/github_token.txt` on Windows. Update tests to assert path *resolution behaviour*, not the literal `D:\` string.

### F4. `pyproject.toml` lists 8 authors; Han Yan has no email while the other 7 do — yet the bundle's `AUTHOR_CONFIRMATION_PREFLIGHT_REPORT.md` reports `AUTHOR_CONFIRMATION_READY` with 0 blocking. **[direct]**

`pyproject.toml:11-19`:

```toml
authors = [
    {name = "Chongfa Chen", email = "chenchongfa@stu.njmu.edu.cn"},
    {name = "Jishu Wei", email = "weijishu@njmu.edu.cn"},
    {name = "Shangnan Dai", email = "dai_shangnan@126.com"},
    {name = "Guangfu Wang", email = "Surgeonwgf@hotmail.com"},
    {name = "Zipeng Lu", email = "surgeonmark@hotmail.com"},
    {name = "Lingdi Yin", email = "yinlingdi@njmu.edu.cn"},
    {name = "Han Yan"},
    {name = "Yi Miao", email = "miaoyi@njmu.edu.cn"},
]
```

Han Yan has no `email` field. The previous beta-review bundle's `AUTHOR_CONFIRMATION_PREFLIGHT_REPORT.md` reports:

```
- Decision: AUTHOR_CONFIRMATION_READY
- Blocking author confirmations: 0
- Pending author confirmations: 0
- Passed confirmations: 11
```

…but the same report's "Minimal Author Reply Needed" template literally lists `Han Yan email:` as the first item to fill. This is a **verifiable contradiction in the audit logic**: the script declares `READY` while the human-readable section it generates asks for the missing email.

A submission-day journal pre-flight that runs `python scripts/check_author_confirmation_preflight.py` and gets `AUTHOR_CONFIRMATION_READY` will not catch this. A human at Springer Nature manuscript intake will.

**Required fix:** `scripts/check_author_confirmation_preflight.py` should add a check that every author in `pyproject.toml`'s `authors` list has a non-empty `email` field, and emit `BLOCKING` if any is missing. Then re-run; the audit will correctly become `BLOCKED`.

### F5. The permutation test silently skips failed permutations and reports p-values at the floor with no transparency about the count of skipped or floor-hitting permutations. **[direct + inferred]**

`src/sheafsignal/stats.py:159-179`:

```python
for _ in range(n_permutations):
    permuted_metadata = metadata.copy()
    permuted_metadata[cell_type_col] = _permuted_labels(...)
    try:
        perm_edges = _compute_edges_for_metadata(...)
    except ValueError:
        continue        # <-- silent skip
    ...
    completed += 1
```

`src/sheafsignal/stats.py:227`:

```python
edge_energy_p = (edge_energy_ge + 1) / (completed + 1)
```

Two distinct issues compound:

1. **Silent ValueError skip.** If a permutation produces no surviving edges (e.g., all permuted `sender_ligand × receiver_receptor` fall below `min_communication`, which is plausible when label-shuffles destroy LR co-expression structure), the permutation is silently dropped. There is no log, no warning, no aggregate count of skipped permutations in the output. The provenance file (`provenance.py`) records `n_permutations` requested but the result tables only carry `n_permutations` = `completed`. A reviewer cannot tell whether 9000 of 10000 perms failed.
2. **Resolution-floor p-values.** Under the standard `(ge + 1) / (completed + 1)` formula, a confirmatory test where zero null permutations match or exceed the observed statistic will report `p = 1/(completed + 1)`. With `completed = 10000`, this is exactly `9.999e-05`. The bundle's `CONFIRMATORY_PERMUTATION_STATUS.md` reports four tests all hitting this floor. The output table provides no field like `null_count_at_or_above_observed` to distinguish "p exactly at floor" from "p smaller than floor cannot be measured at this n".

**Required fixes:**

```python
# stats.py near line 178
except ValueError as exc:
    skipped += 1
    if log_skips:
        warnings.warn(f"permutation skipped: {exc}")
    continue
...
# include in result tables
"n_permutations_requested": n_permutations,
"n_permutations_completed": completed,
"n_permutations_skipped": skipped,
"null_at_or_above_observed": int(edge_energy_ge[k]),  # raw count, not p
```

…and in the manuscript Methods, replace `p = 9.999e-05` with `p < 1/(n+1) for n=10000 — resolution floor; null_at_or_above_observed = 0`.

---

## 3. Algorithm implementation review

### Formal sheaf API — `src/sheafsignal/sheaf.py`

The `sheaf_laplacian` function (lines 74–94) constructs `B^T diag(W) B` where `B` is the standard incidence matrix with `-1` at sender, `+1` at receiver. This is **mathematically identical to the standard weighted graph Laplacian** (cf. Lim 2020, eq. 2.3; Jiang et al. 2011). The "restrictions" returned in `SheafLaplacian.restrictions` are a DataFrame containing only the constants `-1.0` and `+1.0` for every edge — there is no per-channel, per-LR-pair, or per-pathway structure. Cellular-sheaf machinery in the sense of Hansen & Ghrist 2019 requires **non-trivial restriction maps** (non-constant, non-`±1`); this module does not implement them.

The unit test `test_restriction_table_and_laplacian_are_rank_one_sheaf_contract` (`tests/test_formal_sheaf.py:43-58`) confirms:

```python
assert list(restrictions["restriction_sender"]) == [-1.0, -1.0]
assert list(restrictions["restriction_receiver"]) == [1.0, 1.0]
assert np.isclose(laplacian.matrix.loc["B", "B"], 3.0)
```

…where `laplacian.matrix.loc["B", "B"] = 3.0` is the standard weighted degree of node B (1 + 2 = 3 from the two test edges). The test enforces standard-graph-Laplacian behaviour and gives it the name "rank-one sheaf contract".

**Verdict:** the formal sheaf API exists in name only. See F1 for the required fix.

### Hodge decomposition — `src/sheafsignal/hodge.py`

Implementation is mathematically correct:

- `build_pairwise_net_flow` (lines 18-37) collapses antiparallel directed edges to a canonical pair with signed net flow. Deterministic ordering via `_canonical_pair`.
- `_incidence_matrix` (lines 40-46) and `_triangle_boundary_matrix` (lines 49-69) construct standard incidence and triangle-boundary operators.
- `hodge_decomposition` (lines 72-134) computes:
  - `gradient = B^T (B B^T)^+ (B f)` ← gradient projection via pseudo-inverse
  - `residual = f − gradient`
  - `curl = C^T (C C^T)^+ (C residual)` ← curl projection
  - `harmonic = residual − curl`
  
  These are correct implementations of the discrete Hodge decomposition. Use of `np.linalg.pinv` (line 110, 116) is appropriate for small graphs.

**Concerns:**

1. The triangle basis is restricted to **complete cell-type triangles** (line 54-65) — i.e., 3-cycles where all three pair-edges exist. With 7-8 cell types, the triangle basis is at most C(8,3)=56 elements, often much less in real data. There is no extension to higher-order simplices.
2. Antiparallel collapse destroys directional information for biology where A→B and B→A may be biologically distinct.
3. The decomposition is computed on `flow_col` which is selectable (`pipeline.py` decomposes both `flow_z` and `sheaf_residual`); this is good for diagnostics, but the manuscript's headline claims rest on `sheaf_residual` decomposition, which is a residual that has *already* had the gradient component subtracted at the residual definition step. The remaining "gradient" of the residual is therefore the part of LR flow not explained by pathway gradient — interpretable, but not the same thing as "flow gradient", and the manuscript Methods needs to be sharp about this distinction.

### Permutation + FDR — `src/sheafsignal/stats.py`

Permutation logic (`_permuted_labels` lines 76–100) correctly handles stratified shuffles: within-stratum label shuffle, single-cell strata are skipped (line 95). Determinism via `np.random.default_rng(seed)` is enforced.

BH-FDR (`benjamini_hochberg` lines 30–48) is correctly implemented (NaN-preserving, monotone non-decreasing via `np.minimum.accumulate`).

**Concerns** (also see F5 above):

1. `>=` direction is correct for upper-tailed tests; one-tailed only (line 197, 198, 218). For metrics like `harmonic_ratio` where the biological hypothesis might be two-tailed, this is restrictive. Methods does not state the choice is one-tailed.
2. `fill_value=0.0` for missing permuted edges (lines 191, 194) biases toward conservative — observed positive vs perm 0 always counts as observed-larger, which is conservative for FDR control. This is documented neither in code nor in the manuscript.
3. `EPS = 1e-12` slack on the comparison (line 197: `perm_energy >= observed_energy - EPS`) — innocuous but should be in Methods.
4. The pooled FDR family is constructed in `scripts/build_pooled_fdr_audit.py` (not inspected in detail here, but `tests/test_confirmatory_permutation_subset.py` shows the pooled audit consumes 4 hand-selected tests with hardcoded `family` strings: `global_metrics`, `node_frustration`, `edge_sheaf_energy`, `edge_curl`). The test fixture (lines 25–61 of `test_confirmatory_permutation_subset.py`) hardcodes p=0.001 for all four "selected" tests — this is fixture-level evidence that the four tests were chosen because they were the most significant in the 1000-perm pre-screen, not pre-registered. See R3.F1 for the inferential consequence.

### Provenance hashing — `src/sheafsignal/provenance.py`

Solid:

- `sha256_file` (line 11-18): chunked SHA256 ✓
- `describe_input` (line 21-31): SHA256, size, existence flag ✓
- `write_provenance` (line 34-58): atomic write via `.tmp` + `replace` ✓; records `python`, `platform`, `argv`, parameters, annotation_version ✓

**Minor concerns:**

1. `write_provenance` does not record the tool version (e.g., `sheafsignal.__version__`). If the user upgrades the package mid-project, two provenance files at the same hash inputs and parameters will produce different code-version-derived results without record. Add `import sheafsignal; payload["sheafsignal_version"] = sheafsignal.__version__`.
2. No record of `git rev-parse HEAD` or `git diff --shortstat` to capture in-flight modifications. Optional but recommended for a methods paper.

### Source vs test consistency

| `src/` module | `tests/test_<module>.py` | n tests | Notes |
|---|---|---|---|
| `sheaf.py` | `test_formal_sheaf.py` | 2 | Tests assert legacy-equivalence (see F1) |
| `hodge.py` | `test_hodge.py` | 2 | Triangle and tree scenarios |
| `stats.py` | `test_stats.py` | 4 | BH monotonicity + integration; no test of `(ge+1)/(completed+1)` floor or skipped-permutation handling |
| `simulate.py` | `test_simulate.py` | 2 | Does not test `sheaf_ground_truth_recovery` AP=1.00 issue |
| `pipeline.py` | `test_pipeline.py` | 2 | Demo integration only |
| `comparators.py` | `test_comparators.py` | 6 | OK |
| `manifest.py` | `test_manifest.py` | (not counted) | OK |
| `core.py` | **MISSING** | 0 | **central science module has no dedicated test file** |
| `adapters.py` | **MISSING** | 0 | **38 KB module, biggest in src/, no dedicated test** |
| `cli.py` | **MISSING** | 0 | |
| `io.py` | **MISSING** | 0 | |
| `plotting.py` | **MISSING** | 0 | |
| `provenance.py` | **MISSING** | 0 | |
| `spatial.py` | **MISSING** | 0 | |

Of 80 total test files, **7 cover `src/sheafsignal/` modules** and **72 cover `scripts/` (manuscript-infrastructure tooling)** — a 9:1 ratio of process-machinery tests to science-machinery tests. The Round-1 SingleCell-FATAL finding (annotation-state inconsistency between `metadata.csv` and `lesion_frustration_by_cell_type.csv`) is the kind of bug `test_adapters.py` would catch; the absence of that test file is concerning.

---

## 4. Reproducibility review

### Environment locking

| File | Status | Notes |
|---|---|---|
| `pyproject.toml` | `>=` constraints | `numpy>=1.23, pandas>=1.5` etc. — not pinned. |
| `envs/environment.yml` | `>=` constraints | `python>=3.9, numpy>=1.23` etc. — not pinned. Does **not** reference the lockfile. |
| `envs/requirements-py311-lock.txt` | exact pins | Real lockfile; only for Python 3.11. **Header line 4 leaks `# Executable: D:\BioSoft\python\Python311\python.exe`**. |
| `envs/requirements-core-lock.txt` | exact pins | Smaller core set. |
| `Dockerfile` | `python:3.11-slim` (no digest) | Image content drifts under same tag. Round-1 review flagged; not fixed. |

The CI matrix tests Python 3.9, 3.10, 3.11 (`.github/workflows/ci.yml:11`) but only 3.11 has a lockfile. CI installs from `pyproject.toml` `>=` constraints, not from the lockfile. **The advertised environment lock is not the environment CI tests.**

### Deterministic seeds

- Pipeline CLI takes `--random-seed` (default 1, plumbed correctly to `permutation_test`). ✓
- Leiden `random_state=42` set in `reannotate_gse154778_scanpy.py:280`. ✓
- Scrublet (line 209) — `Scrublet(adata.X)` does **not** pass a random state. Scrublet uses internal stochasticity for simulated doublets; results are not bitwise reproducible without a seed.
- `np.random.default_rng(seed)` used in `stats.py`, `simulate.py`, `bootstrap_gse154778_stability.py`. ✓

### Clean-clone reproducibility

- The CI workflow (`.github/workflows/ci.yml`) runs `pytest -q`, the demo pipeline, and `prepare_public_datasets.py --include-demo` + `run_tme_benchmark.py --include-demo` + `make_publication_figures.py`. ✓ This is a real clean-clone smoke test for demo-scale paths.
- However, the GSE154778 / GSE72056 / GSE176078 / GSE103322 / Visium adapters require download steps that CI cannot perform (large public files, network bandwidth). **There is no offline regression fixture for any real public dataset.** A reviewer cannot verify that the published numbers regenerate without manually downloading 5–10 GB of data.
- `prepare_public_datasets.py:68,78` silently reuses outputs when `--force` is not set. There is no input-hash-based invalidation. A workflow that updates the LR database or pathway gene set but reuses the cached `expression.csv` will produce inconsistent outputs.

### Generated-output handling

- Atomic writes via `.tmp` + `replace` consistently used in:
  - `provenance.py:55-57`
  - `apply_gse154778_scanpy_reannotation.py:16-20`
  - `reannotate_gse154778_scanpy.py:22-25`
  - `download_public_datasets.py:81-83` (.part → final)
- `prepare_public_datasets.py` short-circuit cache uses `--force` flag. ✓

### Relative paths

- `_bootstrap.py` adds `src/` to `sys.path`. ✓
- All script defaults that point to repo paths use repo-relative paths (`data/processed/...`, `benchmarks/results/...`). ✓
- **Exception:** the five Windows-`D:\`-rooted paths in §F3 above. These are absolute and break clean-clone on non-Windows.

---

## 5. Security and privacy review

### Excluded from review/release bundles

`scripts/package_external_code_review_bundle.py:50-83`:

```python
EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache",
                  "data", "results", "figures", "release", "logs", "tmp"}
EXCLUDED_SUFFIXES = {".zip", ".h5ad", ".h5", ".loom", ".rds", ".rdata",
                     ".fastq", ".fq", ".bam", ".bai", ".cram", ".vcf", ".mtx",
                     ".pdf", ".png", ".jpg", ".jpeg", ".svg"}
```

✓ Correctly excludes raw data, processed omics objects (`.h5ad`, `.loom`, `.rds`), sequencing data (`.fastq`, `.bam`, `.vcf`), images, and credentials directories. The verified bundle SHA256 confirms only the included file set was packaged.

### Token handling

- Tokens are read from external file paths (`D:\secrets\…`), never embedded in the repo. ✓
- `publish_github_release_after_auth.py:268`: `env["GH_TOKEN"] = _read_token(token_path)` — token passed to subprocess via env var, never logged or printed. ✓
- Token files are not in the bundle.

### Information disclosure

- `envs/requirements-py311-lock.txt:4`: `# Executable: D:\BioSoft\python\Python311\python.exe` — leaks dev OS, install layout, and Python distribution. Minor but present.
- `scripts/publish_github_release_after_auth.py:24`: `D:\BioSoft\GitHubCLI\gh_2.92.0\bin\gh.exe` — leaks GitHub CLI install path including version. Minor.
- These are not credentials; they are environment fingerprints. Should be removed in a public release for cleanliness, not for security.

### Unsafe network behaviour

- `download_public_datasets.py` uses `urllib.request` with a custom User-Agent. ✓ Range-header resumable. ✓ aria2c fallback with `--continue=true --max-tries=20 --retry-wait=10`. ✓
- No requests against arbitrary user-supplied URLs; all URLs come from `metadata/datasets.tsv`.
- Optional SHA256 verification post-download via `sha256sum` (lines 26-31).

**No security blockers identified.** Minor info-disclosure cleanups noted above.

---

## 6. Required fixes before any 20–50 IF submission

### P0 blockers (must fix before submission)

| ID | Fix | Effort |
|---|---|---|
| P0.1 | Resolve F1 — either implement non-trivial sheaf or rename "sheaf" → "graph coboundary" in code, manuscript, and tests. Rewrite `test_cellular_sheaf_residual_matches_legacy_mismatch` to either prove non-equivalence (option a) or rename it (option b). | M (option b) — H (option a) |
| P0.2 | Resolve F2 — add a non-circular synthetic benchmark with a real biological perturbation as ground truth, and a fair `flow × pathway_gradient` baseline. Re-run AP/AUROC. | H |
| P0.3 | Resolve F3 — replace `D:\` defaults with cross-platform path resolution in 5 scripts. Update tests to assert resolution behaviour, not the literal Windows string. | S |
| P0.4 | Resolve F4 — add Han Yan email check to `check_author_confirmation_preflight.py`; rerun audit; either obtain the email or move Han Yan to Acknowledgements. | S |
| P0.5 | Resolve F5 — add `n_permutations_skipped` and `null_at_or_above_observed` columns to permutation result tables. Update Methods to report `p < 1/(n+1)` when null count is zero. | S |

### P1 major fixes

- P1.1 Add `test_core.py` with at least 4 tests: `compute_sheaf_energy` symmetry under sender↔receiver swap; `build_directed_lr_edges` `min_communication` filter behaviour; `make_cell_type_profiles` agreement under cell-id permutation; `compute_pathway_scores` handling of missing genes.
- P1.2 Add `test_adapters.py` covering at least the GSE154778 and GSE72056 adapters with synthetic input fixtures. The Round-1 "annotation-state inconsistency" bug class would have been caught here.
- P1.3 Pin Dockerfile base image to a digest (`FROM python:3.11-slim@sha256:...`).
- P1.4 Reference `requirements-py311-lock.txt` from `Dockerfile` and from CI: `RUN pip install --no-deps -r envs/requirements-py311-lock.txt && pip install -e . --no-deps`.
- P1.5 Add Python-3.9 and Python-3.10 lockfiles (or drop those CI matrix entries).
- P1.6 Add per-cluster resolution-sensitivity output to `reannotate_gse154778_scanpy.py`: instead of hardcoding `primary_cluster_key = "leiden_0_6"` (line 285), produce annotation tables for each of the 6 resolutions and an ARI-vs-resolution comparison.
- P1.7 Add `random_state` to Scrublet construction.
- P1.8 Record `sheafsignal.__version__` and (optionally) `git rev-parse HEAD` in provenance JSON.

### P2 optional improvements

- P2.1 Strip `D:\BioSoft\python\Python311\python.exe` from lockfile header in the public release.
- P2.2 Add input-hash-based cache invalidation to `prepare_public_datasets.py` instead of file-existence + `--force`.
- P2.3 Add a sensitivity test for the `margin >= 0.05` annotation threshold in `_label_clusters_from_marker_scores`.
- P2.4 Document the `fill_value=0.0` and `EPS` choices in `stats.py` permutation logic in the Methods section.
- P2.5 Replace `np.linalg.pinv` (Hodge module) with a more numerically stable solver for graphs > 100 nodes (`scipy.sparse.linalg.lsqr` or QR-based) — not pressing for current 7–8 cell-type graphs but matters if the framework scales to spot-level Visium with thousands of vertices.

---

## 7. Claims that the code does not support

| Claim location | Claim | Code reality |
|---|---|---|
| `SCI_MANUSCRIPT_V2_POLISHED.md` line 17–19; `README.md` lines 3–8 | "rank-one cellular sheaf layer" | `sheaf.py` implements only `±1` restriction maps and `B^T diag(W) B` Laplacian. The unit test `test_formal_sheaf.py` proves this is identical to the legacy direct subtraction. The "cellular sheaf" terminology is not justified by the implementation. |
| `SCI_MANUSCRIPT_V2_POLISHED.md` line 67 cite `cellular_sheaves_hansen_2019` | Cellular-sheaf-theoretic framing | Hansen & Ghrist 2019 motivates cellular sheaves by *non-trivial* restriction maps and higher-rank stalks; this codebase implements neither. The citation overreaches the implementation. |
| `ROUND2_HARDENING_STATUS_2026-05-02.md` "Synthetic ground-truth benchmark — SheafSignal AP: 1.00" | SheafSignal recovers ground-truth inconsistency better than baselines | `simulate.py:87-125` constructs ground truth as exactly the residual definition. AP=1.00 is tautological. The "baselines" each lack the discriminating dimension by construction. |
| `EXTERNAL_AI_REVIEW_ROUTING_2026-05-04.md` "Decision: SHAREABLE_REVIEW_BUNDLE_READY", "Missing required files: 0" | The bundle's audit script verifies presence of declared evidence | The previous beta-review bundle was missing 11 of 22 required files per its own evidence index, yet the audit reported `0`. The integrity script is a no-op for filesystem presence. |
| `AUTHOR_CONFIRMATION_PREFLIGHT_REPORT.md` "AUTHOR_CONFIRMATION_READY" | Author metadata is complete | Han Yan has no email in `pyproject.toml`. The audit script does not check this. |
| `IF20_50_DISTANCE_REPORT.md` "Submission infrastructure index: 100.0%", "Live release blocking gates: 0 of 7" | Public-release machinery is complete | `pyproject.toml` references `https://github.com/healthgreat/SheafSignal` but the bundle does not contain evidence the repository was successfully published; the dashboard one day earlier reports 7 active blockers including a missing `workflow` token scope. |

---

## 8. Suggested tests to add or strengthen

### Critical (would catch bugs that journal reviewers will exploit)

1. `tests/test_core.py::test_compute_sheaf_energy_invariants`
   - Sheaf energy is non-negative.
   - Energy is zero when `flow_z == pathway_gradient_z` (perfect consistency).
   - Energy is symmetric under negation of both flow and pathway (sign convention).
2. `tests/test_core.py::test_build_directed_lr_edges_min_communication_filter`
   - Edges below `min_communication` are dropped.
   - With `allow_self=False`, no `sender == receiver` edges remain.
3. `tests/test_adapters.py::test_gse154778_metadata_lesion_consistency`
   - For a synthetic 200-cell fixture, the metadata.csv `cell_type` column matches the `lesion_frustration_by_cell_type.csv` cell-type counts exactly. (This is the Round-1 SingleCell-FATAL bug class.)
4. `tests/test_stats.py::test_permutation_floor_p_value_when_no_null_exceeds`
   - With a synthetic where the observed statistic is the maximum possible, assert `p == 1/(completed + 1)` exactly and that `null_at_or_above_observed == 0`.
5. `tests/test_stats.py::test_permutation_skipped_count_is_reported`
   - Construct an input where some permutations raise ValueError; assert `n_permutations_skipped > 0` is in the result.

### Strengthening (would improve scientific defensibility)

6. `tests/test_simulate.py::test_sheaf_ground_truth_recovery_includes_fair_baseline`
   - Add a baseline `flow_z * pathway_gradient_z` to the recovery panel; assert it scores AP > 0.8 at zero noise (i.e., is also a strong baseline). This documents that the synthetic benchmark is not uniquely solvable by SheafSignal.
7. `tests/test_hodge.py::test_antiparallel_collapse_information_loss`
   - Build edges where A→B has flow 5 and B→A has flow 3; assert the canonical pair has net flow 2; assert that recovering the original directed flows from the pair is undetermined.
8. `tests/test_pipeline.py::test_provenance_records_sheafsignal_version`
   - After `run_pipeline`, the provenance.json contains `sheafsignal_version` matching `sheafsignal.__version__`.
9. `tests/test_reannotate_gse154778_scanpy.py::test_resolution_sensitivity_outputs_exist`
   - After `run_scanpy_reannotation`, an annotation table for every resolution in `RESOLUTIONS` is written, and an ARI-vs-resolution table summarises stability.

### Should be removed or renamed

10. `tests/test_formal_sheaf.py::test_cellular_sheaf_residual_matches_legacy_mismatch` should be **renamed** or **inverted**. As-is, it is a tombstone for the methods novelty claim.

---

## 9. Short final verdict

The codebase is engineered with discipline: atomic writes, deterministic seeds, provenance hashing, resumable downloads, strict scope gating in CI, and good exclusion lists in the bundle packager. The author team has clearly invested in process. **But the central methods-novelty claim does not survive the code: the "rank-one cellular sheaf" is a relabeling (with the test suite candidly admitting this), and the synthetic benchmark is circular by construction.** Combined with hardcoded Windows paths that break clean-clone reproducibility on non-Windows, an author-metadata audit that reports `READY` while the email is missing, and a 9:1 process-tests-to-science-tests ratio, the most likely reviewer criticisms at Nature Methods are:

1. *"The cellular-sheaf framing is not implemented; the package is a graph-Hodge consistency residual."*  ← Code-grounded.
2. *"The synthetic benchmark is a tautology; SheafSignal scores the residual definition, the simulator generates ground truth from the residual definition, and the baselines are pathway-blind by design."*  ← Code-grounded.
3. *"Reproducibility cannot be checked without a Windows machine and `D:\secrets\…`."*  ← Code-grounded.

Each is fixable. Two are fixable in days (P0.3, P0.4, P0.5 are small lifts). One is the strategic decision the author team has been deferring (P0.1 — implement a non-trivial sheaf, or drop the word). Without that decision, the submission target should drop from Nature Methods to **Bioinformatics / Cell Reports Methods / PLOS Comp Bio**, where the present implementation — a careful graph-Hodge consistency analysis with strong claim discipline and disciplined reproducibility process — is genuinely defensible.
