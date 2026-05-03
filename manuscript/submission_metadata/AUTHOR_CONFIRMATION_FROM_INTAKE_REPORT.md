# Author Response From External Intake Report

- Timestamp: `2026-05-04 00:47:58`
- Decision: `AUTHOR_RESPONSE_FROM_INTAKE_PARTIAL`
- Overwrote canonical response template: `False`
- Derived rows: `4`
- Pending rows: `6`
- Optional pending rows: `1`

## Derivation Audit

- `han_yan_email` -> `Han Yan email`: `derived` (carrick8862@163.com)
- `equal_contribution_wording` -> `equal contribution note`: `derived` (No equal-contribution statement)
- `author_order_approved` -> `author order`: `derived` (Chongfa Chen; Han Yan; Yi Miao)
- `author_order_approved` -> `affiliations`: `derived` (A1 Pancreas Center, The Affiliated BenQ Hospital of Nanjing Medical University)
- `credit_roles_approved` -> `CRediT roles`: `pending` (If not approved, put corrected roles in notes.)
- `funding_statement_approved` -> `funding acquisition`: `pending` (Funding statement derived from intake.)
- `competing_interests_approved` -> `competing interests`: `pending` (Competing interests statement derived from intake.)
- `ethics_data_use_approved` -> `ethics data-use`: `pending` (Ethics/data-use statement derived from intake.)
- `github_public_release_approved` -> `public GitHub release`: `pending` (Required before public release.)
- `zenodo_deposition_approved` -> `Zenodo deposition`: `pending` (Required before DOI release.)
- `orcid_ids` -> `ORCID IDs`: `optional_pending` (Optional ORCID IDs not handled by intake.)

## Next Command When Ready

```bash
python scripts/apply_author_confirmation_response.py --apply
python scripts/check_author_confirmation_preflight.py
```

## Boundary

This script only translates user-provided intake values into an author
response TSV. It does not decide authorship, does not validate email
ownership, does not infer missing declarations, and does not guarantee
journal acceptance.
