from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_pipeline
from .simulate import scenario_edges


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sheafsignal")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Run the SheafSignal MVP pipeline.")
    run.add_argument("--expression", required=True, help="Cells x genes expression CSV/TSV.")
    run.add_argument("--metadata", required=True, help="Cell metadata CSV/TSV.")
    run.add_argument("--lr-db", required=True, help="Ligand-receptor database CSV/TSV.")
    run.add_argument("--gene-set", required=True, help="Pathway gene set file.")
    run.add_argument("--project-dir", default=".", help="Output project directory.")
    run.add_argument("--cell-type-col", default="cell_type", help="Metadata cell type column.")
    run.add_argument(
        "--normalize",
        default="cpm_log1p",
        choices=["cpm_log1p", "log1p", "none"],
        help="Expression normalization method.",
    )
    run.add_argument(
        "--min-communication",
        type=float,
        default=0.0,
        help="Minimum LR communication flow to keep an edge.",
    )
    run.add_argument("--allow-self", action="store_true", help="Keep autocrine self-edges.")
    run.add_argument("--no-plot", action="store_true", help="Skip PDF network plotting.")
    run.add_argument(
        "--n-permutations",
        type=int,
        default=0,
        help="Number of cell-label permutations for empirical p-values.",
    )
    run.add_argument("--random-seed", type=int, default=1, help="Random seed for permutations.")
    run.add_argument(
        "--permutation-strata-col",
        default=None,
        help="Optional metadata column for stratified cell-label permutation, such as sample_id.",
    )

    simulate = subparsers.add_parser(
        "simulate-hodge",
        help="Write a small ground-truth directed flow simulation table.",
    )
    simulate.add_argument(
        "--scenario",
        required=True,
        choices=["gradient_chain", "triangle_curl", "harmonic_ring", "mixed"],
    )
    simulate.add_argument("--output", required=True, help="Output CSV path.")
    simulate.add_argument("--seed", type=int, default=1)
    simulate.add_argument("--noise-sd", type=float, default=0.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        result = run_pipeline(
            expression_path=args.expression,
            metadata_path=args.metadata,
            lr_db_path=args.lr_db,
            gene_set_path=args.gene_set,
            project_dir=args.project_dir,
            cell_type_col=args.cell_type_col,
            normalize=args.normalize,
            min_communication=args.min_communication,
            allow_self=args.allow_self,
            make_plot=not args.no_plot,
            n_permutations=args.n_permutations,
            random_seed=args.random_seed,
            permutation_strata_col=args.permutation_strata_col,
        )
        print(f"SheafSignal finished: {result.n_edges} edges across {result.n_cell_types} cell types")
        print(f"edge results: {Path(result.edge_path).resolve()}")
        print(f"hodge scores: {Path(result.score_path).resolve()}")
        if result.figure_path is not None:
            print(f"network figure: {Path(result.figure_path).resolve()}")
        if result.edge_permutation_path is not None:
            print(f"edge permutation p-values: {Path(result.edge_permutation_path).resolve()}")
        if result.node_permutation_path is not None:
            print(f"node permutation p-values: {Path(result.node_permutation_path).resolve()}")
        if result.global_permutation_path is not None:
            print(f"global permutation p-values: {Path(result.global_permutation_path).resolve()}")
    elif args.command == "simulate-hodge":
        edges = scenario_edges(args.scenario, seed=args.seed, noise_sd=args.noise_sd)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        edges.to_csv(output, index=False)
        print(f"simulation edges: {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
