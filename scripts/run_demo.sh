#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_DIR}"

python -m pip install -e ".[dev]"

sheafsignal run \
  --expression examples/demo_expression.csv \
  --metadata examples/demo_metadata.csv \
  --lr-db examples/demo_ligand_receptor.csv \
  --gene-set examples/demo_pathway_genes.txt \
  --project-dir .

python - <<'PY'
from pathlib import Path
for path in [
    Path("results/sheaf_energy_by_edge.csv"),
    Path("results/hodge_decomposition_scores.csv"),
    Path("figures/communication_curl_network.pdf"),
]:
    if not path.exists():
        raise SystemExit(f"missing expected output: {path}")
    print(f"ok: {path.resolve()}")
PY
