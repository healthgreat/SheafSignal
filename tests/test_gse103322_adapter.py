import gzip
from pathlib import Path

import pandas as pd

from sheafsignal.adapters import (
    parse_gse103322_cell_id,
    prepare_gse103322_hnsc_profiles,
    read_gse103322_selected_genes,
)


def _write_gse103322_fixture(path: Path) -> None:
    rows = [
        ["", "HN28_P15_D06_S330_comb", "HN28_P6_G05_S173_comb", "HN26_P14_D11_S239_comb"],
        ["processed by Maxima enzyme", "1", "1", "1"],
        ["Lymph node", "1", "0", "1"],
        ["classified  as cancer cell", "0", "0", "1"],
        ["classified as non-cancer cells", "1", "1", "0"],
        ["non-cancer cell type", "Fibroblast", "Macrophage", "0"],
        ["'CCL2'", "1.0", "2.0", "3.0"],
        ["'CCR2'", "4.0", "5.0", "6.0"],
        ["'LYZ'", "0.0", "7.0", "1.0"],
    ]
    text = "\n".join("\t".join(row) for row in rows) + "\n"
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write(text)


def test_parse_gse103322_cell_id_extracts_patient_and_sample():
    parsed = parse_gse103322_cell_id("HN28_P15_D06_S330_comb")

    assert parsed["patient_id"] == "HN28"
    assert parsed["sample_id"] == "HN28_P15"


def test_read_gse103322_selected_genes_parses_metadata_and_gene_symbols(tmp_path):
    raw = tmp_path / "GSE103322_HNSCC_all_data.txt.gz"
    _write_gse103322_fixture(raw)

    expression, metadata = read_gse103322_selected_genes(
        raw,
        genes={"CCL2", "CCR2", "LYZ"},
        chunksize=3,
    )

    assert list(expression.columns) == ["CCL2", "CCR2", "LYZ"]
    assert expression.loc["HN28_P6_G05_S173_comb", "LYZ"] == 7.0
    assert metadata.set_index("cell_id").loc["HN28_P15_D06_S330_comb", "cell_type"] == (
        "CAF/Fibroblast"
    )
    assert metadata.set_index("cell_id").loc["HN28_P6_G05_S173_comb", "cell_type"] == "Myeloid"
    assert metadata.set_index("cell_id").loc["HN26_P14_D11_S239_comb", "cell_type"] == (
        "Tumor/Malignant"
    )


def test_prepare_gse103322_hnsc_profiles_writes_outputs(tmp_path):
    raw = tmp_path / "GSE103322_HNSCC_all_data.txt.gz"
    _write_gse103322_fixture(raw)
    lr = tmp_path / "lr.csv"
    genes = tmp_path / "genes.txt"
    pd.DataFrame({"ligand": ["CCL2"], "receptor": ["CCR2"], "weight": [1.0]}).to_csv(
        lr,
        index=False,
    )
    genes.write_text("LYZ\n", encoding="utf-8")

    out = tmp_path / "processed"
    result = prepare_gse103322_hnsc_profiles(
        raw_path=raw,
        profile_out=out / "profiles.csv",
        metadata_out=out / "metadata.csv",
        summary_out=out / "annotation_summary.csv",
        lr_db_path=lr,
        gene_set_path=genes,
        expression_out=out / "expression.csv",
        chunksize=4,
    )

    assert result["status"] == "prepared"
    assert (out / "profiles.csv").exists()
    assert (out / "metadata.csv").exists()
    assert (out / "expression.csv").exists()
    summary = pd.read_csv(out / "annotation_summary.csv")
    assert {"cell_type", "lesion_type", "n_cells", "n_samples"}.issubset(summary.columns)
