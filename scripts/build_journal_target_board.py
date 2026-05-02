#!/usr/bin/env python
"""Build journal-specific targeting files for the SheafSignal manuscript.

Author: SheafSignal contributors
Date: 2026-04-30
Purpose: maintain an auditable 20-50 IF journal route without overstating
publication guarantees.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


JOURNAL_ROWS = [
    {
        "priority": 1,
        "journal": "Nature Methods",
        "publisher": "Springer Nature",
        "jif_2024": 32.1,
        "five_year_jif_2024": 51.7,
        "target_role": "primary_methods_target",
        "fit_score_1_to_5": 5,
        "fit_rationale": (
            "Best fit for a reusable biological method with a new mathematical "
            "object, simulation validation, public benchmarks, and software release."
        ),
        "current_position": "best_aligned_high_risk_first_submission",
        "must_have_before_submission": (
            "Zenodo DOI; frozen figures; clear methods text; no overclaiming beyond "
            "LIANA and bounded nichenetr-engine evidence."
        ),
        "do_not_claim": (
            "Do not claim clinical utility, full pretrained NicheNet benchmarking, "
            "or broad superiority over all CCC tools."
        ),
        "metric_source_url": "https://www.nature.com/nmeth/journal-impact",
    },
    {
        "priority": 2,
        "journal": "Nature Biotechnology",
        "publisher": "Springer Nature",
        "jif_2024": 41.7,
        "five_year_jif_2024": 59.5,
        "target_role": "stretch_methods_platform_target",
        "fit_score_1_to_5": 4,
        "fit_rationale": (
            "Possible only if the manuscript is framed as a broadly reusable "
            "biotechnology/computational platform with strong external benchmarks."
        ),
        "current_position": "stretch_target_not_most_likely",
        "must_have_before_submission": (
            "Stronger user-facing package polish; possibly additional external CCC "
            "comparators or independent application breadth."
        ),
        "do_not_claim": (
            "Do not present a public-only TME case study as a validated biotechnology "
            "platform without broad adoption or prospective validation."
        ),
        "metric_source_url": "https://www.nature.com/nbt/journal-impact",
    },
    {
        "priority": 3,
        "journal": "Molecular Cancer",
        "publisher": "Springer Nature/BMC",
        "jif_2024": 33.9,
        "five_year_jif_2024": 35.9,
        "target_role": "cancer_application_route",
        "fit_score_1_to_5": 3,
        "fit_rationale": (
            "Strong IF fit, but the current package is a method-first public-data "
            "study rather than a definitive cancer-mechanism paper."
        ),
        "current_position": "possible_after_stronger_cancer_story",
        "must_have_before_submission": (
            "Sharper tumor-microenvironment biological narrative; independent "
            "annotation validation; conservative Myeloid-only GSE154778 claim."
        ),
        "do_not_claim": (
            "Do not turn sparse cell-type or Visium marker-spot findings into strong "
            "cancer mechanism conclusions."
        ),
        "metric_source_url": "https://molecular-cancer.biomedcentral.com/about",
    },
    {
        "priority": 4,
        "journal": "Nature Cancer",
        "publisher": "Springer Nature",
        "jif_2024": 28.5,
        "five_year_jif_2024": 28.6,
        "target_role": "cancer_biology_stretch_route",
        "fit_score_1_to_5": 3,
        "fit_rationale": (
            "Good disease-field visibility, but likely requires stronger cancer "
            "biology, histology, clinical, or perturbation validation than available now."
        ),
        "current_position": "not_primary_without_biology_validation",
        "must_have_before_submission": (
            "External biological validation or a much deeper public cancer atlas "
            "story; journal-specific disease relevance."
        ),
        "do_not_claim": (
            "Do not imply clinical or therapeutic relevance from computational "
            "frustration scores alone."
        ),
        "metric_source_url": "https://www.nature.com/natcancer/journal-impact",
    },
    {
        "priority": 5,
        "journal": "Nature Biomedical Engineering",
        "publisher": "Springer Nature",
        "jif_2024": 26.6,
        "five_year_jif_2024": 30.4,
        "target_role": "engineering_translation_route",
        "fit_score_1_to_5": 3,
        "fit_rationale": (
            "In IF range and method-oriented, but SheafSignal currently lacks "
            "engineering or translational validation."
        ),
        "current_position": "fallback_only_if_engineering_angle_strengthens",
        "must_have_before_submission": (
            "Clear deployable workflow, robust software documentation, and stronger "
            "evidence that the method changes biological interpretation."
        ),
        "do_not_claim": (
            "Do not frame as a biomedical engineering tool with clinical deployment "
            "readiness."
        ),
        "metric_source_url": "https://www.nature.com/natbiomedeng/journal-impact",
    },
    {
        "priority": 6,
        "journal": "Nature Machine Intelligence",
        "publisher": "Springer Nature",
        "jif_2024": 23.9,
        "five_year_jif_2024": 31.8,
        "target_role": "computational_algorithm_stretch_route",
        "fit_score_1_to_5": 2,
        "fit_rationale": (
            "Within the target IF range, but SheafSignal is currently a mathematical "
            "bioinformatics method rather than a machine-intelligence contribution."
        ),
        "current_position": "not_recommended_unless_ml_novelty_added",
        "must_have_before_submission": (
            "A stronger AI/ML primitive and ML benchmark suite, not only sheaf/Hodge "
            "bioinformatics."
        ),
        "do_not_claim": (
            "Do not relabel a sheaf/Hodge method as machine intelligence without an "
            "actual ML contribution."
        ),
        "metric_source_url": "https://www.nature.com/nature-portfolio/about/journal-metrics",
    },
]


def _atomic_write_text(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def build_journal_table() -> pd.DataFrame:
    table = pd.DataFrame(JOURNAL_ROWS)
    table["metric_basis"] = "2024 Journal Impact Factor"
    table["source_accessed_date"] = "2026-04-30"
    table["can_guarantee_acceptance"] = False
    return table[
        [
            "priority",
            "journal",
            "publisher",
            "jif_2024",
            "five_year_jif_2024",
            "metric_basis",
            "target_role",
            "fit_score_1_to_5",
            "current_position",
            "fit_rationale",
            "must_have_before_submission",
            "do_not_claim",
            "can_guarantee_acceptance",
            "metric_source_url",
            "source_accessed_date",
        ]
    ]


def build_action_board(table: pd.DataFrame) -> str:
    rows = table.sort_values(["priority", "journal"]).to_dict(orient="records")
    target_lines = []
    for row in rows:
        target_lines.append(
            f"### {row['priority']}. {row['journal']}\n\n"
            f"- 2024 JIF: {row['jif_2024']}; 5-year JIF: {row['five_year_jif_2024']}.\n"
            f"- Role: `{row['target_role']}`.\n"
            f"- Fit score: {row['fit_score_1_to_5']}/5.\n"
            f"- Current position: `{row['current_position']}`.\n"
            f"- Why it fits: {row['fit_rationale']}\n"
            f"- Must have before submission: {row['must_have_before_submission']}\n"
            f"- Boundary: {row['do_not_claim']}\n"
            f"- Metric source: {row['metric_source_url']}\n"
        )

    return """# SheafSignal 20-50 SCI Journal Action Board

