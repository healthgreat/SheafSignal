#!/usr/bin/env python
"""Build verified reference package for the SheafSignal SCI manuscript.

Author: SheafSignal contributors
Date: 2026-05-01
Purpose: replace manuscript reference placeholders with auditable citation keys
and maintain a DOI/source-linked reference table for journal submission.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re

import pandas as pd


OUTPUT_FILES = {
    "references_tsv": "SCI_REFERENCES_VERIFIED.tsv",
    "bibtex": "SCI_REFERENCES.bib",
    "placeholder_map": "SCI_REFERENCE_PLACEHOLDER_MAP.tsv",
    "reference_list": "SCI_REFERENCES.md",
    "gap_report": "SCI_REFERENCE_GAP_REPORT.md",
    "referenced_manuscript": "SCI_MANUSCRIPT_V1_referenced.md",
}


REFERENCE_ROWS = [
    {
        "citation_key": "cellchat_jin_2021",
        "authors": "Jin S.; Guerrero-Juarez C. F.; Zhang L.; Chang I.; Ramos R.; et al.",
        "title": "Inference and analysis of cell-cell communication using CellChat",
        "journal": "Nature Communications",
        "year": "2021",
        "volume": "12",
        "pages": "1088",
        "doi": "10.1038/s41467-021-21246-9",
        "source_url": "https://www.nature.com/articles/s41467-021-21246-9",
        "used_for": "CellChat pairwise ligand-receptor communication reference",
        "verification_status": "verified_from_publisher_page",
    },
    {
        "citation_key": "cellphonedb_efremova_2020",
        "authors": "Efremova M.; Vento-Tormo M.; Teichmann S. A.; Vento-Tormo R.",
        "title": "CellPhoneDB: inferring cell-cell communication from combined expression of multi-subunit ligand-receptor complexes",
        "journal": "Nature Protocols",
        "year": "2020",
        "volume": "15",
        "pages": "1484-1506",
        "doi": "10.1038/s41596-020-0292-x",
        "source_url": "https://www.nature.com/articles/s41596-020-0292-x",
        "used_for": "CellPhoneDB ligand-receptor complex inference reference",
        "verification_status": "verified_from_publisher_page",
    },
    {
        "citation_key": "cellphonedb_troule_2025",
        "authors": "Troule K.; Petryszak R.; Cakir B.; Cranley J.; Harasty A.; et al.",
        "title": "CellPhoneDB v5: inferring cell-cell communication from single-cell multiomics data",
        "journal": "Nature Protocols",
        "year": "2025",
        "volume": "20",
        "pages": "3412-3440",
        "doi": "10.1038/s41596-024-01137-1",
        "source_url": "https://www.nature.com/articles/s41596-024-01137-1",
        "used_for": "current CellPhoneDB protocol context",
        "verification_status": "verified_from_publisher_page",
    },
    {
        "citation_key": "nichenet_browaeys_2020",
        "authors": "Browaeys R.; Saelens W.; Saeys Y.",
        "title": "NicheNet: modeling intercellular communication by linking ligands to target genes",
        "journal": "Nature Methods",
        "year": "2020",
        "volume": "17",
        "pages": "159-162",
        "doi": "10.1038/s41592-019-0667-5",
        "source_url": "https://www.nature.com/articles/s41592-019-0667-5",
        "used_for": "NicheNet ligand-target communication reference",
        "verification_status": "verified_from_publisher_page",
    },
    {
        "citation_key": "nichenet_protocol_sangaram_2025",
        "authors": "Sang-aram C.; Browaeys R.; Seurinck R.; et al.",
        "title": "Unraveling cell-cell communication with NicheNet by inferring active ligands from transcriptomics data",
        "journal": "Nature Protocols",
        "year": "2025",
        "volume": "20",
        "pages": "1439-1467",
        "doi": "10.1038/s41596-024-01121-9",
        "source_url": "https://www.nature.com/articles/s41596-024-01121-9",
        "used_for": "current NicheNet workflow/protocol context",
        "verification_status": "verified_from_publisher_page",
    },
    {
        "citation_key": "liana_plus_dimitrov_2024",
        "authors": "Dimitrov D.; Schaefer P. S. L.; Farr E.; Rodriguez-Mier P.; Lobentanzer S.; et al.",
        "title": "LIANA+ provides an all-in-one framework for cell-cell communication inference",
        "journal": "Nature Cell Biology",
        "year": "2024",
        "volume": "26",
        "pages": "1613-1622",
        "doi": "10.1038/s41556-024-01469-w",
        "source_url": "https://www.nature.com/articles/s41556-024-01469-w",
        "used_for": "LIANA all-in-one cell-cell communication framework reference",
        "verification_status": "verified_from_publisher_page",
    },
    {
        "citation_key": "ccc_comparison_dimitrov_2022",
        "authors": "Dimitrov D.; Turei D.; Garrido-Rodriguez M.; Burmedi P. L.; Nagai J. S.; et al.",
        "title": "Comparison of methods and resources for cell-cell communication inference from single-cell RNA-Seq data",
        "journal": "Nature Communications",
        "year": "2022",
        "volume": "13",
        "pages": "3224",
        "doi": "10.1038/s41467-022-30755-0",
        "source_url": "https://www.nature.com/articles/s41467-022-30755-0",
        "used_for": "benchmarking context for CCC inference methods",
        "verification_status": "verified_from_publisher_page",
    },
    {
        "citation_key": "hodge_rank_jiang_2011",
        "authors": "Jiang X.; Lim L.-H.; Yao Y.; Ye Y.",
        "title": "Statistical ranking and combinatorial Hodge theory",
        "journal": "Mathematical Programming",
        "year": "2011",
        "volume": "127",
        "pages": "203-244",
        "doi": "10.1007/s10107-010-0419-x",
        "source_url": "https://link.springer.com/article/10.1007/s10107-010-0419-x",
        "used_for": "combinatorial Hodge decomposition of edge flows",
        "verification_status": "verified_from_publisher_page",
    },
    {
        "citation_key": "hodge_laplacians_lim_2020",
        "authors": "Lim L.-H.",
        "title": "Hodge Laplacians on Graphs",
        "journal": "SIAM Review",
        "year": "2020",
        "volume": "62",
        "pages": "685-715",
        "doi": "10.1137/18M1223101",
        "source_url": "https://epubs.siam.org/doi/10.1137/18M1223101",
        "used_for": "graph Hodge Laplacian background",
        "verification_status": "verified_from_publisher_page",
    },
    {
        "citation_key": "cellular_sheaves_hansen_2019",
        "authors": "Hansen J.; Ghrist R.",
        "title": "Toward a spectral theory of cellular sheaves",
        "journal": "Journal of Applied and Computational Topology",
        "year": "2019",
        "volume": "3",
        "pages": "315-358",
        "doi": "10.1007/s41468-019-00038-7",
        "source_url": "https://link.springer.com/article/10.1007/s41468-019-00038-7",
        "used_for": "cellular sheaf Laplacian and applied sheaf background",
        "verification_status": "verified_from_publisher_page",
    },
]


PLACEHOLDER_ROWS = [
    {
        "placeholder": "[REF: CellChat]",
        "replacement": "[@cellchat_jin_2021]",
        "citation_keys": "cellchat_jin_2021",
    },
    {
        "placeholder": "[REF: CellPhoneDB]",
        "replacement": "[@cellphonedb_efremova_2020; @cellphonedb_troule_2025]",
        "citation_keys": "cellphonedb_efremova_2020;cellphonedb_troule_2025",
    },
    {
        "placeholder": "[REF: NicheNet]",
        "replacement": "[@nichenet_browaeys_2020; @nichenet_protocol_sangaram_2025]",
        "citation_keys": "nichenet_browaeys_2020;nichenet_protocol_sangaram_2025",
    },
    {
        "placeholder": "[REF: LIANA]",
        "replacement": "[@liana_plus_dimitrov_2024]",
        "citation_keys": "liana_plus_dimitrov_2024",
    },
    {
        "placeholder": "[REF: graph Hodge decomposition]",
        "replacement": "[@hodge_rank_jiang_2011; @hodge_laplacians_lim_2020]",
        "citation_keys": "hodge_rank_jiang_2011;hodge_laplacians_lim_2020",
    },
    {
        "placeholder": "[REF: cellular sheaves]",
        "replacement": "[@cellular_sheaves_hansen_2019]",
        "citation_keys": "cellular_sheaves_hansen_2019",
    },
]


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_table_atomic(path: Path, table: pd.DataFrame) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    table.to_csv(tmp_path, sep="\t", index=False)
    tmp_path.replace(path)


def build_reference_table() -> pd.DataFrame:
    return pd.DataFrame(REFERENCE_ROWS)


def build_placeholder_map() -> pd.DataFrame:
    return pd.DataFrame(PLACEHOLDER_ROWS)


def _bibtex_entry(row: dict[str, str]) -> str:
    fields = {
        "title": row["title"],
        "author": row["authors"].replace("; ", " and "),
        "journal": row["journal"],
        "year": row["year"],
        "volume": row["volume"],
        "pages": row["pages"],
        "doi": row["doi"],
        "url": row["source_url"],
    }
    lines = [f"@article{{{row['citation_key']},"]
    for key, value in fields.items():
        lines.append(f"  {key} = {{{value}}},")
    lines.append("}")
    return "\n".join(lines)


def build_bibtex(reference_table: pd.DataFrame) -> str:
    return "\n\n".join(
        _bibtex_entry(row) for row in reference_table.to_dict(orient="records")
    ) + "\n"


def build_reference_list(reference_table: pd.DataFrame) -> str:
    lines = ["# Verified References", ""]
    for row in reference_table.to_dict(orient="records"):
        lines.append(
            f"- `{row['citation_key']}`: {row['authors']} "
            f"{row['title']}. {row['journal']} {row['volume']}, "
            f"{row['pages']} ({row['year']}). "
            f"https://doi.org/{row['doi']}"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "These references were added to resolve manuscript placeholders. Dataset-specific",
            "source citations and final journal-style formatting still require author review",
            "before submission.",
        ]
    )
    return "\n".join(lines) + "\n"


def replace_placeholders(text: str, placeholder_map: pd.DataFrame) -> str:
    output = text
    for row in placeholder_map.to_dict(orient="records"):
        placeholder = str(row["placeholder"])
        label = placeholder.removeprefix("[REF:").removesuffix("]").strip()
        pattern = r"\[REF:\s*" + r"\s+".join(re.escape(part) for part in label.split()) + r"\]"
        output = re.sub(pattern, str(row["replacement"]), output, flags=re.IGNORECASE)
    return output


def build_gap_report(referenced_text: str, placeholder_map: pd.DataFrame) -> str:
    unresolved = sorted(
        {
            re.sub(r"\s+", " ", match.strip())
            for match in re.findall(r"\[REF:[^\]]+\]", referenced_text, flags=re.IGNORECASE | re.DOTALL)
        }
    )
    expected = sorted(placeholder_map["placeholder"].astype(str).tolist())
    decision = "REFERENCE_GAPS_FOUND" if unresolved else "REFERENCE_PLACEHOLDERS_RESOLVED"
    lines = [
        "# Reference Gap Report",
        "",
        f"Decision: `{decision}`",
        "",
        f"- Placeholder mappings available: {len(expected)}",
        f"- Unresolved placeholders: {len(unresolved)}",
        "",
    ]
    if unresolved:
        lines.extend(["## Unresolved", ""])
        lines.extend(f"- `{item}`" for item in unresolved)
        lines.append("")
    lines.extend(
        [
            "## Remaining Author Tasks",
            "",
            "- Verify final journal reference style.",
            "- Add dataset-specific source citations if required by the target journal.",
            "- Confirm whether protocol references should be kept in the main text or moved to Methods/Supplement.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_package(*, output_dir: Path, manuscript_path: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {key: output_dir / name for key, name in OUTPUT_FILES.items()}
    reference_table = build_reference_table()
    placeholder_map = build_placeholder_map()
    manuscript = manuscript_path.read_text(encoding="utf-8") if manuscript_path.exists() else ""
    referenced = replace_placeholders(manuscript, placeholder_map)

    _write_table_atomic(paths["references_tsv"], reference_table)
    _write_text_atomic(paths["bibtex"], build_bibtex(reference_table))
    _write_table_atomic(paths["placeholder_map"], placeholder_map)
    _write_text_atomic(paths["reference_list"], build_reference_list(reference_table))
    _write_text_atomic(paths["referenced_manuscript"], referenced)
    _write_text_atomic(paths["gap_report"], build_gap_report(referenced, placeholder_map))
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="manuscript/references")
    parser.add_argument("--manuscript", default="manuscript/SCI_MANUSCRIPT_V1.md")
    args = parser.parse_args(argv)

    paths = build_package(output_dir=Path(args.output_dir), manuscript_path=Path(args.manuscript))
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
