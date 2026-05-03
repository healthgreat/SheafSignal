# Author Response From External Intake Report

- Timestamp: `2026-05-04 03:07:39`
- Decision: `AUTHOR_RESPONSE_FROM_INTAKE_READY`
- Overwrote canonical response template: `False`
- Derived rows: `11`
- Pending rows: `0`
- Optional pending rows: `0`

## Derivation Audit

- `han_yan_email` -> `Han Yan email`: `derived` (carrick8862@163.com)
- `equal_contribution_wording` -> `equal contribution note`: `derived` (No equal-contribution statement)
- `author_order_approved` -> `author order`: `derived` (Chongfa Chen, MD; Han Yan, MD, PhD; Yi Miao, MD, PhD)
- `author_order_approved` -> `affiliations`: `derived` (A1 Pancreas Center, The Affiliated BenQ Hospital of Nanjing Medical University, Nanjing, China)
- `credit_roles_approved` -> `CRediT roles`: `derived` (See AUTHOR_CONTRIBUTIONS_CREDIT_TEMPLATE.tsv)
- `funding_statement_approved` -> `funding acquisition`: `derived` (Han Yan National Natural Science Foundation of China Youth Fund; grant number not provided)
- `competing_interests_approved` -> `competing interests`: `derived` (The authors declare no competing interests)
- `ethics_data_use_approved` -> `ethics data-use`: `derived` (Public processed data only; no new human samples; IRB exemption wording to confirm)
- `github_public_release_approved` -> `public GitHub release`: `derived` (Public GitHub release approved.)
- `zenodo_deposition_approved` -> `Zenodo deposition`: `derived` (Zenodo deposition approved.)
- `orcid_ids` -> `ORCID IDs`: `derived` (Yi Miao: https://orcid.org/0000-0003-2542-8663; Han Yan: https://orcid.org/0000-0002-2041-3115)

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
