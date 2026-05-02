#!/usr/bin/env python
"""Generate synthetic expression-to-LR-to-pathway SheafSignal recovery benchmark."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import _bootstrap  # noqa: F401
from sheafsignal.simulate import sheaf_ground_truth_edges, sheaf_ground_truth_recovery


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="benchmarks/results/simulation")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--noise-sd", type=float, action="append", default=[0.0, 0.05, 0.1])
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    all_rows = []
    for noise_sd in args.noise_sd:
        edges = sheaf_ground_truth_edges(noise_sd=noise_sd, seed=args.seed)
        edge_path = out_dir / f"sheaf_ground_truth_edges_noise_{noise_sd:g}.csv"
        edges.to_csv(edge_path, index=False)
        recovery = sheaf_ground_truth_recovery(noise_sd=noise_sd, seed=args.seed)
        recovery["edge_table"] = str(edge_path)
        all_rows.append(recovery)
    summary = pd.concat(all_rows, ignore_index=True)
    summary_path = out_dir / "sheaf_ground_truth_recovery.csv"
    summary.to_csv(summary_path, index=False)
    print(summary.to_string(index=False))
    print(f"wrote {summary_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

