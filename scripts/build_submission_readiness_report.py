#!/usr/bin/env python
"""Build a concise submission-readiness report from SheafSignal gates."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def _atomic_write_text(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _read_optional_table(path: Path, sep: str = ",") -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep=sep)


def _status_counts(gates: pd.DataFrame) -> str:
    if gates.empty:
        return "No gate table found."
    counts = gates["current_status"].value_counts().sort_index()
    return "\n".join(f"- `{status}`: {count}" for status, count in counts.items())


def _gate_rows(gates: pd.DataFrame) -> str:
    if gates.empty:
        return "No gates available."
    rows = []
    for row in gates.to_dict(orient="records"):
        rows.append(
            f"- `{row['gate_id']}` `{row['current_status']}`: "
            f"{row['claim_allowed_now']} Remaining: {row['remaining_action']}"
        )
    return "\n".join(rows)


def _comparator_summary(tool_comparison: pd.DataFrame) -> str:
    if tool_comparison.empty:
        return "No comparator table found."
    tools = ["LRProductBaseline", "LIANA", "NicheNet", "MechanisticTargetPrior"]
    rows = []
    for tool in tools:
        subset = tool_comparison.loc[
            (tool_comparison["tool"].astype(str) == tool)
            & (tool_comparison["status"].astype(str).str.startswith("completed"))
        ]
        if subset.empty:
            rows.append(f"- `{tool}`: not completed")
            continue
        datasets = sorted(subset["dataset_id"].astype(str).tolist())
        rho = pd.to_numeric(
            subset.get("spearman_sheaf_energy_vs_tool_score", pd.Series(dtype=float)),
            errors="coerce",
        )
        rho_text = "NA"
        if not rho.dropna().empty:
            rho_text = f"{float(rho.min()):.3g}-{float(rho.max()):.3g}"
        rows.append(
            f"- `{tool}`: completed for {len(datasets)} datasets "
            f"({';'.join(datasets)}); Spearman range {rho_text}"
        )
    return "\n".join(rows)


def _archive_summary(archive_manifest: pd.DataFrame) -> str:
    if archive_manifest.empty:
        return "No local release archive manifest found."
    rows = []
    for row in archive_manifest.to_dict(orient="records"):
        rows.append(
            f"- `{row['archive_target']}`: `{row['archive_path']}` "
            "(checksum and size are recorded in `release/archive_manifest.tsv`)"
        )
    return "\n".join(rows)


def build_report(
    *,
    gates: pd.DataFrame,
    tool_comparison: pd.DataFrame,
    archive_manifest: pd.DataFrame,
) -> str:
    g10 = ""
    g12 = ""
    if not gates.empty:
        g10_rows = gates.loc[gates["gate_id"] == "G10"]
        g12_rows = gates.loc[gates["gate_id"] == "G12"]
        if not g10_rows.empty:
            g10 = str(g10_rows.iloc[0]["current_status"])
        if not g12_rows.empty:
            g12 = str(g12_rows.iloc[0]["current_status"])

    return f"""# SheafSignal Submission Readiness Report

## Executive Status

- Target route: 20-50 IF computational methods manuscript.
- Local readiness: `{g12 or 'unknown'}`.
- Reproducibility release status: `{g10 or 'unknown'}`.
- Non-local blocker: Zenodo DOI is still required before submission.
- Journal route board: `manuscript/SCI20_50_ACTION_BOARD.md`.
- Nature Methods draft package: `manuscript/nature_methods_package/`.
- Final blocker gate: `manuscript/NATURE_METHODS_GO_NO_GO_REPORT.md`.
- Submission metadata templates: `manuscript/submission_metadata/`.
- Nature Methods format audit: `manuscript/NATURE_METHODS_FORMAT_AUDIT_REPORT.md`.
- Presubmission inquiry package: `manuscript/presubmission_inquiry/`.
- Post-decision response and transfer package: `manuscript/response_transfer/`.
- Figure legends and source map package: `manuscript/figure_legends/`.
- Main figure quality audit: `manuscript/figure_quality/MAIN_FIGURE_QUALITY_REPORT.md`.
- Supplementary artifact audit: `manuscript/supplementary_quality/SUPPLEMENTARY_ARTIFACT_REPORT.md`.
- Benchmark result contract audit: `benchmarks/results/BENCHMARK_RESULT_CONTRACT_REPORT.md`.
- Submission provenance audit: `manuscript/provenance/SUBMISSION_PROVENANCE_REPORT.md`.
- Method reporting and reviewer-risk audit: `manuscript/method_reporting/METHOD_REPORTING_REPORT.md`.
- Manuscript-wide claim safety audit: `manuscript/CLAIM_SAFETY_AUDIT_REPORT.md`.
- Formal SCI manuscript v1: `manuscript/SCI_MANUSCRIPT_V1.md`.
- Formal SCI manuscript v1 claim tracker: `manuscript/SCI_MANUSCRIPT_V1_claim_tracked.md`.
- Verified reference package: `manuscript/references/`.
- Polished SCI manuscript v2: `manuscript/SCI_MANUSCRIPT_V2_POLISHED.md`.
- Submission upload package: `manuscript/submission_upload_package/`.

## Gate Summary

{_status_counts(gates)}

## Gate Details

{_gate_rows(gates)}

## Comparator Evidence

{_comparator_summary(tool_comparison)}

## Local Release Archives

