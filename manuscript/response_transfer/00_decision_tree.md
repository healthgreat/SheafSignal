# SheafSignal Post-Decision Route Tree

## Scope

This document controls what to do after presubmission feedback, editorial
rejection, peer review, or transfer. It is not a guarantee of journal acceptance.
It is a reproducible decision rule for keeping the 20-50 IF route
evidence-bound.

## Current Primary Route

- Primary journal: `Nature Methods`.
- Current position: `best_aligned_high_risk_first_submission`.
- Target role: `primary_methods_target`.
- Local blocker state: 3 blocking item(s), 9 pending non-blocking item(s) in manuscript/FINAL_SUBMISSION_BLOCKERS.tsv.

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
