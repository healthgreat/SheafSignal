#!/usr/bin/env python
"""Generate small ground-truth Hodge simulation benchmarks."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import _bootstrap  # noqa: F401
from sheafsignal.hodge import hodge_decomposition
from sheafsignal.simulate import scenario_edges


SCENARIOS = ["gradient_chain", "triangle_curl", "harmonic_ring", "mixed"]


def expected_dominant_component(scenario: str) -> str:
    if scenario == "gradient_chain":
        return "gradient_ratio"
    if scenario == "triangle_curl":
        return "curl_ratio"
    if scenario == "harmonic_ring":
        return "harmonic_ratio"
    return "mixed"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="benchmarks/results")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--noise-sd", type=float, default=0.0)
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for scenario in SCENARIOS:
        edges = scenario_edges(scenario, seed=args.seed, noise_sd=args.noise_sd)
        edge_path = out_dir / f"{scenario}_edges.csv"
        edges.to_csv(edge_path, index=False)

        _, scores = hodge_decomposition(edges, flow_col="flow_z")
        row = {
            "scenario": scenario,
            "expected_dominant_component": expected_dominant_component(scenario),
            "edge_file": str(edge_path),
            "seed": args.seed,
            "noise_sd": args.noise_sd,
            **scores,
        }
        rows.append(row)

    summary = pd.DataFrame(rows)
    summary_path = out_dir / "simulation_component_recovery.csv"
    summary.to_csv(summary_path, index=False)
    print(summary.to_string(index=False))
    print(f"wrote {summary_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
