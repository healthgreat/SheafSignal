from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


CELL_ID_COLUMNS = {"cell_id", "cell", "barcode", "spot_id", "sample_id"}


def read_table(path: str | Path) -> pd.DataFrame:
    """Read a CSV/TSV table with separator inference."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, sep=None, engine="python")


def read_expression(path: str | Path) -> pd.DataFrame:
    """Read a cells x genes expression matrix."""
    df = read_table(path)
    if df.empty:
        raise ValueError("Expression table is empty.")

    first_col = str(df.columns[0])
    if first_col.lower() in CELL_ID_COLUMNS:
        df = df.set_index(first_col)
    elif not pd.api.types.is_numeric_dtype(df.iloc[:, 0]):
        df = df.set_index(first_col)

    df.index = df.index.astype(str)
    df.columns = df.columns.astype(str)
    df = df.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    return df


def read_metadata(path: str | Path, cell_id_col: str = "cell_id") -> pd.DataFrame:
    """Read cell metadata and set cell IDs as the index."""
    df = read_table(path)
    if cell_id_col not in df.columns:
        raise ValueError(f"Metadata must contain '{cell_id_col}'.")
    df[cell_id_col] = df[cell_id_col].astype(str)
    return df.set_index(cell_id_col, drop=False)


def read_ligand_receptor_db(path: str | Path) -> pd.DataFrame:
    """Read a ligand-receptor database."""
    df = read_table(path)
    required = {"ligand", "receptor"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"LR database is missing required columns: {sorted(missing)}")

    df = df.copy()
    df["ligand"] = df["ligand"].astype(str)
    df["receptor"] = df["receptor"].astype(str)
    if "weight" not in df.columns:
        df["weight"] = 1.0
    df["weight"] = pd.to_numeric(df["weight"], errors="coerce").fillna(1.0)
    return df


def read_gene_set(path: str | Path) -> list[str]:
    """Read pathway genes from a one-column text/CSV/TSV file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    if path.suffix.lower() in {".csv", ".tsv"}:
        df = read_table(path)
        if "gene" in df.columns:
            values: Iterable[str] = df["gene"].astype(str)
        else:
            values = df.iloc[:, 0].astype(str)
        genes = list(values)
    else:
        genes = path.read_text(encoding="utf-8").splitlines()

    clean = []
    seen = set()
    for gene in genes:
        gene = str(gene).strip()
        if not gene or gene.startswith("#") or gene in seen:
            continue
        clean.append(gene)
        seen.add(gene)
    if not clean:
        raise ValueError("Gene set is empty after removing blank/comment lines.")
    return clean
