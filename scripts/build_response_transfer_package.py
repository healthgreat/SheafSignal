#!/usr/bin/env python
"""Build post-decision response and transfer materials for SheafSignal.

Author: SheafSignal contributors
Date: 2026-04-30
Purpose: keep a 20-50 IF publication route executable after presubmission
feedback, desk rejection, peer review, or transfer to another journal.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


OUTPUT_FILES = {
    "decision_tree": "00_decision_tree.md",
    "editorial_rejection_response": "01_editorial_rejection_response_template.md",
    "reviewer_response": "02_reviewer_response_skeleton.md",
    "transfer_package": "03_transfer_package_by_journal.tsv",
    "rewrite_actions": "04_target_specific_rewrite_actions.tsv",
    "do_not_claim": "05_do_not_claim_checklist.md",
}


def _read_tsv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t")


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_table_atomic(path: Path, table: pd.DataFrame) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    table.to_csv(tmp_path, sep="\t", index=False)
    tmp_path.replace(path)


def _row_for_journal(journal_targets: pd.DataFrame, journal: str) -> dict[str, object]:
    if journal_targets.empty or "journal" not in journal_targets.columns:
        return {}
    subset = journal_targets.loc[journal_targets["journal"].astype(str) == journal]
    if subset.empty:
        return {}
    return dict(subset.iloc[0])


def _value(row: dict[str, object], key: str, default: str = "not specified") -> str:
    value = row.get(key, default)
    if pd.isna(value):
        return default
    return str(value)


def _blocking_summary(final_blockers: pd.DataFrame) -> str:
    if final_blockers.empty or "severity" not in final_blockers.columns:
        return "Final blocker table not available; rerun check_final_submission_blockers.py."
    blocking = final_blockers.loc[final_blockers["severity"].astype(str) == "blocking"]
    pending = final_blockers.loc[final_blockers["severity"].astype(str) == "pending"]
    return (
        f"{len(blocking)} blocking item(s), {len(pending)} pending non-blocking "
        "item(s) in manuscript/FINAL_SUBMISSION_BLOCKERS.tsv."
    )


def build_decision_tree(
    journal_targets: pd.DataFrame,
    final_blockers: pd.DataFrame,
) -> str:
    nm = _row_for_journal(journal_targets, "Nature Methods")
    return f"""# SheafSignal Post-Decision Route Tree

## Scope

This document controls what to do after presubmission feedback, editorial
rejection, peer review, or transfer. It is not a guarantee of journal acceptance.
It is a reproducible decision rule for keeping the 20-50 IF route
evidence-bound.

## Current Primary Route

- Primary journal: `{_value(nm, "journal", "Nature Methods")}`.
- Current position: `{_value(nm, "current_position", "primary methods route")}`.
- Target role: `{_value(nm, "target_role", "primary_methods_target")}`.
- Local blocker state: {_blocking_summary(final_blockers)}

## Decision States

1. Before first submission:
   - Stop if `manuscript/NATURE_METHODS_GO_NO_GO_REPORT.md` says `NO_GO`.
   - Do not submit while Zenodo DOI, GitHub release, or author metadata are
     unresolved.

2. Presubmission inquiry receives positive scope feedback:
   - Submit the Nature Methods package with the sheaf/Hodge method as the
     first message.
   - Keep tumor microenvironment results as validation, not as clinical proof.

3. Presubmission or desk rejection says "not enough method novelty":
   - Do not argue with the editor.
   - Recheck Figure 1, abstract, cover letter, and novelty matrix for whether
     the changed mathematical object is visible within the first page.
   - Transfer only after `03_transfer_package_by_journal.tsv` marks the target
     as `transfer_ready` or `conditional_transfer`.

4. Presubmission or desk rejection says "too biological / too cancer-specific":
   - Consider `Molecular Cancer` or `Nature Cancer` only if the manuscript is
     rewritten as a conservative TME communication-frustration story.
   - Do not inflate sparse cell-type categories into mechanisms.

5. External review requests stronger benchmarking:
   - Add focused comparator or sensitivity analyses only if they directly test
     sheaf/Hodge novelty.
   - Keep full LIANA, bounded nichenetr-engine, MechanisticTargetPrior, and
     LRProductBaseline evidence separate from claims about CellChat,
     CellPhoneDB, or niche-DE.

6. Rejection after review:
   - Use `02_reviewer_response_skeleton.md` to map every criticism to a
     concrete change.
   - Use `04_target_specific_rewrite_actions.tsv` to choose the smallest
     scientifically honest rewrite for the next journal.

## Hard Stop Rules

- Never promise or imply guaranteed publication.
- Never claim clinical utility, treatment guidance, or treatment-response
  prediction.
