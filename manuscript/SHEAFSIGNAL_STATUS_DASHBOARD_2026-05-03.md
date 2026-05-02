# SheafSignal Status Dashboard

Timestamp: 2026-05-03 01:15:42 +08:00

## Direct Status

SheafSignal is a scientifically hardened 20-50 IF methods-manuscript candidate,
but it is not submission-ready yet.

Current readiness snapshot:

- Overall readiness index: 79.3%.
- Scientific/method hardening index: 97.0%.
- Submission infrastructure index: 44.5%.
- Final local decision: NO_GO for formal submission.
- Current live blocker: the public GitHub repository exists at
  `https://github.com/healthgreat/SheafSignal`, and `origin` is configured, but
  the push was rejected because the local token has `repo` but not `workflow`
  scope. GitHub refuses commits that create or update `.github/workflows/ci.yml`
  without `workflow` scope.

Interpretation boundary: these are internal readiness indices, not acceptance
probabilities.

## What Is Finished

- Formal rank-one cellular sheaf implementation is complete.
- Primary decomposition is now based on `sheaf_residual`, not only raw
  communication flow.
- GSE154778 full Scanpy reannotation is frozen as `scanpy_full_v1`.
- Sample-stratified permutation and FDR workflow are implemented.
- The 10,000-permutation confirmatory subset has been executed.
- Primary scRNA comparator scope is locked and passes for GSE72056, GSE154778,
  and GSE176078.
- CellPhoneDB and CellChat are complete inside the primary scRNA comparator
  scope.
- GSE103322 is complete as supplement-grade HNSCC workflow replication.
- Visium is restricted to spot-level hotspot demonstration.
- Claim safety audits show no blocking overclaim language.
- Python environment lock and local clean-export reproduction preflight pass.
- Author metadata placeholders have been replaced by author-provided draft
  metadata, with remaining author confirmations tracked explicitly.
- Novelty/overlap table has been expanded from 5 to 7 comparison classes,
  adding niche/regression methods and spatial neighborhood/domain methods.
- Reviewer reproducibility quickstart has been added to separate tracked-file
  demo checks, public-data checks, release audits, and final DOI/GitHub gates.
- Nature Methods Article formatting audit has been refreshed against official
  source pages on 2026-05-03; abstract is now 121 words and local format status
  is `FORMAT_LOCALLY_READY`.
- Author confirmation packet and checklist have been added for Han Yan email,
  equal-contribution wording, CRediT, funding, COI, ethics/data-use and
  GitHub/Zenodo release approval.
- A Chinese 20-50 IF status brief has been added for user-facing handoff:
  `manuscript/SHEAFSIGNAL_20_50_IF_STATUS_BRIEF_ZH_2026-05-03.md`.
- A release unblocker matrix and Chinese runbook now track the GitHub, Zenodo,
  author-confirmation, and public clean-clone gates:
  `release/RELEASE_UNBLOCKER_MATRIX.tsv` and
  `release/RELEASE_UNBLOCKER_RUNBOOK_ZH.md`.
- External authorization health checks now validate GitHub CLI, the local
  GitHub token, Zenodo token availability, release archive presence, and DOI
  placeholders without printing token contents:
  `release/EXTERNAL_RELEASE_AUTHORIZATION_REPORT.md`.
- A guarded GitHub release publisher has been added:
  `scripts/publish_github_release_after_auth.py`. It refuses to push until the
  local token has both `repo` and `workflow` scopes and writes
  `release/GITHUB_RELEASE_PUBLICATION_REPORT.md`.
- The real GitHub repository URL has been inserted into `CITATION.cff`,
  `pyproject.toml`, and `release/zenodo_deposition_metadata.json`; GitHub URL
  placeholders are now cleared. The remaining release-metadata placeholders are
  Zenodo DOI placeholders.
- Zenodo deposition metadata now synchronizes with `release/archive_manifest.tsv`:
  archive size, SHA256, file count, uncompressed manifest size, and the public
  GitHub URL are aligned before DOI upload.

## What Is Blocking Submission

