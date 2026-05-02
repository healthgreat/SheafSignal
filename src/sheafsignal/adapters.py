from __future__ import annotations

from pathlib import Path
import tarfile

import numpy as np
import pandas as pd

from .core import normalize_expression


GSE154778_MARKERS: dict[str, list[str]] = {
    "Tumor/Epithelial": ["EPCAM", "KRT8", "KRT18", "KRT19", "MUC1"],
    "CAF/Fibroblast": ["COL1A1", "COL1A2", "DCN", "LUM", "FAP"],
    "Endothelial": ["PECAM1", "VWF", "KDR", "ENG"],
    "Myeloid": ["LYZ", "CD68", "C1QA", "LST1"],
    "T/NK": ["CD3D", "CD3E", "NKG7", "GNLY"],
    "B/Plasma": ["MS4A1", "CD79A", "MZB1", "JCHAIN"],
}

GSE72056_NONMALIGNANT_CELL_TYPES = {
    1: "T/NK",
    2: "B/Plasma",
    3: "Myeloid",
    4: "Endothelial",
    5: "CAF/Fibroblast",
    6: "T/NK",
}

GSE176078_CELL_TYPE_MAP = {
    "Cancer Epithelial": "Tumor/Malignant",
    "Normal Epithelial": "Normal/Epithelial",
    "T-cells": "T/NK",
    "B-cells": "B/Plasma",
    "Plasmablasts": "B/Plasma",
    "Myeloid": "Myeloid",
    "Endothelial": "Endothelial",
    "CAFs": "CAF/Fibroblast",
    "PVL": "Perivascular",
}

GSE103322_NON_CANCER_CELL_TYPE_MAP = {
    "b cell": "B/Plasma",
    "dendritic": "Myeloid",
    "endothelial": "Endothelial",
    "fibroblast": "CAF/Fibroblast",
    "-fibroblast": "CAF/Fibroblast",
    "macrophage": "Myeloid",
    "mast": "Myeloid",
    "t cell": "T/NK",
    "myocyte": "Other/Stromal",
}


def parse_gse154778_cell_id(cell_id: str) -> dict[str, str]:
    """Parse GSE154778 cell IDs such as P01:1 or MET01:1."""
    text = str(cell_id)
    sample_id = text.split(":", 1)[0]
    if sample_id.startswith("P") and sample_id[1:].isdigit():
        lesion_type = "Primary"
    elif sample_id.startswith("MET") and sample_id[3:].isdigit():
        lesion_type = "Metastatic"
    else:
        lesion_type = "Unknown"
    return {"sample_id": sample_id, "lesion_type": lesion_type}


def parse_gse103322_cell_id(cell_id: str) -> dict[str, str]:
    """Parse GSE103322 Smart-seq2 cell IDs such as HN28_P15_D06_S330_comb."""
    text = str(cell_id)
    parts = text.split("_")
    patient_id = parts[0] if parts else "Unknown"
    sample_id = "_".join(parts[:2]) if len(parts) >= 2 else patient_id
    return {"patient_id": patient_id, "sample_id": sample_id}


def _clean_gse103322_label(value: object) -> str:
    return str(value).strip().strip("'\"")


def _normalize_gse103322_metadata_label(value: object) -> str:
    return " ".join(_clean_gse103322_label(value).split()).lower()


def _gse103322_cell_type(cancer_flag: object, non_cancer_type: object) -> str:
    cancer_code = _coerce_int_like(cancer_flag)
    if cancer_code == 1:
        return "Tumor/Malignant"
    label = _normalize_gse103322_metadata_label(non_cancer_type)
    if label in {"", "0", "nan", "none", "na"}:
        return "Unknown"
    return GSE103322_NON_CANCER_CELL_TYPE_MAP.get(label, "Unknown")


def read_gse154778_dge_matrix(raw_path: str | Path, max_cells: int | None = None) -> pd.DataFrame:
    """Read GSE154778 processed DGE CSV as cells x genes."""
    raw_path = Path(raw_path)
    if not raw_path.exists():
        raise FileNotFoundError(raw_path)

    read_kwargs: dict[str, object] = {"index_col": 0, "compression": "infer"}
    if max_cells is not None:
        if max_cells <= 0:
            raise ValueError("max_cells must be positive when provided.")
        header = pd.read_csv(raw_path, nrows=0, compression="infer")
        usecols = list(header.columns[: max_cells + 1])
        read_kwargs["usecols"] = usecols

    genes_by_cells = pd.read_csv(raw_path, **read_kwargs)
    if genes_by_cells.empty:
        raise ValueError(f"GSE154778 matrix is empty: {raw_path}")

    genes_by_cells.index = genes_by_cells.index.astype(str)
    genes_by_cells.columns = genes_by_cells.columns.astype(str)

    cells_by_genes = genes_by_cells.transpose()
    cells_by_genes.index.name = "cell_id"
    cells_by_genes = cells_by_genes.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    return cells_by_genes