- Never claim broad superiority over all CCC tools.
- Never make a main-text biological mechanism from sparse or unsupported
  categories.
"""


def build_editorial_rejection_response_template() -> str:
    return """# Editorial Rejection Response Template

Dear Editors,

Thank you for evaluating our manuscript, "SheafSignal maps frustration in cell
communication networks." We appreciate the editorial assessment and understand
that the manuscript is not being sent for review at this journal in its current
form.

We will use the decision to revise the positioning of the work. In particular,
we will keep the central claim focused on the sheaf-valued/Hodge formulation of
cell-cell communication consistency and will avoid claims of clinical utility,
treatment guidance, or broad superiority over all communication tools.

If the editorial decision identified a specific scope issue, we will address it
before considering any transfer or resubmission route. We do not interpret this
decision as evidence against the biological findings themselves, only as a
journal-scope and manuscript-positioning decision.

Sincerely,

TBD

## Internal Use Only

- Record the exact editor reason before rewriting.
- Do not send an appeal unless the editor made a factual error about the method
  or evidence package.
- If transferring, update the cover letter, title, abstract, figure order, and
  claim-evidence map together.
"""


def build_reviewer_response_skeleton() -> str:
    return """# Reviewer Response Skeleton

## Cover Response

We thank the reviewers for their detailed assessment. We have revised the
manuscript to clarify the mathematical contribution of SheafSignal, strengthen
benchmark transparency, and sharpen the boundaries of biological interpretation.

## Response Table Template

| Comment ID | Reviewer Comment | Response Strategy | Manuscript Change | Evidence File | Status |
|---|---|---|---|---|---|
| R1.1 | TBD | Clarify sheaf-valued flow versus pairwise LR scoring. | Abstract, Figure 1, Methods. | `manuscript/nature_methods_package/05_claim_evidence_map.tsv` | pending |
| R1.2 | TBD | Add or cite benchmark/sensitivity evidence. | Results or Supplement. | `benchmarks/results/` | pending |
| R2.1 | TBD | Downgrade unsupported biology claims. | Results, Discussion, Limitations. | `benchmarks/results/gse154778_pdac_scrna/qc/claim_gating_by_cell_type.csv` | pending |
| R2.2 | TBD | Clarify comparator boundary. | Methods, Supplementary Methods. | `benchmarks/results/tool_comparison.csv` | pending |

## Response Rules

- Every response must name the exact file or figure that changed.
- Null or weak results should be disclosed, not hidden.
- Sparse cell types remain supplementary/QC unless they pass the pre-specified
  evidence-tier filter.
- If a reviewer asks for clinical interpretation, answer that the current study
  is computational and hypothesis-generating.
