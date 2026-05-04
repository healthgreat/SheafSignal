# External Beta Review Triage Report

- Decision: `EXTERNAL_BETA_REVIEW_TRIAGED_FATAL_OR_REJECT_CONCERNS`
- Input directory: `external_ai_review_packet/returned_reviews`
- Returned review findings: `317`
- Fatal findings: `21`
- Major findings: `46`
- Minor findings: `6`

## Domain Counts

- `claims`: `5`
- `code_quality`: `60`
- `comparators`: `11`
- `general`: `29`
- `journal_fit`: `34`
- `methods`: `84`
- `reproducibility`: `18`
- `security_privacy`: `9`
- `single_cell`: `42`
- `statistics`: `25`

## Top Parsed Findings

- `comment` / `methods`: # Reviewer 1 — Methods and Novelty
- `comment` / `reproducibility`: external_references_consulted:** None beyond the supplied bundle. Public GitHub (`github.com/healthgreat/SheafSignal`) and the Zenodo DOI (`10.5281/zenodo.20012189`) listed in the routing document **were not fetched** — review is based only on the bundled markdown/TSV evidence.
- `fatal` / `journal_fit`: Review mode:** Aggressive — explicitly simulating Nature Methods first-round desk-reject / referee-stage rejection threshold, as requested.
- `fatal` / `journal_fit`: Reject (not ready for Nature Methods or Nature Biotechnology in current form). Strong major revision required for any 20–30 IF route.
- `comment` / `methods`: The package shows real engineering effort, honest claim gating, and round-on-round hardening. But the two pillars that a high-impact methods journal will scrutinize first — **mathematical novelty of the sheaf framing** and **algorithmic added value over GSP/Hodge baselines on a non-self-fulfilling task** — remain mathematically thin. The Round 2 "formal sheaf" fix is a *labelling* fix, not a *structural* one. A Nature Methods Associate Editor reading this package would, in my judgement, return it without sending out for review, citing insufficient methodological novelty and circular validation.
- `fatal` / `general`: ## 2. Top 5 fatal or near-fatal methods concerns
- `comment` / `methods`: ### F1. The "rank-one cellular sheaf" is mathematically degenerate and equivalent to a standard weighted directed graph with node potentials. **[direct + inferred]
- `comment` / `methods`: `ROUND2_HARDENING_STATUS_2026-05-02.md` defines the rank-one cellular sheaf as:
- `comment` / `methods`: This is precisely the **standard graph coboundary operator δ⁰** acting on a scalar function over vertices, which is the central object of graph signal processing (Sandryhaila & Moura 2013), graph Hodge theory (Jiang et al. 2011 — already cited), and discrete exterior calculus on graphs (Lim 2020 — already cited). With ±1 restriction maps and ℝ stalks, the cellular-sheaf machinery collapses: the sheaf Laplacian equals the ordinary graph Laplacian, the coboundary is the ordinary gradient, and the "sheaf-valued flow" is a scalar edge function. There is **no nontrivial restriction-map structure left to exploit**. The "rank-one cellular sheaf" claim is technically correct but mathematically vacuous — it is the trivial sheaf on a graph.
- `fatal` / `methods`: The bundle's own `SHEAFSIGNAL_NOVELTY_OVERLAP_REPORT.md` already acknowledges this risk: *"Do not claim first-ever use of sheaves in biology"; "presents an integrated sheaf/Hodge workflow for CCC graphs"*. But the manuscript abstract (`SCI_MANUSCRIPT_V2_POLISHED.md` lines 17–19) still leads with *"models cell-cell communication as a sheaf-valued flow over a biological graph"*. A reviewer with a graph-signal-processing or applied-topology background will recognize within a paragraph that the sheaf framing adds no expressive power over a directed weighted graph. **This is the single most likely first-round desk-reject driver at Nature Methods.

## How To Use This

Place returned human or external-AI reviews in the input directory as `.md`, `.txt`, or `.tsv` files, then rerun:

```bash
python scripts/triage_external_beta_reviews.py
```

Fatal or major returned-review items should be transferred into the response matrix before a 20-50 IF submission decision.
Reviewer model metadata is written to `external_ai_review_packet/external_beta_review_reviewer_metadata.tsv` when returned reviews report it.

## Boundary

This triage is keyword-assisted and reviewer-facing. It does not replace human judgment, public GitHub release, Zenodo DOI, author confirmation, or final clean-clone reproduction.