| Blocker | Current status | Why it matters | Owner |
|---|---|---|---|
| GitHub public repository | Public repo created and `origin` configured; branch push blocked by missing token `workflow` scope | Journals and reviewers need public, citable code | User must regenerate token with `repo` + `workflow`; Codex handles push/tag/release |
| Zenodo DOI | Not minted | Data/code availability needs a permanent DOI | User Zenodo login/token once; Codex handles metadata insertion |
| Public clean-clone reproduction | Pending | Local clean export is not enough for final reproducibility | Codex after GitHub/Zenodo identifiers are real |
| Final journal metric/CAS/warning check | Pending submission-day check | IF, CAS zone, and warning status can change | Codex checks again before submission |
| Corresponding author confirmation | Draft metadata filled | COI, CRediT, funding, and ethics text need author approval | User/corresponding authors |

## Distance To A 20-50 IF SCI Submission

Short answer: the project is close on the scientific and software side, but
blocked by external release infrastructure.

Practical distance:

- To a realistic 20-50 IF submission package: one release/metadata cycle away,
  after a GitHub token with `repo` + `workflow` scope and a Zenodo DOI are
  available.
- To Nature Methods as the primary methods target: technically plausible as a
  stretch submission after GitHub, Zenodo, and clean-clone checks, but still
  high risk.
- To Nature Biotechnology: stretch only; would benefit from stronger platform
  framing and more external adoption or independent user feedback.
- To Molecular Cancer or Nature Cancer: possible only if the biological cancer
  story is strengthened without overclaiming computational signals.

## Recommended Journal Route

| Priority | Journal | Current role | 2024 JIF basis in current audit | Current fit |
|---|---|---|---|---|
| 1 | Nature Methods | Primary methods target | 32.1 JIF; 51.7 five-year JIF | Best aligned, high risk |
| 2 | Nature Biotechnology | Stretch methods platform | 41.7 JIF; 59.5 five-year JIF | Stretch only |
| 3 | Molecular Cancer | Cancer application fallback | 33.9 JIF; 35.9 five-year JIF | Possible if cancer story strengthens |
| 4 | Nature Cancer | Cancer biology stretch | 28.5 JIF | Needs stronger biology validation |
| 5 | Nature Biomedical Engineering | Fallback only | 26.6 JIF | Needs stronger engineering/translation angle |
| 6 | Nature Machine Intelligence | Not recommended currently | 23.9 JIF | Needs real ML novelty beyond sheaf/Hodge workflow |

CAS zone and warning-list status remain official submission-day checks.

## Gantt Chart

```mermaid
gantt
    title SheafSignal 20-50 IF Route: Current Position On 2026-05-03
    dateFormat  YYYY-MM-DD

    section Completed Scientific Hardening
    Formal sheaf implementation                    :done, 2026-05-02, 1d
    Primary Hodge on sheaf residual                :done, 2026-05-02, 1d
    GSE154778 full Scanpy reannotation             :done, 2026-05-02, 1d
    Sample-stratified permutation and FDR          :done, 2026-05-02, 1d
    10000-permutation confirmatory subset          :done, 2026-05-02, 1d
    Primary scRNA comparator scope                 :done, 2026-05-02, 1d
    CellChat and CellPhoneDB primary imports       :done, 2026-05-02, 1d
    GSE103322 supplement-grade replication         :done, 2026-05-02, 1d
    Claim-language and Visium hotspot gates        :done, 2026-05-02, 1d
    Environment lock and local clean-export check  :done, 2026-05-02, 1d
    Author metadata draft fill                     :done, 2026-05-02, 1d
    GitHub CLI portable install                    :done, 2026-05-02, 1d
    Novelty overlap expansion                      :done, 2026-05-03, 1d
    Reviewer reproducibility quickstart            :done, 2026-05-03, 1d
    Nature Methods local official format audit     :done, 2026-05-03, 1d
    Author confirmation packet                     :done, 2026-05-03, 1d
    Release unblocker matrix and runbook           :done, 2026-05-03, 1d
    External authorization health check            :done, 2026-05-03, 1d
    Guarded GitHub release publisher              :done, 2026-05-03, 1d
    GitHub URL metadata finalization               :done, 2026-05-03, 1d
    Zenodo metadata/archive sync                   :done, 2026-05-03, 1d

    section Current Submission Blockers
    Regenerate GitHub token with workflow scope    :crit, active, 2026-05-03, 1d
    Push branch to public GitHub and tag release   :crit, 2026-05-03, 1d
    Zenodo DOI minting                             :crit, 2026-05-04, 1d
    DOI and GitHub URL metadata insertion          :crit, 2026-05-04, 1d
    Public clean-clone reproduction preflight      :crit, 2026-05-05, 1d
    Final submission package regeneration          :crit, 2026-05-05, 1d

    section High-Value Strengthening
    External beta review return collection         :2026-05-06, 7d
    Final CAS and warning-list check               :2026-05-08, 1d
    Presubmission inquiry package refresh          :2026-05-09, 2d
    Journal-specific formatting pass               :2026-05-10, 1d
```