"""


def build_transfer_package_by_journal(journal_targets: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if journal_targets.empty:
        journals = [
            "Nature Methods",
            "Nature Biotechnology",
            "Molecular Cancer",
            "Nature Cancer",
            "Nature Biomedical Engineering",
            "Nature Machine Intelligence",
        ]
        journal_targets = pd.DataFrame({"journal": journals})

    transfer_rules = {
        "Nature Methods": {
            "transfer_status": "primary_first_submission",
            "trigger_condition": "Use before first submission or after positive presubmission feedback.",
            "positioning_to_use": "Reusable computational method with sheaf/Hodge formulation.",
            "minimum_rewrite": "Keep method-first title, abstract, Figure 1, and cover letter.",
            "evidence_to_emphasize": "Simulation recovery, public TME benchmarks, comparator alignment, reproducibility release.",
            "evidence_to_downplay": "Cancer mechanism and clinical relevance.",
            "go_no_go_gate": "Submit only when final blocker report is not NO_GO.",
        },
        "Nature Biotechnology": {
            "transfer_status": "conditional_transfer",
            "trigger_condition": "Use only if the work can be framed as a broadly reusable computational platform.",
            "positioning_to_use": "Technology/platform method for communication-network consistency.",
            "minimum_rewrite": "Strengthen software polish, external comparators, documentation, and cross-dataset generality.",
            "evidence_to_emphasize": "Reusable package, benchmarks across cancers, public release, deterministic workflow.",
            "evidence_to_downplay": "Single disease-specific biological claims.",
            "go_no_go_gate": "No-go if only a public TME case study remains.",
        },
        "Molecular Cancer": {
            "transfer_status": "conditional_transfer",
            "trigger_condition": "Use after methods-journal rejection if cancer TME story is the strongest reviewer-facing route.",
            "positioning_to_use": "Computational discovery of TME communication frustration with conservative Myeloid focus.",
            "minimum_rewrite": "Move method proof into Methods/Supplement and foreground cancer atlas consistency.",
            "evidence_to_emphasize": "PDAC Myeloid claim gate, melanoma/breast replication, spatial hotspot QC.",
            "evidence_to_downplay": "Mathematical formalism beyond what is needed for cancer readers.",
            "go_no_go_gate": "No-go without conservative biology language and annotation validation summary.",
        },
        "Nature Cancer": {
            "transfer_status": "high_risk_conditional",
            "trigger_condition": "Use only if additional cancer biology validation becomes available.",
            "positioning_to_use": "Cancer biology insight enabled by a new computational method.",
            "minimum_rewrite": "Add deeper cancer evidence, disease-specific figure order, and stronger external validation.",
            "evidence_to_emphasize": "Biologically interpretable Myeloid signal and replication across cancer datasets.",
            "evidence_to_downplay": "Tool packaging details unless required for reproducibility.",
            "go_no_go_gate": "No-go for public-data-only method package without stronger biology.",
        },
        "Nature Biomedical Engineering": {
            "transfer_status": "fallback_only",
            "trigger_condition": "Use only if the manuscript gains an engineering or deployable-workflow angle.",
            "positioning_to_use": "Reproducible computational workflow for biomedical network analysis.",
            "minimum_rewrite": "Add usability, deployment, validation, and engineering-readiness material.",
            "evidence_to_emphasize": "Workflow robustness, release package, reproducibility, benchmark automation.",
            "evidence_to_downplay": "Unvalidated clinical deployment.",
            "go_no_go_gate": "No-go if clinical/engineering readiness cannot be shown.",
        },
        "Nature Machine Intelligence": {
            "transfer_status": "not_recommended_currently",
            "trigger_condition": "Use only if a real ML primitive and ML benchmark suite are added.",
            "positioning_to_use": "Machine intelligence contribution, not just bioinformatics math.",
            "minimum_rewrite": "Add ML objective, learning benchmark, baselines, and ablation suite.",
            "evidence_to_emphasize": "Only future ML-specific evidence.",
            "evidence_to_downplay": "Sheaf/Hodge alone as machine intelligence.",
            "go_no_go_gate": "Current package should not be submitted here.",
        },
    }

    for row in journal_targets.to_dict(orient="records"):
        journal = str(row.get("journal", "unknown"))
        rule = transfer_rules.get(
            journal,
            {
                "transfer_status": "not_prioritized",
                "trigger_condition": "Use only after manual journal fit review.",
                "positioning_to_use": "To be determined from journal scope.",
                "minimum_rewrite": "Prepare a journal-specific fit audit before transfer.",
                "evidence_to_emphasize": "Evidence must be selected after scope review.",
                "evidence_to_downplay": "Do not overclaim beyond current evidence.",
                "go_no_go_gate": "No-go until journal-specific gate is written.",
            },
        )
        rows.append(
            {
                "priority": row.get("priority", ""),
                "journal": journal,
                "target_role": row.get("target_role", ""),
                "current_position": row.get("current_position", ""),
                "transfer_status": rule["transfer_status"],
                "trigger_condition": rule["trigger_condition"],
                "positioning_to_use": rule["positioning_to_use"],
                "minimum_rewrite": rule["minimum_rewrite"],
                "evidence_to_emphasize": rule["evidence_to_emphasize"],
                "evidence_to_downplay": rule["evidence_to_downplay"],
                "do_not_claim": row.get("do_not_claim", "Do not overclaim beyond current evidence."),
                "go_no_go_gate": rule["go_no_go_gate"],
            }
        )
    return pd.DataFrame(rows)


def build_target_specific_rewrite_actions(journal_targets: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "action_id": "A01",
            "journal": "Nature Methods",
            "when_needed": "Before first submission and after presubmission feedback.",
            "rewrite_action": "Keep the title, abstract and Figure 1 centered on sheaf-valued flow and Hodge decomposition.",
            "required_evidence": "component_recovery.csv; claim_evidence_map.tsv; tool_comparison.csv",
            "stop_condition": "Stop if final blocker report is NO_GO.",
        },
        {
            "action_id": "A02",
            "journal": "Nature Methods",
            "when_needed": "If editors say the work looks like another CCC tool.",
            "rewrite_action": "Move pairwise LR examples later and start with graph-level inconsistency, curl and harmonic circulation.",
            "required_evidence": "09_full_manuscript_draft.md; communication_curl_network.pdf",
            "stop_condition": "Do not add unsupported claims of broad superiority.",
        },
        {
            "action_id": "A03",
            "journal": "Nature Biotechnology",
            "when_needed": "Only after method-scope rejection with platform potential.",
            "rewrite_action": "Emphasize software robustness, reproducibility release, and cross-dataset deployment.",
            "required_evidence": "release/archive_manifest.tsv; pytest report; release_audit.py",
            "stop_condition": "Stop if user-facing platform maturity is still weak.",
        },
        {
            "action_id": "A04",
            "journal": "Molecular Cancer",
            "when_needed": "If transferring to a cancer application journal.",
            "rewrite_action": "Foreground TME communication frustration and retain Myeloid as the only GSE154778 main claim.",
            "required_evidence": "myeloid_claim_readiness_summary.csv; public_tme_sheafsignal_summary.csv",
            "stop_condition": "Stop if sparse categories are needed for the central claim.",
        },
        {
            "action_id": "A05",
            "journal": "Nature Cancer",
            "when_needed": "Only with stronger cancer validation.",
            "rewrite_action": "Add disease-focused validation and move software details to supplement.",
            "required_evidence": "Additional validation not currently present.",
            "stop_condition": "Stop under current public-data-only evidence if no deeper validation is added.",
        },
        {
            "action_id": "A06",
            "journal": "Nature Biomedical Engineering",
            "when_needed": "Only if an engineering/deployment story is added.",
            "rewrite_action": "Add workflow deployment, failure handling, and usability evaluation.",
            "required_evidence": "New deployment/usability evidence.",
            "stop_condition": "Stop if clinical or engineering readiness would be implied without evidence.",
        },
        {
            "action_id": "A07",
            "journal": "Nature Machine Intelligence",
            "when_needed": "Only if a machine-learning primitive is added.",
            "rewrite_action": "Do not relabel sheaf/Hodge bioinformatics as ML; add real ML objective and baselines first.",
            "required_evidence": "New ML benchmark suite not currently present.",
            "stop_condition": "Current SheafSignal package is not an NMI submission.",
        },
    ]
    allowed_journals = set(journal_targets.get("journal", pd.Series(dtype=str)).astype(str))
    if allowed_journals:
        rows = [row for row in rows if row["journal"] in allowed_journals]
    return pd.DataFrame(rows)


def build_do_not_claim_checklist() -> str:
    return """# Do-Not-Claim Checklist

