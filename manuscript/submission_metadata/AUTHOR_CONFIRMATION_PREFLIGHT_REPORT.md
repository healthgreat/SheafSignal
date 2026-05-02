# Author Confirmation Preflight Report

- Decision: `AUTHOR_CONFIRMATION_BLOCKED`
- Blocking author confirmations: `2`
- Pending author confirmations: `8`
- Optional author metadata items: `1`
- Passed confirmations: `0`
- Review-needed rows: `0`

## Blocking Author Confirmations

- `Han Yan email`: `missing_email` -> Provide final email for corresponding author Han Yan
- `equal contribution note`: `Equal contribution with Yi Miao; user text also contained YM and YH` -> Confirm exact wording, likely HY and YM rather than YM and YH

## Pending Author Confirmations

- `author order`: `draft_pending_author_confirmation` -> Confirm final author order and degrees
- `affiliations`: `draft_pending_author_confirmation` -> Confirm institution names and numbering
- `CRediT roles`: `draft_pending_author_confirmation` -> Approve or correct CRediT assignments
- `funding acquisition`: `needs_author_confirmation` -> Confirm no funding role or provide funding authors/grants
- `competing interests`: `draft_pending_author_confirmation` -> Confirm or provide disclosure
- `ethics data-use`: `draft_pending_author_confirmation` -> Confirm institutional/journal wording
- `public GitHub release`: `external_release_confirmation` -> Confirm public repository release is allowed
- `Zenodo deposition`: `external_release_confirmation` -> Confirm Zenodo deposition contents and restrictions

## Optional Metadata

- `ORCID IDs`: Optional: provide ORCID IDs if authors want them included

## Minimal Author Reply Needed

```text
Han Yan email:
Equal contribution wording:
CRediT roles approved: yes/no
Funding statement approved or grant details:
Competing interests approved: yes/no
Ethics/data-use wording approved: yes/no
Public GitHub and Zenodo release approved: yes/no
```

## Boundary

This report checks author-owned submission facts. It does not infer or
fabricate author confirmations, does not change scientific claims, and
does not guarantee journal acceptance.