## What The User Must Still Do

The user does not need to run bioinformatics code manually. The remaining user
actions are account/author-confirmation steps that Codex cannot legitimately
bypass:

1. Regenerate a GitHub token with both `repo` and `workflow` scopes, or complete
   GitHub browser authorization for GitHub CLI.
2. The public GitHub repository is already created:
   `https://github.com/healthgreat/SheafSignal`.
3. Complete Zenodo login or provide a local token file path outside the repo.
4. Confirm Han Yan's email, COI, CRediT, funding, and ethics/data-use wording.
   A dedicated packet is available at
   `manuscript/submission_metadata/AUTHOR_CONFIRMATION_PACKET.md`.

Codex can handle the rest: pushing, tagging, release metadata updates, DOI
insertion, clean-clone tests, final reports, and submission package regeneration.

## What Can Be Added To Improve 20-50 IF Defensibility

- Returned external beta review from 2-3 independent computational biology
  readers.
- A short user-facing tutorial notebook that reproduces the demo and one public
  benchmark subset. Current status: a reviewer quickstart document now covers
  demo, benchmark smoke-test, public download validation, and clean-export
  preflight commands.
- A final novelty table cross-check against graph signal processing, Hodge
  omics, sheaf-theoretic biology, niche/regression, and spatial neighborhood
  methods. Current status: expanded to 7 classes; citation placeholders still
  require author/literature verification.
- Optional Visium deconvolution or histology/pathology annotation if the spatial
  story is promoted beyond hotspot demonstration.
- Optional additional cancer dataset only if it can be processed with the same
  reproducibility and annotation gates.

## Bottom Line

SheafSignal should not be submitted today. It is, however, close to a defensible
20-50 IF submission package once GitHub, Zenodo, and final clean-clone release
checks are completed.

## Live GitHub Authorization Note

The file `D:\secrets\github_token.txt` exists and GitHub API accepts it for
`healthgreat`, but the token scopes are currently:

```text
gist, read:org, repo
```

The missing scope is:

```text
workflow
```

Without `workflow`, GitHub refuses to push commits that include
`.github/workflows/ci.yml`. Regenerate the token with `repo` and `workflow`,
overwrite `D:\secrets\github_token.txt`, and rerun:

```bash
python scripts/check_external_release_authorization.py
```

## Latest Non-Release Strengthening

On 2026-05-03, the novelty/overlap package was strengthened:

- `manuscript/novelty_overlap/SHEAFSIGNAL_NOVELTY_OVERLAP_TABLE.tsv`
  now compares 7 method classes.
- `manuscript/novelty_overlap/SHEAFSIGNAL_NOVELTY_OVERLAP_REPORT.md`
  now states the safest one-sentence novelty claim.
- `manuscript/presubmission_inquiry/03_novelty_evidence_matrix.tsv`
  now reflects the completed primary scRNA comparator scope including
  CellPhoneDB and CellChat.

This improves reviewer defensibility, but it does not remove the GitHub/Zenodo
release blockers.