{_archive_summary(archive_manifest)}

## Allowed Claims

- SheafSignal reframes cell-cell communication as sheaf-valued flow with Hodge decomposition.
- The method reports communication inconsistency, feedback/curl, and harmonic/global circulation features not reducible to simple LR intensity.
- Public TME benchmarks support context-specific frustration architecture across PDAC, melanoma, and breast cancer.
- GSE154778 Myeloid can be discussed as the main claim-gated computational signal, with sparse cell types kept in supplement/QC.
- Full LIANA, bounded nichenetr-engine, and MechanisticTargetPrior comparators are available for the three public scRNA-seq benchmarks.

## Not Allowed

- Do not guarantee acceptance in any journal.
- Do not claim clinical utility, therapeutic recommendations, or treatment-response prediction.
- Do not claim full pretrained NicheNet network benchmarking unless that resource is explicitly added.
- Do not claim broad superiority over all CCC tools while CellChat, CellPhoneDB, and niche-DE remain pending.
- Do not make strong biology claims from sparse cell types or marker-dominant Visium spot labels.

## Required Before Submission

1. Upload files listed in `release/zenodo_upload_manifest.tsv` or `release/archives/sheafsignal_zenodo_upload.zip` to Zenodo.
2. Insert the minted Zenodo DOI into the data availability statement and dataset manifest.
3. Use `release/zenodo_deposition_metadata.json` and `release/ZENODO_DEPOSITION_INSTRUCTIONS.md` for deposition.
4. After DOI minting, run `python scripts/finalize_zenodo_doi.py --doi <ZENODO_DOI>`.
5. Freeze manuscript figures and rerun `python -m pytest`, `python scripts/release_audit.py`, and `python scripts/build_reproducibility_release.py`.
6. Keep `manuscript/JOURNAL_TARGETS_20_50.tsv` and `manuscript/SCI20_50_ACTION_BOARD.md` synchronized with the final target journal.
7. Update `manuscript/nature_methods_package/` after final figures, author list, and Zenodo DOI are frozen.
8. Run `python scripts/check_final_submission_blockers.py --report-only`; final submission is not allowed while the report says `NO_GO`.
9. Fill author metadata, affiliations, CRediT roles, competing interests, and submission-system metadata templates before journal upload.
10. Run `python scripts/check_nature_methods_format.py --report-only` and resolve any `FORMAT_PENDING` items.
11. Use `manuscript/presubmission_inquiry/01_presubmission_inquiry_letter.md` for a Nature Methods presubmission inquiry if the authors want editorial triage before full submission.
12. Use `manuscript/response_transfer/` after editorial feedback, review, or rejection; do not transfer to another 20-50 IF target unless the journal-specific transfer gate is marked appropriate.
13. Review `manuscript/figure_legends/03_figure_source_map.tsv` before figure assembly so every captioned claim maps to a source table and a claim boundary.
14. Run `python scripts/check_main_figure_quality.py` after regenerating figures and before rebuilding the upload package.
15. Run `python scripts/check_supplementary_artifacts.py` after regenerating supplementary figures, tables, or support files.
16. Run `python scripts/check_benchmark_result_contracts.py` after regenerating benchmark summaries or comparator imports.
17. Run `python scripts/check_submission_provenance.py` after rebuilding manuscript, figure, upload, release, or quality-gate artifacts.
18. Run `python scripts/check_method_reporting_readiness.py` before final blocker checks so reviewer-risk boundaries are current.
19. Run `python scripts/check_claim_safety.py --report-only` before every submission or rebuttal and resolve any `blocking_positive_claim` rows.
20. Use `manuscript/SCI_MANUSCRIPT_V2_POLISHED.md` as the current working manuscript and `manuscript/SCI_MANUSCRIPT_V2_POLISHED_claim_tracked.md` to audit evidence-linked claims during revision.
21. Use `manuscript/references/SCI_MANUSCRIPT_V1_referenced.md` for the reference-resolved manuscript and keep `manuscript/references/SCI_REFERENCE_GAP_REPORT.md` at `REFERENCE_PLACEHOLDERS_RESOLVED`.
22. Keep `manuscript/SCI_MANUSCRIPT_V2_EDITORIAL_AUDIT.tsv` and `manuscript/SCI_MANUSCRIPT_V2_CHANGELOG.tsv` with the manuscript package so the v2 editorial changes remain auditable.
23. Use `manuscript/submission_upload_package/` for DOCX upload artifacts, but rerun `python scripts/build_submission_upload_package.py` after any manuscript, DOI, author metadata, or release-package change.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gates", default="manuscript/SCI20_50_SUBMISSION_GATES.tsv")
    parser.add_argument(
        "--tool-comparison", default="benchmarks/results/tool_comparison.csv"
    )
    parser.add_argument("--archive-manifest", default="release/archive_manifest.tsv")
    parser.add_argument("--output", default="manuscript/SUBMISSION_READINESS_REPORT.md")
    args = parser.parse_args(argv)

    gates = _read_optional_table(Path(args.gates), sep="\t")
    tool_comparison = _read_optional_table(Path(args.tool_comparison))
    archive_manifest = _read_optional_table(Path(args.archive_manifest), sep="\t")
    report = build_report(
        gates=gates,
        tool_comparison=tool_comparison,
        archive_manifest=archive_manifest,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(output, report)
    print(f"wrote {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
