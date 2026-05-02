#!/usr/bin/env python
"""Run a transparent ligand-target prior comparator.

Author: SheafSignal contributors
Date: 2026-04-30
Method reference: NicheNet-style ligand-target activity scoring concept
implemented as an auditable curated-prior baseline, not as the nichenetr R
package.
Purpose: add a mechanistic target-program comparator that links sender ligand
expression to receiver receptor expression and receiver target-program activity.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import _bootstrap  # noqa: F401
from import_external_comparator import import_external_comparator


TOOL_NAME = "MechanisticTargetPrior"


def _atomic_write_csv(table: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    table.to_csv(tmp, index=False)
    tmp.replace(path)


def _atomic_write_json(payload: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def load_profiles(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing profile table: {path}")
    profiles = pd.read_csv(path)
    if "cell_type" in profiles.columns:
        profiles = profiles.set_index("cell_type")
    elif profiles.columns[0].startswith("Unnamed"):
        profiles = profiles.set_index(profiles.columns[0])
    else:
        profiles = profiles.set_index(profiles.columns[0])
    profiles.index = profiles.index.astype(str)
    profiles.columns = profiles.columns.astype(str)
    return profiles.apply(pd.to_numeric, errors="coerce").fillna(0.0)


def load_lr_database(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing ligand-receptor database: {path}")
    lr_db = pd.read_csv(path, sep=None, engine="python")
    required = {"ligand", "receptor"}
    missing = required.difference(lr_db.columns)
    if missing:
        raise ValueError(f"LR database is missing required columns: {sorted(missing)}")
    lr_db = lr_db.copy()
    lr_db["ligand"] = lr_db["ligand"].astype(str)
    lr_db["receptor"] = lr_db["receptor"].astype(str)
    if "weight" not in lr_db.columns:
        lr_db["weight"] = 1.0
    lr_db["weight"] = pd.to_numeric(lr_db["weight"], errors="coerce").fillna(1.0)
    return lr_db


def load_ligand_target_prior(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing ligand-target prior: {path}")
    prior = pd.read_csv(path, sep=None, engine="python")
    required = {"ligand", "target"}
    missing = required.difference(prior.columns)
    if missing:
        raise ValueError(f"Ligand-target prior is missing required columns: {sorted(missing)}")
    prior = prior.copy()
    prior["ligand"] = prior["ligand"].astype(str)
    prior["target"] = prior["target"].astype(str)
    if "weight" not in prior.columns:
        prior["weight"] = 1.0
    prior["weight"] = pd.to_numeric(prior["weight"], errors="coerce").fillna(1.0)
    return prior


def _target_program_score(
    receiver_profile: pd.Series,
    target_prior: pd.DataFrame,
) -> tuple[float, int, str]:
    present = target_prior.loc[target_prior["target"].isin(receiver_profile.index)].copy()
    if present.empty:
        return 0.0, 0, ""
    weights = present["weight"].astype(float).clip(lower=0.0)
    values = receiver_profile.loc[present["target"]].astype(float).clip(lower=0.0)
    denominator = float(weights.sum())
    if denominator <= 0.0:
        return 0.0, int(len(present)), ";".join(present["target"].astype(str).tolist())
    score = float(np.average(values.to_numpy(), weights=weights.to_numpy()))
    ranked = present.assign(target_expression=values.to_numpy()).sort_values(
        ["weight", "target_expression", "target"],
        ascending=[False, False, True],
    )
    return score, int(len(present)), ";".join(ranked["target"].head(8).astype(str).tolist())


def mechanistic_prior_edges(
    *,
    profiles: pd.DataFrame,
    lr_db: pd.DataFrame,
    ligand_target_prior: pd.DataFrame,
    sheaf_edges: pd.DataFrame,
    min_target_genes: int = 1,
) -> pd.DataFrame:
    """Score directed cell-type edges with LR expression and target activity."""
    required_edges = {"sender", "receiver"}
    missing = required_edges.difference(sheaf_edges.columns)
    if missing:
        raise ValueError(f"Sheaf edge table is missing required columns: {sorted(missing)}")
    if min_target_genes <= 0:
        raise ValueError("min_target_genes must be positive.")

    prior_by_ligand = {
        ligand: group.copy()
        for ligand, group in ligand_target_prior.groupby("ligand", sort=False)
    }
    rows: list[dict[str, object]] = []
    for edge in sheaf_edges[["sender", "receiver"]].drop_duplicates().to_dict(orient="records"):
        sender = str(edge["sender"])
        receiver = str(edge["receiver"])
        if sender not in profiles.index or receiver not in profiles.index:
            continue
        sender_profile = profiles.loc[sender]
        receiver_profile = profiles.loc[receiver]
        for lr_row in lr_db.to_dict(orient="records"):
            ligand = str(lr_row["ligand"])
            receptor = str(lr_row["receptor"])
            if ligand not in sender_profile.index or receptor not in receiver_profile.index:
                continue
            target_prior = prior_by_ligand.get(ligand)
            if target_prior is None:
                continue
            target_score, n_targets, targets = _target_program_score(
                receiver_profile,
                target_prior,
            )
            if n_targets < min_target_genes:
                continue
            ligand_expr = float(max(sender_profile[ligand], 0.0))
            receptor_expr = float(max(receiver_profile[receptor], 0.0))
            lr_weight = float(max(lr_row.get("weight", 1.0), 0.0))
            score = ligand_expr * receptor_expr * target_score * lr_weight
            if score <= 0.0:
                continue
            rows.append(
                {
                    "sender": sender,
                    "receiver": receiver,
                    "ligand": ligand,
                    "receptor": receptor,
                    "score": score,
                    "sender_ligand_expression": ligand_expr,
                    "receiver_receptor_expression": receptor_expr,
                    "receiver_target_program_score": target_score,
                    "lr_weight": lr_weight,
                    "n_targets_available": n_targets,
                    "target_genes": targets,
                    "notes": (
                        "score=sender_ligand_expression*receiver_receptor_expression*"
                        "receiver_target_program_score*lr_weight; curated prior baseline, "
                        "not nichenetr package output"
                    ),
                }
            )
    if not rows:
        raise ValueError("No positive mechanistic prior edge scores were produced.")
    return pd.DataFrame(rows).sort_values(
        ["score", "sender", "receiver", "ligand", "receptor"],
        ascending=[False, True, True, True, True],
    )


def run_mechanistic_prior_comparator(
    *,
    dataset_id: str,
    processed_dir: Path,
    benchmark_dir: Path,
    results_dir: Path,
    lr_db_path: Path,
    ligand_target_prior_path: Path,
    output_dir: Path,
    min_target_genes: int,
) -> dict[str, Path]:
    profiles = load_profiles(processed_dir / "profiles.csv")
    lr_db = load_lr_database(lr_db_path)
    prior = load_ligand_target_prior(ligand_target_prior_path)
    sheaf_edge_path = benchmark_dir / "results" / "sheaf_energy_by_edge.csv"
    if not sheaf_edge_path.exists():
        raise FileNotFoundError(f"Missing SheafSignal edge table: {sheaf_edge_path}")
    sheaf_edges = pd.read_csv(sheaf_edge_path)

    raw = mechanistic_prior_edges(
        profiles=profiles,
        lr_db=lr_db,
        ligand_target_prior=prior,
        sheaf_edges=sheaf_edges,
        min_target_genes=min_target_genes,
    )

    raw_path = output_dir / "mechanistic_target_prior_raw_edges.csv"
    metadata_path = output_dir / "mechanistic_target_prior_metadata.json"
    _atomic_write_csv(raw, raw_path)
    _atomic_write_json(
        {
            "dataset_id": dataset_id,
            "tool": TOOL_NAME,
            "processed_dir": str(processed_dir),
            "lr_db_path": str(lr_db_path),
            "ligand_target_prior_path": str(ligand_target_prior_path),
            "min_target_genes": min_target_genes,
            "n_profiles": int(profiles.shape[0]),
            "n_profile_genes": int(profiles.shape[1]),
            "n_lr_pairs": int(lr_db.shape[0]),
            "n_prior_rows": int(prior.shape[0]),
            "n_raw_scored_rows": int(raw.shape[0]),
            "claim_boundary": (
                "Curated ligand-target prior baseline; useful as a mechanistic comparator "
                "but not a substitute for a full nichenetr/NicheNet package run."
            ),
        },
        metadata_path,
    )

    imported = import_external_comparator(
        dataset_id=dataset_id,
        tool=TOOL_NAME,
        input_path=raw_path,
        benchmark_dir=benchmark_dir,
        results_dir=results_dir,
        sender_col="sender",
        receiver_col="receiver",
        score_col="score",
        ligand_col="ligand",
        receptor_col="receptor",
        aggregate="max",
        score_ascending=False,
    )
    return {
        "raw_edges": raw_path,
        "metadata": metadata_path,
        **imported,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--processed-dir", default=None)
    parser.add_argument("--benchmark-dir", default=None)
    parser.add_argument("--results-dir", default="benchmarks/results")
    parser.add_argument("--lr-db", default="metadata/tme_ligand_receptor.csv")
    parser.add_argument(
        "--ligand-target-prior",
        default="metadata/tme_ligand_target_prior.csv",
    )
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--min-target-genes", type=int, default=1)
    args = parser.parse_args(argv)

    dataset_id = args.dataset_id
    processed_dir = Path(args.processed_dir or f"data/processed/{dataset_id}")
    benchmark_dir = Path(args.benchmark_dir or f"benchmarks/results/{dataset_id}")
    output_dir = Path(
        args.output_dir or benchmark_dir / "comparators" / "mechanistic_target_prior_run"
    )
    paths = run_mechanistic_prior_comparator(
        dataset_id=dataset_id,
        processed_dir=processed_dir,
        benchmark_dir=benchmark_dir,
        results_dir=Path(args.results_dir),
        lr_db_path=Path(args.lr_db),
        ligand_target_prior_path=Path(args.ligand_target_prior),
        output_dir=output_dir,
        min_target_genes=args.min_target_genes,
    )
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