This checklist must be reviewed before every submission, rebuttal, appeal, or
transfer. It protects the manuscript from claims that the current evidence does
not support.

## Forbidden Claims

- Guaranteed acceptance or guaranteed publication.
- Clinical utility, clinical decision support, treatment-response prediction,
  or therapeutic guidance.
- Broad superiority over all cell-cell communication tools.
- Full pretrained NicheNet benchmarking, unless that exact resource is added
  and documented.
- Strong mechanisms from sparse cell types, including unsupported stromal or
  lymphoid categories.
- Pure cell-type interpretation of Visium spots without deconvolution or
  spot-level QC boundaries.
- Causal immune or tumor mechanisms from public observational single-cell data
  alone.

## Allowed Replacements

- "SheafSignal introduces a sheaf/Hodge formulation for graph-level
  communication consistency."
- "Public tumor microenvironment benchmarks support reproducible,
  hypothesis-generating frustration signals."
- "GSE154778 supports Myeloid as a claim-gated computational signal; sparse
  categories are retained as QC or supplementary context."
- "Comparator analyses show alignment and complementarity, not universal
  superiority."

## Final Check

If a sentence would require prospective clinical validation, perturbation
experiments, full pretrained comparator resources, or dense sampling of a sparse
cell type, it cannot be used as a main claim in the current manuscript.
"""


def build_package(
    *,
    output_dir: Path,
    journal_targets: pd.DataFrame,
    final_blockers: pd.DataFrame,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {key: output_dir / name for key, name in OUTPUT_FILES.items()}
    _write_text_atomic(paths["decision_tree"], build_decision_tree(journal_targets, final_blockers))
    _write_text_atomic(
        paths["editorial_rejection_response"],
        build_editorial_rejection_response_template(),
    )
    _write_text_atomic(paths["reviewer_response"], build_reviewer_response_skeleton())
    _write_table_atomic(paths["transfer_package"], build_transfer_package_by_journal(journal_targets))
    _write_table_atomic(paths["rewrite_actions"], build_target_specific_rewrite_actions(journal_targets))
    _write_text_atomic(paths["do_not_claim"], build_do_not_claim_checklist())
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="manuscript/response_transfer")
    parser.add_argument("--journal-targets", default="manuscript/JOURNAL_TARGETS_20_50.tsv")
    parser.add_argument("--final-blockers", default="manuscript/FINAL_SUBMISSION_BLOCKERS.tsv")
    args = parser.parse_args(argv)

    paths = build_package(
        output_dir=Path(args.output_dir),
        journal_targets=_read_tsv(Path(args.journal_targets)),
        final_blockers=_read_tsv(Path(args.final_blockers)),
    )
    for path in paths.values():
        print(f"wrote {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