def read_gse103322_selected_genes(
    raw_path: str | Path,
    genes: set[str] | list[str],
    max_cells: int | None = None,
    chunksize: int = 2000,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read selected GSE103322 gene rows and author metadata from GEO TXT."""
    raw_path = Path(raw_path)
    if not raw_path.exists():
        raise FileNotFoundError(raw_path)
    if chunksize <= 0:
        raise ValueError("chunksize must be positive.")

    gene_set = {str(gene) for gene in genes}
    metadata_rows: dict[str, pd.Series] = {}
    selected_chunks = []
    read_kwargs: dict[str, object] = {
        "sep": "\t",
        "compression": "infer",
        "chunksize": chunksize,
        "dtype": str,
    }
    if max_cells is not None:
        if max_cells <= 0:
            raise ValueError("max_cells must be positive when provided.")
        header = pd.read_csv(raw_path, sep="\t", nrows=0, compression="infer")
        read_kwargs["usecols"] = list(header.columns[: max_cells + 1])

    metadata_aliases = {
        "lymph node": "lymph_node",
        "classified as cancer cell": "classified_as_cancer_cell",
        "classified as non-cancer cells": "classified_as_non_cancer_cells",
        "non-cancer cell type": "non_cancer_cell_type",
    }
    for chunk in pd.read_csv(raw_path, **read_kwargs):
        label_col = chunk.columns[0]
        raw_labels = chunk[label_col].map(_clean_gse103322_label)
        normalized_labels = raw_labels.map(_normalize_gse103322_metadata_label)

        for normalized, canonical in metadata_aliases.items():
            matched = chunk.loc[normalized_labels == normalized]
            if not matched.empty:
                metadata_rows[canonical] = matched.iloc[0].drop(labels=[label_col])

        selected = chunk.loc[raw_labels.isin(gene_set)].copy()
        if selected.empty:
            continue
        selected[label_col] = raw_labels.loc[selected.index]
        selected = selected.set_index(label_col)
        selected = selected.apply(pd.to_numeric, errors="coerce")
        selected_chunks.append(selected)

    required_metadata = {"lymph_node", "classified_as_cancer_cell", "non_cancer_cell_type"}
    missing_metadata = required_metadata.difference(metadata_rows)
    if missing_metadata:
        raise ValueError(f"GSE103322 metadata rows were not found: {sorted(missing_metadata)}")
    if not selected_chunks:
        raise ValueError("None of the requested genes were found in GSE103322 matrix.")

    genes_by_cells = pd.concat(selected_chunks, axis=0)
    genes_by_cells = genes_by_cells.groupby(level=0).mean()
    genes_by_cells.columns = genes_by_cells.columns.astype(str)
    cells_by_genes = genes_by_cells.transpose()
    cells_by_genes.index.name = "cell_id"
    cells_by_genes = cells_by_genes.apply(pd.to_numeric, errors="coerce").fillna(0.0)

    cancer = metadata_rows["classified_as_cancer_cell"]
    lymph_node = metadata_rows["lymph_node"]
    non_cancer_type = metadata_rows["non_cancer_cell_type"]
    rows = []
    for cell_id in cells_by_genes.index.astype(str):
        parsed = parse_gse103322_cell_id(cell_id)
        lymph_node_code = _coerce_int_like(lymph_node.get(cell_id))
        rows.append(
            {
                "cell_id": cell_id,
                "cell_type": _gse103322_cell_type(cancer.get(cell_id), non_cancer_type.get(cell_id)),
                "sample_id": parsed["sample_id"],
                "patient_id": parsed["patient_id"],
                "lesion_type": "LymphNode" if lymph_node_code == 1 else "Primary",
                "lymph_node_code": lymph_node_code if lymph_node_code is not None else pd.NA,
                "non_cancer_cell_type_original": str(non_cancer_type.get(cell_id, "")),
                "annotation_source": "GSE103322_author_metadata",
            }
        )
    metadata = pd.DataFrame(rows)
    return cells_by_genes, metadata


def read_gse154778_selected_genes(
    raw_path: str | Path,
    genes: set[str] | list[str],
    max_cells: int | None = None,
    chunksize: int = 2000,
) -> pd.DataFrame:
    """Read only selected gene rows from GSE154778 as cells x selected genes."""
    raw_path = Path(raw_path)
    if not raw_path.exists():
        raise FileNotFoundError(raw_path)
    if chunksize <= 0:
        raise ValueError("chunksize must be positive.")

    gene_set = {str(gene) for gene in genes}
    read_kwargs: dict[str, object] = {"compression": "infer", "chunksize": chunksize}
    if max_cells is not None:
        if max_cells <= 0:
            raise ValueError("max_cells must be positive when provided.")
        header = pd.read_csv(raw_path, nrows=0, compression="infer")
        read_kwargs["usecols"] = list(header.columns[: max_cells + 1])

    selected_chunks = []
    for chunk in pd.read_csv(raw_path, **read_kwargs):
        gene_col = chunk.columns[0]
        chunk[gene_col] = chunk[gene_col].astype(str)
        selected = chunk.loc[chunk[gene_col].isin(gene_set)].copy()
        if selected.empty:
            continue
        selected = selected.set_index(gene_col)
        selected_chunks.append(selected)

    if not selected_chunks:
        raise ValueError("None of the requested genes were found in GSE154778 matrix.")

    genes_by_cells = pd.concat(selected_chunks, axis=0)
    genes_by_cells = genes_by_cells.groupby(level=0).mean()
    genes_by_cells.columns = genes_by_cells.columns.astype(str)
    cells_by_genes = genes_by_cells.transpose()
    cells_by_genes.index.name = "cell_id"
    cells_by_genes = cells_by_genes.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    return cells_by_genes


def _coerce_int_like(value: object) -> int | None:
    try:
        if pd.isna(value):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _gse72056_cell_type(malignant_code: int | None, non_malignant_code: int | None) -> str:
    if malignant_code == 2:
        return "Tumor/Malignant"
    if malignant_code == 1:
        return GSE72056_NONMALIGNANT_CELL_TYPES.get(non_malignant_code or -1, "Unknown")
    return "Unknown"


def read_gse72056_selected_genes(
    raw_path: str | Path,
    genes: set[str] | list[str],
    max_cells: int | None = None,
    chunksize: int = 2000,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read selected GSE72056 gene rows and author-provided cell metadata."""
    raw_path = Path(raw_path)
    if not raw_path.exists():
        raise FileNotFoundError(raw_path)
    if chunksize <= 0:
        raise ValueError("chunksize must be positive.")

    read_kwargs: dict[str, object] = {"sep": "\t", "compression": "infer", "chunksize": chunksize}
    if max_cells is not None:
        if max_cells <= 0:
            raise ValueError("max_cells must be positive when provided.")
        header = pd.read_csv(raw_path, sep="\t", nrows=0, compression="infer")
        read_kwargs["usecols"] = list(header.columns[: max_cells + 1])

    gene_set = {str(gene) for gene in genes}
    metadata_rows: dict[str, pd.Series] = {}
    selected_chunks = []
    for chunk in pd.read_csv(raw_path, **read_kwargs):
        label_col = chunk.columns[0]
        chunk[label_col] = chunk[label_col].astype(str)
        for label in [
            "tumor",
            "malignant(1=no,2=yes,0=unresolved)",
            "non-malignant cell type (1=T,2=B,3=Macro.4=Endo.,5=CAF;6=NK)",
        ]:
            matched = chunk.loc[chunk[label_col] == label]
            if not matched.empty:
                metadata_rows[label] = matched.iloc[0].drop(labels=[label_col])

        selected = chunk.loc[chunk[label_col].isin(gene_set)].copy()
        if selected.empty:
            continue
        selected = selected.set_index(label_col)
        selected_chunks.append(selected)

    if not metadata_rows:
        raise ValueError("GSE72056 metadata rows were not found.")
    if not selected_chunks:
        raise ValueError("None of the requested genes were found in GSE72056 matrix.")

    genes_by_cells = pd.concat(selected_chunks, axis=0)
    genes_by_cells = genes_by_cells.groupby(level=0).mean()
    genes_by_cells.columns = genes_by_cells.columns.astype(str)
    cells_by_genes = genes_by_cells.transpose()
    cells_by_genes.index.name = "cell_id"
    cells_by_genes = cells_by_genes.apply(pd.to_numeric, errors="coerce").fillna(0.0)

    tumor = metadata_rows["tumor"]
    malignant = metadata_rows["malignant(1=no,2=yes,0=unresolved)"]
    non_malignant = metadata_rows[
        "non-malignant cell type (1=T,2=B,3=Macro.4=Endo.,5=CAF;6=NK)"
    ]
    rows = []
    for cell_id in cells_by_genes.index.astype(str):
        tumor_code = _coerce_int_like(tumor.get(cell_id))
        malignant_code = _coerce_int_like(malignant.get(cell_id))
        non_malignant_code = _coerce_int_like(non_malignant.get(cell_id))
        rows.append(
            {
                "cell_id": cell_id,
                "cell_type": _gse72056_cell_type(malignant_code, non_malignant_code),
                "sample_id": f"Mel{tumor_code}" if tumor_code is not None else "Unknown",
                "tumor_id": tumor_code if tumor_code is not None else pd.NA,
                "malignant_code": malignant_code if malignant_code is not None else pd.NA,
                "non_malignant_code": (
                    non_malignant_code if non_malignant_code is not None else pd.NA
                ),
                "annotation_source": "GSE72056_author_metadata",
            }
        )
    metadata = pd.DataFrame(rows)
    return cells_by_genes, metadata


def _find_tar_member(tar: tarfile.TarFile, suffix: str) -> tarfile.TarInfo:
    matches = [member for member in tar.getmembers() if member.name.endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one archive member ending with {suffix!r}.")
    return matches[0]


def _read_tar_lines(tar: tarfile.TarFile, suffix: str) -> list[str]:
    member = _find_tar_member(tar, suffix)
    handle = tar.extractfile(member)
    if handle is None:
        raise FileNotFoundError(member.name)
    return [line.decode("utf-8").rstrip("\n").split("\t")[0] for line in handle]


def _read_tar_csv(tar: tarfile.TarFile, suffix: str) -> pd.DataFrame:
    member = _find_tar_member(tar, suffix)
    handle = tar.extractfile(member)
    if handle is None:
        raise FileNotFoundError(member.name)
    return pd.read_csv(handle)


def _gse176078_metadata(raw_metadata: pd.DataFrame, barcodes: list[str]) -> pd.DataFrame:
    metadata = raw_metadata.copy()
    first_col = metadata.columns[0]
    if first_col != "cell_id":
        metadata = metadata.rename(columns={first_col: "cell_id"})
    metadata["cell_id"] = metadata["cell_id"].astype(str)
    metadata = metadata.set_index("cell_id").reindex(barcodes).reset_index()
    metadata["celltype_major"] = metadata["celltype_major"].fillna("Unknown")
    metadata["cell_type"] = (
        metadata["celltype_major"].map(GSE176078_CELL_TYPE_MAP).fillna("Unknown")
    )
    metadata["sample_id"] = metadata["orig.ident"].fillna("Unknown").astype(str)
    metadata["subtype"] = metadata["subtype"].fillna("Unknown").astype(str)
    metadata["cell_type_original"] = metadata["celltype_major"].astype(str)
    metadata["annotation_source"] = "GSE176078_author_metadata"
    return metadata[
        [
            "cell_id",
            "cell_type",
            "sample_id",
            "subtype",
            "cell_type_original",
            "celltype_subset",
            "celltype_minor",
            "nCount_RNA",
            "nFeature_RNA",
            "percent.mito",
            "annotation_source",
        ]
    ]


def read_gse176078_selected_genes(
    raw_path: str | Path,
    genes: set[str] | list[str],
    max_cells: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read selected genes from GSE176078 tar.gz Matrix Market archive."""
    raw_path = Path(raw_path)
    if not raw_path.exists():
        raise FileNotFoundError(raw_path)
    if max_cells is not None and max_cells <= 0:
        raise ValueError("max_cells must be positive when provided.")

    gene_set = {str(gene) for gene in genes}
    with tarfile.open(raw_path, "r:gz") as tar:
        archive_genes = _read_tar_lines(tar, "count_matrix_genes.tsv")
        archive_barcodes = _read_tar_lines(tar, "count_matrix_barcodes.tsv")
        raw_metadata = _read_tar_csv(tar, "metadata.csv")
        selected_genes = sorted(gene_set.intersection(archive_genes))
        if not selected_genes:
            raise ValueError("None of the requested genes were found in GSE176078 matrix.")

        n_cells = len(archive_barcodes) if max_cells is None else min(max_cells, len(archive_barcodes))
        barcodes = archive_barcodes[:n_cells]
        expression_values = np.zeros((n_cells, len(selected_genes)), dtype=float)
        gene_to_column = {gene: idx for idx, gene in enumerate(selected_genes)}
        selected_rows = {
            row_idx: gene_to_column[gene]
            for row_idx, gene in enumerate(archive_genes, start=1)
            if gene in gene_to_column
        }

        mtx_member = _find_tar_member(tar, "count_matrix_sparse.mtx")
        mtx_handle = tar.extractfile(mtx_member)
        if mtx_handle is None:
            raise FileNotFoundError(mtx_member.name)

        header = mtx_handle.readline().decode("utf-8").strip()
        if not header.startswith("%%MatrixMarket matrix coordinate"):
            raise ValueError("GSE176078 matrix is not a Matrix Market coordinate file.")
        dims = ""
        while True:
            line = mtx_handle.readline().decode("utf-8").strip()
            if not line.startswith("%"):
                dims = line
                break
        n_gene_rows, n_barcode_cols, _ = [int(value) for value in dims.split()[:3]]
        if n_gene_rows != len(archive_genes) or n_barcode_cols != len(archive_barcodes):
            raise ValueError("GSE176078 Matrix Market dimensions do not match genes/barcodes.")

        for raw_line in mtx_handle:
            row_text, col_text, value_text = raw_line.decode("utf-8").split()[:3]
            col_idx = int(col_text)
            if col_idx > n_cells:
                if max_cells is not None:
                    break
            selected_col = selected_rows.get(int(row_text))
            if selected_col is not None:
                expression_values[col_idx - 1, selected_col] += float(value_text)

    expression = pd.DataFrame(expression_values, index=barcodes, columns=selected_genes)
    expression.index.name = "cell_id"
    metadata = _gse176078_metadata(raw_metadata, barcodes)
    return expression, metadata


def read_10x_h5_selected_genes(
    h5_path: str | Path,
    genes: set[str] | list[str],
) -> pd.DataFrame:
    """Read selected gene rows from a 10x Genomics filtered feature-barcode HDF5."""
    import h5py
    from scipy import sparse

    h5_path = Path(h5_path)
    if not h5_path.exists():
        raise FileNotFoundError(h5_path)

    gene_set = {str(gene) for gene in genes}
    with h5py.File(h5_path, "r") as h5:
        matrix = h5["matrix"]
        feature_names = [value.decode("utf-8") for value in matrix["features/name"][:]]
        barcodes = [value.decode("utf-8") for value in matrix["barcodes"][:]]
        selected = [idx for idx, name in enumerate(feature_names) if name in gene_set]
        if not selected:
            raise ValueError("None of the requested genes were found in 10x HDF5 matrix.")

        shape = tuple(int(value) for value in matrix["shape"][:])
        counts = sparse.csc_matrix(
            (matrix["data"][:], matrix["indices"][:], matrix["indptr"][:]),
            shape=shape,
        )
        selected_counts = counts[selected, :].transpose().toarray()

    selected_genes = [feature_names[idx] for idx in selected]
    expression = pd.DataFrame(selected_counts, index=barcodes, columns=selected_genes)
    expression.index.name = "cell_id"
    return expression


def read_visium_spatial_positions(spatial_tar_path: str | Path) -> pd.DataFrame:
    """Read Visium tissue positions from a 10x spatial tar.gz bundle."""
    spatial_tar_path = Path(spatial_tar_path)
    if not spatial_tar_path.exists():
        raise FileNotFoundError(spatial_tar_path)

    with tarfile.open(spatial_tar_path, "r:gz") as tar:
        member = _find_tar_member(tar, "tissue_positions_list.csv")
        handle = tar.extractfile(member)
        if handle is None:
            raise FileNotFoundError(member.name)
        positions = pd.read_csv(
            handle,
            header=None,
            names=[
                "cell_id",
                "in_tissue",
                "array_row",
                "array_col",
                "pxl_row_in_fullres",
                "pxl_col_in_fullres",
            ],
        )

    positions["cell_id"] = positions["cell_id"].astype(str)
    positions["x"] = positions["pxl_col_in_fullres"].astype(float)
    positions["y"] = positions["pxl_row_in_fullres"].astype(float)
    return positions


def annotate_cells_by_markers(
    expression: pd.DataFrame,
    markers: dict[str, list[str]] | None = None,
    margin: float = 0.05,
) -> pd.DataFrame:
    """Assign coarse cell types using mean log1p marker expression."""
    markers = markers or GSE154778_MARKERS
    if margin < 0:
        raise ValueError("margin must be non-negative.")

    log_expr = np.log1p(expression)
    score_columns: dict[str, pd.Series] = {}
    for cell_type, genes in markers.items():
        present = [gene for gene in genes if gene in log_expr.columns]
        if present:
            score_columns[cell_type] = log_expr[present].mean(axis=1)
        else:
            score_columns[cell_type] = pd.Series(0.0, index=log_expr.index)

    scores = pd.DataFrame(score_columns, index=expression.index)
    ordered = scores.to_numpy(dtype=float)
    best_idx = np.argmax(ordered, axis=1)
    best_scores = ordered[np.arange(len(scores)), best_idx]

    if ordered.shape[1] > 1:
        sorted_scores = np.sort(ordered, axis=1)
        margins = sorted_scores[:, -1] - sorted_scores[:, -2]
    else:
        margins = best_scores

    cell_types = np.array(scores.columns, dtype=object)[best_idx]
    cell_types[(best_scores <= 0) | (margins < margin)] = "Unknown"

    out = pd.DataFrame(
        {
            "cell_id": expression.index.astype(str),
            "cell_type": cell_types,
            "marker_score": best_scores,
            "marker_score_margin": margins,
        }
    )
    return out


def genes_required_for_sheafsignal(
    lr_db_path: str | Path,
    gene_set_path: str | Path,
    markers: dict[str, list[str]] | None = None,
) -> set[str]:
    """Collect genes required for marker annotation and SheafSignal scoring."""
    markers = markers or GSE154778_MARKERS
    lr_db = pd.read_csv(lr_db_path, sep=None, engine="python")
    required = set()
    for column in ["ligand", "receptor"]:
        if column in lr_db.columns:
            required.update(lr_db[column].dropna().astype(str))

    gene_set_path = Path(gene_set_path)
    for line in gene_set_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            required.add(line)

    for genes in markers.values():
        required.update(genes)
    return required


def aggregate_profiles_by_cell_type(
    expression: pd.DataFrame,
    metadata: pd.DataFrame,
    cell_type_col: str = "cell_type",
) -> pd.DataFrame:
    """Aggregate cells x genes expression to cell-type mean profiles."""
    if cell_type_col not in metadata.columns:
        raise ValueError(f"metadata must contain '{cell_type_col}'.")
    aligned = metadata.set_index("cell_id").loc[expression.index]
    profiles = expression.groupby(aligned[cell_type_col].astype(str)).mean()
    profiles.index.name = "cell_type"
    return profiles


def prepare_gse154778_pdac_profiles(
    raw_path: str | Path,
    profile_out: str | Path,
    metadata_out: str | Path,
    summary_out: str | Path,
    lr_db_path: str | Path,
    gene_set_path: str | Path,
    expression_out: str | Path | None = None,
    max_cells: int | None = None,
    marker_margin: float = 0.05,
    chunksize: int = 2000,
) -> dict[str, object]:
    """Prepare compact GSE154778 cell-type profiles for full benchmark runs."""
    required_genes = genes_required_for_sheafsignal(lr_db_path, gene_set_path)
    expression = read_gse154778_selected_genes(
        raw_path,
        genes=required_genes,
        max_cells=max_cells,
        chunksize=chunksize,
    )
    metadata = annotate_cells_by_markers(expression, margin=marker_margin)
    parsed = metadata["cell_id"].map(parse_gse154778_cell_id).apply(pd.Series)
    metadata = pd.concat([metadata, parsed], axis=1)
    profiles = aggregate_profiles_by_cell_type(expression, metadata)

    profile_out = Path(profile_out)
    metadata_out = Path(metadata_out)
    summary_out = Path(summary_out)
    profile_out.parent.mkdir(parents=True, exist_ok=True)
    metadata_out.parent.mkdir(parents=True, exist_ok=True)
    summary_out.parent.mkdir(parents=True, exist_ok=True)
    if expression_out is not None:
        expression_out = Path(expression_out)
        expression_out.parent.mkdir(parents=True, exist_ok=True)
        expression.reset_index().to_csv(expression_out, index=False)

    profiles.to_csv(profile_out)
    metadata.to_csv(metadata_out, index=False)
    summary = (
        metadata.groupby(["cell_type", "lesion_type"], dropna=False)
        .size()
        .reset_index(name="n_cells")
        .sort_values(["cell_type", "lesion_type"])
    )
    summary.to_csv(summary_out, index=False)

    status = "prepared" if expression_out is not None else "profile_prepared"
    message = (
        "Prepared selected-gene GSE154778 PDAC cell-level expression and "
        "cell-type profiles using coarse marker annotations."
        if expression_out is not None
        else "Prepared compact GSE154778 cell-type profiles without dense full expression export."
    )
    result = {
        "status": status,
        "prepared_profile": str(profile_out),
        "prepared_metadata": str(metadata_out),
        "annotation_summary": str(summary_out),
        "n_cells": int(expression.shape[0]),
        "n_genes": int(expression.shape[1]),
        "n_cell_types": int(metadata["cell_type"].nunique()),
        "message": message,
    }
    if expression_out is not None:
        result["prepared_expression"] = str(expression_out)
    return result


def prepare_gse72056_melanoma_profiles(
    raw_path: str | Path,
    profile_out: str | Path,
    metadata_out: str | Path,
    summary_out: str | Path,
    lr_db_path: str | Path,
    gene_set_path: str | Path,
    expression_out: str | Path | None = None,
    max_cells: int | None = None,
    chunksize: int = 2000,
) -> dict[str, object]:
    """Prepare compact GSE72056 melanoma profiles using author annotations."""
    required_genes = genes_required_for_sheafsignal(lr_db_path, gene_set_path)
    expression, metadata = read_gse72056_selected_genes(
        raw_path,
        genes=required_genes,
        max_cells=max_cells,
        chunksize=chunksize,
    )
    profiles = aggregate_profiles_by_cell_type(expression, metadata)

    profile_out = Path(profile_out)
    metadata_out = Path(metadata_out)
    summary_out = Path(summary_out)
    profile_out.parent.mkdir(parents=True, exist_ok=True)
    metadata_out.parent.mkdir(parents=True, exist_ok=True)
    summary_out.parent.mkdir(parents=True, exist_ok=True)
    if expression_out is not None:
        expression_out = Path(expression_out)
        expression_out.parent.mkdir(parents=True, exist_ok=True)
        expression.reset_index().to_csv(expression_out, index=False)
    profiles.to_csv(profile_out)
    metadata.to_csv(metadata_out, index=False)
    summary = (
        metadata.groupby(["cell_type"], dropna=False)
        .agg(n_cells=("cell_id", "size"), n_samples=("sample_id", "nunique"))
        .reset_index()
        .sort_values("cell_type")
    )
    summary.to_csv(summary_out, index=False)
    status = "prepared" if expression_out is not None else "profile_prepared"
    message = (
        "Prepared selected-gene GSE72056 melanoma cell-level expression and "
        "cell-type profiles using author annotations."
        if expression_out is not None
        else "Prepared compact GSE72056 melanoma profiles using author annotations."
    )
    result = {
        "status": status,
        "prepared_profile": str(profile_out),
        "prepared_metadata": str(metadata_out),
        "annotation_summary": str(summary_out),
        "n_cells": int(expression.shape[0]),
        "n_genes": int(expression.shape[1]),
        "n_cell_types": int(metadata["cell_type"].nunique()),
        "message": message,
    }
    if expression_out is not None:
        result["prepared_expression"] = str(expression_out)
    return result


def prepare_gse176078_brca_profiles(
    raw_path: str | Path,
    profile_out: str | Path,
    metadata_out: str | Path,
    summary_out: str | Path,
    lr_db_path: str | Path,
    gene_set_path: str | Path,
    expression_out: str | Path | None = None,
    max_cells: int | None = None,
) -> dict[str, object]:
    """Prepare compact GSE176078 breast cancer profiles using author annotations."""
    required_genes = genes_required_for_sheafsignal(lr_db_path, gene_set_path)
    expression, metadata = read_gse176078_selected_genes(
        raw_path,
        genes=required_genes,
        max_cells=max_cells,
    )
    profiles = aggregate_profiles_by_cell_type(expression, metadata)

    profile_out = Path(profile_out)
    metadata_out = Path(metadata_out)
    summary_out = Path(summary_out)
    profile_out.parent.mkdir(parents=True, exist_ok=True)
    metadata_out.parent.mkdir(parents=True, exist_ok=True)
    summary_out.parent.mkdir(parents=True, exist_ok=True)
    if expression_out is not None:
        expression_out = Path(expression_out)
        expression_out.parent.mkdir(parents=True, exist_ok=True)
        expression.reset_index().to_csv(expression_out, index=False)
    profiles.to_csv(profile_out)
    metadata.to_csv(metadata_out, index=False)
    summary = (
        metadata.groupby(["cell_type", "subtype"], dropna=False)
        .agg(n_cells=("cell_id", "size"), n_samples=("sample_id", "nunique"))
        .reset_index()
        .sort_values(["cell_type", "subtype"])
    )
    summary.to_csv(summary_out, index=False)
    status = "prepared" if expression_out is not None else "profile_prepared"
    message = (
        "Prepared selected-gene GSE176078 breast cancer cell-level expression "
        "and cell-type profiles using author annotations."
        if expression_out is not None
        else "Prepared compact GSE176078 breast cancer profiles using author annotations."
    )
    result = {
        "status": status,
        "prepared_profile": str(profile_out),
        "prepared_metadata": str(metadata_out),
        "annotation_summary": str(summary_out),
        "n_cells": int(expression.shape[0]),
        "n_genes": int(expression.shape[1]),
        "n_cell_types": int(metadata["cell_type"].nunique()),
        "message": message,
    }
    if expression_out is not None:
        result["prepared_expression"] = str(expression_out)
    return result


def prepare_gse103322_hnsc_profiles(
    raw_path: str | Path,
    profile_out: str | Path,
    metadata_out: str | Path,
    summary_out: str | Path,
    lr_db_path: str | Path,
    gene_set_path: str | Path,
    expression_out: str | Path | None = None,
    max_cells: int | None = None,
    chunksize: int = 2000,
) -> dict[str, object]:
    """Prepare compact GSE103322 HNSCC profiles using author metadata."""
    required_genes = genes_required_for_sheafsignal(lr_db_path, gene_set_path)
    expression, metadata = read_gse103322_selected_genes(
        raw_path,
        genes=required_genes,
        max_cells=max_cells,
        chunksize=chunksize,
    )
    profiles = aggregate_profiles_by_cell_type(expression, metadata)

    profile_out = Path(profile_out)
    metadata_out = Path(metadata_out)
    summary_out = Path(summary_out)
    profile_out.parent.mkdir(parents=True, exist_ok=True)
    metadata_out.parent.mkdir(parents=True, exist_ok=True)
    summary_out.parent.mkdir(parents=True, exist_ok=True)
    if expression_out is not None:
        expression_out = Path(expression_out)
        expression_out.parent.mkdir(parents=True, exist_ok=True)
        expression.reset_index().to_csv(expression_out, index=False)
    profiles.to_csv(profile_out)
    metadata.to_csv(metadata_out, index=False)
    summary = (
        metadata.groupby(["cell_type", "lesion_type"], dropna=False)
        .agg(n_cells=("cell_id", "size"), n_samples=("sample_id", "nunique"))
        .reset_index()
        .sort_values(["cell_type", "lesion_type"])
    )
    summary.to_csv(summary_out, index=False)
    status = "prepared" if expression_out is not None else "profile_prepared"
    message = (
        "Prepared selected-gene GSE103322 HNSCC cell-level expression and "
        "cell-type profiles using author metadata."
        if expression_out is not None
        else "Prepared compact GSE103322 HNSCC profiles using author metadata."
    )
    result = {
        "status": status,
        "prepared_profile": str(profile_out),
        "prepared_metadata": str(metadata_out),
        "annotation_summary": str(summary_out),
        "n_cells": int(expression.shape[0]),
        "n_genes": int(expression.shape[1]),
        "n_cell_types": int(metadata["cell_type"].nunique()),
        "message": message,
    }
    if expression_out is not None:
        result["prepared_expression"] = str(expression_out)
    return result


def prepare_tenx_breast_visium(
    h5_path: str | Path,
    spatial_tar_path: str | Path,
    expression_out: str | Path,
    metadata_out: str | Path,
    profile_out: str | Path,
    summary_out: str | Path,
    lr_db_path: str | Path,
    gene_set_path: str | Path,
    marker_margin: float = 0.0,
) -> dict[str, object]:
    """Prepare selected-gene 10x breast Visium spots and marker-dominant profiles."""
    required_genes = genes_required_for_sheafsignal(lr_db_path, gene_set_path)
    counts = read_10x_h5_selected_genes(h5_path, genes=required_genes)
    positions = read_visium_spatial_positions(spatial_tar_path)
    positions = positions.loc[positions["in_tissue"].astype(int) == 1].copy()

    common = counts.index.astype(str).intersection(positions["cell_id"].astype(str))
    if len(common) == 0:
        raise ValueError("No overlapping Visium barcodes between HDF5 and spatial positions.")

    expression = normalize_expression(counts.loc[common], method="cpm_log1p")
    positions = positions.set_index("cell_id").loc[common].reset_index()
    annotation = annotate_cells_by_markers(expression, margin=marker_margin)
    metadata = positions.merge(annotation, on="cell_id", how="left")
    metadata["spot_id"] = metadata["cell_id"]
    metadata["sample_id"] = "V1_Breast_Cancer_Block_A_Section_1"
    metadata["annotation_source"] = "marker-dominant Visium spot"
    metadata = metadata[
        [
            "cell_id",
            "spot_id",
            "cell_type",
            "sample_id",
            "in_tissue",
            "array_row",
            "array_col",
            "x",
            "y",
            "marker_score",
            "marker_score_margin",
            "annotation_source",
        ]
    ]
    profiles = aggregate_profiles_by_cell_type(expression, metadata)

    expression_out = Path(expression_out)
    metadata_out = Path(metadata_out)
    profile_out = Path(profile_out)
    summary_out = Path(summary_out)
    expression_out.parent.mkdir(parents=True, exist_ok=True)
    metadata_out.parent.mkdir(parents=True, exist_ok=True)
    profile_out.parent.mkdir(parents=True, exist_ok=True)
    summary_out.parent.mkdir(parents=True, exist_ok=True)

    expression.reset_index().to_csv(expression_out, index=False)
    metadata.to_csv(metadata_out, index=False)
    profiles.to_csv(profile_out)
    summary = (
        metadata.groupby("cell_type", dropna=False)
        .agg(n_spots=("cell_id", "size"), median_marker_margin=("marker_score_margin", "median"))
        .reset_index()
        .sort_values("cell_type")
    )
    summary.to_csv(summary_out, index=False)
    return {
        "status": "prepared",
        "prepared_expression": str(expression_out),
        "prepared_profile": str(profile_out),
        "prepared_metadata": str(metadata_out),
        "annotation_summary": str(summary_out),
        "n_cells": int(expression.shape[0]),
        "n_genes": int(expression.shape[1]),
        "n_cell_types": int(metadata["cell_type"].nunique()),
        "message": "Prepared selected-gene 10x breast Visium spots with marker-dominant annotations.",
    }


def prepare_gse154778_pdac(
    raw_path: str | Path,
    expression_out: str | Path,
    metadata_out: str | Path,
    max_cells: int | None = None,
    marker_margin: float = 0.05,
) -> dict[str, object]:
    """Prepare GSE154778 DGE matrix for SheafSignal."""
    expression = read_gse154778_dge_matrix(raw_path, max_cells=max_cells)
    metadata = annotate_cells_by_markers(expression, margin=marker_margin)

    parsed = metadata["cell_id"].map(parse_gse154778_cell_id).apply(pd.Series)
    metadata = pd.concat([metadata, parsed], axis=1)

    expression_out = Path(expression_out)
    metadata_out = Path(metadata_out)
    expression_out.parent.mkdir(parents=True, exist_ok=True)
    metadata_out.parent.mkdir(parents=True, exist_ok=True)

    expression.reset_index().to_csv(expression_out, index=False)
    metadata.to_csv(metadata_out, index=False)
    profiles = aggregate_profiles_by_cell_type(expression, metadata)
    profile_out = expression_out.parent / "profiles.csv"
    summary_out = expression_out.parent / "annotation_summary.csv"
    profiles.to_csv(profile_out)
    summary = (
        metadata.groupby(["cell_type", "lesion_type"], dropna=False)
        .size()
        .reset_index(name="n_cells")
        .sort_values(["cell_type", "lesion_type"])
    )
    summary.to_csv(summary_out, index=False)

    return {
        "status": "prepared",
        "prepared_expression": str(expression_out),
        "prepared_profile": str(profile_out),
        "prepared_metadata": str(metadata_out),
        "annotation_summary": str(summary_out),
        "n_cells": int(expression.shape[0]),
        "n_genes": int(expression.shape[1]),
        "n_cell_types": int(metadata["cell_type"].nunique()),
        "message": "Prepared GSE154778 genes x cells DGE matrix with marker-based coarse annotation.",
    }