## Decision

The first submission target is `Nature Methods`. It is the best-aligned 20-50
IF route because SheafSignal is a method-first contribution: a new
sheaf-valued communication-flow object, Hodge decomposition, simulations,
public tumor microenvironment benchmarks, external comparator alignments, and
reproducible software/data packaging.

This board does not guarantee acceptance. It defines the strongest defensible
submission route and the claims that must stay out of the manuscript.

## Submission Order

1. `Nature Methods` as the primary methods target.
2. `Nature Biotechnology` only as a high-risk stretch if the package is framed
   as a broadly reusable platform.
3. `Molecular Cancer` if the manuscript is rewritten around a cancer biology
   application and keeps the Myeloid claim carefully gated.
4. `Nature Cancer` only if biological validation becomes stronger.
5. `Nature Biomedical Engineering` only if the engineering/translation angle is
   strengthened.
6. `Nature Machine Intelligence` is not recommended unless a real ML primitive
   is added.

## Required Non-Negotiable Actions

1. Mint Zenodo DOI for the processed benchmark objects and archive manifests.
2. Keep GSE154778 main-text biology to the Myeloid claim-gated computational
   signal; sparse cell types remain supplement/QC only.
3. State that NicheNet evidence uses the official nichenetr scoring engine with
   a project-curated TME prior matrix, not a full pretrained NicheNet network.
4. Avoid broad superiority language over CellChat, CellPhoneDB, LIANA, NicheNet,
   and niche-DE.
5. Re-run `python -m pytest`, `python scripts/release_audit.py`,
   `python scripts/build_reproducibility_release.py`, and
   `python scripts/build_submission_readiness_report.py` after any file change.

## Target Details

""" + "\n".join(target_lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--table-out", default="manuscript/JOURNAL_TARGETS_20_50.tsv")
    parser.add_argument("--board-out", default="manuscript/SCI20_50_ACTION_BOARD.md")
    args = parser.parse_args(argv)

    table = build_journal_table()
    table_out = Path(args.table_out)
    board_out = Path(args.board_out)
    table_out.parent.mkdir(parents=True, exist_ok=True)
    board_out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(table_out, sep="\t", index=False)
    _atomic_write_text(board_out, build_action_board(table))
    print(f"wrote {table_out.resolve()}")
    print(f"wrote {board_out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
